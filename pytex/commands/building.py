import subprocess
import os
import glob
import shlex
import shutil
import time
import hashlib

from pytex.monitors import monitor
from pytex.subcommands import Command
from pytex.utils import find_files_of_type

import re


class Compile(Command):

    name = 'compile'
    help = 'Compile the LaTeX sources into a PDF document.'

    def execute(self, args):
        tempdir = self.config.get('compilation', 'tempdir')
        tempdir = os.path.realpath(tempdir)

        master = args.master

        if args.define:
            defs = [a.split('=', 1) for a in args.define]
        else:
            defs = []

        name = os.path.basename(os.getcwd())
        if master != 'master':
            name = '{}-{}'.format(name, master)

        if args.destination:
            dest = args.destination
        else:
            dest = os.path.join(os.path.realpath('.'), name + '.pdf')

        self.mktempdir(tempdir)

        # TODO: Make a plugin architecture to allow additional actions
        # to be run when compiling. This would allow to move the bibtex,
        # glossary and nomenclature out of this class.

        nomencl = self.get_nomencl_version(tempdir, master)

        success = self.compile(tempdir, master, defs=defs)

        nomencl = nomencl != self.get_nomencl_version(tempdir, master)

        recompile = args.bibtex or args.glossary or nomencl

        if success and recompile:
            support = []
            if args.bibtex:
                support.append('bibliography')
            if args.glossary:
                support.append('glossaries')
            if nomencl:
                support.append('nomenclature')

            support = ' and '.join([', '.join(support[:-1]), support[-1]])

            self.logger.info('Compiling document with {} support'.format(
                support))

            if args.bibtex:
                self.compile_bib(tempdir, master)

            if args.glossary:
                self.compile_glossary(tempdir, master)

            if nomencl:
                self.compile_nomencl(tempdir, master)

            self.compile(tempdir, master, defs=defs)
            success = self.compile(tempdir, master, defs=defs)

        if success:
            self.copy_pdf(tempdir, master, dest)

    def get_nomencl_version(self, tempdir, master):
        try:
            with open(os.path.join(tempdir, '{}.nlo'.format(master))) as fh:
                return hashlib.sha256(fh.read()).hexdigest()
        except IOError:
            return None

    def parser(self):
        parser = self.parser_class()
        parser.add_argument('--bibtex', '-b', action='store_const', const=True,
                            default=False)
        parser.add_argument('--glossary', '-g', action='store_const',
                            const=True, default=False)
        parser.add_argument('--define', '-d', action='append')
        parser.add_argument('master', nargs='?', default='master')
        parser.add_argument('destination', nargs='?')

        return parser

    def mktempdir(self, tempdir):
        # Find every *.tex file in the source directory to ecreate the dir
        # tree under tempdir for the dirname of each found *.tex file
        matches = set()

        for root, dirnames, filenames in os.walk('.', topdown=False):
            if root in matches:
                # If a subdirectory of root was already scheduled for
                # creation ignore root altogether
                continue

            for f in filenames:
                if f.endswith('.tex'):
                    head, tail = root, ''
                    while head != '.':
                        matches.add(head)
                        head, tail = os.path.split(head)
                    break

        # A lexicographic sort would work as well, but sorting on the
        # string length is more efficient as the length is cached and
        # only integer comparisons are needed
        dirs = sorted(matches, key=len)
        dirs = (os.path.join(tempdir, d) for d in dirs)
        dirs = (os.path.realpath(d) for d in dirs)

        if not os.path.exists(tempdir):
            os.mkdir(tempdir)
        else:
            dirs = (d for d in dirs if not os.path.exists(d))

        for d in dirs:
            os.mkdir(d)

    def compile_nomencl(self, tempdir, master):
        cmd = shlex.split(self.config.get('compilation', 'nomenclature'))
        cmd += [
            '-o', '{}.nls'.format(master),
            '{}.nlo'.format(master),
        ]
        self.logger.debug(' '.join(cmd))

        try:
            subprocess.check_output(cmd, cwd=tempdir)
            pass
        except subprocess.CalledProcessError as e:
            self.logger.error(e.output)
            self.logger.error(e)
        else:
            self.logger.info('Nomenclature updated')

    def compile_glossary(self, tempdir, master):
        cmd = shlex.split(self.config.get('compilation', 'glossary'))
        cmd += [
            master,
        ]
        self.logger.debug(' '.join(cmd))

        try:
            subprocess.check_output(cmd, cwd=tempdir)
            pass
        except subprocess.CalledProcessError as e:
            self.logger.error(e.output)
            self.logger.error(e)
        else:
            self.logger.info('Glossaries updated')

    def compile_bib(self, tempdir, master):
        base = os.path.realpath('.')

        cmd = shlex.split(self.config.get('compilation', 'bibliography'))
        cmd += [
            '{}.aux'.format(master),
        ]
        self.logger.debug(' '.join(cmd))

        try:
            if tempdir.startswith(base):
                exclude = tempdir[len(base) + 1:]
            else:
                exclude = tempdir
            for f in find_files_of_type(os.path.realpath('.'),
                                        ('bib',), (exclude,)):
                self.logger.debug('Copying bib {!r} file to build dir'
                                  .format(f))
                shutil.copyfile(f, os.path.join(tempdir, f))
            subprocess.check_output(cmd, cwd=tempdir)
            pass
        except subprocess.CalledProcessError as e:
            self.logger.error(e.output)
            self.logger.error(e)
        else:
            self.logger.info('Bibliography updated')

    def compile(self, tempdir, master, dest=None, runs=1, defs=None):
        cmd = shlex.split(self.config.get('compilation', 'command'))
        cmd += [
            '--output-directory', tempdir,
            '--file-line-error',
            '--interaction=nonstopmode',
        ]

        if defs:
            defs = [r'\def\{}{{{}}}'.format(*a) for a in defs]
            cmd += [
                '{}\input{{master}}'.format(''.join(defs))
            ]
        else:
            cmd += [
                '{}.tex'.format(master),
            ]

        self.logger.debug(' '.join(cmd))

        try:
            for _ in range(runs):
                subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            self.logger.error(e.output)
            self.logger.error(e)
            return False
        else:
            if dest:
                self.logger.info('Done')
                self.copy_pdf(tempdir, master, dest)
            else:
                self.logger.debug('Intermediary compilation done')
            return True

    def copy_pdf(self, tempdir, master, dest):
        shutil.copyfile(os.path.join(tempdir, '{}.pdf'.format(master)), dest)


