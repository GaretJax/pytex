from pytex.subcommands import Command

import subprocess
import os
import shlex
import shutil
import time

from pytex.monitors import monitor


class Compile(Command):

    name = "compile"

    def execute(self, args):
        tempdir = self.config.get('compilation', 'tempdir')
        tempdir = os.path.realpath(tempdir)

        name = os.path.basename(os.getcwd())
        dest = os.path.join(os.path.realpath('.'), name + '.pdf')

        self.compile(tempdir, dest)

    def compile(self, tempdir, dest):
        if not os.path.exists(tempdir):
            os.mkdir(tempdir)

        cmd = shlex.split(self.config.get('compilation', 'command'))
        cmd += [
            '-output-directory', tempdir,
            '-file-line-error',
            'master.tex',
        ]

        try:
            subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            pass
        else:
            self.logger.info('Done')
            with file(dest, 'a'):
                os.utime(dest, None)

        shutil.copyfile(os.path.join(tempdir, 'master.pdf'), dest)


compile_command = Compile()


class Watch(Compile):

    name = 'watch'

    def execute(self, args):
        tempdir = self.config.get('compilation', 'tempdir')
        tempdir = os.path.realpath(tempdir)

        name = os.path.basename(os.getcwd())
        dest = os.path.join(os.path.realpath('.'), name + '.pdf')

        def handler(event):
            if event.path.startswith(tempdir):
                return

            if event.path == dest:
                return

            self.logger.info('Change detected at {}, recompiling...'.format(
                event.path))
            self.compile(tempdir, dest)

        observer = monitor.Observer()
        observer.monitor(os.path.realpath('.'), handler)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()


vimwatch_command = Watch()
