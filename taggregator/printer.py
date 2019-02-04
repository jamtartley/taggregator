#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from __future__ import print_function # Fix python2 runtime error with end=x
from collections import defaultdict
from os import get_terminal_size
from .taggregator import Match
import statistics

class TerminalColours:
    END = '\033[0m'
    HEADER = '\033[1;37m'
    PRIORITY_NONE = END
    PRIORITY_LOW = '\033[0;32m'
    PRIORITY_MEDIUM = '\033[0;33m'
    PRIORITY_HIGH = '\033[0;31m'

def get_truncated_text(text, max_length, truncate_indicator="..."):
    """
    Truncate text at given length and append truncate_indicator if truncated.
    If the text is shorter than or equal to max_length, just return text unmodified
    """
    return (text[:max_length] + truncate_indicator) if len(text) > max_length else text

def print_right_pad(text, pad_size, append_new_line=False):
    end = "\n" if append_new_line else ""
    print(text + pad_size * " ", end=end)

def print_new_line():
    print("\n")

def log(text, tag_text, append_new_line=False):
    log_tag = "[%s] " %(tag_text.upper())
    print(log_tag + text)

    if (append_new_line):
        print_new_line()

def print_separator():
    dash_count = int(terminal_columns / 2)
    dashes = "-" * dash_count
    print(dashes)

def get_priority_to_colour_map(priority_value_map):
    priority_to_colour_map = { Match.DEFAULT_PRIORITY: TerminalColours.PRIORITY_NONE}
    median_value = statistics.median(priority_value_map.values())

    for p in priority_value_map.values():
        if p < median_value:
            priority_to_colour_map[p] = TerminalColours.PRIORITY_LOW
        elif p > median_value:
            priority_to_colour_map[p] = TerminalColours.PRIORITY_HIGH
        else:
            priority_to_colour_map[p] = TerminalColours.PRIORITY_MEDIUM

    return priority_to_colour_map

def print_matches(matches, priority_value_map):
    # Arrange every match into a dictionary with a key the item's priority
    priority_to_colour_map = get_priority_to_colour_map(priority_value_map)
    matches_by_priority = defaultdict(list)
    matches.sort(key=lambda x: x.priority, reverse=True)
    max_file_name_size = max([len(match.file_name) for match in matches], default=0)
    max_line_number_size = max([len(str(match.line_number)) for match in matches], default=0)
    max_line_size = max([len(match.line) for match in matches], default=0)
    text_padding = 2

    for match in matches:
        matches_by_priority[match.priority].append(match)

    print_separator()

    for p in matches_by_priority: # Grab each key
        for match in matches_by_priority[p]: # Grab each match
            print_match(match, priority_to_colour_map, max_file_name_size, max_line_number_size, max_line_size, text_padding)

        print_separator()

    if (len(matches) > 0):
        print_new_line()

def print_match(match, priority_to_colour_map, max_file_name_size, max_line_number_size, max_line_size, text_padding):
    priority_colour = priority_to_colour_map[match.priority]

    file_name_padding = max_file_name_size - len(match.file_name) + text_padding
    line_number_padding = max_line_number_size - len(match.line_number) + text_padding
    line_padding = max_line_size - len(match.line) + text_padding

    print_right_pad(match.file_name, file_name_padding)
    print_right_pad(":" + match.line_number, line_number_padding)
    print_right_pad(priority_colour + match.line + TerminalColours.END, line_padding, append_new_line=True)

terminal_columns = 80

try:
    terminal_columns = get_terminal_size()[0]
except OSError:
    pass # Leave at 80
