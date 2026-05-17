from __future__ import annotations

import math
import re
import subprocess
import sys

from . import ansi

_ANSI_ESCAPE = re.compile(r"\x1b[^m]*m")


def _terminal_size() -> tuple[int, int]:
    result = subprocess.run(["stty", "size"], capture_output=True, text=True)
    rows_str, cols_str = result.stdout.split()
    return int(rows_str) - 1, int(cols_str)


def _visible_len(s: str) -> int:
    return len(_ANSI_ESCAPE.sub("", s))


def _num_rows(line: str, columns: int) -> int:
    return max(1, math.ceil(_visible_len(line) / columns))


def erase() -> None:
    ansi.move_cursor_line_beggining()
    ansi.erase_from_cursor_to_end()


def refresh(state: object) -> None:
    erase()
    lines, num_rows = _build_output(state)
    for line in lines[:-1]:
        print(line)
    if lines:
        sys.stdout.write(lines[-1])
    ansi.move_cursor_previous_lines(num_rows - 1)
    cursor_col = len("search for: ") + state.cursor_pos + 1  # type: ignore[attr-defined]
    ansi.move_cursor_horizental(cursor_col)
    ansi.flush()


def _build_output(state: object) -> tuple[list[str], int]:
    rows, columns = _terminal_size()
    lines: list[str] = []
    total_rows = 0

    prompt = "search for: " + state.input  # type: ignore[attr-defined]
    lines.append(prompt)
    total_rows += _num_rows(prompt, columns)

    matches = state.get_matches()  # type: ignore[attr-defined]
    if not matches:
        not_found = "Nothing found"
        lines.append(not_found)
        total_rows += _num_rows(not_found, columns)
        return lines, total_rows

    selected = state.get_selected_match()  # type: ignore[attr-defined]
    selected_idx = matches.index(selected)
    num_results = 10

    while True:
        window = matches[
            max(0, selected_idx - num_results + 1) : max(num_results, selected_idx + 1)
        ]
        window_rows = sum(_num_rows(" " + str(m), columns) for m in window)
        if rows - total_rows >= window_rows or num_results <= 1:
            break
        num_results -= 1

    for m in window:
        line = " " + str(m)
        total_rows += _num_rows(line, columns)
        for word in state.input.split():  # type: ignore[attr-defined]
            if word:
                line = line.replace(word, ansi.bold_text(word))
        if m is selected:
            line = ansi.select_text(line)
        lines.append(line)

    return lines, total_rows
