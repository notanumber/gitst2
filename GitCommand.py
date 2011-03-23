import subprocess

import sublime
import sublime_plugin


class GitCommand(sublime_plugin.WindowCommand):
    def run(self):
        p = subprocess.Popen(self.command_string, shell=True, bufsize=1024, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        stdout = p.stdout
        stderr = p.stderr
        results = [stdout.read(), stderr.read()]

        self.output_view = self.window.get_output_panel('git')
        self.window.get_output_panel('git')

        self.window.run_command('show_panel', {'panel': 'output.git'})

        self.output_view.set_read_only(False)
        edit = self.output_view.begin_edit()
        self.output_view.insert(edit, self.output_view.size(), '\n'.join(results))
        self.output_view.end_edit(edit)
        self.output_view.set_read_only(True)


# class GitCommitCommand(GitCommand):
#     command_string = 'git commit'

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

class GitStatusCommand(GitCommand):
    command_string = 'git status'
