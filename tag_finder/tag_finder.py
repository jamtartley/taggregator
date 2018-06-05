#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from tag_finder import printer
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
    pattern_start = "**/*" if should_recurse else "*"

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

    try:
        with open(config_path) as config_json:
            return json.load(config_json)
    except JSONDecodeError as je:
        error_string = "Error in your tag_finder config file at line %d, column %d, exiting..." %(je.lineno, je.colno)
        printer.log(error_string, "fatal error")
        raise SystemExit()

def set_config_property(config, key, value):
    config[key] = value
    config_path = get_existing_config_path()

    printer.log("Found unset config property: '%s', setting it to '%s'" %(key, value), "warning")

    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)

def main(args):
    text_padding = 2
    root = os.getcwd() + "/" + args.root
    if not root.endswith("/"):
        root += "/"
    should_recurse = not args.no_recursion
    printer.is_verbose = args.verbose
    is_header_mode = args.print_headers

    config = get_config_file()
    default_config = get_default_config_json()

    for key in default_config:
        if key not in config:
            set_config_property(config, key, default_config[key])

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

    # @BUG(MEDIUM) Incorrect finding of files when running from outside project directory.
    # There are some issues with assigning the root from the command line if it is done
    # from higher up in the hierarchy than the project root folder
    tags = set([re.escape(tag.strip().upper()) for tag in config["tags"]])
    priority_regex = get_priority_regex(priorities)
    tag_regex = get_tag_regex(tag_marker, "|".join(tags), priority_regex)
    glob_patterns = get_glob_patterns(root, should_recurse, extensions)
    exclude = [os.getcwd() + "/" + d for d in config["exclude"]]

    files = [glob.iglob(pattern, recursive=should_recurse) for pattern in glob_patterns][0]
    matches = []

    for file_name in files:
        if any(file_name.startswith(e) for e in exclude):
            printer.verbose_log("Skipped file %s because it matched an exclusion rule" %(file_name), "information")
            continue

        try:
            for match in find_matches(tag_regex, file_name, priority_value_map):
                # Determine whether duplicate by checking if an item with the same
                # file name and line number has already been inserted into the match list
                if not any(m.file_name == match.file_name and m.line_number == match.line_number for m in matches):
                    matches.append(match)
        except IsADirectoryError:
            pass
        except UnicodeDecodeError:
            pass

    if not is_header_mode and len(matches) > 0:
        print("\n")

    # Arrange every match into a dictionary with a key the item's priority
    matches_by_property = defaultdict(list)
    matches.sort(key=lambda x: x.priority, reverse=True)
    longest_file_name_size = max([len(match.file_name) for match in matches], default=0)
    longest_line_number_size = max([len(str(match.line_number)) for match in matches], default=0)
    longest_line_size = max([len(match.line) for match in matches], default=0)

    for match in matches:
        matches_by_property[match.priority].append(match)

    for key in matches_by_property:
        matches_by_property[key].sort(key=lambda x: x.priority, reverse=True)

        if is_header_mode:
            printer.print_header(value_priority_map.get(key, "NONE"))

        for match in matches_by_property[key]:
            priority_colour = priority_colours[match.priority]
            file_name_padding = longest_file_name_size - len(match.file_name) + text_padding
            line_number_padding = longest_line_number_size - len(match.line_number) + text_padding
            line_padding = longest_line_size - len(match.line) + text_padding

            printer.print_right_pad(match.file_name, file_name_padding)
            printer.print_right_pad(":" + match.line_number, line_number_padding)
            printer.print_right_pad(priority_colour + match.line + printer.TerminalColours.END, line_padding, append_new_line=True)

    if (len(matches) > 0):
        print("\n")

default_priority = -1
config_folder_name = "/.tag_finder/"
config_file_name = "config.json"
current_dir_config_dir_path = os.getcwd() + config_folder_name
current_dir_config_file_path = current_dir_config_dir_path + config_file_name
home_config_dir_path = str(Path.home()) + config_folder_name
home_config_file_path = home_config_dir_path + config_file_name
