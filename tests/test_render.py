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
