#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from . import printer
from collections import defaultdict
from itertools import groupby
from pathlib import Path
import glob
import json
import os
import pkg_resources
import re
import statistics
import sys

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

def find_matches(tags, tag_regex_map, file_name, priority_value_map, is_case_sensitive):
    with open(file_name) as f:
        for number, line in enumerate(f):
            for tag in tags:
                processed_line = line if is_case_sensitive else line.upper()
                priority_match = tag_regex_map[tag].search(processed_line)

                if priority_match is not None:
                    truncated_line = printer.get_truncated_text(line.strip(), 100)
                    priority_char_idx = processed_line.find(tag)
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
    colour_map = {default_priority: printer.TerminalColours.PRIORITY_NONE}
    median_value = statistics.median(priority_value_map.values())

    for p in priority_value_map:
        priority_value = priority_value_map[p]

        if priority_value < median_value:
            colour_map[priority_value] = printer.TerminalColours.PRIORITY_LOW
        elif priority_value > median_value:
            colour_map[priority_value] = printer.TerminalColours.PRIORITY_HIGH
        else:
            colour_map[priority_value] = printer.TerminalColours.PRIORITY_MEDIUM

    return colour_map

def get_existing_config_path(current_dir_config, home_config):
    if os.path.isfile(current_dir_config):
        return current_dir_config
    else:
        if os.path.isfile(home_config):
            return home_config

    return ""

def get_created_config_path(home_config_dir_path, home_config_file_path, default_config_json):
    if not os.path.exists(home_config_dir_path):
        os.makedirs(home_config_dir_path)
        printer.log("Creating default config directory at: " + home_config_dir_path, "information")

    printer.log("Creating default config file at: " + home_config_file_path, "information")

    with open(home_config_file_path, "w") as home_file:
        json.dump(default_config_json, home_file, indent=4)

    return home_config_file_path

def get_default_config_json():
    with open(pkg_resources.resource_filename(__name__, "default_config.json"), encoding="utf-8") as default_config_file:
        return json.loads(default_config_file.read())

def get_config_file():
    # Look for existing config in first {current dir}/.tag_finder and then ~/.tag_finder 
    # If neither of these exist, create ~/.tag_finder and copy in the default config
    # file from bundle resources
    config_folder_name = "/.tag_finder/"
    config_file_name = "config.json"
    current_dir_config_file_path = os.getcwd() + config_folder_name + config_file_name
    home_config_dir_path = str(Path.home()) + config_folder_name
    home_config_file_path = home_config_dir_path + config_file_name
    default_config_json = get_default_config_json()
    config_path = get_existing_config_path(current_dir_config_file_path, home_config_file_path)

    if config_path != "":
        printer.verbose_log("Config found at: " + config_path, "information", append_new_line=True)
    else:
        printer.log("No config file found!", "warning")
        config_path = get_created_config_path(home_config_dir_path, home_config_file_path, default_config_json)

    # @ROBUSTNESS(MEDIUM): Detect malformed config file
    # We should be analysing the file we found and if it isn't in the format we expect
    # we should be logging a warning and either giving the user the chance to abort and fix
    # it or overwrite it with default settings
    with open(config_path) as config_json:
        return json.load(config_json)

def main(args):
    found_matches = defaultdict(list)
    text_padding = 2

    config = get_config_file()
    root = args.root

    printer.is_verbose = args.verbose

    is_case_sensitive = config["is_case_sensitive"]
    tag_marker = re.escape(config["tag_marker"])
    extensions = config["extensions"]
    priorities = config["priorities"]
    priority_value_map = get_priority_value_map(priorities)
    priority_colours = get_priority_colours(priority_value_map)

    # Allow temporary overriding of tags from command line, check if command line flag
    # set. If yes use them, otherwise default to config file.
    #
    # We also do a large amount of the regex pre-processing we need to do here (escaping
    # special characters and compiling) so that we can avoid recomputing during the actual
    # file parsing phase.

    args_tags = [tag.strip() for tag in args.tags.split(",")] if args.tags is not None else None
    raw_tags = args_tags if args_tags is not None else config["tags"]
    tags = [re.escape(tag if is_case_sensitive else tag.upper()) for tag in raw_tags]
    tag_regex_map = {t:r for t,r in [(tag, re.compile(tag_marker + tag + r"\(([^)]+)\)")) for tag in tags]}

    for files_of_extension in [glob.iglob(root + type_name_to_extension(ext), recursive=True) for ext in extensions]:
        for file_name in files_of_extension:
            printer.verbose_log(file_name, "searching for tags")

            try:
                for tag, match in find_matches(tags, tag_regex_map, file_name, priority_value_map, is_case_sensitive):
                    found_matches[tag].append(match)
            except IsADirectoryError:
                pass
            except UnicodeDecodeError:
                pass

    for tag in found_matches:
        found_matches[tag].sort(key=lambda x: x.priority, reverse=True)

        printer.print_tag_header(tag if is_case_sensitive else tag.upper())

        for match in found_matches[tag]:
            priority_colour = priority_colours[match.priority]
            file_name_padding = len(longest_file_name) - len(match.file_name) + text_padding
            line_number_padding = len(longest_line_number) - len(match.line_number) + text_padding
            line_padding = len(longest_line) - len(match.line) + text_padding

            printer.print_right_pad(match.file_name, file_name_padding) 
            printer.print_right_pad(":" + match.line_number, line_number_padding)
            printer.print_right_pad(priority_colour + match.line + printer.TerminalColours.END, line_padding, is_end=True)

    print("\n")

longest_file_name = ""
longest_line_number = ""
longest_line = ""
default_priority = -1
