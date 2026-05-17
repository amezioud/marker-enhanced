from __future__ import annotations

import os
import subprocess
from pathlib import Path

try:
    import readline  # noqa: F401 — enables arrow keys and history in input()
except ImportError:
    pass

from . import command, keys, readchar, renderer
from .command import Command
from .filter import filter_commands


def _get_os() -> str:
    import sys
    if sys.platform == "darwin":
        return "osx"
    if sys.platform.startswith("linux"):
        return "linux"
    return "unknown"


def _data_dir() -> Path:
    return Path(os.environ["MARKER_DATA_HOME"])


def _user_marks_path() -> Path:
    return _data_dir() / "user_commands.txt"


def _bundled_tldr_path(name: str) -> Path:
    return Path(os.environ["MARKER_HOME"]) / "tldr" / name


def mark_command(cmd_string: str | None, alias: str | None) -> None:
    if cmd_string:
        cmd_string = cmd_string.strip()
    if not cmd_string:
        try:
            cmd_string = input("Command:")
        except KeyboardInterrupt:
            return
    else:
        print(f"command: {cmd_string}")
    if not cmd_string:
        print("command field is required")
        return
    if not alias:
        try:
            alias = input("Alias?:")
        except KeyboardInterrupt:
            return
    else:
        print(f"alias: {alias}")
    if "##" in cmd_string or "##" in (alias or ""):
        print("command can't contain ## (it's used as command alias separator)")
        return
    commands = command.load(_user_marks_path())
    command.add(commands, Command(cmd_string, alias or ""))
    command.save(commands, _user_marks_path())


def _all_commands() -> tuple[list[Command], frozenset[tuple[str, str]]]:
    from .sources import navi, cheatsh, history
    from .sources import tldr as tldr_src

    data = _data_dir()
    os_name = _get_os()

    user_cmds = command.load(_user_marks_path())
    user_ids: frozenset[tuple[str, str]] = frozenset((m.cmd, m.alias) for m in user_cmds)

    cmds = list(user_cmds)

    updated_tldr = tldr_src.load(data, os_name)
    if updated_tldr:
        cmds += updated_tldr
    else:
        cmds += command.load(_bundled_tldr_path(f"{os_name}.txt"))
        cmds += command.load(_bundled_tldr_path("common.txt"))

    cmds += navi.load(data)
    cmds += cheatsh.load(data)
    cmds += history.load(data)

    return cmds, user_ids


def get_selected_command_or_input(search: str | None) -> str:
    from .aliases import load as load_aliases
    from . import usage as usage_mod
    from .context import detect, boosted_prefixes

    data = _data_dir()
    commands, user_ids = _all_commands()
    state = State(
        commands,
        search,
        aliases=load_aliases(data),
        user_ids=user_ids,
        usage=usage_mod.load(data),
        context_prefixes=boosted_prefixes(detect()),
    )
    renderer.refresh(state)
    output = _read_line(state)
    renderer.erase()
    if output:
        usage_mod.record(data, output)
        return output.cmd
    return state.input or ""


def complete_placeholder(shell_command: str) -> str | None:
    """Run shell_command, show its output lines in the TUI, return the selected line."""
    result = subprocess.run(shell_command, shell=True, capture_output=True, text=True)
    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    if not lines:
        return None
    commands = [Command(line, "") for line in lines]
    state = State(commands, None)
    renderer.refresh(state)
    output = _read_line(state)
    renderer.erase()
    return output.cmd if output else None


def update_cache(cheatsh_topics: list[str] | None = None, history: bool = False) -> None:
    from .sources import navi, cheatsh
    from .sources import tldr as tldr_src
    from .sources import history as history_src

    data = _data_dir()
    data.mkdir(parents=True, exist_ok=True)

    print("Updating tldr-pages...", flush=True)
    counts = tldr_src.update(data)
    for platform, n in counts.items():
        print(f"  tldr/{platform}: {n} commands")

    print("Importing navi cheat files...", flush=True)
    n = navi.update(data)
    print(f"  navi: {n} commands")

    if history:
        print("Importing shell history...", flush=True)
        n = history_src.update(data)
        print(f"  history: {n} commands")

    if cheatsh_topics:
        print("Fetching cheat.sh topics...", flush=True)
        cheatsh.update(data, cheatsh_topics)

    print("Done.")


