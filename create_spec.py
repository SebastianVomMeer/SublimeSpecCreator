import sublime, sublime_plugin, os.path, re
from subprocess import call

class CreateSpecCommand(sublime_plugin.TextCommand):

    invalid_method_names = ["", "def", "self", "self.", "class", "module", "if", "end"]
    
    def run(self, edit):
        view = self.view
        region = view.sel()[0]
        if region.empty():
            view.window().run_command('find_under_expand')
            region = view.sel()[0]
        method_name = view.substr(view.word(region)).strip()
        if method_name in self.invalid_method_names:
            sublime.status_message("Select a valid method name to create a spec.")
            return
        spec_appender = SpecAppenderFactory().for_method_name_and_file_name(view.substr(region), view.file_name())
        if spec_appender is None:
            sublime.status_message("Failed to determine appropriate spec file for this type of file.")
            return
        spec_appender.create_file_if_missing()
        spec_appender.append_spec()
        new_view = sublime.active_window().open_file(spec_appender.spec_file.file_path())


class SpecAppenderFactory:
    
    def for_method_name_and_file_name(self, method_name, file_path):
        for appender_type in [ControllerSpecAppender, ModelSpecAppender, LibSpecAppender, MailerSpecAppender]:
            if "/app/" + appender_type.component_dir + "/" in file_path:
                return self.for_appender_type(appender_type, method_name, file_path)
        return None 

    def for_appender_type(self, appender_type, method_name, file_path):
        component_dir = appender_type.component_dir
        self.extract_path_components(file_path, component_dir)
        spec_file = SpecFile(self.project_dir, component_dir, self.namespace_dir, self.file_name)
        return appender_type(method_name, self.file_name, spec_file, self.namespace_dir)

    def extract_path_components(self, file_path, component_dir):
        remaining_path, self.file_name = os.path.split(file_path)
        remaining_path, top_dir = os.path.split(remaining_path)
        if top_dir != component_dir:
            self.namespace_dir = top_dir
            remaining_path = os.path.split(remaining_path)[0]
        else:
            self.namespace_dir = ""
        self.project_dir = os.path.split(remaining_path)[0]


class AbstractSpecAppender:

    def __init__(self, method_name, file_name, spec_file, namespace_dir):
        self.method_name = method_name
        self.file_name = file_name
        self.spec_file = spec_file
        self.namespace_dir = namespace_dir

    def create_file_if_missing(self):
        if not self.spec_file.exists():
            self.spec_file.create_for_subject(self.subject_description())

    def append_spec(self):
        self.spec_file.append_named_describe_block(self.spec_description())

    def spec_description(self):
        if self.method_name.startswith("self."):
            return "::" + self.method_name.replace("self.", "")
        else:
            return "#" + self.method_name

    def subject_description(self):
        name, extenion = os.path.splitext(self.file_name)
        class_name = self.underscore_to_camelcase(name)
        if self.namespace_dir != "":
            class_name = self.underscore_to_camelcase(self.namespace_dir) + "::" + class_name
        return class_name

    def underscore_to_camelcase(self, word):
        return ''.join(x.capitalize() or '_' for x in word.split('_'))


class ControllerSpecAppender(AbstractSpecAppender):
    component_dir = "controllers"


class ModelSpecAppender(AbstractSpecAppender):
    component_dir = "models"


class LibSpecAppender(AbstractSpecAppender):
    component_dir = "lib"


class MailerSpecAppender(AbstractSpecAppender):
    component_dir = "mailers"


class SpecFile:

    spec_dir = "spec"
    file_name_suffix = "_spec"

    def __init__(self, project_dir, component_dir, namespace_dir, original_file_name):
        self.project_dir = project_dir
        self.component_dir = component_dir
        self.namespace_dir = namespace_dir
        self.original_file_name = original_file_name

    def file_name(self):
        name, extension = os.path.splitext(self.original_file_name)
        return name + self.file_name_suffix + extension

    def file_path(self):
        return os.path.join(self.project_dir, self.spec_dir, self.component_dir, self.namespace_dir, self.file_name())

    def exists(self):
        return os.path.exists(self.file_path())

    def create_for_subject(self, subject_description):
        call(["mkdir", "-p", os.path.split(self.file_path())[0]])
        file_pointer = open(str(self.file_path()), 'a')
        file_pointer.write(self.content_for_new_file(subject_description))
        file_pointer.flush()
        file_pointer.close()

    def content_for_new_file(self, subject_description):
        return ("require 'spec_helper'\n"
                "\n"
                "describe " + subject_description + " do\n"
                "end")

    def append_named_describe_block(self, name):
        file_pointer = open(str(self.file_path()), 'r')
        lines = []
        end_marker_matcher = re.compile("^end\s*$")
        for line in file_pointer:
            if (end_marker_matcher.match(line)):
                lines.append("\n")
                lines.append("  describe '" + name + "' do\n")
                lines.append("    \n")
                lines.append("  end\n")
                lines.append("\n")
            lines.append(line)
        file_pointer.close()


        file_pointer = open(str(self.file_path()), 'w')
        for line in lines:
            file_pointer.write(line)
        file_pointer.close()
