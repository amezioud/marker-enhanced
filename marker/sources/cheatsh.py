"""Fetch and cache cheat.sh pages as marker commands."""
from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ..command import Command, load as cmd_load, save

# plain text, no ANSI, no section header
_BASE_URL = "https://cheat.sh/{}?T&Q"
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def fetch(topic: str) -> list[Command]:
    """Fetch cheat.sh/<topic> and return parsed Commands."""
    url = _BASE_URL.format(urllib.parse.quote(topic, safe=""))
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError):
        return []

    return _parse(raw)


def _parse(text: str) -> list[Command]:
    """Convert cheat.sh plain-text output to Commands.

    Expected patterns (mixed in the same output):
      # comment / description
      command ...
    or tldr-style:
      - description:
        `command`
    """
    commands: list[Command] = []
    description = ""
    lines = _ANSI_RE.sub("", text).splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("tldr:") or stripped.startswith("cheat:"):
            continue
        if stripped.startswith("#"):
            description = stripped.lstrip("# ").strip()
        elif stripped.startswith("- ") and stripped.endswith(":"):
            description = stripped[2:].rstrip(":")
        elif stripped.startswith("`") and stripped.endswith("`"):
            cmd = stripped[1:-1].strip()
            if cmd:
                commands.append(Command(cmd, description))
                description = ""
        elif not stripped.startswith(("//", "/*", " *")) and " " in stripped:
            # bare command line (not a comment)
            commands.append(Command(stripped, description))
            description = ""

    return commands


def update(data_dir: Path, topics: list[str]) -> dict[str, int]:
    """Fetch each topic from cheat.sh and merge into cheatsh.txt. Returns per-topic counts."""
    data_dir.mkdir(parents=True, exist_ok=True)
    cache_file = data_dir / "cheatsh.txt"
    existing = {cmd.cmd: cmd for cmd in cmd_load(cache_file)}

    counts: dict[str, int] = {}
    for topic in topics:
        cmds = fetch(topic)
        for cmd in cmds:
            existing[cmd.cmd] = cmd
        counts[topic] = len(cmds)
        print(f"  cheat.sh/{topic}: {len(cmds)} commands")

    save(list(existing.values()), cache_file)
    return counts


def load(data_dir: Path) -> list[Command]:
    return cmd_load(data_dir / "cheatsh.txt")