from __future__ import annotations

from marker.command import Command
from marker.filter import filter_commands


def _cmd(cmd: str, alias: str = "") -> Command:
    return Command(cmd, alias)


def test_empty_search_returns_all():
    marks = [_cmd("git diff"), _cmd("ls -la")]
    assert len(filter_commands(marks, "")) == 2


def test_exact_word_match():
    marks = [_cmd("git diff"), _cmd("ls -la")]
    result = filter_commands(marks, "git")
    assert any(m.cmd == "git diff" for m in result)
    assert all(m.cmd != "ls -la" for m in result)


def test_alias_match():
    marks = [_cmd("git diff HEAD~1", "show last commit")]
    result = filter_commands(marks, "last commit")
    assert len(result) == 1


def test_no_match_returns_empty():
    marks = [_cmd("git diff"), _cmd("ls -la")]
    assert filter_commands(marks, "xyzzy") == []


def test_partial_last_word():
    marks = [_cmd("cd /tmp"), _cmd("ls -la")]
    result = filter_commands(marks, "cd tm")
    assert any(m.cmd == "cd /tmp" for m in result)


def test_multi_word_exact_then_partial():
    marks = [_cmd("git diff HEAD"), _cmd("git log --oneline")]
    result = filter_commands(marks, "git di")
    assert any(m.cmd == "git diff HEAD" for m in result)
