import functools
import os
import subprocess
import thread

import sublime
import sublime_plugin


class ProcessListener(object):
    def on_data(self, proc, data):
        pass

    def on_finished(self, proc):
        pass


class AsyncProcess(object):
    def __init__(self, arg_list, listener):
        self.listener = listener
        self.killed = False

        # Hide the console window on Windows
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc_env = os.environ.copy()

        self.proc = subprocess.Popen(arg_list, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, startupinfo=startupinfo, env=proc_env)

        if self.proc.stdout:
            thread.start_new_thread(self.read_stdout, ())

        if self.proc.stderr:
            thread.start_new_thread(self.read_stderr, ())

    def kill(self):
        if not self.killed:
            self.killed = True
            self.proc.kill()
            self.listener = None

    def poll(self):
        return self.proc.poll() == None

    def read_stdout(self):
        while True:
            data = os.read(self.proc.stdout.fileno(), 2**15)

            if data != "":
                if self.listener:
                    self.listener.on_data(self, data)
            else:
                self.proc.stdout.close()
                if self.listener:
                    self.listener.on_finished(self)
                break

    def read_stderr(self):
        while True:
            data = os.read(self.proc.stderr.fileno(), 2**15)

            if data != "":
                if self.listener:
                    self.listener.on_data(self, data)
            else:
                self.proc.stderr.close()
                break


class GitAddCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        if self.view.file_name():
            return True
        return False
    
    def run(self, edit):
        if self.view.file_name():
            folder_name, file_name = os.path.split(self.view.file_name())

        print folder_name, file_name
        self.view.window().run_command('exec', {'cmd': ['git', 'add', file_name], 'working_dir': folder_name, 'quiet': True})


class GitCheckoutCommand(sublime_plugin.TextCommand):
    def run(self, edit, branch_or_path=''):
        if not branch_or_path:
            if self.view.file_name():
                folder_name = os.path.dirname(self.view.file_name())
            else:
                file_name = ''
            self.view.window().show_input_panel('Branch or Path:', file_name, self.on_done, None, None)
        else:
            self.on_done(branch_or_path)

    def on_done(self, branch_or_path):
        if self.view.file_name():
            folder_name = os.path.dirname(self.view.file_name())

        self.view.window().run_command('exec', {'cmd': ['git', 'checkout', branch_or_path], 'working_dir': folder_name, 'quiet': True})
        self.view.run_command('revert')


class GitCommitCommand(sublime_plugin.TextCommand):
    def run(self, edit, message='', all=False):
        if all:
            on_done = self.commit_all
        else:
            on_done = self.commit_one

        if not message:
            self.view.window().show_input_panel('Commit Message:', '', on_done, None, None)
        else:
            on_done(message)

    def commit_one(self, message):
        if self.view.file_name():
            folder_name, file_name = os.path.split(self.view.file_name())

        self.view.window().run_command('exec', {'cmd': ['git', 'commit', '-m', message, file_name], 'working_dir': folder_name, 'quiet': True})

    def commit_all(self, message):
        if self.view.file_name():
            folder_name = os.path.dirname(self.view.file_name())

        self.view.window().run_command('exec', {'cmd': ['git', 'commit', '-am', message], 'working_dir': folder_name, 'quiet': True})


class GitDiffCommand(sublime_plugin.TextCommand, ProcessListener):
    def run(self, edit, encoding='utf-8', kill=False):
        if kill:
            if self.proc:
                self.proc.kill()
                self.proc = None
            return

        if self.view.file_name():
            folder_name, file_name = os.path.split(self.view.file_name())

        if not hasattr(self, 'output_view'):
            self.output_view = self.view.window().new_file()

        self.encoding = encoding
        self.proc = None

        self.output_view.set_scratch(True)
        self.output_view.set_name('%s.diff' % os.path.basename(file_name))
        self.output_view.set_syntax_file('Packages/Diff/Diff.tmLanguage')

        os.chdir(folder_name)

        err_type = OSError
        if os.name == "nt":
            err_type = WindowsError

        try:
            self.proc = AsyncProcess(['git', 'diff'], self)
        except err_type as e:
            self.append_data(None, str(e) + '\n')

    def is_enabled(self, kill=False):
        if kill:
            return hasattr(self, 'proc') and self.proc and self.proc.poll()
        else:
            return True

    def append_data(self, proc, data):
        if proc != self.proc:
            # a second call to exec has been made before the first one
            # finished, ignore it instead of intermingling the output.
            if proc:
                proc.kill()
            return

        try:
            str = data.decode(self.encoding)
        except:
            str = '[Decode error - output not ' + self.encoding + ']'
            proc = None

        # Normalize newlines, Sublime Text always uses a single \n separator
        # in memory.
        str = str.replace('\r\n', '\n').replace('\r', '\n')

        selection_was_at_end = (len(self.output_view.sel()) == 1
            and self.output_view.sel()[0]
                == sublime.Region(self.output_view.size()))
        self.output_view.set_read_only(False)
        edit = self.output_view.begin_edit()
        self.output_view.insert(edit, self.output_view.size(), str)
        if selection_was_at_end:
            self.output_view.show(self.output_view.size())
        self.output_view.end_edit(edit)
        self.output_view.set_read_only(True)

    def finish(self, proc):
        if proc != self.proc:
            return

        # Set the selection to the start, so that next_result will work as expected
        edit = self.output_view.begin_edit()
        self.output_view.sel().clear()
        self.output_view.sel().add(sublime.Region(0))
        self.output_view.end_edit(edit)

    def on_data(self, proc, data):
        sublime.set_timeout(functools.partial(self.append_data, proc, data), 0)

    def on_finished(self, proc):
        sublime.set_timeout(functools.partial(self.finish, proc), 0)


