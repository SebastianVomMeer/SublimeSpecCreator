import sublime, sublime_plugin, os.path, re
from subprocess import call, Popen


class ActionContextHandler(sublime_plugin.EventListener):
    def on_query_context(self, view, key, op, operand, match_all):
        print "on_query_context"
        print view.find("kernel", 0)

    def on_load(self, view):
        print "on_load"
        print view.find("kernel", 0)

    def on_modified(self, view):
        print "on_modified"
        print view.find("kernel", 0)

    def on_activated(self, view):
        print "on_activated"
        print view.find("kernel", 0)

sublime.active_window().open_file("/var/log/syslog")
