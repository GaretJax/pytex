"""
Tools and utilities to work with subcommands and argparse.
"""

import os
import inspect
import importlib
import itertools
import argparse


class Command(object):
    """
    Superclass for each
    """

    parser_class = argparse.ArgumentParser
    help = ''

    def attach(self, parser):
        subparser = self.parser()
        subparser.set_defaults(command=self)
        parser.attach_parser(self.name, subparser, help=self.help)

    def set_logger(self, logger):
        self.logger = logger.get_logger(self.name)

    def set_config(self, config):
        self.config = config

    def parser(self):
        return self.parser_class()

    def execute(self, args):
        raise NotImplementedError()


class _AttachableSubParsersAction(argparse._SubParsersAction):
    def attach_parser(self, name, parser, help=None):
        parser.prog = '%s %s' % (self._prog_prefix, name)

        # create a pseudo-action to hold the choice help
        if help:
            choice_action = self._ChoicesPseudoAction(name, help)
            self._choices_actions.append(choice_action)

        # add the parser to the map
        self._name_parser_map[name] = parser
        return parser


def iscommand(obj):
    return isinstance(obj, Command)


def load(package):
    base = os.path.dirname(importlib.import_module(package).__file__)

    commands = os.listdir(base)
    commands = (c for c in commands if not c.startswith('_'))
    commands = (c for c in commands if c.endswith('.py'))
    commands = (c.rsplit('.', 1)[0] for c in commands)
    commands = ('{}.{}'.format(package, c) for c in commands)
    commands = (importlib.import_module(c) for c in commands)
    commands = list((inspect.getmembers(c, iscommand) for c in commands))
    commands = itertools.chain.from_iterable(commands)
    commands = (c[1] for c in commands)

    return commands


def attach(parser, subcommands):
    parser.register('action', 'parsers', _AttachableSubParsersAction)

    subparsers = parser.add_subparsers(title='subcommands')
    for command in subcommands:
        command.attach(subparsers)

    return parser
