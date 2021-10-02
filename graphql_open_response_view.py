import sublime
import sublime_plugin
import os.path
from .src.graphql_view_manager import GraphqlViewManager


class GraphqlOpenResponseViewCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        window = self.view.window()
        settings = sublime.load_settings("graphql_playground.sublime-settings")
        _args = { "force": True }
        _args.update(args)

        if window is None:
            return

        # settings = sublime.load_settings("graphql_playground.sublime-settings")

        # fileTitle = "GraphQL: %s" % args['operationName']
        responseView = GraphqlViewManager.get(self.view.id())

        filePath = self.view.file_name()
        fileName = None
        # variablesFile = None
        # print('aaaa')
        # print(responseView)
        # print(GraphqlViewManager.all())

        if filePath:
            fileName = os.path.splitext(os.path.basename(filePath))[0]
            # variablesFile = os.path.join(os.path.dirname(filePath), "%s.var.json" % (fileName))

        if fileName and responseView is None:
            responseView = GraphqlViewManager.get(fileName)
            GraphqlViewManager.add(self.view.id(), responseView)

        if fileName and responseView is None and _args['force']:
            responseView = window.new_file()
            responseView.set_scratch(True)
            responseView.assign_syntax(settings.get('json_syntax', 'Packages/JSON/JSON.sublime-syntax'))
            GraphqlViewManager.add(self.view.id(), responseView)
            GraphqlViewManager.add(fileName, responseView)

        # if args['operationName'] is None:
        #     fileTitle = "GraphQL"

        sheets = [self.view.sheet(), None]

        if responseView is not None:
            sheets = sheets + [responseView.sheet()]

        # file.set_name(fileTitle)

        # if responseView:
        #     fsheet = responseView.sheet()
        #     if fsheet:
        #         sheets.append(fsheet)

        # vsheet = self.view.sheet()
        # if vsheet:
        #     sheets.append(vsheet)

        # if variablesFile:
        #     vview = self.getVariables(variablesFile)

            # if vview['view'] and vview['sheet']:
            #     sheets.append(vview['sheet'])

        sheets = list(set(sheets + window.selected_sheets()))
        window.select_sheets(filter(None, sheets))

    def getVariables(self, file):
        window = self.view.window()

        if window is None:
            return { "view": None, "sheet": None }

        view = window.find_open_file(file)
        sheet = None

        if view:
            sheet = view.sheet()

        return { "view": view, "sheet": sheet }

    def is_visible(self):
        return False
