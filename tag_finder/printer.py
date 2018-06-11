#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from __future__ import print_function # Fix python2 runtime error with end=x
from os import get_terminal_size

class TerminalColours():
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

def log(text, tag_text, append_new_line=False):
    log_tag = "[%s] " %(tag_text.upper())
    print(log_tag + text + ("\n" if append_new_line else ""))

def verbose_log(text, tag_text, append_new_line=False):
    if not is_verbose:
        return

    log(text, tag_text, append_new_line)

def print_header(text, colour):
    dash_count = int(terminal_columns / 2)
    dashes = "-" * dash_count
    print("\n")
    print(dashes)
    print(colour + str(text) + TerminalColours.END)
    print(dashes)

is_verbose = False
terminal_columns = 80

try:
    terminal_columns = get_terminal_size()[0]
except OSError:
    pass # Leave at 80
