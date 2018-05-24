from collections import defaultdict
from itertools import groupby
import argparse
import glob
import re

tag_colour = "\033[92m"
colour_end = "\033[0m"
extensions = []
tags = ["@TODO", "@HACK", "@CLEANUP", "@FIXME"]
found_matches = defaultdict(list)
text_padding = 4
longest_file_name = ""
longest_line_number = ""
longest_line = ""

class Match:
    def __init__(self, file_name, line_number, line):
        global longest_file_name
        global longest_line_number
        global longest_line

        self.file_name = file_name
        self.line_number = str(line_number)
        self.line = line

        longest_file_name = max([file_name, longest_file_name], key=len)
        longest_line_number = max([str(line_number), longest_line_number], key=len)
        longest_line = max([line, longest_line], key=len)


    def __str__(self):
        return self.file_name

def type_name_to_extension(t):
    return "**/*." + t

def find_matches(file_name):
    with open(file_name, "r") as f:
        for number, line in enumerate(f):
            for tag in tags:
                if tag in line:
                    yield tag, Match(file_name, number, line.rstrip())

def print_right_pad(text, pad_size, is_end=False):
    print(text + pad_size * " ", end = "\n" if is_end else "")

def parse_file_extensions(args):
    return [e.strip() for e in args.extensions.split(",")]

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--root", default="", help="Path from which to start search")
parser.add_argument("-e", "--extensions", default="txt", help="Comma-separated list of extensions to test")
args = parser.parse_args()

root = args.root
extensions = parse_file_extensions(args)

for files_of_extension in [glob.iglob(root + type_name_to_extension(ext), recursive=True) for ext in extensions]:
    for file_name in files_of_extension:
        for tag, match in find_matches(file_name):
            found_matches[tag].append(match)

for tag in found_matches:
    print(tag_colour + tag + colour_end)
    print("-------------")

    for match in found_matches[tag]:
        print_right_pad(match.file_name, len(longest_file_name) - len(match.file_name) + text_padding)
        print_right_pad(":" + match.line_number, len(longest_line_number) - len(match.line_number) + text_padding)
        print_right_pad(match.line, len(longest_line) - len(match.line) + text_padding, True)

    print("\n")