compile_command = Compile()


class Watch(Compile):

    name = 'watch'
    help = ('Monitor the current directory for changes and rebuild the '
            'document when needed.')

    def parser(self):
        parser = self.parser_class()
        parser.add_argument(
            '-i', '--initial',
            help='Execute a build before entering the watching loop',
            action='store_true'
        )
        parser.add_argument('--define', '-d', action='append')
        parser.add_argument('master', nargs='?', default='master')
        parser.add_argument('destination', nargs='?')
        return parser

    def execute(self, args):

        base = os.path.realpath('.')

        tempdir = self.config.get('compilation', 'tempdir')
        tempdir = os.path.realpath(tempdir)

        master = args.master

        if args.define:
            defs = [a.split('=', 1) for a in args.define]
        else:
            defs = []

        name = os.path.basename(os.getcwd())
        if master != 'master':
            name = '{}-{}'.format(name, master)

        if args.destination:
            dest = args.destination
        else:
            dest = os.path.join(os.path.realpath('.'), name + '.pdf')

        ignore_regex_str = self.config.get('watch', 'ignore')
        if ignore_regex_str:
            ignore_regex = re.compile(ignore_regex_str)

        def handler(event):
            relative = event.path[len(base) + 1:]

            self.logger.debug('Event received: {!r}'.format(event))

            if relative.startswith('.git/'):
                self.logger.debug('Ignoring GIT action')
                return

            if ignore_regex_str and ignore_regex.search(relative):
                self.logger.debug('Ignoring {!r} because of ignore regex '
                                  'from config'.format(relative))
                return

            if event.path.startswith(tempdir):
                self.logger.debug('Ignoring {!r}'.format(relative))
                return

            if event.path == dest:
                self.logger.debug('Ignoring {!r}'.format(relative))
                return

            if os.path.basename(event.path).startswith('.'):
                self.logger.debug('Ignoring {!r}'.format(relative))
                return

            if os.path.basename(event.path).endswith('~'):
                self.logger.debug('Ignoring {!r}'.format(relative))
                return

            if os.path.isdir(event.path):
                self.logger.debug('Ignoring directory {!r}'.format(relative))
                return

            if event.path.endswith('.log'):
                self.logger.debug('Ignoring {!r}'.format(relative))
                return

            if isinstance(event, monitor.base.FileCreated):
                if event.path.endswith('.tex'):
                    subdir = os.path.dirname(relative)
                    builddir = os.path.join(tempdir, subdir)
                    if not os.path.exists(builddir):
                        # If a new .tex file was added and the containing
                        # directory does not exist in the build root, create it
                        os.mkdir(builddir)
                        self.logger.info('Added subdirectory {!r} to the '
                                         'build directory'.format(subdir))

            if event.path.endswith('.bib'):
                self.logger.info('Change detected at {!r}, recompiling with '
                                 'bibliography support...'.format(relative))
                self.compile(tempdir, master, defs=defs)
                self.compile_bib(tempdir, master)
                self.compile(tempdir, master, defs=defs)
                self.compile(tempdir, master, dest, defs=defs)
                self.logger.info('All done')
            elif event.path.endswith('.gls'):
                self.logger.info('Change detected at {!r}, recompiling with '
                                 'glossary support...'.format(relative))
                self.compile(tempdir, master, defs=defs)
                self.compile_glossary(tempdir, master, defs=defs)
                self.compile(tempdir, master, defs=defs)
                self.compile(tempdir, master, dest, defs=defs)
                self.logger.info('All done')
            else:
                self.logger.info('Change detected at {!r}, recompiling...'
                                 .format(relative))
                nomencl = self.get_nomencl_version(tempdir, master)
                success = self.compile(tempdir, master, defs=defs)
                if success and nomencl != self.get_nomencl_version(tempdir,
                                                                   master):
                    self.logger.info(
                        'Detected nomenclature change, recompiling...')
                    self.compile_nomencl(tempdir, master)
                    self.compile(tempdir, master, defs=defs)
                    success = self.compile(tempdir, master, defs=defs)
                    self.logger.info('All done')

                if success:
                    self.copy_pdf(tempdir, master, dest)

        self.mktempdir(tempdir)

        if args.initial:
            self.logger.info('Compiling initial version...'.format(base))
            self.compile(tempdir, master, dest, defs=defs)

        self.logger.info('Watching {} for changes...'.format(base))

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
    help = ('Clean the document by deleting all files resulted from the '
            'building process.')

    def parser(self):
        parser = self.parser_class()
        parser.add_argument('--all', '-a', action='store_const', const=True,
                            default=False)

        return parser

    @staticmethod
    def rmfile(file):
        if os.path.exists(file):
            os.remove(file)
            return True
        return False

    def execute(self, args):
        tempdir = self.config.get('compilation', 'tempdir')
        tempdir = os.path.realpath(tempdir)

        if os.path.exists(tempdir):
            self.logger.info('Deleting temp folder at {}'.format(tempdir))
            shutil.rmtree(tempdir)

        if self.rmfile('hunSPELL.bak'):
            self.logger.info('Deleted hunspell backup file')

        if self.rmfile('pytex.log'):
            self.logger.info('Deleted pytex log file')

        name = os.path.basename(os.getcwd())
        dest = os.path.join(os.path.realpath('.'), name + '.pdf')

        if args.all:
            if self.rmfile(dest):
                self.logger.info('Deleted document at {}'.format(dest))

            diffs = glob.glob('{}-diff-*-*.pdf'.format(name))
            for diff in diffs:
                self.rmfile(diff)
                self.logger.info('Deleted diff document at {}'.format(diff))

        self.logger.info('Done')

clean_command = Clean()
