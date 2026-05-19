"""CLI: panelize run | show | init | validate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from . import __version__
from .config import DashboardConfig, find_config, load_config

SAMPLE_CONFIG = """# panelize-code config — TOML
#
# Define panels (one per dashboard tile) and optional actions.
# Each panel runs a shell command on an interval and renders the parsed output.

[app]
title = "My Dashboard"
refresh = 30                  # global refresh interval (seconds)
theme = "panelize"

# ----- Panels -----

[[panels]]
id = "git"
title = "Git Status"
icon = "G"
command = "git status --short"
parser = "lines"
refresh = 15

[[panels]]
id = "disk"
title = "Disk Usage"
icon = "D"
command = "df -h --output=target,pcent,avail / /home"
parser = "regex"
pattern = "^(?P<mount>\\\\S+)\\\\s+(?P<pct>\\\\S+)\\\\s+(?P<avail>\\\\S+)$"
columns = ["mount", "pct", "avail"]

[[panels]]
id = "ports"
title = "Listening Ports"
icon = "P"
command = "ss -tlnH | awk '{print $4}' | sort -u | head -20"
parser = "lines"

[[panels]]
id = "weather"
title = "Weather (Paris)"
icon = "W"
command = "curl -s wttr.in/Paris?format=3"
parser = "raw"
refresh = 600

# ----- Actions (press shortcut key in TUI) -----

[[actions]]
name = "git pull"
command = "git pull"
shortcut = "g"

[[actions]]
name = "fetch all"
command = "git fetch --all"
shortcut = "f"
"""


def cmd_run(args: argparse.Namespace) -> int:
    config = _load(args.config)
    from .app import PanelizeApp

    app = PanelizeApp(config)
    return app.run() or 0


def cmd_show(args: argparse.Namespace) -> int:
    config = _load(args.config)
    from .render import render_snapshot

    return render_snapshot(config, Console())


def cmd_init(args: argparse.Namespace) -> int:
    dest = Path(args.path).resolve()
    if dest.exists() and not args.force:
        print(f"error: {dest} already exists (use --force to overwrite)", file=sys.stderr)
        return 1
    dest.write_text(SAMPLE_CONFIG, encoding="utf-8")
    print(f"sample config written to {dest}")
    print(f"run: panelize run --config {dest}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        config = _load(args.config)
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"OK · {len(config.panels)} panel(s) · {len(config.actions)} action(s)")
    for p in config.panels:
        print(f"  - {p.id:20s} ({p.parser:6s}) {p.title}")
    return 0


def _load(config_path: str | None) -> DashboardConfig:
    if config_path:
        path = Path(config_path).expanduser().resolve()
    else:
        found = find_config()
        if found is None:
            print(
                "error: no config file found. Run `panelize init` or pass --config PATH.",
                file=sys.stderr,
            )
            sys.exit(1)
        path = found
    return load_config(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="panelize",
        description="Config-driven terminal dashboard. Point TOML at shell commands, get a TUI.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", required=False)

    p_run = sub.add_parser("run", help="Run the live TUI (default)")
    p_run.add_argument("-c", "--config", help="Path to config TOML")
    p_run.set_defaults(func=cmd_run)

    p_show = sub.add_parser("show", help="One-shot snapshot (rich, for CI/cron)")
    p_show.add_argument("-c", "--config", help="Path to config TOML")
    p_show.set_defaults(func=cmd_show)

    p_init = sub.add_parser("init", help="Write a sample config file")
    p_init.add_argument("path", nargs="?", default="panelize.toml")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_val = sub.add_parser("validate", help="Validate a config file")
    p_val.add_argument("-c", "--config", help="Path to config TOML")
    p_val.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        # no subcommand -> default to `run`
        args.config = None
        return cmd_run(args)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
