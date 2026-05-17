"""Use shell history to pre-populate MRU scores — not as a raw command source."""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path

from ..command import Command

_NOISE_RE = re.compile(
    r"^(cd(\s|$)|ls(\s|$)|ll(\s|$)|la(\s|$)|pwd|clear|exit|history|echo\s|cat\s|man\s"
    r"|which\s|type\s|alias(\s|$)|source\s|\.\s|sudo -i|su -|reboot|shutdown|rm -rf\s*/)"
)


def _zsh_history_path() -> Path:
    return Path(os.getenv("HISTFILE", str(Path.home() / ".zsh_history")))


def _parse_zsh(path: Path) -> list[str]:
    cmds: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(": ") and ";" in line:
            _, _, cmd = line.partition(";")
            if cmd.strip():
                cmds.append(cmd.strip())
        elif not line.startswith(":"):
            cmds.append(line)
    return cmds


def _parse_bash(path: Path) -> list[str]:
    return [
        l.strip()
        for l in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if l.strip() and not l.startswith("#")
    ]


def update(data_dir: Path, min_length: int = 10) -> int:
    """Parse shell history and merge frequency counts into usage.json.

    History commands are NOT added as searchable entries — they only boost
    MRU scores for commands that already exist in user marks / tldr / navi.
    Returns the number of distinct commands counted.
    """
    data_dir.mkdir(parents=True, exist_ok=True)

    raw: list[str] = []
    zsh = _zsh_history_path()
    if zsh.exists():
        raw = _parse_zsh(zsh)
    else:
        bash = Path.home() / ".bash_history"
        if bash.exists():
            raw = _parse_bash(bash)

    if not raw:
        return 0

    counts: Counter[str] = Counter(
        line
        for line in raw
        if len(line) >= min_length and not _NOISE_RE.match(line) and "##" not in line
    )

    # Merge into existing usage.json (history counts weigh less than explicit selections)
    usage_path = data_dir / "usage.json"
    try:
        existing: dict[str, int] = json.loads(usage_path.read_text())
    except (OSError, json.JSONDecodeError):
        existing = {}

    for cmd, count in counts.items():
        # History frequency is scaled down — one explicit selection outweighs many history hits
        history_score = max(1, count // 5)
        existing[cmd] = existing.get(cmd, 0) + history_score

    usage_path.write_text(json.dumps(existing, indent=2))
    return len(counts)


def load(data_dir: Path) -> list[Command]:
    """History no longer exposes raw commands — always returns empty."""
    return []
