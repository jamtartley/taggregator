#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from . import printer
from collections import defaultdict
from json.decoder import JSONDecodeError
from pathlib import Path
import glob
import itertools
import json
import os
import pkg_resources
import re
import statistics
import sys

class Match:
    def __init__(self, file_name, line_number, line, tag, priority):
        self.file_name = file_name
        self.line_number = str(line_number)
        self.line = line
        self.tag = tag
        self.priority = priority

    def __str__(self):
        return self.file_name

def get_glob_patterns(root, should_recurse, extensions):
    is_wildcard_extension = "*" in extensions
    pattern_start = "/**/*" if should_recurse else "/*"

    if is_wildcard_extension:
        return [root + pattern_start]
    else:
        return [root + pattern_start + "." + ext for ext in extensions]

def get_tag_regex(tag_marker, tag_string, priority_regex):
    # -> match tag_marker + tag_string as group
    # -> match priority as group

    # @BUG(LOW) Slightly weird matching property
    # Because we have decided that priorities can be optional, we allow zero parentheses around
    # the priority regex. This has the interesting property that the line below would be marked
    # as high priority even though the user might not want it to be:
    # TODO High priority test
    # Not really sure if this is undesired behaviour or not.
    regex_string = tag_marker + "(" + tag_string + ")" + r"\s*\(*" + priority_regex + "\)*"

    # Return regex which will match (for example): @HACK|SPEED|TODO(LOW|MEDIUM)
    # with the priority being an optional match
    return re.compile(regex_string, re.IGNORECASE)

def get_priority_regex(priorities):
    return "\s*(" + "|".join(priorities) + ")?\s*"

def find_matches(tag_regex, file_name, priority_value_map):
    with open(file_name) as f:
        for number, line in enumerate(f, 1):
            # @SPEED(MEDIUM) Regex search of processed line
            matches = tag_regex.findall(line)

            for match in matches:
                tag = match[0].upper()
                priority = match[1]
                priority_idx = priority_value_map.get(priority.upper(), default_priority)
                truncated_line = printer.get_truncated_text(line.strip(), 100)

                yield Match(file_name, number, truncated_line, tag, priority_idx)

def get_priority_value_map(all_priorities):
    # Maps an index of increasing size to each priority ranging from low -> high
    # e.g. given ['LOW', 'MEDIUM', 'HIGH'] will return {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
    return dict((priority_text.upper(), priority_index) for priority_index, priority_text in enumerate(all_priorities))

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
    text_padding = 2
    root = args.root
    should_recurse = not args.disable_recursive_search
    printer.is_verbose = args.verbose
    is_simple_mode = args.simple_mode

    config = get_config_file()

    # @ROBUSTNESS(MEDIUM) Sanity check values retrieved from config file
    tag_marker = re.escape(config["tag_marker"])
    extensions = config["extensions"]
    priorities = config["priorities"]
    priority_value_map = get_priority_value_map(priorities)
    value_priority_map = dict(reversed(item) for item in priority_value_map.items())
    priority_colours = get_priority_colours(priority_value_map)

    # Allow temporary overriding of tags from command line, check if command line flag
    # set. If yes use them, otherwise default to config file.
    #
    # We also do a large amount of the regex pre-processing we need to do here (escaping
    # special characters and compiling) so that we can avoid recomputing during the actual
    # file parsing phase.

    # @TODO(MEDIUM) Allow runtime choosing of only certain priorities as is done with tags
    args_tags = [tag for tag in args.tags.split(",")] if args.tags is not None else None
    raw_tags = args_tags if args_tags is not None else config["tags"]
    tags = set([re.escape(tag.strip().upper()) for tag in raw_tags])
    priority_regex = get_priority_regex(priorities)
    tag_regex = get_tag_regex(tag_marker, "|".join(tags), priority_regex)
    glob_patterns = get_glob_patterns(root, should_recurse, extensions)
    files = [glob.iglob(pattern, recursive=should_recurse) for pattern in glob_patterns][0]
    matches = []

    for file_name in files:
        printer.verbose_log(file_name, "searching for tags")

        try:
            matches.extend(find_matches(tag_regex, file_name, priority_value_map))
        except IsADirectoryError:
            pass
        except UnicodeDecodeError:
            pass

    if is_simple_mode:
        print("\n")

    # Arrange every match into a dictionary with the key as either
    # the tag of the match or its priority then run through and print to standard output
    # @USABILITY(LOW) Allow user to switch sort by tag/priority modes
    is_by_tag = True
    matches_by_property = defaultdict(list)
    matches.sort(key=lambda x: x.tag if is_by_tag else x.priority, reverse=True)
    longest_file_name_size = max(len(match.file_name) for match in matches)
    longest_line_number_size = max(len(str(match.line_number)) for match in matches)
    longest_line_size = max(len(match.line) for match in matches)

    for match in matches:
        matches_by_property[match.tag if is_by_tag else match.priority].append(match)

    for key in matches_by_property:
        matches_by_property[key].sort(key=lambda x: x.priority, reverse=True)

        if not is_simple_mode:
            printer.print_header(key if is_by_tag else value_priority_map.get(key, "NONE"))

        for match in matches_by_property[key]:
            priority_colour = priority_colours[match.priority]
            file_name_padding = longest_file_name_size - len(match.file_name) + text_padding
            line_number_padding = longest_line_number_size - len(match.line_number) + text_padding
            line_padding = longest_line_size - len(match.line) + text_padding

            printer.print_right_pad(match.file_name, file_name_padding)
            printer.print_right_pad(":" + match.line_number, line_number_padding)
            printer.print_right_pad(priority_colour + match.line + printer.TerminalColours.END, line_padding, append_new_line=True)

    print("\n")

default_priority = -1
config_folder_name = "/.tag_finder/"
config_file_name = "config.json"
current_dir_config_dir_path = os.getcwd() + config_folder_name
current_dir_config_file_path = os.getcwd() + config_folder_name + config_file_name
home_config_dir_path = str(Path.home()) + config_folder_name
home_config_file_path = home_config_dir_path + config_file_name
