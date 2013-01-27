import os
import shlex
import subprocess


from pytex import utils
from pytex.subcommands import Command


class Spellcheck(Command):

    name = 'spellcheck', 'sp'
    help = 'Checks every LaTeX source file in the document for spelling errors.'

    def execute(self, args):
        base = os.path.realpath('.')
        files = utils.find_files_of_type(
            base,
            ('tex',),
            ('/build',),
            ('preamble.tex',),
        )

        for f in files:
            if self.spellcheck_file(f) is False:
                self.logger.info('Process interrupted by user')
                break
        else:
            self.logger.info('Done')


    def spellcheck_file(self, file):
        base = os.path.realpath('.')
        dictionary = os.path.join(base, 'dictionary.dic')

        cmd = shlex.split(self.config.get('spellcheck', 'command'))
        cmd += [
            '-p', dictionary,
            file,
        ]

        if not os.path.exists(dictionary):
            open(dictionary, 'w').close()

        self.logger.debug(' '.join(cmd))

        try:
            subprocess.check_call(cmd)
        except KeyboardInterrupt:
            return False
        except subprocess.CalledProcessError as e:
            self.logger.error(e.output)
            self.logger.error(e)

command = Spellcheck()
