import pytest
from tag_finder import tag_finder as tag_f

def pipe_join(items):
    return "|".join(items)

def get_compiled_regex(tags, priorities):
    priority_regex = tag_f.get_priority_regex(priorities)
    tags_piped = pipe_join(tags)
    return tag_f.get_tag_regex("@", tags_piped, priority_regex)

def test_get_priority_regex():
    priorities = ["HIGH", "LOW"]
    assert(tag_f.get_priority_regex(priorities) == "\s*(HIGH|LOW)?\s*")

def test_match_all_upper_no_spaces():
    line = "@TODO(HIGH) test"
    tag_regex = get_compiled_regex(["TODO", "HACK"], ["HIGH", "LOW"])

    assert(len(tag_regex.findall(line)) == 1)

def test_match_all_upper_with_spaces():
    line = "@TODO  (       HIGH ) test"
    tag_regex = get_compiled_regex(["TODO", "HACK"], ["HIGH", "LOW"])

    assert(len(tag_regex.findall(line)) == 1)

def test_random_cases_no_spaces():
    line = "@todo(high) test"
    tag_regex = get_compiled_regex(["TODO"], ["HIGH", "LOW"])

    assert(len(tag_regex.findall(line)) == 1)

def test_random_cases_with_spaces():
    line = "@todo       (   high       ) test"
    tag_regex = get_compiled_regex(["TODO"], ["HIGH", "LOW"])

    assert(len(tag_regex.findall(line)) == 1)

def test_match_with_no_priority():
    line = "@todo test"
    tag_regex = get_compiled_regex(["TODO"], ["HIGH", "LOW"])
    matches = tag_regex.findall(line)

    assert(len(matches) == 1)
    assert(matches[0][0] == "todo")
    assert(matches[0][1] == "")

def test_multi_tags_line_with_priorities_match():
    line = "@TODO(HIGH) @HACK(LOW) test"
    tag_regex = get_compiled_regex(["TODO", "HACK"], ["HIGH", "LOW"])
    matches = tag_regex.findall(line)

    assert(len(matches) == 2)
    assert(matches[0][0] == "TODO")
    assert(matches[0][1] == "HIGH")
    assert(matches[1][0] == "HACK")
    assert(matches[1][1] == "LOW")

def test_multi_tags_line_with_not_all_priorities_match():
    line = "@TODO @HACK(LOW) test"
    tag_regex = get_compiled_regex(["TODO", "HACK"], ["LOW"])
    matches = tag_regex.findall(line)

    assert(len(matches) == 2)
    assert(matches[0][0] == "TODO")
    assert(matches[0][1] == "")
    assert(matches[1][0] == "HACK")
    assert(matches[1][1] == "LOW")
