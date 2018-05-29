from . import tag_finder
import argparse
import os
import sys

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument("root", default=os.getcwd(), nargs="?", help="Path from which to start search")
    args = parser.parse_args()
    tag_finder.main(args)

if __name__ == "__main__":
    main()
