from pytex.subcommands import Command

import os


class Init(Command):

    name = 'init'
    help = 'Creates a new pytex document with the given name.'

    def parser(self):
        parser = self.parser_class()
        parser.add_argument('path', metavar='NAME')

        return parser


    def execute(self, args, logger):
        path = os.path.realpath(args.path)
        base = os.path.dirname(path)

        if os.path.exists(path):
            print "The given name is already taken"
            return 1

        logger.log("Create")

        print base


command = Init()
