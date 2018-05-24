from collections import defaultdict
from itertools import groupby
import glob
import re

class Match:
    def __init__(self, file_name, line_number, line):
        self.file_name = file_name
        self.line_number = line_number
        self.line = line

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

root = "example_files/"
extensions = ["txt", "c"]
tags = ["@TODO", "@HACK", "@CLEANUP", "@FIXME"]
found_matches = defaultdict(list)

for files_of_extension in [glob.iglob(root + type_name_to_extension(ext), recursive=True) for ext in extensions]:
    for file_name in files_of_extension:
        for tag, match in find_matches(file_name):
            found_matches[tag].append(match)

for tag in found_matches:
    print(tag)
    print("-------------")

    for match in found_matches[tag]:
        print(match)

    print("\n")
