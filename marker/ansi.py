from __future__ import annotations

import sys

BOLD = "\x1b[1m"
CLEAR = "\x1b[0m"
ERASE_SCREEN = "\x1b[J"
ERASE_LINE = "\x1b[2K"
FG_BLACK = "\x1b[30m"
BG_WHITE = "\x1b[47m"
FG_GREY = "\x1b[34m"


def _cursor_column(pos: int) -> str:
    return f"\x1b[{pos}G"


def _cursor_prev_lines(n: int) -> str:
    return f"\x1b[{n}F"


def _active_formats(text: str) -> str:
    """Re-emit any formatting codes that were active before the last CLEAR."""
    if CLEAR in text:
        return _active_formats(text[text.index(CLEAR) + len(CLEAR) :])
    return "".join(s for s in (BOLD, FG_GREY, FG_BLACK, BG_WHITE) if s in text)


def select_text(text: str) -> str:
    body = text.replace(CLEAR, CLEAR + FG_BLACK + BG_WHITE)
    return FG_BLACK + BG_WHITE + body + CLEAR + _active_formats(text)


def bold_text(text: str) -> str:
    body = text.replace(CLEAR, CLEAR + BOLD)
    return BOLD + body + CLEAR + _active_formats(text)


def grey_text(text: str) -> str:
    body = text.replace(CLEAR, CLEAR + FG_GREY)
    return FG_GREY + body + CLEAR + _active_formats(text)


def move_cursor_line_beggining() -> None:
    sys.stdout.write(_cursor_column(0))


def move_cursor_horizental(n: int) -> None:
    sys.stdout.write(_cursor_column(n))


def move_cursor_previous_lines(n: int) -> None:
    sys.stdout.write(_cursor_prev_lines(n))


def erase_from_cursor_to_end() -> None:
    sys.stdout.write(ERASE_SCREEN)


def erase_line() -> None:
    sys.stdout.write(ERASE_LINE)


def flush() -> None:
    sys.stdout.flush()
