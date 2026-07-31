"""Tests for the static snapshot renderer."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from panelize_code.config import DashboardConfig, PanelConfig
from panelize_code.render import render_snapshot


def _capture(config: DashboardConfig) -> tuple[int, str]:
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=120)
    code = render_snapshot(config, console)
    return code, buf.getvalue()


def test_render_all_ok() -> None:
    cfg = DashboardConfig(
        panels=[
            PanelConfig(id="a", title="Echo", command="echo hi", parser="raw"),
        ]
    )
    code, output = _capture(cfg)
    assert code == 0
    assert "Echo" in output
    assert "hi" in output


def test_render_failure_returns_exit_2() -> None:
    cfg = DashboardConfig(
        panels=[
            PanelConfig(id="a", title="Bad", command="exit 7", parser="raw"),
        ]
    )
    code, output = _capture(cfg)
    assert code == 2
    assert "Bad" in output


def test_render_mixed() -> None:
    cfg = DashboardConfig(
        panels=[
            PanelConfig(id="a", title="Good", command="echo ok", parser="raw"),
            PanelConfig(id="b", title="Bad", command="exit 1", parser="raw"),
        ]
    )
    code, output = _capture(cfg)
    assert code == 2
    assert "Good" in output
    assert "Bad" in output


def test_show_runs_panels_concurrently() -> None:
    """Four 0.3s commands must finish in ~0.3s, not 1.2s.

    `show` feeds CI and cron jobs. Run serially, a dashboard polling Docker,
    kubectl or the network pays the sum of every latency.
    """
    import time

    panels = [
        PanelConfig(id=f"p{i}", title=f"P{i}", command="sleep 0.3", parser="raw")
        for i in range(4)
    ]
    config = DashboardConfig(panels=panels)
    console = Console(file=StringIO(), width=80)

    started = time.monotonic()
    render_snapshot(config, console=console)
    elapsed = time.monotonic() - started

    # Serial: ~1.2s. Concurrent: ~0.3s. Loose bound so scheduling jitter does
    # not make this flaky, tight enough to catch a regression.
    assert elapsed < 0.8, f"panels ran serially ({elapsed:.2f}s)"
