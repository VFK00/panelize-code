"""Static snapshot rendering (rich). Used by `panelize show` for CI / cron."""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table

from .config import DashboardConfig
from .provider import run_panel


def render_snapshot(config: DashboardConfig, console: Console | None = None) -> int:
    """Run all panels once, print as rich panels, return exit code.

    Exit code: 0 if all OK, 2 if at least one panel failed.
    """
    if console is None:
        console = Console()

    panels_render = []
    any_failed = False
    for panel_cfg in config.panels:
        snap = run_panel(panel_cfg)
        if not snap.ok:
            any_failed = True

        if not snap.ok:
            body: object = f"[red]✗ {snap.error}[/red]"
        elif not snap.rows:
            body = "[dim]no output[/dim]"
        else:
            tbl = Table(show_header=bool(panel_cfg.columns), box=None, padding=(0, 1))
            cols = panel_cfg.columns or [""] * max(len(r) for r in snap.rows)
            for c in cols:
                tbl.add_column(c)
            for row in snap.rows:
                padded = row + [""] * (len(cols) - len(row))
                tbl.add_row(*padded[: len(cols)])
            body = tbl

        title = f"{panel_cfg.icon} {panel_cfg.title}".strip()
        footer = f"[dim]{snap.duration_ms}ms[/dim]"
        panels_render.append(
            Panel(body, title=title, subtitle=footer, border_style="cyan", expand=True)
        )

    console.print(Group(*panels_render))
    return 2 if any_failed else 0
