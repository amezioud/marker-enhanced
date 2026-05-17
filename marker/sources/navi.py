"""Import navi .cheat files into marker format."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from ..command import Command, save

_PLACEHOLDER_RE = re.compile(r"<(\w+)>")
_VAR_DEF_RE = re.compile(r"^\$\s+\w+:")


def _cheat_dirs() -> list[Path]:
    try:
        result = subprocess.run(
            ["navi", "info", "cheats-path"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return [Path(p) for p in result.stdout.strip().splitlines() if p]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # common fallback locations
    fallbacks = [
        Path.home() / ".local/share/navi/cheats",
        Path.home() / ".config/navi/cheats",
    ]
    return [p for p in fallbacks if p.exists()]


def _parse_cheat_file(path: Path) -> list[Command]:
    commands: list[Command] = []
    description = ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("%"):
            continue
        if stripped.startswith("#"):
            description = stripped.lstrip("# ").strip()
        elif not _VAR_DEF_RE.match(stripped):
            # convert <placeholder> → {{placeholder}}
            cmd = _PLACEHOLDER_RE.sub(r"{{\1}}", stripped)
            if cmd:
                commands.append(Command(cmd, description))
                description = ""
    return commands


def update(data_dir: Path) -> int:
    """Scan navi cheat dirs and write navi.txt in data_dir. Returns command count."""
    data_dir.mkdir(parents=True, exist_ok=True)
    dirs = _cheat_dirs()
    if not dirs:
        return 0

    all_commands: list[Command] = []
    for cheat_dir in dirs:
        for cheat_file in cheat_dir.rglob("*.cheat"):
            all_commands.extend(_parse_cheat_file(cheat_file))

    save(all_commands, data_dir / "navi.txt")
    return len(all_commands)


def load(data_dir: Path) -> list[Command]:
    from ..command import load as cmd_load
    return cmd_load(data_dir / "navi.txt")