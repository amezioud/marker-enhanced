from __future__ import annotations

import errno
import fcntl
import os
import sys
import termios
import tty

from . import keys


def get_symbol() -> int:
    """Read one logical key — single byte or multi-byte escape sequence."""
    ch = _read_char()
    code = ord(ch)
    if code != keys.ESC:
        return code

    nxt = _read_char_nonblocking()
    if nxt == "":
        return keys.ESC
    if nxt not in ("O", "["):
        return ord(nxt)

    arrow = _read_char_nonblocking()
    return {
        "A": keys.UP,
        "B": keys.DOWN,
        "C": keys.RIGHT,
        "D": keys.LEFT,
    }.get(arrow, ord(arrow))


def _read_char() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd, termios.TCSADRAIN)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _read_char_nonblocking() -> str:
    """Return one char without blocking; empty string if nothing is available."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    try:
        tty.setraw(fd, termios.TCSADRAIN)
        fcntl.fcntl(fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)
        return sys.stdin.read(1)
    except OSError as e:
        # EAGAIN / EWOULDBLOCK means no data available — that's expected
        if e.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
            raise
        return ""
    finally:
        fcntl.fcntl(fd, fcntl.F_SETFL, old_flags)
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
