from __future__ import annotations

import re

from . import string_score
from .aliases import abbreviate, expand
from .command import Command

_WORDS_RE = re.compile(r"\w+")
_MarkId = tuple[str, str]


def filter_commands(
    marks: list[Command],
    search_string: str,
    aliases: dict[str, str] | None = None,
    user_ids: frozenset[_MarkId] | None = None,
    usage: dict[str, int] | None = None,
    context_prefixes: frozenset[str] | None = None,
) -> list[Command]:
    """Return marks matching search_string, ranked by score.

    Ranking layers (highest priority first):
      1. User personal marks always appear before external sources.
      2. Within each group: fuzzy score + MRU boost + directory-context boost.

    Alias matching is bidirectional (tf ↔ terraform).
    """
    from . import usage as usage_mod
    from .context import CONTEXT_BOOST

    def contained(candidate: list[str], container: list[str]) -> bool:
        pool = container[:]
        for i, word in enumerate(candidate):
            if i == len(candidate) - 1:
                return any(word in c for c in pool)
            try:
                pool.remove(word)
            except ValueError:
                return False
        return True

    original = search_string.lstrip()
    expanded = expand(original, aliases or {})
    abbreviated = abbreviate(original, aliases or {})
    forms = {original, expanded, abbreviated}

    def sort_key(m: Command) -> float:
        base = max(
            string_score.score(m.cmd, f) * 2 + string_score.score(m.alias, f)
            for f in forms
        )
        if usage:
            base += usage_mod.boost(usage, m)
        if context_prefixes:
            first = m.cmd.split()[0].lower() if m.cmd.strip() else ""
            if first in context_prefixes:
                base += CONTEXT_BOOST
        return base

    if not original:
        return sorted(marks, key=sort_key, reverse=True)

    form_words = [_WORDS_RE.findall(f.lower()) for f in forms]
    mark_words = [
        _WORDS_RE.findall(m.cmd.lower()) + _WORDS_RE.findall(m.alias.lower())
        for m in marks
    ]

    filtered = [
        m
        for m, words in zip(marks, mark_words)
        if any(contained(fw, words) for fw in form_words)
    ]

    if not user_ids:
        return sorted(filtered, key=sort_key, reverse=True)

    user = sorted([m for m in filtered if (m.cmd, m.alias) in user_ids], key=sort_key, reverse=True)
    other = sorted([m for m in filtered if (m.cmd, m.alias) not in user_ids], key=sort_key, reverse=True)
    return user + other
