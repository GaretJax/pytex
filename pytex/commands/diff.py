import os
import shutil
import subprocess

from pytex.subcommands import Command
from pytex.commands import building


class Compare(Command):

    name = 'diff'
    help = 'Creates a PDF document highlighting the changes'\
           'between two tags in the repository.'

    def parser(self):
        parser = self.parser_class()
        parser.add_argument('from_ref', metavar='from-tag')
        parser.add_argument('to_ref', metavar='to-tag')
        return parser

    def compile(self, diff_dir, dest):
        base = os.getcwd()
        tempdir = self.config.get('compilation', 'tempdir')

        compilator = building.Compile()
        compilator.set_config(self.config)
        compilator.logger = self.logger

        os.chdir(diff_dir)

        tempdir = os.path.realpath(tempdir)

        compilator.mktempdir(tempdir)
        compilator.compile(tempdir)
        compilator.compile_bib(tempdir)
        compilator.compile(tempdir)
        compilator.compile(tempdir, dest=dest)

        os.chdir(base)

    def execute(self, args):
        tempdir = self.config.get('compilation', 'tempdir')
        tempdir = os.path.realpath(tempdir)
        base = os.getcwd()
        name = os.path.basename(base)

        from_dir = os.path.join(tempdir, name + '-ref-' + args.from_ref)
        to_dir = os.path.join(tempdir, name + '-ref-' + args.to_ref)
        diff_dir = os.path.join(tempdir, name + '-diff')

        ver = self.versions()
        ver.export_tag(args.from_ref, from_dir)
        ver.export_tag(args.to_ref, to_dir)

        # Copy over all non .tex files from the newest version
        if os.path.exists(diff_dir):
            shutil.rmtree(diff_dir)
        shutil.copytree(to_dir, diff_dir,
                        ignore=shutil.ignore_patterns('*.tex'))

        # TODO: Is it correct to simply ignore files present in
        # the older version which aren't anymore in the new one?

        ignore = (
            'preamble.tex',
            'languages/prompts.tex',
            'headers-footers.tex',
        )

        for root, _, files in os.walk(to_dir):
            relative_path = root[len(to_dir)+1:]
            for f in files:
                if f.endswith('.tex'):
                    relative = os.path.join(relative_path, f)
                    from_f = os.path.join(from_dir, relative)
                    to_f = os.path.join(to_dir, relative)
                    diff_f = os.path.join(diff_dir, relative)

                    # If it does not exist, compare it against an
                    # empty file
                    if not os.path.exists(from_f):
                        base = os.path.dirname(from_f)
                        if not os.path.exists(base):
                            os.makedirs(base)
                        open(from_f, 'w').close()

                    if relative in ignore:
                        with open(to_f) as fh:
                            out = fh.read()
                    else:
                        out = subprocess.check_output([
                            'latexdiff',
                            '--e', 'utf8',
                            from_f, to_f
                        ])

                    with open(diff_f, 'w') as fh:
                        fh.write(out)

        # Build the resulting document
        dest = os.path.join(base, '{}-diff-{}-{}.pdf'
                                  .format(name, args.from_ref, args.to_ref))
        self.compile(diff_dir, dest)


command = Compare()
