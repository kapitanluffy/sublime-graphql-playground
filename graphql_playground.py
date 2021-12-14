import sublime
import sublime_plugin
import requests
import os.path
import re
from .src.graphql_view_manager import GraphqlViewManager
from .graphql_config import readGraphqlConfig
from random import randint

CONNID = None
PATTERN = r'^ *(?:query|mutation) *(\w*) *'


def getQueryVariablesFile(view):
    filePath = view.file_name()

    if filePath is None:
        return None

    fileName = os.path.splitext(
        os.path.basename(filePath)
    )
    filename = "%s.var.json" % (fileName[0])

    return os.path.join(os.path.dirname(filePath), filename)


class GraphqlRunQueryCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        global CONNID

        data = {
            "operationName": args['operationName'] if args['operationName'] != "" else None,
            "query": args['query'],
            "variables": args['variables'],
        }

        if "config" not in args:
            return

        CONNID = randint(1, 100)
        sublime.set_timeout_async(lambda: self.sendRequest(data, args, CONNID))

    def sendRequest(self, data, args, conn):
        string = "// Error occurred"
        resp = None
        settings = sublime.load_settings("graphql_playground.sublime-settings")

        if settings.get('debug'):
            _data = sublime.encode_value(data)
            print("-- Grapqhl Playground debug::start --")
            print("\t%s" % (_data))
            print("-- Grapqhl Playground debug::end --")

        try:
            if isinstance(args['config']['schema'], list):
                schema = args['config']['schema']
                for value in schema[0].keys():
                    schema_url = value

                headers = schema[0][schema_url]['headers']
                resp = requests.post(schema_url, headers=headers, json=data)
            else:
                resp = requests.post(args['config']['schema'], json=data)
            string = resp.text
        except Exception as e:
            print("Graphql Playground error:", e)

        try:
            if resp is not None:
                string = sublime.encode_value(resp.json(), True)
        except Exception as e:
            print("Graphql Playground error:", e)

        self.view.run_command("graphql_print_response", { "content": string, "connection": conn })


class GraphqlPrintResponseCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        global CONNID

        if "content" not in args:
            return

        if args["connection"] != CONNID:
            return

        self.view.replace(
            edit,
            sublime.Region(0, self.view.size()),
            args['content']
        )


class GraphqlPrepareViewCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        operationName = args['operationName']

        if args['operationName'] is None:
            operationName = "Query"

        if self.view.size() <= 0:
            self.view.replace(edit, sublime.Region(0, self.view.size()), "// Running %s..." % (operationName))

        window = self.view.window()
        if window is not None:
            window.status_message("❄ Running %s..." % (operationName))

        self.view.run_command("graphql_run_query", args)

    def is_visible(self):
        return False


class GraphqlOpenViewCommand(sublime_plugin.WindowCommand):
    def run(self, **args):
        view = next(v for v in self.window.views() if v.id() == args['view'])

        fileTitle = "GraphQL: %s" % args['operationName']
        if args['operationName'] is None:
            fileTitle = "GraphQL"

        view.run_command("graphql_open_response_view", { "force": True })
        responseView = GraphqlViewManager.get(view.id())

        if responseView is None:
            return

        sheets = [view.sheet(), None]
        variables = {}

        variablesFile = getQueryVariablesFile(view)

        if variablesFile is not None:
            vview = self.window.find_open_file(variablesFile)

            if vview:
                view.run_command("graphql_open_query_variables", { "force": False })

                variables = sublime.decode_value(
                    vview.substr(
                        sublime.Region(0, vview.size())
                    )
                )

            if variables == {} and os.path.exists(variablesFile):
                fh = open(variablesFile, 'r')
                variables = sublime.decode_value(fh.read())
                fh.close()

        responseView.set_name(fileTitle)
        sheets = sheets + [responseView.sheet()]

        query = view.substr(sublime.Region(0, view.size()))
        graphqlConfig = readGraphqlConfig(view)

        responseView.run_command("graphql_prepare_view", {
            "operationName": args['operationName'],
            "query": query,
            "variables": variables,
            "config": graphqlConfig
        })

        sheets = list(set(sheets + self.window.selected_sheets()))
        self.window.select_sheets(filter(None, sheets))
        self.window.focus_view(view)

    def is_visible(self):
        return False


class GraphqlBuildAnnotationsCommand(sublime_plugin.TextCommand):
    ANNOTATIONS_KEY = 'graphql_runner_annotations'

    def __init__(self, view):
        super().__init__(view)
        self.keys = []

    def run(self, edit, **args):
        syntax = self.view.syntax()

        if not syntax or syntax.name != "GraphQL":
            return

        for k in self.keys:
            self.view.erase_regions(k)
        self.keys = []

        sublime.set_timeout(lambda: self._build_annotations(), 1000)

    def _build_annotations(self):
        matches = []
        regions = self.view.find_all(PATTERN, sublime.IGNORECASE, "$1", matches)
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

        for [index, operationName] in enumerate(matches):
            key = "%s_%s" % (self.ANNOTATIONS_KEY, index)
            self.keys.append(key)

            if operationName == "":
                operationName = None

            query = sublime.encode_value({
                "operationName": operationName,
                "view": self.view.id()
            })

            cmd = "subl:graphql_open_view %s" % (query)
            annotations = html.format(cmd=cmd)

            self.view.add_regions(key, [regions[index]], "", "", flags, [annotations], annotation_styles["foreground"])


class GraphqlQuickRunQueryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selection = self.view.sel()

        if len(selection) <= 0:
            return

        line = self.view.line(selection[0])
        match = re.match(PATTERN, self.view.substr(line))
        upperLines = self.view.lines(sublime.Region(0, line.a))
        upperLines.reverse()

        if match is None:
            for u in upperLines:
                match = re.match(PATTERN, self.view.substr(u))

                if match is not None:
                    break

        if match is None:
            return

        w = self.view.window()

        if w is None:
            return

        w.run_command("graphql_open_view", {
            "operationName": match.group(1),
            "view": self.view.id()
        })


class GraphqlPlaygroundViewListener(sublime_plugin.ViewEventListener):
    @classmethod
    def applies_to_primary_view_only(cls):
        return True

    def _build_annotations(self):
        syntax = self.view.syntax()
        if not syntax or syntax.name != "GraphQL":
            return

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
        if not syntax or syntax.name != "GraphQL":
            return

        self.view.run_command("graphql_open_response_view", { "force": False })
        self.view.run_command("graphql_open_query_variables", { "force": False })

    def on_query_context(self, key, operator, operand, match_all):
        if not key.startswith("graphql_playground."):
            return None

        syntax = self.view.syntax()

        if syntax and operator == sublime.OP_EQUAL:
            return (syntax.name == "GraphQL") == operand

        if syntax and operator == sublime.OP_NOT_EQUAL:
            return (syntax.name == "GraphQL") == operand

        return False

    def on_close(self):
        GraphqlViewManager.removeView(self.view)
