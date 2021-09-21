import sublime
import sublime_plugin
from threading import Timer
import requests
import os.path
from .src.graphql_view_manager import GraphqlViewManager
from .graphql_config import readGraphqlConfig


class GraphqlRunQueryCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        data = {
            "operationName": args['operationName'],
            "query": args['query'],
            "variables": args['variables'],
        }

        graphqlConfig = readGraphqlConfig(self.view)

        if graphqlConfig is None:
            return

        resp = requests.post(graphqlConfig['schema'], json=data)

        string = resp.text

        try:
            string = resp.json()
        except:
            print("Invalid JSON response")

        self.view.replace(
            edit,
            sublime.Region(0, self.view.size()),
            sublime.encode_value(string, True)
        )


class GraphqlPrepareViewCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        operationName = args['operationName']

        if args['operationName'] is None:
            operationName = "Query"

        if self.view.size() <= 0:
            self.view.replace(edit, sublime.Region(0, self.view.size()), "// Running %s..." % (operationName))

        sublime.set_timeout_async(lambda: self.view.run_command("graphql_run_query", args), 500)

    def is_visible(self):
        return False


class GraphqlOpenViewCommand(sublime_plugin.WindowCommand):
    def run(self, **args):
        view = next(v for v in self.window.views() if v.id() == args['view'])
        settings = sublime.load_settings("graphql_playground.sublime-settings")

        fileTitle = "GraphQL: %s" % args['operationName']
        if args['operationName'] is None:
            fileTitle = "GraphQL"

        view.run_command("graphql_open_response_view", { "force": True })
        responseView = GraphqlViewManager.get(view.id())

        if responseView is None:
            return

        sheets = [view.sheet(), None]

        vview = self.window.find_open_file(args['variablesFile'])
        variables = {}

        if vview:
            view.run_command("graphql_open_query_variables", { "force": False })

            variables = sublime.decode_value(
                vview.substr(
                    sublime.Region(0, vview.size())
                )
            )

        if variables == {} and os.path.exists(args['variablesFile']):
            fh = open(args['variablesFile'], 'r')
            variables = sublime.decode_value(fh.read())
            fh.close()

        responseView.set_name(fileTitle)
        sheets = sheets + [responseView.sheet()]

        print("xxxxxx")
        responseView.run_command("graphql_prepare_view", {
            "operationName": args['operationName'],
            "query": args['query'],
            "variables": variables,
        })

        sheets = list(set(sheets + self.window.selected_sheets()))
        self.window.select_sheets(filter(None, sheets))

    def is_visible(self):
        return False


class GraphqlBuildAnnotationsCommand(sublime_plugin.TextCommand):
    ANNOTATIONS_KEY = 'graphql_runner_annotations'
    keys = []

    def run(self, edit, **args):
        syntax = self.view.syntax()

        if (syntax != None and syntax.name != "GraphQL"): return

        for k in self.keys:
            self.view.erase_regions(k)

        sublime.set_timeout(lambda: self._build_annotations(), 1000)

    def _build_annotations(self):
        matches = [];
        regions = self.view.find_all(r'(?:query|mutation) (\w*) ?', sublime.IGNORECASE, "$1", matches);
        flags = sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
        annotation_styles = self.view.style_for_scope("region.purplish")

        html = """
        <style>
            html, div {{
                padding: 0;
                margin: 0;
                border: 0;
            }}
            .gql-run-label {{
                color: var(--accent);
            }}
        </style>
        <body id='graphql-run-box'>
            <a class=\"gql-run-label\" href='{cmd}'>Run Query</a>
        </body>
        """

        path = self.view.file_name()
        varFile = None
        baseFileName = None

        if path:
            n = os.path.splitext(os.path.basename(path))
            filename = "%s.var.json" % (n[0])
            varFile = os.path.join(os.path.dirname(path), filename)
            baseFileName = n[0]

        for [index, operationName] in enumerate(matches):
            key = "%s_%s" % (self.ANNOTATIONS_KEY, index)
            self.keys.append(key)

            if operationName == "":
                operationName = None

            query = sublime.encode_value({
                "operationName": operationName,
                "query": self.view.substr(sublime.Region(0, self.view.size())),
                "view": self.view.id(),
                "variablesFile": varFile,
                "scriptName": baseFileName
            })

            cmd = "subl:graphql_open_view %s" % (query)
            annotations = html.format(cmd=cmd)

            self.view.add_regions(key, [regions[index]], "", "", flags, [annotations], annotation_styles["foreground"])


class GraphqlAutoQueryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selection = self.view.sel()
        expand = self.view.expand_by_class(selection[0].a, sublime.CLASS_EMPTY_LINE)

        selection.clear()
        selection.add(expand)


class GraphqlPlaygroundViewListener(sublime_plugin.ViewEventListener):
    @classmethod
    def applies_to_primary_view_only(cls):
        return True

    def _build_annotations(self):
        syntax = self.view.syntax()
        if (syntax != None and syntax.name != "GraphQL"): return

        graphqlConfig = readGraphqlConfig(self.view)

        if graphqlConfig is None:
            print("GraphqlPlayground: No .graphqlrc.json found")
            return

        self.view.run_command("graphql_build_annotations")

    def on_load(self):
        self._build_annotations()

    def on_modified(self):
        self._build_annotations()

    def on_activated(self):
        syntax = self.view.syntax()
        if (syntax != None and syntax.name != "GraphQL"): return

        self.view.run_command("graphql_open_response_view", { "force": False })
        self.view.run_command("graphql_open_query_variables", { "force": False })

    def on_close(self):
        GraphqlViewManager.removeView(self.view)

def plugin_loaded():
    print("GraphQL loaded")
