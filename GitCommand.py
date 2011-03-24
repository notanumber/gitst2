import os
import subprocess

import sublime
import sublime_plugin


class GitCommandBase(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super(GitCommandBase, self).__init__(*args, **kwargs)

        self.folder_name, self.file_name = os.path.split(self.window.active_view().file_name())

        os.chdir(self.folder_name)

    def exec_command(self, command_string):
        p = subprocess.Popen(command_string, shell=True, bufsize=1024, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

        stdout = p.stdout
        stderr = p.stderr

        return '\n'.join([stdout.read(), stderr.read()])

    def show_results(self, results):
        self.output_view = self.window.get_output_panel('git')
        self.window.get_output_panel('git')
        self.window.run_command('show_panel', {'panel': 'output.git'})
        self.output_view.set_read_only(False)
        
        edit = self.output_view.begin_edit()

        self.output_view.insert(edit, self.output_view.size(), results)
        self.output_view.end_edit(edit)
        self.output_view.set_read_only(True)


class GitStatusCommand(GitCommandBase):
    def run(self):
        self.show_results(self.exec_command('git status'))


class GitDiffCommand(GitCommandBase):
    def run(self):
        self.show_results(self.exec_command('git diff'))


class GitCommitWithMessageCommand(GitCommandBase):
    def run(self, message):
        # TODO: Why doesn't this show the output?
        self.show_results(self.exec_command('git commit -m "%s"' % message.replace('"', '\"')))


class GitCommitCommand(GitCommandBase):
    def on_done(self, text):
        try:
            if self.window.active_view():
                self.window.run_command('git_commit_with_message', {'message': text})
        except ValueError:
            pass
    
    def run(self):
        self.window.show_input_panel("Commit Message:", "", self.on_done, None, None)


class GitAddCommand(GitCommandBase):
    def run(self):
        self.exec_command('git add %s' % self.file_name)
        self.show_results('Added %s' % self.file_name)

# class GitInitCommand(GitCommandBase):
#    def run(self):
#        TODO: This should probably prompt for where to `init` rather than assuming the same folder as `file_name`
#        self.show_results(self.exec_command('git init'))

class GitRmCommand(GitCommandBase):
    def run(self):
        self.show_results(self.exec_command('git rm %s' % self.file_name))