def remove_command(search: str | None) -> Command | None:
    from .aliases import load as load_aliases

    commands = command.load(_user_marks_path())
    user_ids: frozenset[tuple[str, str]] = frozenset((m.cmd, m.alias) for m in commands)
    state = State(commands, search, aliases=load_aliases(_data_dir()), user_ids=user_ids)
    renderer.refresh(state)
    selected = _read_line(state)
    if selected:
        command.remove(commands, selected)
        command.save(commands, _user_marks_path())
    renderer.erase()
    return selected


def _read_line(state: State) -> Command | None:
    while True:
        c = readchar.get_symbol()
        if c == keys.ENTER:
            return state.get_selected_match() if state.get_matches() else None
        if c in (keys.CTRL_C, keys.ESC):
            state.reset_input()
            return None
        if c == keys.CTRL_U:
            state.clear_input()
        elif c == keys.CTRL_A:
            state.cursor_home()
        elif c == keys.CTRL_E:
            state.cursor_end()
        elif c == keys.LEFT:
            state.cursor_left()
        elif c == keys.RIGHT:
            state.cursor_right()
        elif c == keys.BACKSPACE:
            pos = state.cursor_pos
            if pos > 0:
                state.set_input(state.input[: pos - 1] + state.input[pos:], cursor_pos=pos - 1)
        elif c == keys.UP:
            state.select_previous()
        elif c in (keys.DOWN, keys.TAB):
            state.select_next()
        elif 32 <= c <= 126:
            pos = state.cursor_pos
            state.set_input(state.input[:pos] + chr(c) + state.input[pos:], cursor_pos=pos + 1)
        renderer.refresh(state)


class State:
    def __init__(
        self,
        bookmarks: list[Command],
        default_input: str | None,
        aliases: dict[str, str] | None = None,
        user_ids: frozenset[tuple[str, str]] | None = None,
        usage: dict[str, int] | None = None,
        context_prefixes: frozenset[str] | None = None,
    ) -> None:
        self.bookmarks = bookmarks
        self.aliases = aliases or {}
        self.user_ids = user_ids
        self.usage = usage
        self.context_prefixes = context_prefixes
        self._selected_index = 0
        self._cursor_pos = 0
        self.matches: list[Command] = []
        self.default_input = default_input or ""
        self.set_input(self.default_input)

    @property
    def cursor_pos(self) -> int:
        return self._cursor_pos

    def get_matches(self) -> list[Command]:
        return self.matches

    def reset_input(self) -> None:
        self.input = self.default_input
        self._cursor_pos = len(self.input)

    def set_input(self, text: str, cursor_pos: int | None = None) -> None:
        self.input = text or ""
        self._cursor_pos = len(self.input) if cursor_pos is None else cursor_pos
        self._refresh_matches()

    def clear_input(self) -> None:
        self.set_input("")

    def cursor_left(self) -> None:
        self._cursor_pos = max(0, self._cursor_pos - 1)

    def cursor_right(self) -> None:
        self._cursor_pos = min(len(self.input), self._cursor_pos + 1)

    def cursor_home(self) -> None:
        self._cursor_pos = 0

    def cursor_end(self) -> None:
        self._cursor_pos = len(self.input)

    def select_next(self) -> None:
        if self.matches:
            self._selected_index = (self._selected_index + 1) % len(self.matches)

    def select_previous(self) -> None:
        if self.matches:
            self._selected_index = (self._selected_index - 1) % len(self.matches)

    def _refresh_matches(self) -> None:
        self.matches = filter_commands(
            self.bookmarks,
            self.input,
            self.aliases,
            self.user_ids,
            self.usage,
            self.context_prefixes,
        )
        self._selected_index = 0

    def get_selected_match(self) -> Command | None:
        if self.matches:
            return self.matches[self._selected_index]
        return None
