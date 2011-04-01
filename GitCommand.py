import os
import subprocess

import sublime
import sublime_plugin


class GitTextCommandBase(sublime_plugin.TextCommand):
    folder_name = ''
    file_name = ''

    def __init__(self, *args, **kwargs):
        super(GitTextCommandBase, self).__init__(*args, **kwargs)

        if self.view.file_name():
            self.folder_name, self.file_name = os.path.split(self.view.file_name())
  
    def exec_command(self, command_string, cwd=None):
        if not cwd:
            cwd = self.folder_name
        p = subprocess.Popen(
            command_string, cwd=cwd, shell=True, bufsize=1024,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        p.wait()

        stdout = p.stdout
        stderr = p.stderr

        return '\n'.join([stdout.read(), stderr.read()])
    
    def show_output(self, output):
        window = self.view.window()
        view = window.get_output_panel('git')
        edit = view.begin_edit()

        view.set_read_only(False)
        view.insert(edit, view.size(), output)
        view.end_edit(edit)
        view.set_read_only(True)

        window.run_command('show_panel', {'panel': 'output.git'})

    def is_enabled(self, *args):
        if self.folder_name:
            p = subprocess.Popen('git rev-parse HEAD > /dev/null > /dev/null', cwd=self.folder_name, shell=True)
            return p.wait() == 0
        else:
            return False


class GitStatusCommand(GitTextCommandBase):
    def run(self, edit):
        self.show_output(self.exec_command('git status'))


class GitDiffCommand(GitTextCommandBase):
    def run(self, edit):
        results = self.exec_command('git diff')
        window = self.view.window()
        view = self.view.window().new_file()
        edit = view.begin_edit()

        view.set_scratch(True)
        view.set_name('%s.diff' % os.path.basename(self.file_name))
        view.set_syntax_file('Packages/Diff/Diff.tmLanguage')

        view.insert(edit, 0, results)
        view.end_edit(edit)


class GitAddCommand(GitTextCommandBase):
    def run(self, edit):
        self.exec_command('git add "%s"' % self.file_name)
        self.show_output('Added "%s"' % self.file_name)


class GitRmCommand(GitTextCommandBase):
    def run(self, edit):
        self.show_output(self.exec_command('git rm "%s"' % self.file_name))


class GitResetCommand(GitTextCommandBase):
    def run(self, edit):
        self.show_output(self.exec_command('git reset HEAD "%s"' % self.file_name))


class GitLogCommand(GitTextCommandBase):
    def run(self, edit):
        self.show_output(self.exec_command('git log'))


class GitCommitWithMessageCommand(GitTextCommandBase):
    def run(self, edit, message):
        self.show_output(self.exec_command('git commit -m "%s"' % message.replace('"', '\"')))


class GitCommitCommand(GitTextCommandBase):
    def on_done(self, text):
        try:
            if self.view:
                self.view.run_command('git_commit_with_message', {'message': text})
        except ValueError:
            pass
    
    def run(self, edit):
        self.view.window().show_input_panel('Commit Message:', '', self.on_done, None, None)


class GitTagWithNameCommand(GitTextCommandBase):
    def run(self, edit, tag):
        self.show_output(self.exec_command('git tag %s' % tag))


class GitTagCommand(GitTextCommandBase):
    def on_done(self, text):
        try:
            if self.view:
                self.view.run_command('git_tag_with_name', {'tag': text})
        except ValueError:
            pass
    
    def run(self, edit):
        self.view.window().show_input_panel('Tag Name:', '', self.on_done, None, None)


class GitInitInFolderCommand(GitTextCommandBase):
    def run(self, edit, folder):
        self.show_output(self.exec_command('git init', cwd=folder))


class GitInitCommand(GitTextCommandBase):
    def is_enabled(self, *args):
        return not super(GitInitCommand, self).is_enabled(*args)

    def on_done(self, text):
        try:
            if self.view:
                self.view.run_command('git_init_in_folder', {'folder': text})

        except ValueError:
            pass
    
    def run(self, edit):
        self.view.window().show_input_panel('Project Folder:', self.folder_name, self.on_done, None, None)