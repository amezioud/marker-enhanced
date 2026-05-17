#!/usr/bin/env python3
from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
from pathlib import Path

SUPPORTED_SHELLS = ("bash", "zsh")


def _current_shell() -> str:
    return os.path.basename(os.getenv("SHELL", ""))


def _generate_marker_sh(config_dir: Path, install_dir: Path) -> str:
    return (
        f'export MARKER_DATA_HOME="{config_dir}"\n'
        f'export MARKER_HOME="{install_dir}"\n'
        f"source ${{MARKER_HOME}}/bin/marker.sh\n"
    )


def _show_post_install(config_dir_rel: str) -> None:
    print("Marker installed successfully\n")
    sourced = f"$HOME/{config_dir_rel}/marker.sh"
    source_line = f'[[ -s "{sourced}" ]] && source "{sourced}"'

    if platform.system() == "Darwin" and _current_shell() == "bash":
        rcfile = ".bash_profile"
    else:
        rcfile = f".{_current_shell()}rc"

    print(f"\nAdd this line to your ~/{rcfile}:\n\n{source_line}\n")
    print("Restart the terminal (or re-source your rc file) afterwards.")


def _verify_requirements() -> None:
    shell = _current_shell()
    if shell not in SUPPORTED_SHELLS:
        sys.exit(f"Shell {shell!r} is not supported (bash or zsh required)")

    if shell == "bash":
        result = subprocess.run(
            ["bash", "--version"], capture_output=True, text=True
        )
        m = re.search(r"(\d+)\.(\d+)", result.stdout)
        if not m:
            sys.exit("Could not determine bash version")
        major, minor = int(m.group(1)), int(m.group(2))
        if (major, minor) < (4, 3):
            sys.exit(f"Bash 4.3+ required (found {major}.{minor})")

    if sys.version_info < (3, 8):
        sys.exit("Python 3.8+ required")


def main() -> None:
    _verify_requirements()
    print("---------------------------------------")
    rel = ".local/share/marker"
    config_dir = Path.home() / rel
    install_dir = Path(__file__).parent.resolve()

    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "marker.sh").write_text(
        _generate_marker_sh(config_dir, install_dir)
    )
    _show_post_install(rel)
    print("---------------------------------------")


if __name__ == "__main__":
    main()