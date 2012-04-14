from pytex.subcommands import Command

import os
import shutil


class Init(Command):

    name = 'init'
    help = 'Creates a new pytex document with the given name.'

    def parser(self):
        parser = self.parser_class()
        parser.add_argument('path', metavar='NAME')
        parser.add_argument('-t', '--template', help='Template name to use')

        return parser

    def execute(self, args):
        path = os.path.realpath(args.path)
        base = os.path.dirname(path)

        if os.path.exists(path):
            print "The given name is already taken"
            return 1

        self.logger.info("Creating new pytex document at '{}'".format(path))

        template = args.template or self.config.get('templates', 'default')

        self.logger.info("Selected template '{}'".format(template))

        template_dir = os.path.join(
            os.path.expanduser(self.config.get('templates', 'directory')),
            template
        )

        shutil.copytree(template_dir, path)

        print base


command = Init()
