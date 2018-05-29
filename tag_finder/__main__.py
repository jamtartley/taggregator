#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from . import tag_finder
import argparse
import os
import sys

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument("root", default=os.getcwd(), nargs="?", help="Path from which to start search")
    parser.add_argument("-v", "--verbose", action="store_true", help="Set if program should print verbose output")
    args = parser.parse_args()
    tag_finder.main(args)

if __name__ == "__main__":
    main()
