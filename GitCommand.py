import os
import subprocess

import sublime
import sublime_plugin


def exec_command(command_string):
    p = subprocess.Popen(command_string, shell=True, bufsize=1024, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()

    stdout = p.stdout
    stderr = p.stderr

    return '\n'.join([stdout.read(), stderr.read()])


def show_results(window, results):
    output_view = window.get_output_panel('git')
    window.get_output_panel('git')
    window.run_command('show_panel', {'panel': 'output.git'})
    output_view.set_read_only(False)

    edit = output_view.begin_edit()

    output_view.insert(edit, output_view.size(), results)
    output_view.end_edit(edit)
    output_view.set_read_only(True)


class GitStatusCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        os.chdir(os.path.dirname(self.view.file_name()))
        return os.system('git rev-parse 2> /dev/null > /dev/null') == 0

    def run(self, edit):
        os.chdir(os.path.dirname(self.view.file_name()))
        show_results(self.view.window(), exec_command('git status'))


class GitDiffCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        os.chdir(os.path.dirname(self.view.file_name()))
        return os.system('git rev-parse 2> /dev/null > /dev/null') == 0

    def run(self, edit):
        os.chdir(os.path.dirname(self.view.file_name()))
        show_results(self.view.window(), exec_command('git diff'))


class GitAddCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        os.chdir(os.path.dirname(self.view.file_name()))
        return os.system('git rev-parse 2> /dev/null > /dev/null') == 0

    def run(self, edit):
        cmd = 'git add %s' % self.view.file_name()
        os.chdir(os.path.dirname(self.view.file_name()))
        exec_command(cmd)
        show_results(self.view.window(), cmd)


class GitRmCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        os.chdir(os.path.dirname(self.view.file_name()))
        return os.system('git rev-parse 2> /dev/null > /dev/null') == 0

    def run(self, edit):
        cmd = 'git rm %s' % self.view.file_name()
        os.chdir(os.path.dirname(self.view.file_name()))
        exec_command(cmd)
        show_results(self.view.window(), cmd)


class GitResetCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        os.chdir(os.path.dirname(self.view.file_name()))
        return os.system('git rev-parse 2> /dev/null > /dev/null') == 0

    def run(self, edit):
        cmd = 'git reset HEAD %s' % self.view.file_name()
        os.chdir(os.path.dirname(self.view.file_name()))
        exec_command(cmd)
        show_results(self.view.window(), cmd)


class GitCommitWithMessageCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        os.chdir(os.path.dirname(self.view.file_name()))
        return os.system('git rev-parse 2> /dev/null > /dev/null') == 0

    def run(self, edit, message):
        os.chdir(os.path.dirname(self.view.file_name()))
        show_results(self.view.window(), exec_command('git commit -m "%s"' % message.replace('"', '\"')))


class GitCommitCommand(sublime_plugin.WindowCommand):
    def is_enabled(self, *args):
        os.chdir(os.path.dirname(self.window.active_view().file_name()))
        return os.system('git rev-parse 2> /dev/null > /dev/null') == 0

    def on_done(self, text):
        try:
            if self.window.active_view():
                self.window.active_view().run_command('git_commit_with_message', {'message': text})
        except ValueError:
            pass
    
    def run(self):
        self.window.show_input_panel('Commit Message:', '', self.on_done, None, None)


class GitInitInFolderCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        os.chdir(os.path.dirname(self.view.file_name()))
        return os.system('git rev-parse 2> /dev/null > /dev/null') == 0

    def run(self, edit, folder):
        os.chdir(folder)
        show_results(self.view.window(), exec_command('git init'))


class GitInitCommand(sublime_plugin.WindowCommand):
    def is_enabled(self, *args):
        os.chdir(os.path.dirname(self.window.active_view().file_name()))
        return not os.system('git rev-parse 2> /dev/null > /dev/null') == 0

    def on_done(self, text):
        try:
            if self.window.active_view():
                self.window.active_view().run_command('git_init_in_folder', {'folder': text})
        except ValueError:
            pass
    
    def run(self):
        folder_name = os.path.dirname(self.window.active_view().file_name())
        self.window.show_input_panel('Project Folder:', folder_name, self.on_done, None, None)