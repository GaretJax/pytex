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

        self.mktempdir(tempdir)
        self.compile(tempdir, dest)

    def compile(self, tempdir, dest):
    def mktempdir(self, tempdir):
        # Find every *.tex file in the source directory
        # Recreate the dir tree under tempdir for the dirname of each found *.tex file
        matches = set()

        for root, dirnames, filenames in os.walk('.', topdown=False):
            if root in matches:
                # If a subdirectory of root was already scheduled for creation
                # ignore root altogether
                continue

            for f in filenames:
                if f.endswith('.tex'):
                    head, tail = root, ''
                    while head != '.':
                        matches.add(head)
                        head, tail = os.path.split(head)
                    break

        dirs = sorted(matches, key=len)  # A lexicographic sort would work as well,
                                         # but sorting on the string length is more
                                         # efficient as the length is cached and
                                         # only integer comparisons are needed
        dirs = (os.path.join(tempdir, d) for d in dirs)
        dirs = (os.path.realpath(d) for d in dirs)

        if not os.path.exists(tempdir):
            os.mkdir(tempdir)
        else:
            dirs = (d for d in dirs if not os.path.exists(d))

        for d in dirs:
            os.mkdir(d)

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
            if os.path.isdir(event.path):
                self.logger.debug('Ignoring directory \'{}\''.format(relative))
                return

            if isinstance(event, monitor.base.FileCreated):
                if event.path.endswith('.tex'):
                    subdir = os.path.dirname(relative)
                    builddir = os.path.join(tempdir, subdir)
                    if not os.path.exists(builddir):
                        # If a new .tex file was added ans the containing directory does not
                        # exist in the build root, then create it
                        os.mkdir(builddir)
                        self.logger.info("Added subdirectory {!r} to the build directory".format(subdir))


        self.mktempdir(tempdir)

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
