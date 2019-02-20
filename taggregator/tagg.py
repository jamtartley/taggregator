#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from taggregator import printer
from pathlib import Path
import itertools
import os
import re
import sys

class Match:
    NO_PRIORITY = -1

    def __init__(self, file_name, line_number, line, tag, priority):
        self.file_name = file_name
        self.line_number = str(line_number)
        self.line = line
        self.tag = tag
        self.priority = priority

    def __str__(self):
        return self.file_name

    def __eq__(self, other):
        return self.file_name == other.file_name and self.line_number == other.line_number and self.tag == other.tag

def get_piped_list(items):
    return "|".join(items)

def get_tag_regex(tag_marker, tags, priority_regex):
    """
    Get compiled regex for matching tags by:
        -> match tag_marker + tag_string as group
        -> match priority as group
    """

    # @BUG(LOW) Slightly weird matching property
    # Because we have decided that priorities can be optional, we allow zero parentheses around
    # the priority regex. This has the interesting property that the line below would be marked
    # as high priority even though the user might not want it to be:
    # @FEATURE High priority test
    # Not really sure if this is undesired behaviour or not.
    regex_string = tag_marker + "(" + get_piped_list(tags) + ")" + r"\s*\(*" + priority_regex + "\)*"

    # Return regex which will match (for example): @HACK|SPEED|FEATURE(LOW|MEDIUM)
    # with the priority being an optional match
    return re.compile(regex_string, re.IGNORECASE)

def get_priority_regex(priorities):
    return "\s*(" + get_piped_list(priorities) + ")?\s*"

def find_matches(tag_regex, tags, file_name, priority_value_map):
    if os.path.isdir(file_name):
        return

    # @SPEED(HIGH) File opening/reading
    # Profiling shows that this is the greatest bottleneck in the app
    # at the minute, experiments with multiprocessing only slowed it down
    # because it is IO bound work
    with open(file_name) as f:
        # Read whole file into one buffer and see if any of the tags
        # match against it so we dont need to do the expensive regex
        # findall on every line individually unless we find a whole match
        try:
            file_contents = f.read()
        except UnicodeDecodeError:
            # Ignore non utf-8 files
            return

        lower_contents = file_contents.lower()
        lower_tags = [t.lower() for t in tags]

        if any(t in lower_contents for t in lower_tags):
            # @BUG(HIGH) Throws OSError on some files if in use
            # Can't repro on *nix but happens on Cygwin if the file is in use
            for number, line in enumerate(file_contents.split('\n'), 1):
                # @SPEED(MEDIUM) Regex search of processed line
                matches = tag_regex.findall(line)

                for match in matches:
                    tag = match[0].upper()
                    priority = match[1]
                    priority_idx = priority_value_map.get(priority.upper(), Match.NO_PRIORITY)
                    truncated_line = printer.get_truncated_text(line.strip(), 100)

                    yield Match(file_name, number, truncated_line, tag, priority_idx)

def get_priority_value_map(all_priorities):
    """
    Maps an index of increasing size to each priority ranging from low -> high
    e.g. given ['LOW', 'MEDIUM', 'HIGH'] will return {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
    """
    return dict((priority_text.upper(), priority_index) for priority_index, priority_text in enumerate(all_priorities))

def run(config_map):
    tag_marker = re.escape(config_map["tag_marker"])
    extensions = config_map["extensions"]
    priorities = config_map["priorities"]
    tags = config_map["tags"]

    priority_value_map = get_priority_value_map(priorities)
    value_priority_map = dict(reversed(item) for item in priority_value_map.items())
    priority_regex = get_priority_regex(priorities)
    tag_regex = get_tag_regex(tag_marker, tags, priority_regex)
    exclude = [os.path.join(os.getcwd(), d) for d in config_map["exclude"]]
    can_search_any_extension = "*" in extensions

    files = []

    for root, dirs, files_in_dir in os.walk(os.getcwd()):
        for file_name in files_in_dir:
            file_path = os.path.join(root, file_name)
            # We only want to search for tags in files which have one of the correct
            # extensions (or user has chosen to include every extension with '*')
            # and are not inside one of the excluded folders.
            if can_search_any_extension or any(file_path.endswith(ext) for ext in extensions):
                if not any(file_path.startswith(e) for e in exclude):
                    files.append(file_path)

    matches = []

    for file_name in files:
        for match in find_matches(tag_regex, tags, file_name, priority_value_map):
            # Equality check is handled by the overridden __eq__ in the Match class
            if not any(match == m for m in matches):
                matches.append(match)

    printer.print_matches(matches, tag_marker, priority_value_map)
