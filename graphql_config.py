import sublime
import sublime_plugin
import os.path


class GraphqlCreateConfigCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()

        if window is None:
            return

        windowVariables = window.extract_variables()
        targetDirectory = None
        configView = None

        if "folder" in windowVariables:
            targetDirectory = windowVariables['folder']

        if targetDirectory is None and "file_path" in windowVariables:
            targetDirectory = windowVariables['file_path']

        folders = window.folders()

        if targetDirectory is None and len(folders) > 0:
            targetDirectory = folders[0]

        if targetDirectory is None:
            configView = window.new_file()
            configView.set_name(".graphqlrc.json")

        if targetDirectory is not None:
            configView = window.open_file(os.path.join(targetDirectory, ".graphqlrc.json"))

        if configView is not None and configView.size() <= 0:
            sublime.set_timeout(lambda: configView and configView.run_command("insert", { "characters": "{\n\"schema\": \"\"\n}" }), 200)


def readGraphqlConfig(view):
        window = view.window()

        if window is None:
            return

        windowVariables = window.extract_variables()
        targetDirectory = None

        if "folder" in windowVariables:
            targetDirectory = windowVariables['folder']

        if targetDirectory is None and "file_path" in windowVariables:
            targetDirectory = windowVariables['file_path']

        folders = window.folders()

        if targetDirectory is None and len(folders) > 0:
            targetDirectory = folders[0]

        if targetDirectory is None:
            return

        configFile = os.path.join(targetDirectory, ".graphqlrc.json")

        if os.path.exists(configFile) is False:
            return

        fh = open(configFile, "r")
        graphqlConfig = sublime.decode_value(fh.read())
        fh.close()

        return graphqlConfig

