#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

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

def print_right_pad(text, pad_size, is_end=False):
    end = "\n" if is_end else ""
    print(text + pad_size * " ", end=end)

def log(text, tag_text, append_new_line=False):
    log_tag = "[%s] " %(tag_text.upper())
    print(log_tag + text + ("\n" if append_new_line else ""))

def verbose_log(text, tag_text, append_new_line=False):
    if not is_verbose:
        return

    log(text, tag_text, append_new_line)

def print_tag_header(tag):
    dash_count = 80
    dashes = "-" * dash_count
    print("\n")
    print(dashes)
    print(TerminalColours.HEADER + tag + TerminalColours.END)
    print(dashes)

is_verbose = False
