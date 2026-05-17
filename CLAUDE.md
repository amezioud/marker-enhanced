# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Marker is a terminal command palette — it lets users bookmark shell commands (with optional aliases and `{{placeholder}}` templates) and retrieve them via fuzzy search. It integrates with Bash and Zsh via key bindings sourced into the shell.

## Development commands

```sh
# Run tests
python3 -m pytest tests/ -v

# Lint + format (requires ruff)
ruff check marker/ tests/
ruff format marker/ tests/

# Type-check (requires mypy)
mypy marker/
```

## Running the tool

Marker is not run directly; it must be sourced into the shell first:

```sh
# Install (one-time)
python install.py

# After install, source in your shell rc file:
[[ -s "$HOME/.local/share/marker/marker.sh" ]] && source "$HOME/.local/share/marker/marker.sh"
```

Once sourced, the CLI is available:

```sh
marker mark --command='git diff' --alias='show diff'
marker get --search='diff'
marker remove --search='diff'
```

Two environment variables must be set (done by the sourced marker.sh):
- `MARKER_HOME` — path to the repo root
- `MARKER_DATA_HOME` — path to user data dir (`~/.local/share/marker`)

## Architecture

```
bin/marker        # Python CLI entry point (argparse, calls marker.core)
bin/marker.sh     # Shell integration: key bindings for Bash and Zsh,
                  # runs `marker get` and writes result to a tmp file,
                  # then injects the result back into the readline buffer

marker/
  core.py         # Main application logic: mark_command, get_selected_command_or_input,
                  # remove_command, and the interactive read_line loop + State class
  command.py      # Command model: serialization (cmd##alias format), load/save/add/remove
  filter.py       # Fuzzy filtering: word-based containment check + string_score ranking
  renderer.py     # Terminal UI: ANSI-based prompt + scrollable results list
  ansi.py         # Raw ANSI escape code helpers (cursor movement, text styling)
  readchar.py     # Low-level single-char stdin reader
  keys.py         # Key constant definitions (ENTER, ESC, CTRL_C, arrows, etc.)
  string_score.py # Fuzzy scoring algorithm for ranking matches
  tldr.py         # Stub for tldr cache update (not implemented)

tldr/             # Bundled tldr command pages (common.txt, linux.txt, osx.txt, sunos.txt)
                  # Loaded as read-only bookmarks alongside user_commands.txt
install.py        # Verifies requirements, creates ~/.local/share/marker/, writes marker.sh
```

### Data flow for `Ctrl-Space` (get)

1. `bin/marker.sh:_marker_get` captures the current readline word and calls `marker get --search=<word> --stdout=<tmpfile>`
2. `bin/marker:cmd_get` → `core.get_selected_command_or_input(search)`
3. `core` loads user bookmarks + tldr OS/common files via `command.load()`
4. `State` is initialized; `renderer.refresh(state)` draws the TUI
5. `core.read_line(state)` loops on `readchar.get_symbol()` until Enter/Esc
6. Result is written to the tmp file; the shell function reads it and replaces the buffer

### Command storage format

User commands are stored in `$MARKER_DATA_HOME/user_commands.txt`, one per line:

```
git diff HEAD~1##show last commit diff
docker ps -a
```

`##` separates the command from its alias. Commands without aliases omit the separator.

## Key constraints

- Supports Python 2.7+ and Python 3.x (uses `raw_input`/`input` compat shim in `core.py`)
- Requires Bash 4.3+ or Zsh (Bash 3.x on macOS is not supported)
- `##` is a reserved separator — it cannot appear in commands or aliases
- Placeholder syntax is `{{name}}` — `Ctrl-T` moves the cursor to the next one