import os
import pytest
import re
from taggregator import taggregator as tagg

tags = ["TODO", "HACK", "ROBUSTNESS", "SPEED"]
priorities = ["LOW", "MEDIUM", "HIGH"]

def get_compiled_regex():
    priority_regex = tagg.get_priority_regex(priorities)
    return tagg.get_tag_regex("@", tags, priority_regex)

def test_get_tag_regex():
    correct_regex = re.compile("@(TODO|HACK|ROBUSTNESS|SPEED)\\s*\\(*\\s*(LOW|MEDIUM|HIGH)?\\s*\\)*", re.IGNORECASE)

    assert(tagg.get_tag_regex("@", tags, tagg.get_priority_regex(priorities)) == correct_regex)

def test_get_priority_regex():
    priorities = ["HIGH", "LOW"]
    assert(tagg.get_priority_regex(priorities) == r"\s*(HIGH|LOW)?\s*")

def test_find_matches():
    matches = tagg.find_matches(get_compiled_regex(), tags, os.path.join(os.getcwd(), "taggregator/example_files/test.txt"), tagg.get_priority_value_map(priorities))

    assert(len(list(matches)) == 14)

def test_get_priority_value_map():
    priorities = ["LOW", "MEDIUM", "HIGH"]
    priority_value_map = tagg.get_priority_value_map(priorities)

    assert("LOW" in priority_value_map)
    assert("MEDIUM" in priority_value_map)
    assert("HIGH" in priority_value_map)

    assert(priority_value_map["LOW"] == 0)
    assert(priority_value_map["MEDIUM"] == 1)
    assert(priority_value_map["HIGH"] == 2)

def test_match_all_upper_no_spaces():
    line = "@TODO(HIGH) test"
    tag_regex = get_compiled_regex()

    assert(len(tag_regex.findall(line)) == 1)

def test_match_all_upper_with_spaces():
    line = "@TODO  (       HIGH ) test"
    tag_regex = get_compiled_regex()

    assert(len(tag_regex.findall(line)) == 1)

def test_random_cases_no_spaces():
    line = "@todo(high) test"
    tag_regex = get_compiled_regex()

    assert(len(tag_regex.findall(line)) == 1)

def test_random_cases_with_spaces():
    line = "@todo       (   high       ) test"
    tag_regex = get_compiled_regex()

    assert(len(tag_regex.findall(line)) == 1)

def test_match_with_no_priority():
    line = "@todo test"
    tag_regex = get_compiled_regex()
    matches = tag_regex.findall(line)

    assert(len(matches) == 1)
    assert(matches[0][0] == "todo")
    assert(matches[0][1] == "")

def test_multi_tags_line_with_priorities_match():
    line = "@TODO(HIGH) @HACK(LOW) test"
    tag_regex = get_compiled_regex()
    matches = tag_regex.findall(line)

    assert(len(matches) == 2)
    assert(matches[0][0] == "TODO")
    assert(matches[0][1] == "HIGH")
    assert(matches[1][0] == "HACK")
    assert(matches[1][1] == "LOW")

def test_multi_tags_line_with_not_all_priorities_match():
    line = "@TODO @HACK(LOW) test"
    tag_regex = get_compiled_regex()
    matches = tag_regex.findall(line)

    assert(len(matches) == 2)
    assert(matches[0][0] == "TODO")
    assert(matches[0][1] == "")
    assert(matches[1][0] == "HACK")
    assert(matches[1][1] == "LOW")
