import pytest
from taggregator import printer as printer

def test_get_truncated_text():
    text = "Lorem ipsum dolor sit amet"
    truncate_indicator = "..."

    assert(len(text) == 26)

    truncated_20 = printer.get_truncated_text(text, 20, truncate_indicator)
    truncated_full = printer.get_truncated_text(text, len(text), truncate_indicator)
    truncated_over = printer.get_truncated_text(text, 100, truncate_indicator)

    assert(len(truncated_20) == 20 + len(truncate_indicator))
    assert(truncated_20[20:20 + len(truncate_indicator)] == "...")

    # Method should return the text itself if it fits into the length given
    assert(len(truncated_full) == len(text))
    assert(truncated_full == text)
    assert(truncated_over == text)

