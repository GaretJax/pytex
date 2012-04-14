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

    def compile(self, tempdir, dest):
        cmd = shlex.split(self.config.get('compilation', 'command'))
        cmd += [
            '--output-directory', tempdir,
            '--file-line-error',
            '--interaction=nonstopmode',
            'master.tex',
        ]

        self.logger.debug(' '.join(cmd))

        try:
            subprocess.check_output(cmd)
            pass
        except subprocess.CalledProcessError as e:
            self.logger.error(e.output)
            self.logger.error(e)
        else:
            self.logger.info('Done')
            shutil.copyfile(os.path.join(tempdir, 'master.pdf'), dest)


compile_command = Compile()


class Watch(Compile):

    name = 'watch'

    def parser(self):
        parser = self.parser_class()
        parser.add_argument('-i', '--initial', help='Execute a build before entering the watching loop', action='store_true')

        return parser


    def execute(self, args):

        base = os.path.realpath('.')

        tempdir = self.config.get('compilation', 'tempdir')
        tempdir = os.path.realpath(tempdir)

        name = os.path.basename(os.getcwd())
        dest = os.path.join(base, name + '.pdf')

        def handler(event):
            if event.path.startswith(tempdir):
                return

            if event.path == dest:
                return

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

            self.logger.info('Change detected at \'{}\', recompiling...'.format(
                relative))
            self.compile(tempdir, dest)

        self.mktempdir(tempdir)

        if args.initial:
            self.logger.info('Compiling initial version...'.format(base))
            self.compile(tempdir, dest)

        observer = monitor.Observer()
        observer.monitor(os.path.realpath('.'), handler)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()


watch_command = Watch()


class Clean(Command):

    name = 'clean'

    def parser(self):
        parser = self.parser_class()
        parser.add_argument('--all', '-a', action='store_const', const=True, default=False)

        return parser


    def execute(self, args):
        tempdir = self.config.get('compilation', 'tempdir')
        tempdir = os.path.realpath(tempdir)

        if os.path.exists(tempdir):
            self.logger.info('Deleting temp folder at {}'.format(tempdir))
            shutil.rmtree(tempdir)

        name = os.path.basename(os.getcwd())
        dest = os.path.join(os.path.realpath('.'), name + '.pdf')

        if args.all and os.path.exists(dest):
            self.logger.info('Deleting document at {}'.format(dest))
            os.remove(dest)

        self.logger.info('Done')

clean_command = Clean()
