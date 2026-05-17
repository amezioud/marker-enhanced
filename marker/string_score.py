from __future__ import annotations


def _first_valid_index(a: int, b: int) -> int:
    min_idx = min(a, b)
    return min_idx if min_idx > -1 else max(a, b)


def score(string: str, abbreviation: str) -> float:
    """Quicksilver-style fuzzy score in [0, 1].

    Returns 1.0 for an exact match, 0 if abbreviation chars are not found
    in order inside string.
    """
    if not abbreviation or string == abbreviation:
        return 1.0

    total = 0.0
    start_bonus = False
    abbr_len = len(abbreviation)
    str_len = len(string)
    remaining = string

    for i, c in enumerate(abbreviation):
        idx = _first_valid_index(remaining.find(c.lower()), remaining.find(c.upper()))
        if idx == -1:
            return 0.0

        char_score = 0.09
        if remaining[idx] == c:
            char_score += 0.09  # case match bonus

        if idx == 0:
            char_score += 0.79  # start of remaining string
            if i == 0:
                start_bonus = True

        if idx > 0 and remaining[idx - 1] == " ":
            char_score += 0.79  # acronym / word-boundary bonus

        remaining = remaining[idx + 1 :]
        total += char_score

    abbr_score = total / abbr_len
    pct_matched = abbr_len / str_len
    word_score = abbr_score * pct_matched
    final = (word_score + abbr_score) / 2
    if start_bonus and final + 0.09 < 1:
        final += 0.09
    return final
