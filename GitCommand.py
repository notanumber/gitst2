import os
import subprocess

import sublime
import sublime_plugin


class GitCommandBase(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super(GitCommandBase, self).__init__(*args, **kwargs)

        self.folder_name = os.path.dirname(self.window.active_view().file_name())

        os.chdir(self.folder_name)


    def exec_command(self, command_string):
        p = subprocess.Popen(command_string, shell=True, bufsize=1024, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

        stdout = p.stdout
        stderr = p.stderr
        return [stdout.read(), stderr.read()]

    def show_results(self, results):
        self.output_view = self.window.get_output_panel('git')
        self.window.get_output_panel('git')
        self.window.run_command('show_panel', {'panel': 'output.git'})
        self.output_view.set_read_only(False)
        
        edit = self.output_view.begin_edit()

        self.output_view.insert(edit, self.output_view.size(), '\n'.join(results))
        self.output_view.end_edit(edit)
        self.output_view.set_read_only(True)


class GitStatusCommand(GitCommandBase):
    def run(self):
        self.show_results(self.exec_command('git status'))


class GitDiffCommand(GitCommandBase):
    def run(self):
        self.show_results(self.exec_command('git diff'))


class GitCommitCommand(GitCommand):
    def run(self):
        self.show_results(self.exec_command('git commit'))

# class GitAddCommand(GitCommand):
#     command_string = 'git add "%s"' % str(self.view.fileName())

# class GitInitCommand(GitCommand):
#     command_string = 'git init'

# class GitRmCommand(GitCommand):
#     command_string = 'git rm "%s"' % str(self.view.fileName())

# class GitDiffCommand(GitCommand):
#     command_string = 'git diff "%s"' % str(self.view.fileName())

# class GitPushCommand(GitCommand):
#     command_string = 'git push'

# class GitPullCommand(GitCommand):
#     command_string = 'git pull'
