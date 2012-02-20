from __future__ import absolute_import

import sys
import os
import argparse
import pytex

from pytex import logging, settings, subcommands


def build_parser():
    parser = argparse.ArgumentParser(description='')

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + pytex.VERSION)
    parser.add_argument('-v', '--verbose', default=list(),
                        action='append_const', const=1, help='Increments the' \
                        ' verbosity (can be used multiple times).')
    parser.add_argument('-q', '--quiet', default=list(),
                        action='append_const', const=1, help='Decrements the' \
                        ' verbosity (can be used multiple times).')

    commands = subcommands.load('pytex.commands')
    subcommands.attach(parser, commands)

    return parser


def main(args=None):
    # Setup logging
    logfile = os.getenv('PYTEX_LOGFILE') or 'pytex.log'
    logger = logging.LoggingSubsystem(logging.INFO, logfile)
    logger.start()

    # Build argument parser and parse command line
    parser = build_parser()
    args = parser.parse_args(args)

    # Set the verbosity level
    logger.increment_verbosity(len(args.verbose) - len(args.quiet))
    logger.capture_stdout()

    # Load settings
    config = settings.load_config()

    # Execute command
    args.command.set_logger(logger)
    args.command.set_config(config)
    res = args.command.execute(args)

    # Shutdown logging
    logger.stop(res)

    return res


if __name__ == '__main__':
    sys.exit(main(sys.argv))
