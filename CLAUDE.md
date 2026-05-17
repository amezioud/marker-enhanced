# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Marker is a terminal command palette — it lets users bookmark shell commands (with optional aliases and `{{placeholder}}` templates) and retrieve them via fuzzy search. It integrates with Bash and Zsh via key bindings sourced into the shell.

Enhanced fork of [pindexis/marker](https://github.com/pindexis/marker) with DevOps-focused additions: external command sources (tldr-pages, navi, cheat.sh), bidirectional alias expansion, MRU ranking, context-aware boosting, dynamic placeholder completion, and left/right cursor navigation in the search field.

## Development commands

```sh
# Run tests
python3 -m pytest tests/ -v

# Lint + format (requires ruff)
ruff check marker/ tests/
ruff format marker/ tests/

# Type-check (requires mypy)
mypy marker/

# Update external command sources
marker update                          # tldr + navi
marker update --history                # also seeds MRU from shell history
marker update --cheatsh git,docker     # also fetch cheat.sh topics
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
  core.py         # Main logic: mark_command, get_selected_command_or_input,
                  # remove_command, interactive _read_line loop + State class
  command.py      # Command model: serialization (cmd##alias format), load/save/add/remove
  filter.py       # Fuzzy filtering: two-pass sort (user marks first), alias expansion,
                  # MRU boost, context boost
  renderer.py     # Terminal UI: ANSI-based prompt + scrollable results list
  ansi.py         # Raw ANSI escape code helpers (cursor movement, text styling)
  readchar.py     # Low-level single-char stdin reader
  keys.py         # Key constant definitions (ENTER, ESC, CTRL_C, arrows, etc.)
  string_score.py # Quicksilver-style fuzzy scoring algorithm
  aliases.py      # Bidirectional alias expansion (k↔kubectl, tf↔terraform, etc.)
  usage.py        # MRU tracking: load/record/boost via $MARKER_DATA_HOME/usage.json
  context.py      # Project context detection (terraform, docker, k8s, ansible, git…)
                  # and prefix boosting for matching commands

  sources/
    tldr.py       # Downloads tldr-pages ZIP from GitHub, filters by topics whitelist,
                  # saves per-platform txt files in data dir
    navi.py       # Scans navi .cheat dirs, converts <placeholder> → {{placeholder}}
    cheatsh.py    # Fetches topics from cheat.sh API, saves to cheatsh.txt
    history.py    # Parses zsh/bash history → merges frequency counts into usage.json only
                  # (does NOT add raw history as searchable commands)

tldr/             # Bundled tldr pages (common.txt, linux.txt, osx.txt, sunos.txt)
                  # Used as fallback when no downloaded cache exists
install.py        # Verifies requirements, creates ~/.local/share/marker/, writes marker.sh
```

### Data flow for `Ctrl-Space` (get)

1. `bin/marker.sh:_marker_get` captures the current readline word and calls `marker get --search=<word> --stdout=<tmpfile>`
2. `bin/marker:cmd_get` → `core.get_selected_command_or_input(search)`
3. `core` loads user bookmarks + all external sources, aliases, usage, context
4. `State` is initialized; `renderer.refresh(state)` draws the TUI
5. `core._read_line(state)` loops on `readchar.get_symbol()` until Enter/Esc
6. Selection is recorded in `usage.json`; result written to tmp file; shell replaces buffer

### Data flow for `Ctrl-T` (next placeholder)

1. `bin/marker.sh:_move_cursor_to_next_placeholder` finds the next `{{name}}` or `{{name:command}}`
2. For static `{{name}}`: selects the placeholder text for overwriting
3. For dynamic `{{name:command}}`: runs `marker complete --command="<command>" --stdout=<tmpfile>`, shows TUI with command output lines, inserts the selected line

### Ranking logic (filter.py)

Results are sorted in two passes:
1. **User marks** (from `user_commands.txt`) always appear before external sources
2. Within each group, score = `max(fuzzy_score across original/expanded/abbreviated forms) + mru_boost + context_boost`

- `mru_boost` = `log1p(count) * 0.3` — logarithmic, from `usage.json`
- `context_boost` = `+0.4` if command prefix matches detected project context

### Alias expansion (aliases.py)

Three search forms are computed: original input, expanded (`k` → `kubectl`), abbreviated (`kubectl` → `k`). Matching and scoring run against all three; the max score wins. Most-specific abbreviation wins (`tfa` beats `tf` for "terraform apply").

Customise via `$MARKER_DATA_HOME/aliases.txt`:
```
kns=kubectl -n kube-system   # add
-d                            # remove default 'd' alias
```

### Command storage format

User commands are stored in `$MARKER_DATA_HOME/user_commands.txt`, one per line:

```
git diff HEAD~1##show last commit diff
docker ps -a
terraform plan -out {{plan:terraform workspace list | grep -v '^\*' | tr -d ' '}}##tf plan
```

`##` separates the command from its alias. Dynamic placeholders use `{{name:shell-command}}`.

### tldr topic filtering

Control which tldr pages are imported via `$MARKER_DATA_HOME/topics.txt`:
```
+helm        # add a topic not in the default whitelist
-curl        # remove a topic from the default whitelist
```

## Key constraints

- Requires Python 3.10+
- Requires Bash 4.3+ or Zsh (Bash 3.x on macOS is not supported)
- `##` is a reserved separator — it cannot appear in commands or aliases
- Static placeholder syntax: `{{name}}` — `Ctrl-T` moves cursor to next one
- Dynamic placeholder syntax: `{{name:shell-command}}` — `Ctrl-T` runs the command and shows TUI
