#!/usr/bin/env python

"""
Template script for demonstarting pyCommonTools argeparse commands. 
"""

import sys
import pyCommonTools as pct
import argparse

def main():

    epilog = 'Stephen Richer, University of Bath, Bath, UK (sr467@bath.ac.uk)'
    
    parser = pct.make_parser(epilog = epilog)
    base_args = pct.get_base_args()
    subparser = pct.make_subparser(parser)

    run_parser = subparser.add_parser(
        'run', help='Reverse file contents',
        description=run.__doc__,
        parents=[base_args],
        epilog=epilog)
    run_parser.add_argument(
        '-n', '--number', default=[0],
        help='Enter a number. (default: %(default)s)')
    run_parser.add_argument(
        '-o', '--out',
        help='Output file. (default: stdout)')
    run_parser.add_argument(
        'infile', nargs = '?', 
        help='Input file. (default: stdin)')
       
    run_parser.set_defaults(function=run)
    
    return (pct.execute(parser))
    

def run(infile, out, number):

    with pct.open(infile) as f:
        with pct.open(out, 'w') as fo:
            for line in f:
                fo.write(line[::-1])


main()
