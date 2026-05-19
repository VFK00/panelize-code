# panelize-code

**Config-driven terminal dashboard.** Define panels in TOML, point them at shell commands, get a live TUI.

Built with [Textual](https://textual.textualize.io). No code required — anything that prints to stdout becomes a dashboard tile.

```
┌─ Git Status ──────────────┐ ┌─ Disk ───────────────────┐
│  M src/app.py             │ │  /         45%   120G    │
│  ?? notes.md              │ │  /home     67%   80G     │
└──────────────────────────┘ └──────────────────────────┘
┌─ Containers ─────────────┐ ┌─ Listening Ports ────────┐
│  api      Up 2h          │ │  :22                     │
│  db       Up 2h          │ │  :8080                   │
│  worker   Restarting     │ │  :5432                   │
└──────────────────────────┘ └──────────────────────────┘
```

## Features

- **TOML config** — declare panels and refresh intervals. No code.
- **6 parsers** — `raw`, `lines`, `tsv`, `csv`, `json`, `regex`. Bring your own output format.
- **Per-panel refresh** — each panel can have its own interval.
- **Auto grid layout** — N panels → optimal rows × cols (1, 2, 4, 6, 9, 12, …).
- **Actions** — bind shell commands to single-key shortcuts.
- **Two modes** — `run` (interactive Textual TUI) and `show` (rich one-shot snapshot, CI-friendly).
- **Themes** — built-in dark theme + cycle through tokyo-night, monokai, gruvbox, nord, flexoki.
- **Graceful errors** — missing binary, non-zero exit, timeout → panel shows error, others keep running.

## Install

```bash
# With uv (recommended)
uv tool install panelize-code

# With pipx
pipx install panelize-code

# With pip
pip install panelize-code
```

Requires **Python 3.11+**.

## Quick start

```bash
# 1. Generate a sample config
panelize init

# 2. Edit panelize.toml to your taste

# 3. Run
panelize run
# or, default subcommand:
panelize
```

## Configuration

A minimal `panelize.toml`:

```toml
[app]
title = "My Dashboard"
refresh = 30

[[panels]]
id = "git"
title = "Git Status"
command = "git status --short"
parser = "lines"
```

### App settings

| Key | Default | Description |
|-----|---------|-------------|
| `title` | `"panelize"` | Window/title bar text |
| `refresh` | `30` | Global refresh interval (seconds) |
| `theme` | `"panelize"` | Initial theme (cycle with `t`) |
| `splash` | `true` | Reserved (future use) |

### Panel settings

| Key | Type | Description |
|-----|------|-------------|
| `id` | string | Unique slug (alphanumeric, `-`, `_`) |
| `title` | string | Display title |
| `command` | string \| list | Shell command (string = via shell, list = direct) |
| `parser` | enum | `raw` \| `lines` \| `tsv` \| `csv` \| `json` \| `regex` |
| `refresh` | int | Override global refresh (optional) |
| `timeout` | int | Subprocess timeout in seconds (default `10`) |
| `icon` | string | 1–2 character icon prefix |
| `columns` | list[str] | Column headers (parsers `tsv`/`csv`/`json`/`regex`) |
| `pattern` | string | Regex pattern (required if `parser = "regex"`) |
| `template` | string | Format string for `json` parser, e.g. `"{name}: {status}"` |
| `shell` | bool | Run via shell (default `true` for string commands) |

### Parsers

| Parser | Input | Output |
|--------|-------|--------|
| `raw` | any | Whole stdout as one cell |
| `lines` | line-based | One row per non-empty line |
| `tsv` | tab-separated | Split on `\t` |
| `csv` | comma-separated | Standard CSV parse |
| `json` | JSON list/dict | Render via `template` or extract `columns` (supports dotted paths: `meta.name`) |
| `regex` | line-based | Each line matched against `pattern`; capture groups → columns |

### Actions

```toml
[[actions]]
name = "git pull"
command = "git pull"
shortcut = "g"          # press 'g' in TUI to fire
confirm = false         # ask before running (reserved)
timeout = 60
```

After an action succeeds, all panels refresh automatically.

## Keyboard

| Key | Action |
|-----|--------|
| `r` | Refresh all panels |
| `a` | Show actions menu |
| `t` | Cycle theme |
| `p` | Pause / resume auto-refresh |
| `q` | Quit |
| `?` / `F1` | Help |
| any other | Trigger an action whose `shortcut` matches |

## Modes

### `panelize run` (default)

Interactive Textual TUI. Auto-refresh on the global interval, per-panel overrides apply, actions are live.

### `panelize show`

One-shot rich snapshot. Useful for `watch -n 30 panelize show`, cron, CI.

- Exit code `0` → all panels OK
- Exit code `2` → at least one panel failed

```bash
panelize show -c devops.toml
```

### `panelize init`

Write a sample config (`panelize.toml`) you can edit.

### `panelize validate`

Validate a config file without running.

```bash
panelize validate -c my.toml
# OK · 4 panel(s) · 2 action(s)
#   - git-status   (lines ) Git Status
#   - disk         (regex ) Disk
#   - containers   (tsv   ) Containers
#   - weather      (raw   ) Weather (Paris)
```

## Config lookup order

If no `-c PATH` is given, panelize looks for:

1. `./panelize.toml`
2. `./.panelize.toml`
3. `~/.config/panelize/config.toml`
4. `~/.panelize.toml`

## Examples

See [`examples/`](./examples/):

- `dev-toolkit.toml` — git status, branch, commits, stash
- `devops.toml` — docker, disk, load, ports
- `k8s.toml` — pods, nodes, services, events
- `system.toml` — load, memory, top processes, users

## Use cases

- Personal dev cockpit (git, builds, todos)
- Cluster watch (kubectl, docker, systemd)
- Home server overview (disk, network, services)
- Trading or data feeds (any CLI that prints JSON)
- Replace a wall of `watch -n …` panes with a single TUI

## Comparison

Unlike `tmux` panes or `watch`:

- One config = one dashboard you can version and share
- Each panel has its own refresh interval
- Structured parsers (TSV / JSON / regex) → searchable tables, not text walls
- Theme + keyboard + actions baked in

Unlike full monitoring stacks (Prometheus + Grafana):

- Zero infrastructure. No daemon, no DB, no agent.
- Works anywhere `bash` and `python` work.

## Development

```bash
git clone https://github.com/VFK00/panelize-code.git
cd panelize-code
uv sync --all-extras
uv run pytest                       # tests, 70% coverage gate
uv run ruff check .
uv run mypy src/
```

## License

MIT. See [LICENSE](./LICENSE).

## Acknowledgements

Inspired by `glances`, `htop`, `lazygit`, `k9s`, and an in-house TUI that started life as a project-specific dashboard before realizing it should be a generic tool.
