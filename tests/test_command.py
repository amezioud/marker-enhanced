from __future__ import annotations

import pytest

from marker.command import Command, add, load, remove, save


def test_serialize_with_alias():
    assert Command("git diff", "show diff").serialize() == "git diff##show diff"


def test_serialize_without_alias():
    assert Command("git diff", "").serialize() == "git diff"


def test_deserialize_with_alias():
    cmd = Command.deserialize("git diff##show diff")
    assert cmd.cmd == "git diff"
    assert cmd.alias == "show diff"


def test_deserialize_without_alias():
    cmd = Command.deserialize("git diff")
    assert cmd.cmd == "git diff"
    assert cmd.alias == ""


def test_equals():
    assert Command("git diff", "d").equals(Command("git diff", "d"))
    assert not Command("git diff", "d").equals(Command("git diff", ""))


def test_empty_cmd_raises():
    with pytest.raises(ValueError):
        Command("")


def test_add_deduplicates():
    cmds: list[Command] = [Command("git diff", "")]
    add(cmds, Command("git diff", ""))
    assert len(cmds) == 1


def test_remove():
    cmds = [Command("git diff", ""), Command("ls -la", "")]
    remove(cmds, Command("git diff", ""))
    assert len(cmds) == 1
    assert cmds[0].cmd == "ls -la"


def test_save_and_load(tmp_path):
    path = tmp_path / "commands.txt"
    original = [Command("git diff", "show diff"), Command("ls -la", "")]
    save(original, path)
    loaded = load(path)
    assert len(loaded) == 2
    assert loaded[0].cmd == "git diff"
    assert loaded[0].alias == "show diff"
    assert loaded[1].cmd == "ls -la"


def test_load_missing_file(tmp_path):
    assert load(tmp_path / "nonexistent.txt") == []
