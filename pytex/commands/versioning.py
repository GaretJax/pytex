from pytex.subcommands import Command

import subprocess
import tempfile
import os
import shlex


class Save(Command):

    name = 'save'

    def parser(self):
        parser = self.parser_class()
        parser.add_argument('-m', '--message')
        return parser

    def execute(self, args):
        message = args.message

        if not message:
            message = 'Savepoint without message'

        self.versions().addall().commit(message)

saving_command = Save()


class Tag(Command):

    name = 'tag'

    def parser(self):
        parser = self.parser_class()
        parser.add_argument('name')
        parser.add_argument('-m', '--message')
        return parser

    def get_message(self):
        fd, path = tempfile.mkstemp()

        try:
            os.close(fd)
            cmd = shlex.split(
                self.config.get('general', 'editor')
            ) + [path]
            subprocess.check_call(cmd)
            with open(path) as fh:
                message = fh.read().strip()
        finally:
            os.remove(path)

        return message

    def execute(self, args):
        message = args.message
        if not message:
            message = self.get_message()

        self.versions().tag(args.name, message)

tagging_command = Tag()
