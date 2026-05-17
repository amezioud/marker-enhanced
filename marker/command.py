from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import ansi


def load(file_path: Path | str) -> list[Command]:
    try:
        with open(file_path) as f:
            return [Command.deserialize(line.strip()) for line in f if line.strip()]
    except OSError:
        return []


def save(commands: list[Command], file_path: Path | str) -> None:
    with open(file_path, "w") as f:
        f.write("\n".join(cmd.serialize() for cmd in commands))


def add(commands: list[Command], command: Command) -> None:
    remove(commands, command)
    commands.append(command)


def remove(commands: list[Command], command: Command) -> None:
    try:
        match = next(m for m in commands if command.equals(m))
        commands.remove(match)
    except StopIteration:
        pass


@dataclass
class Command:
    """A shell command with an optional alias."""

    cmd: str
    alias: str = field(default="")

    def __post_init__(self) -> None:
        if not self.cmd:
            raise ValueError("cmd cannot be empty")

    def __repr__(self) -> str:
        if self.alias and self.alias != self.cmd:
            return self.cmd + " " + ansi.grey_text(self.alias)
        return self.cmd

    def __str__(self) -> str:
        return self.__repr__()

    @staticmethod
    def deserialize(s: str) -> Command:
        if "##" in s:
            cmd, alias = s.split("##", 1)
        else:
            cmd, alias = s, ""
        return Command(cmd, alias)

    def serialize(self) -> str:
        return f"{self.cmd}##{self.alias}" if self.alias else self.cmd

    def equals(self, other: Command) -> bool:
        return self.cmd == other.cmd and self.alias == other.alias
