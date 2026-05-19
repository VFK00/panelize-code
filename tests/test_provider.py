"""Tests for subprocess provider (real subprocess calls — no mocking)."""

from __future__ import annotations

from panelize_code.config import ActionConfig, PanelConfig
from panelize_code.provider import run_action, run_panel


def test_run_panel_simple_lines() -> None:
    panel = PanelConfig(
        id="t", title="T", command="printf 'a\\nb\\nc'", parser="lines"
    )
    snap = run_panel(panel)
    assert snap.ok
    assert snap.rows == [["a"], ["b"], ["c"]]
    assert snap.exit_code == 0
    assert snap.duration_ms >= 0


def test_run_panel_command_not_found_returns_error() -> None:
    panel = PanelConfig(
        id="t",
        title="T",
        command=["this-binary-does-not-exist-zzz"],
        parser="raw",
        shell=False,
    )
    snap = run_panel(panel)
    assert not snap.ok
    assert "not found" in snap.error.lower() or "command not found" in snap.error.lower()


def test_run_panel_nonzero_exit() -> None:
    panel = PanelConfig(id="t", title="T", command="exit 3", parser="raw")
    snap = run_panel(panel)
    assert not snap.ok
    assert snap.exit_code == 3


def test_run_panel_timeout() -> None:
    panel = PanelConfig(id="t", title="T", command="sleep 5", parser="raw", timeout=1)
    snap = run_panel(panel)
    assert not snap.ok
    assert "timeout" in snap.error.lower()


def test_run_action_ok() -> None:
    action = ActionConfig(name="ok", command="true")
    result = run_action(action)
    assert result.ok
    assert result.exit_code == 0


def test_run_action_fail() -> None:
    action = ActionConfig(name="fail", command="false")
    result = run_action(action)
    assert not result.ok
    assert result.exit_code == 1


def test_run_panel_list_command() -> None:
    panel = PanelConfig(
        id="t", title="T", command=["echo", "hello"], parser="raw", shell=False
    )
    snap = run_panel(panel)
    assert snap.ok
    assert snap.rows == [["hello"]]
