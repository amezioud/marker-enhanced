"""Track command selection frequency for MRU ranking."""
from __future__ import annotations

import json
import math
from pathlib import Path

from .command import Command


def _key(command: Command) -> str:
    return f"{command.cmd}##{command.alias}" if command.alias else command.cmd


def load(data_dir: Path) -> dict[str, int]:
    path = data_dir / "usage.json"
    try:
        data = json.loads(path.read_text())
        return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, int)}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def record(data_dir: Path, command: Command) -> None:
    usage = load(data_dir)
    k = _key(command)
    usage[k] = usage.get(k, 0) + 1
    (data_dir / "usage.json").write_text(json.dumps(usage, indent=2))


def boost(usage: dict[str, int], command: Command) -> float:
    """Score boost in [0, ~0.9] — logarithmic so frequent use helps without drowning relevance."""
    count = usage.get(_key(command), 0)
    return math.log1p(count) * 0.3
