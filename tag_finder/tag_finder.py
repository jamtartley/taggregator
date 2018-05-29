#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from collections import defaultdict
from itertools import groupby
from pathlib import Path
from shutil import copyfile
import glob
import json
import os
import re
import statistics
import sys

class TerminalColours():
    END = '\033[0m'
    HEADER = '\033[1;37m'
    PRIORITY_NONE = END
    PRIORITY_LOW = '\033[0;32m'
    PRIORITY_MEDIUM = '\033[0;33m'
    PRIORITY_HIGH = '\033[0;31m'

class Match:
    def __init__(self, file_name, line_number, line, priority):
        global longest_file_name
        global longest_line_number
        global longest_line

        self.file_name = file_name
        self.line_number = str(line_number)
        self.line = line
        self.priority = priority

        longest_file_name = max([file_name, longest_file_name], key=len)
        longest_line_number = max([str(line_number), longest_line_number], key=len)
        longest_line = max([line, longest_line], key=len)


    def __str__(self):
        return self.file_name

def type_name_to_extension(t):
    return "/**/*." + t

def get_truncated_text(text, max_length, truncate_indicator="..."):
    truncate_at = max_length - len(truncate_indicator)
    return (text[:truncate_at] + truncate_indicator) if len(text) > truncate_at else text

def find_matches(tags, tag_marker, file_name, priority_value_map, is_case_sensitive):
    with open(file_name) as f:
        for number, line in enumerate(f):
            for tag in tags:
                processed_tag = tag if is_case_sensitive else tag.upper()
                processed_line = line if is_case_sensitive else line.upper()
                regex = re.compile(re.escape(tag_marker + processed_tag) + r"\(([^)]+)\)")
                priority_match = regex.search(processed_line)

                if priority_match is not None:
                    truncated_line = get_truncated_text(line.strip(), 100)
                    priority_char_idx = processed_line.find(processed_tag)
                    priority = default_priority
                    priority_text = priority_match.group(1)
                    priority = priority_value_map.get(priority_text, default_priority)

                    yield tag, Match(file_name, number, truncated_line, priority)

def get_priority_value_map(all_priorities):
    priority_value_map = {}

    for number, p in enumerate(all_priorities):
        priority_value_map[p] = number

    return priority_value_map

def get_priority_colours(priority_value_map):
    colour_map = {default_priority: TerminalColours.PRIORITY_NONE}
    median_value = statistics.median(priority_value_map.values())

    for p in priority_value_map:
        priority_value = priority_value_map[p]

        if priority_value < median_value:
            colour_map[priority_value] = TerminalColours.PRIORITY_LOW
        elif priority_value > median_value:
            colour_map[priority_value] = TerminalColours.PRIORITY_HIGH
        else:
            colour_map[priority_value] = TerminalColours.PRIORITY_MEDIUM

    return colour_map

def print_right_pad(text, pad_size, is_end=False):
    print(text + pad_size * " ", end = "\n" if is_end else "")

def verbose_log(text, append_new_line=False):
    if not is_verbose:
        return

    print(text + ("\n" if append_new_line else ""))

def main(args):
    global is_verbose

    found_matches = defaultdict(list)
    text_padding = 2
    root = args.root
    is_verbose = args.verbose
    config = {}
    config_path = ""
    current_dir_config = os.getcwd() + "/.tag_finder/config.json"
    home_path = str(Path.home()) + "/.tag_finder/config.json"

    if os.path.isfile(current_dir_config):
        config_path = current_dir_config
    else:
        if os.path.isfile(home_path):
            config_path = home_path

    if config_path != "":
        verbose_log("Config found at: " + config_path, True)
    else:
        verbose_log("No config file found!")
        home_config_path_dir = str(Path.home()) + "/.tag_finder"

        if not os.path.exists(home_config_path_dir):
            os.makedirs(home_config_path_dir)
            verbose_log("Creating dir ~/.tag_finder")

        copyfile("tag_finder/default_config.json", home_config_path_dir + "/config.json")
        verbose_log("Creating default config file at: " + home_path)
        config_path = home_path

    with open(config_path) as config_json:
        config = json.load(config_json)

    is_case_sensitive = config["is_case_sensitive"]
    tag_marker = config["tag_marker"]
    tags = config["tags"]
    extensions = config["extensions"]
    priorities = config["priorities"]
    priority_value_map = get_priority_value_map(priorities)
    priority_colours = get_priority_colours(priority_value_map)

    for files_of_extension in [glob.iglob(root + type_name_to_extension(ext), recursive=True) for ext in extensions]:
        for file_name in files_of_extension:
            verbose_log("Searching: " + file_name)

            try:
                for tag, match in find_matches(tags, tag_marker, file_name, priority_value_map, is_case_sensitive):
                    found_matches[tag].append(match)
            except IsADirectoryError:
                pass
            except UnicodeDecodeError:
                pass

    for tag in found_matches:
        found_matches[tag].sort(key=lambda x: x.priority, reverse=True)

        print("\n")
        print(TerminalColours.HEADER + (tag if is_case_sensitive else tag.upper()) + TerminalColours.END)
        print("--------------------------------------------------")

        for match in found_matches[tag]:
            priority_colour = priority_colours[match.priority]

            print_right_pad(match.file_name, len(longest_file_name) - len(match.file_name) + text_padding)
            print_right_pad(":" + match.line_number, len(longest_line_number) - len(match.line_number) + text_padding)
            print_right_pad(priority_colour + match.line + TerminalColours.END, len(longest_line) - len(match.line) + text_padding, True)

    print("\n")

longest_file_name = ""
longest_line_number = ""
longest_line = ""
default_priority = -1
is_verbose = False
