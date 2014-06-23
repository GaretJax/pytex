from __future__ import absolute_import

import sys
import argparse

from pytex.processors import RstProcessor


def build_parser():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('file')

    return parser


def main(args=None):
    # Build argument parser and parse command line
    parser = build_parser()
    args = parser.parse_args(args)

    # Instantiate the processor and transform the file
    processor = RstProcessor()
    processor.process_file_out(args.file)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
