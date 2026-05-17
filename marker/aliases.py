"""Command abbreviation expansion for fuzzy search."""
from __future__ import annotations

from pathlib import Path

# Abbreviations used daily in DevOps — expanded before matching so that
# typing "k" ranks kubectl commands identically to typing "kubectl".
DEFAULT_ALIASES: dict[str, str] = {
    "k": "kubectl",
    "tf": "terraform",
    "tfa": "terraform apply",
    "tfp": "terraform plan",
    "dc": "docker-compose",
    "d": "docker",
    "g": "git",
    "ap": "ansible-playbook",
    "av": "ansible-vault",
}


def load(data_dir: Path) -> dict[str, str]:
    """Merge DEFAULT_ALIASES with optional $MARKER_DATA_HOME/aliases.txt.

    File format (one entry per line):
        k=kubectl
        tf=terraform
        -d          # remove 'd' from defaults
    """
    aliases = dict(DEFAULT_ALIASES)
    aliases_file = data_dir / "aliases.txt"
    if not aliases_file.exists():
        return aliases

    for raw in aliases_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-"):
            aliases.pop(line[1:].strip(), None)
        elif "=" in line:
            key, _, value = line.partition("=")
            aliases[key.strip()] = value.strip()
    return aliases


def expand(search: str, aliases: dict[str, str]) -> str:
    """Expand the first token of search if it matches a known alias.

    'tf get' → 'terraform get'
    """
    if not aliases or not search.strip():
        return search
    tokens = search.split(None, 1)
    expanded = aliases.get(tokens[0])
    if not expanded:
        return search
    return expanded if len(tokens) == 1 else f"{expanded} {tokens[1]}"


def abbreviate(search: str, aliases: dict[str, str]) -> str:
    """Reverse lookup: replace a known full name with its abbreviation.

    Picks the most specific match (longest alias value wins).
    'terraform apply foo' → 'tfa foo'  (tfa=terraform apply beats tf=terraform)
    'terraform get'       → 'tf get'
    """
    if not aliases or not search.strip():
        return search

    lower = search.lower()
    best: str | None = None
    best_len = 0

    for abbr, full in aliases.items():
        full_lower = full.lower()
        # Full-phrase prefix match
        if lower == full_lower or lower.startswith(full_lower + " "):
            if len(full_lower) > best_len:
                best_len = len(full_lower)
                best = abbr + search[len(full_lower):]
        # First-word-only match (fallback when no full-phrase match found yet)
        elif best_len == 0 and full_lower.split()[0] == lower.split()[0]:
            rest = search[len(lower.split()[0]):]
            best = abbr + rest

    return best if best else search
