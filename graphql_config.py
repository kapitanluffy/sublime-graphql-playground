import sublime
import sublime_plugin
import os.path
import os
import re
import toml
import yaml

CONFIG_PATTERN = r'(\.graphqlrc|graphql\.config)(\.json|\.toml|\.yaml|\.yml|)'

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
            configView.set_name(".graphqlrc")

        if targetDirectory is None:
            return

        configFile = os.path.join(targetDirectory, ".graphqlrc")
        configView = window.open_file(configFile, sublime.CLEAR_TO_RIGHT)

        if os.path.exists(configFile) is False:
            sublime.set_timeout(lambda: configView and configView.run_command("insert", { "characters": "{\n\"schema\": \"\"\n}" }), 200)

        window.select_sheets(filter(None, [configView.sheet()]))


def readGraphqlConfig(view):
    window = view.window()

    if window is None:
        return

    configFile = None
    graphqlConfig = None
    openFolders = window.folders()
    filePath = view.file_name()

    if filePath is not None:
        openFolders.append(os.path.dirname(filePath))

    for d in openFolders:
        items = os.listdir(d)
        try:
            f = next(i for i in items if re.match(CONFIG_PATTERN, i))
            configFile = os.path.join(d, f)
            break
        except:
            pass

    if configFile is None:
        return

    filename, extension = os.path.splitext(configFile)
    fh = open(configFile, "r")

    if extension == ".toml":
        graphqlConfig = toml.load(fh)

    if extension == ".json":
        graphqlConfig = sublime.decode_value(fh.read())

    if extension == ".yaml" or extension == ".yml" or extension == "":
        graphqlConfig = yaml.safe_load(fh.read())

    fh.close()
    return graphqlConfig
