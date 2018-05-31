#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from . import printer
from collections import defaultdict
from itertools import groupby
from json.decoder import JSONDecodeError
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
        self.file_name = file_name
        self.line_number = str(line_number)
        self.line = line
        self.priority = priority

    def __str__(self):
        return self.file_name

def type_name_to_extension(t):
    return "/**/*." + t

def get_tag_regex(tag_marker, tags, priority_regex):
    tag_string = "|".join(tags)
    regex_string = tag_marker + "(" + tag_string + ")" + r"\(*(" + priority_regex + ")?\)*" 

    # Return regex which will match (for example): @HACK|SPEED|TODO(LOW|MEDIUM)
    # with the priority being an optional match
    return re.compile(regex_string)

def get_priority_regex(priorities):
    return "|".join(priorities)

def find_matches(tag_regex, file_name, priority_value_map, is_case_sensitive):
    with open(file_name) as f:
        for number, line in enumerate(f):
            processed_line = (line if is_case_sensitive else line.upper()).replace(" ", "")
            truncated_line = printer.get_truncated_text(line.strip(), 100)

            # @SPEED(MEDIUM) Regex search of processed line
            matches = tag_regex.findall(processed_line)

            for match in matches:
                tag = match[0]
                priority = match[1]
                priority_idx = priority_value_map.get(priority, default_priority)

                yield tag, Match(file_name, number, truncated_line, priority_idx)

def get_priority_value_map(all_priorities):
    # Maps an index of increasing size to each priority ranging from low -> high
    # e.g. given ['LOW', 'MEDIUM', 'HIGH'] will return {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
    return dict((priority_text, priority_index) for priority_index, priority_text in enumerate(all_priorities))

def get_priority_colours(priority_value_map):
    colour_map = {default_priority: printer.TerminalColours.PRIORITY_NONE}
    median_value = statistics.median(priority_value_map.values())

    for p in priority_value_map.values():
        if p < median_value:
            colour_map[p] = printer.TerminalColours.PRIORITY_LOW
        elif p > median_value:
            colour_map[p] = printer.TerminalColours.PRIORITY_HIGH
        else:
            colour_map[p] = printer.TerminalColours.PRIORITY_MEDIUM

    return colour_map

def get_existing_config_path():
    # Look for existing config in first {current dir}/.tag_finder and then .tag_finder
    current_dir_config_file_path = os.getcwd() + config_folder_name + config_file_name

    if os.path.isfile(current_dir_config_file_path):
        return current_dir_config_file_path
    else:
        if os.path.isfile(home_config_file_path):
            return home_config_file_path

    return None

def create_default_config_file_current_dir():
    create_default_config_file(current_dir_config_dir_path)

def create_default_config_file(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        printer.log("Creating config directory at: " + directory, "information")

    path = directory + config_file_name

    if os.path.exists(path):
        while True:
            answer = input("[WARNING] File already exists, do you wish to overwrite it? (y/n): ").lower().strip()
            if answer == "y":
                copy_default_config_to_path(path)
                return path
            elif answer == "n":
                return None

    copy_default_config_to_path(path)
    return path

def copy_default_config_to_path(path):
    default_config_json = get_default_config_json()
    printer.log("Creating config file at: " + path, "information")

    with open(path, "w") as config_file:
        json.dump(default_config_json, config_file, indent=4)

def get_default_config_json():
    with open(pkg_resources.resource_filename(__name__, "default_config.json"), encoding="utf-8") as default_config_file:
        return json.loads(default_config_file.read())

def get_config_file():
    # If neither ~/.tag_finder or {current dir}/.tag_finder exists,
    # create ~/.tag_finder and copy in the default config file from bundle resources
    config_path = get_existing_config_path()

    if config_path:
        printer.verbose_log("Config found at: " + config_path, "information", append_new_line=True)
    else:
        printer.log("No config file found!", "warning")
        config_path = create_default_config_file(home_config_dir_path)

    # @ROBUSTNESS(MEDIUM) Detect malformed config file
    # Currently we just exit when we detect that the JSON file is not strictly correct JSON.
    #
    # @USABILITY(MEDIUM) We should be further analysing the file we found and maybe giving the user 
    # the option to fix it themselves or overwrite with the default config file
    try:
        with open(config_path) as config_json:
            return json.load(config_json)
    except JSONDecodeError as je:
        error_string = "Error in your tag_finder config file at line %d, column %d, exiting..." %(je.lineno, je.colno)
        printer.log(error_string, "fatal error")
        raise SystemExit()

def main(args):
    found_matches = defaultdict(list)
    text_padding = 2
    longest_file_name = ""
    longest_line_number = ""
    longest_line = ""

    config = get_config_file()
    root = args.root

    printer.is_verbose = args.verbose

    # @ROBUSTNESS(MEDIUM) Sanity check values retrieved from config file
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
    priority_regex = get_priority_regex(priorities)
    tag_regex = get_tag_regex(tag_marker, tags, priority_regex)

    for files_of_extension in [glob.iglob(root + type_name_to_extension(ext), recursive=True) for ext in extensions]:
        for file_name in files_of_extension:
            printer.verbose_log(file_name, "searching for tags")

            try:
                for tag, match in find_matches(tag_regex, file_name, priority_value_map, is_case_sensitive):
                    found_matches[tag].append(match)

                    longest_file_name = max([match.file_name, longest_file_name], key=len)
                    longest_line_number = max([str(match.line_number), longest_line_number], key=len)
                    longest_line = max([match.line, longest_line], key=len)

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

default_priority = -1
config_folder_name = "/.tag_finder/"
config_file_name = "config.json"
current_dir_config_dir_path = os.getcwd() + config_folder_name
current_dir_config_file_path = os.getcwd() + config_folder_name + config_file_name
home_config_dir_path = str(Path.home()) + config_folder_name
home_config_file_path = home_config_dir_path + config_file_name
