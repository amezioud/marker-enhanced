from __future__ import annotations

import pytest

from marker.placeholder import dynamic_command, find_first, replace


# --- find_first ---

def test_find_static():
    text = "git checkout -b {{branch}}"
    result = find_first(text)
    assert result == ("{{branch}}", 16)


def test_find_dynamic():
    text = "terraform workspace select {{env:terraform workspace list}}"
    placeholder, offset = find_first(text)
    assert placeholder == "{{env:terraform workspace list}}"
    assert offset == 27


def test_find_first_of_multiple():
    text = "cmd {{first}} and {{second}}"
    placeholder, offset = find_first(text)
    assert placeholder == "{{first}}"
    assert offset == 4


def test_find_none():
    assert find_first("git status") is None


def test_find_with_special_chars_in_command():
    text = "export ENV={{ENV:terraform workspace list | grep -v '^\\*' | tr -d ' '}}"
    placeholder, offset = find_first(text)
    assert placeholder.startswith("{{ENV:")
    assert placeholder.endswith("}}")
    assert offset == 11


# --- dynamic_command ---

def test_dynamic_command_extracts():
    ph = "{{env:terraform workspace list | grep -v '^\\*' | tr -d ' '}}"
    cmd = dynamic_command(ph)
    assert cmd == "terraform workspace list | grep -v '^\\*' | tr -d ' '"


def test_dynamic_command_none_for_static():
    assert dynamic_command("{{branch}}") is None


def test_dynamic_command_with_pipes():
    ph = "{{branch:git branch --format '%(refname:short)'}}"
    assert dynamic_command(ph) == "git branch --format '%(refname:short)'"


# --- replace ---

def test_replace_static():
    text = "git checkout -b {{branch}}"
    new_text, cursor = replace(text, "{{branch}}", "my-feature")
    assert new_text == "git checkout -b my-feature"
    assert cursor == len("git checkout -b my-feature")


def test_replace_dynamic():
    text = "export ENV={{ENV:terraform workspace list}} && terraform apply"
    new_text, cursor = replace(text, "{{ENV:terraform workspace list}}", "preprod")
    assert new_text == "export ENV=preprod && terraform apply"
    assert cursor == len("export ENV=preprod")


def test_replace_cursor_after_value():
    text = "{{a}} and {{b}}"
    new_text, cursor = replace(text, "{{a}}", "hello")
    assert new_text == "hello and {{b}}"
    assert cursor == 5  # right after "hello"


def test_replace_with_quotes_in_value():
    text = "grep {{pattern}} file"
    new_text, cursor = replace(text, "{{pattern}}", "'^\\*'")
    assert new_text == "grep '^\\*' file"


def test_replace_missing_placeholder_raises():
    with pytest.raises(ValueError):
        replace("git status", "{{missing}}", "value")
