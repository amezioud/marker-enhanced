# marker-enhanced

A terminal command palette with fuzzy search, DevOps-focused alias expansion, MRU ranking, and dynamic placeholder completion.

Enhanced fork of [pindexis/marker](https://github.com/pindexis/marker).

![marker](https://cloud.githubusercontent.com/assets/2557967/14209204/d99db934-f81a-11e5-910c-9d34ac155d18.gif)

## Features

- **Fuzzy search** across bookmarked commands and their descriptions
- **External command sources**: tldr-pages, navi cheat files, cheat.sh — imported with `marker update`
- **Bidirectional alias expansion**: type `k` to find `kubectl` commands, or `kubectl` to find `k` shortcuts. Works for `tf`, `tfa`, `tfp`, `dc`, `d`, `g`, `ap`, `av` out of the box
- **MRU ranking**: frequently selected commands bubble up automatically
- **Context-aware boosting**: in a Terraform repo, `tf`/`terraform` commands rank higher; in a k8s repo, `kubectl`/`helm` rank higher; etc.
- **Dynamic placeholders**: `{{name:shell-command}}` — pressing `Ctrl-T` runs the command and lets you pick a value from its output in the TUI
- **Static placeholders**: `{{name}}` — `Ctrl-T` places the cursor at the next one
- **Left/right cursor navigation** in the search field (`←` `→` `Ctrl-A` `Ctrl-E`)
- **Shell history → MRU seeding**: `marker update --history` uses your zsh/bash history to pre-populate frequency scores (raw history entries are never shown as search results)
- Supports Bash 4.3+ and Zsh

## Key bindings

| Key | Action |
|-----|--------|
| `Ctrl-Space` | Search bookmarks |
| `Ctrl-K` (or `marker mark`) | Bookmark a command |
| `Ctrl-T` | Move cursor to next placeholder / complete dynamic placeholder |
| `↑` / `↓` or `Tab` | Navigate results |
| `←` / `→` | Move cursor in search field |
| `Ctrl-A` / `Ctrl-E` | Jump to start / end of search field |
| `Ctrl-U` | Clear search field |
| `Enter` | Select |
| `Esc` / `Ctrl-C` | Cancel |

Key bindings are customisable via environment variables: `MARKER_KEY_GET`, `MARKER_KEY_MARK`, `MARKER_KEY_NEXT_PLACEHOLDER`.

## Installation

```sh
git clone --depth=1 https://github.com/amezioud/marker-enhanced ~/.marker
~/.marker/install.py
```

Add to your shell rc file (`~/.zshrc` or `~/.bashrc`):

```sh
[[ -s "$HOME/.local/share/marker/marker.sh" ]] && source "$HOME/.local/share/marker/marker.sh"
```

## Importing external commands

```sh
# Download tldr-pages + scan navi cheat files
marker update

# Also seed MRU from your shell history
marker update --history

# Also fetch specific cheat.sh topics
marker update --cheatsh git,docker,kubectl
```

## Placeholder syntax

**Static** — cursor jumps to the placeholder on `Ctrl-T`:
```
git checkout -b {{branch_name}}
```

**Dynamic** — `Ctrl-T` runs the command and shows a TUI picker:
```
terraform workspace select {{env:terraform workspace list | grep -v '^\*' | tr -d ' '}}
glab mr create --source-branch {{branch:git branch --format '%(refname:short)'}}
```

## Customisation

**Alias map** (`~/.local/share/marker/aliases.txt`):
```
kns=kubectl -n kube-system   # add custom alias
-d                            # remove default 'd' alias
```

**tldr topic whitelist** (`~/.local/share/marker/topics.txt`):
```
+helm        # add topic
-curl        # remove topic
```

## Requirements

- Python 3.10+
- Bash 4.3+ or Zsh
- Linux or macOS

## License

[MIT](LICENSE)
