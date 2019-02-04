#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from taggregator import printer
from pathlib import Path
import glob
import itertools
import os
import re
import sys

class Match:
    DEFAULT_PRIORITY = -1

    def __init__(self, file_name, line_number, line, tag, priority):
        self.file_name = file_name
        self.line_number = str(line_number)
        self.line = line
        self.tag = tag
        self.priority = priority

    def __str__(self):
        return self.file_name

def get_glob_patterns(root, extensions):
    is_wildcard_extension = "*" in extensions
    pattern_start = "**/*"

    if is_wildcard_extension:
        return [os.path.join(root, pattern_start)]
    else:
        return [os.path.join(root, pattern_start) + "." + ext for ext in extensions]

def get_tag_regex(tag_marker, tag_string, priority_regex):
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
    regex_string = tag_marker + "(" + tag_string + ")" + r"\s*\(*" + priority_regex + "\)*"

    # Return regex which will match (for example): @HACK|SPEED|FEATURE(LOW|MEDIUM)
    # with the priority being an optional match
    return re.compile(regex_string, re.IGNORECASE)

def get_priority_regex(priorities):
    return "\s*(" + "|".join(priorities) + ")?\s*"

def find_matches(tag_regex, lower_tags, file_name, priority_value_map):
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

        if not any(t in lower_contents for t in lower_tags):
            return

        # @BUG(HIGH) Throws OSError on some files if in use
        # Can't repro on *nix but happens on Cygwin if the file is in use
        for number, line in enumerate(file_contents.split('\n'), 1):
            # @SPEED(MEDIUM) Regex search of processed line
            matches = tag_regex.findall(line)

            for match in matches:
                tag = match[0].upper()
                priority = match[1]
                priority_idx = priority_value_map.get(priority.upper(), Match.DEFAULT_PRIORITY)
                truncated_line = printer.get_truncated_text(line.strip(), 100)

                yield Match(file_name, number, truncated_line, tag, priority_idx)

def get_priority_value_map(all_priorities):
    """
    Maps an index of increasing size to each priority ranging from low -> high
    e.g. given ['LOW', 'MEDIUM', 'HIGH'] will return {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
    """
    return dict((priority_text.upper(), priority_index) for priority_index, priority_text in enumerate(all_priorities))

def main(config_map):
    tag_marker = re.escape(config_map["tag_marker"])
    extensions = config_map["extensions"]
    priorities = config_map["priorities"]
    tags = config_map["tags"]

    # Allow temporary overriding of tags from command line, check if command line flag
    # set. If yes use them, otherwise default to config file.
    #
    # We also do a large amount of the regex pre-processing we need to do here (escaping
    # special characters and compiling) so that we can avoid recomputing during the actual
    # file parsing phase.

    priority_value_map = get_priority_value_map(priorities)
    value_priority_map = dict(reversed(item) for item in priority_value_map.items())
    lower_tags = [t.lower() for t in tags]
    priority_regex = get_priority_regex(priorities)
    tag_regex = get_tag_regex(tag_marker, "|".join(tags), priority_regex)
    glob_patterns = get_glob_patterns(config_map["root"], extensions)
    exclude = [os.path.join(os.getcwd(), d) for d in config_map["exclude"]]

    file_sets = [glob.glob(pattern, recursive=True) for pattern in glob_patterns]
    files = [f for sublist in file_sets for f in sublist]
    matches = []

    for file_name in files:
        if any(file_name.startswith(e) for e in exclude):
            continue

        for match in find_matches(tag_regex, lower_tags, file_name, priority_value_map):
            # Determine whether duplicate by checking if an item with the same
            # file name and line number has already been inserted into the match list
            if not any(m.file_name == match.file_name and m.line_number == match.line_number for m in matches):
                matches.append(match)

    printer.print_matches(matches, priority_value_map)
