#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from __future__ import print_function # Fix python2 runtime error with end=x
from collections import defaultdict
from os import get_terminal_size
from taggregator.tagg import Match
import math
import statistics

class TerminalColours:
    END             = '\033[0m'
    HEADER          = '\033[1;37m'
    PRIORITY_NONE   = '\033[0m'
    PRIORITY_LOW    = '\033[0;32m'
    PRIORITY_MEDIUM = '\033[0;33m'
    PRIORITY_HIGH   = '\033[0;31m'

def get_truncated_text(text, max_length, truncate_indicator="..."):
    """
    Truncate text at given length and append truncate_indicator if truncated.
    If the text is shorter than or equal to max_length, just return text unmodified
    """
    return (text[:max_length - len(truncate_indicator)] + truncate_indicator) if len(text) > max_length else text

def log(text, tag, append_new_line=False):
    """
    Prints log entries which look like:
    [INFORMATION] Config file created at ~/.taggregator/config.json
    """
    print("[%s] %s" %(tag.upper(), text))

    if (append_new_line):
        print("\n")

def print_right_pad(text, pad_size, append_new_line=False):
    end = "\n" if append_new_line else ""
    print(text + pad_size * " ", end=end)

def print_separator():
    sep_count = int(terminal_columns * 0.75)
    dashes = "-" * sep_count
    print(dashes)

def get_priority_to_colour_map(priority_value_map):
    """
    Map a priority value to a colour based
    on its value relative to the median priority value.
    """
    priority_to_colour_map = { Match.NO_PRIORITY: TerminalColours.PRIORITY_NONE}
    median_value = statistics.median(priority_value_map.values())

    for p in priority_value_map.values():
        if p < median_value:
            priority_to_colour_map[p] = TerminalColours.PRIORITY_LOW
        elif p > median_value:
            priority_to_colour_map[p] = TerminalColours.PRIORITY_HIGH
        else:
            priority_to_colour_map[p] = TerminalColours.PRIORITY_MEDIUM

    return priority_to_colour_map

def get_highlight_colour(orig_colour):
    """
    Keep same colour but switch foreground with background.
    Reference https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters
    """
    return orig_colour.replace("0", "7")

def print_match_line(match, tag_marker, normal_colour, highlighted_colour, pad_size, append_new_line=False):
    """
    Prints a found match, highlighting the tag so that it is clear
    in case there is a line with two different tags.
    """
    line = match.line
    tag = match.tag

    # Find the beginning of the tag and slice the line up into 3 parts:
    # 1) Before the tag 2) During the tag 3) After the tag
    idx = line.find(tag) - len(tag_marker)
    end_idx = idx + len(tag) + len(tag_marker)

    before = line[0:idx]
    during = line[idx:end_idx]
    after = line[end_idx:len(line)]

    # Switch between normal and highlighted based on whether printing the tag
    to_print = normal_colour + before + highlighted_colour + during + normal_colour + after + TerminalColours.END
    print_right_pad(to_print, pad_size, append_new_line)

def print_matches(matches, tag_marker, priority_value_map):
    priority_to_colour_map = get_priority_to_colour_map(priority_value_map)

    # Arrange every match into a dictionary with a key the item's priority,
    # sorted so that we display the highest priority ones at the top.
    matches_by_priority = defaultdict(list)
    matches.sort(key=lambda x: x.priority, reverse=True)

    for match in matches:
        matches_by_priority[match.priority].append(match)

    # Calculate the longest piece of each type of data so that
    # we can do some simple maths to line them up nicely.
    size_longest_name = max([len(match.file_name) for match in matches], default=0)
    size_longest_line_no = max([len(str(match.line_number)) for match in matches], default=0)
    size_longest_line = max([len(match.line) for match in matches], default=0)
    section_padding = 2

    # Looks stupid to draw heading if there are no matches
    if len(matches) > 0:
        print("Your taggregator todo list:")
        print_separator()
    else:
        print("No taggregator tags found - start commenting your code!")

    for p in matches_by_priority: # Grab each key
        matches_by_priority[p].sort(key=lambda x: (x.tag)) # Sort each set of matches by tag in alphabetical order
        for match in matches_by_priority[p]: # Grab each match
            colour = priority_to_colour_map[match.priority]
            highlighted_colour = get_highlight_colour(colour)
            print_right_pad(match.file_name, size_longest_name - len(match.file_name) + section_padding)
            print_right_pad(":" + match.line_number, size_longest_line_no - len(match.line_number) + section_padding)
            print_match_line(match, tag_marker, colour, highlighted_colour, size_longest_line - len(match.line) + section_padding, append_new_line=True)

        # Separator in between sets of matches by priority
        print_separator()

terminal_columns = 80 # Sane default

try:
    terminal_columns = get_terminal_size()[0]
except OSError:
    pass # Leave at 80
