import pytest
from taggregator import printer as printer

def test_get_truncated_text():
    text = "Lorem ipsum dolor sit amet"
    truncate_indicator = "..."
    trunc_len = len(truncate_indicator)

    assert(len(text) == 26)

    truncated_20 = printer.get_truncated_text(text, 20, truncate_indicator)
    truncated_full = printer.get_truncated_text(text, len(text), truncate_indicator)
    truncated_over = printer.get_truncated_text(text, 100, truncate_indicator)

    assert(len(truncated_20) == 20)
    assert(truncated_20[20 - trunc_len:] == truncate_indicator)

    # Method should return the text itself if it fits into the length given
    assert(len(truncated_full) == len(text))
    assert(truncated_full == text)
    assert(truncated_over == text)

def test_get_priority_to_colour_map():
    priority_value_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    expected_colour_map = {-1: printer.TerminalColours.PRIORITY_NONE, 0: printer.TerminalColours.PRIORITY_LOW, 1: printer.TerminalColours.PRIORITY_MEDIUM, 2: printer.TerminalColours.PRIORITY_HIGH}
    actual_colour_map = printer.get_priority_to_colour_map(priority_value_map)

    assert(expected_colour_map == actual_colour_map)
