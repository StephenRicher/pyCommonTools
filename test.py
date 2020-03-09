#!/usr/bin/env python

"""
Template script for demonstarting pyCommonTools argeparse commands.
"""

import sys
import pyCommonTools as pct
import argparse
from version import __version__

def main():

    epilog = 'Stephen Richer, University of Bath, Bath, UK (sr467@bath.ac.uk)'

    parser = pct.make_parser(epilog = epilog, version=__version__)

    base_args = pct.get_base_args()
    in_arg = pct.get_in_arg()
    subparser = pct.make_subparser(parser)

    run_parser = subparser.add_parser(
        'run', help='Reverse file contents',
        description=run.__doc__,
        parents=[base_args, in_arg],
        epilog=parser.epilog)
    run_parser.add_argument(
        '-n', '--number', default=[0],
        help='Enter a number. (default: %(default)s)')

    run_parser.set_defaults(function=run)

    return (pct.execute(parser))


def run(infile, number):

    log = pct.create_logger()
    log.debug('hello')
    with pct.open(infile) as f:
        for line in f:
            print(line[::-1])


main()
