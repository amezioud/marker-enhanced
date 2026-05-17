"""Placeholder detection and replacement for {{name}} and {{name:command}} syntax."""
from __future__ import annotations

import re

_PLACEHOLDER_RE = re.compile(r"\{\{.+?\}\}")
_DYNAMIC_RE = re.compile(r"^\{\{[^:}]+:(.+)\}\}$")


def find_first(text: str) -> tuple[str, int] | None:
    """Return (placeholder_text, offset) for the first placeholder, or None."""
    m = _PLACEHOLDER_RE.search(text)
    if m is None:
        return None
    return m.group(), m.start()


def dynamic_command(placeholder: str) -> str | None:
    """Return the shell command embedded in a dynamic placeholder, or None."""
    m = _DYNAMIC_RE.match(placeholder)
    return m.group(1) if m else None


def replace(text: str, placeholder: str, value: str) -> tuple[str, int]:
    """Replace the first occurrence of placeholder with value.

    Returns (new_text, cursor_pos) where cursor_pos is the position
    immediately after the inserted value.
    """
    offset = text.index(placeholder)
    new_text = text[:offset] + value + text[offset + len(placeholder):]
    return new_text, offset + len(value)
