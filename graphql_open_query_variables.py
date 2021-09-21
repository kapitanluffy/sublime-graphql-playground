import sublime
import sublime_plugin
import os.path


class GraphqlOpenQueryVariablesCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        window = self.view.window()
        _args = { "force": True }
        _args.update(args)

        if window is None:
            return

        path = self.view.file_name()

        if path is None:
            return

        n = os.path.splitext(os.path.basename(path))
        filename = "%s.var.json" % (n[0])
        variablesFile = os.path.join(os.path.dirname(path), filename)
        variablesView = window.find_open_file(variablesFile)

        if _args['force'] is False:
            return

        if variablesView is None and os.path.exists(variablesFile) is False:
            variablesView = window.new_file()
            variablesView.set_name(filename)
            variablesView.replace(edit, sublime.Region(0, self.view.size()), "{}")

        if variablesView is None and os.path.exists(variablesFile):
            variablesView = window.open_file(variablesFile)

        if variablesView:
            sheets = [self.view.sheet(), variablesView.sheet(), None] + window.selected_sheets()
            window.select_sheets(filter(None, sheets))