class GitInitCommand(sublime_plugin.TextCommand):
    def run(self, edit, folder_name=''):
        if not folder_name:
            if self.view.file_name():
                folder_name = os.path.dirname(self.view.file_name())
            self.view.window().show_input_panel('Folder:', folder_name, self.on_done, None, None)
        else:
            self.on_done(folder_name)

    def on_done(self, folder_name):
        self.view.window().run_command('exec', {'cmd': ['git', 'init'], 'working_dir': folder_name, 'quiet': True})


class GitLogCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        if self.view.file_name():
            return True
        return False
    
    def run(self, edit):
        if self.view.file_name():
            folder_name, file_name = os.path.split(self.view.file_name())

        self.view.window().run_command('exec', {'cmd': ['git', 'log', file_name], 'working_dir': folder_name, 'quiet': True})


class GitMvCommand(sublime_plugin.TextCommand):
    def run(self, edit, destination=''):
        if not destination:
            self.view.window().show_input_panel('Destination:', '', self.on_done, None, None)
        else:
            self.on_done(tag_name)

    def on_done(self, destination):
        if self.view.file_name():
            folder_name, source = os.path.split(self.view.file_name())

        self.view.window().run_command('exec', {'cmd': ['git', 'mv', source, destination], 'working_dir': folder_name, 'quiet': True})


class GitResetCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        if self.view.file_name():
            return True
        return False
    
    def run(self, edit, mode='--', commit='HEAD'):
        if self.view.file_name():
            folder_name, file_name = os.path.split(self.view.file_name())

        self.view.window().run_command('exec', {'cmd': ['git', 'reset', mode, commit, file_name], 'working_dir': folder_name, 'quiet': True})


class GitRmCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        if self.view.file_name():
            return True
        return False
    
    def run(self, edit):
        if self.view.file_name():
            folder_name, file_name = os.path.split(self.view.file_name())

        self.view.window().run_command('exec', {'cmd': ['git', 'rm', file_name], 'working_dir': folder_name, 'quiet': True})


class GitStatusCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        if self.view.file_name():
            return True
        return False
    
    def run(self, edit):
        if self.view.file_name():
            folder_name = os.path.dirname(self.view.file_name())

        self.view.window().run_command('exec', {'cmd': ['git', 'status'], 'working_dir': folder_name, 'quiet': True})


class GitBlameCommand(sublime_plugin.TextCommand):
    def is_enabled(self, *args):
        if self.view.file_name():
            return True
        return False
    
    def run(self, edit):
        if self.view.file_name():
            folder_name, file_name = os.path.split(self.view.file_name())

        self.view.window().run_command('exec', {'cmd': ['git', 'blame', file_name], 'working_dir': folder_name, 'quiet': True})


class GitBlameCommand(sublime_plugin.TextCommand, ProcessListener):
    def run(self, edit, encoding='utf-8', kill=False):
        if kill:
            if self.proc:
                self.proc.kill()
                self.proc = None
            return

        if self.view.file_name():
            folder_name, file_name = os.path.split(self.view.file_name())

        if not hasattr(self, 'output_view'):
            self.output_view = self.view.window().new_file()

        self.encoding = encoding
        self.proc = None

        self.output_view.set_scratch(True)

        os.chdir(folder_name)

        err_type = OSError
        if os.name == "nt":
            err_type = WindowsError

        try:
            self.proc = AsyncProcess(['git', 'blame', file_name], self)
        except err_type as e:
            self.append_data(None, str(e) + '\n')

    def is_enabled(self, kill=False):
        if kill:
            return hasattr(self, 'proc') and self.proc and self.proc.poll()
        else:
            return True

    def append_data(self, proc, data):
        if proc != self.proc:
            # a second call to exec has been made before the first one
            # finished, ignore it instead of intermingling the output.
            if proc:
                proc.kill()
            return

        try:
            str = data.decode(self.encoding)
        except:
            str = '[Decode error - output not ' + self.encoding + ']'
            proc = None

        # Normalize newlines, Sublime Text always uses a single \n separator
        # in memory.
        str = str.replace('\r\n', '\n').replace('\r', '\n')

        selection_was_at_end = (len(self.output_view.sel()) == 1
            and self.output_view.sel()[0]
                == sublime.Region(self.output_view.size()))
        self.output_view.set_read_only(False)
        edit = self.output_view.begin_edit()
        self.output_view.insert(edit, self.output_view.size(), str)
        if selection_was_at_end:
            self.output_view.show(self.output_view.size())
        self.output_view.end_edit(edit)
        self.output_view.set_read_only(True)

    def finish(self, proc):
        if proc != self.proc:
            return

        # Set the selection to the start, so that next_result will work as expected
        edit = self.output_view.begin_edit()
        self.output_view.sel().clear()
        self.output_view.sel().add(sublime.Region(0))
        self.output_view.end_edit(edit)

    def on_data(self, proc, data):
        sublime.set_timeout(functools.partial(self.append_data, proc, data), 0)

    def on_finished(self, proc):
        sublime.set_timeout(functools.partial(self.finish, proc), 0)


class GitTagCommand(sublime_plugin.TextCommand):
    def run(self, edit, tag_name=''):
        if not tag_name:
            self.view.window().show_input_panel('Tag Name:', '', self.on_done, None, None)
        else:
            self.on_done(tag_name)

    def on_done(self, tag_name):
        if self.view.file_name():
            folder_name = os.path.dirname(self.view.file_name())

        self.view.window().run_command('exec', {'cmd': ['git', 'tag', tag_name], 'working_dir': folder_name, 'quiet': True})
