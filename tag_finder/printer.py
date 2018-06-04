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
    truncate_at = max_length - len(truncate_indicator)
    return (text[:truncate_at] + truncate_indicator) if len(text) > truncate_at else text

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

def print_header(text):
    dash_count = int(terminal_columns / 2)
    dashes = "-" * dash_count
    print("\n")
    print(dashes)
    print(TerminalColours.HEADER + str(text) + TerminalColours.END)
    print(dashes)

is_verbose = False
terminal_columns = 80

try:
    terminal_columns = get_terminal_size()[0]
except OSError:
    pass # Leave at 80
