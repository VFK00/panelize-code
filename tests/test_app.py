"""Smoke tests for the Textual App + PanelWidget (via textual.pilot)."""

from __future__ import annotations

import pytest

from panelize_code.app import PanelizeApp
from panelize_code.config import AppConfig, DashboardConfig, PanelConfig
from panelize_code.provider import PanelSnapshot
from panelize_code.widgets import PanelWidget


def _mini_config(refresh: int = 0) -> DashboardConfig:
    """Build a config with refresh=0 to avoid the auto-refresh interval."""
    return DashboardConfig(
        app=AppConfig(title="Test", refresh=refresh or 1),
        panels=[
            PanelConfig(id="p1", title="P1", command="echo hello", parser="raw"),
            PanelConfig(id="p2", title="P2", command="echo world", parser="raw"),
        ],
    )


@pytest.mark.asyncio
async def test_app_mounts_and_quits() -> None:
    app = PanelizeApp(_mini_config())
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.title == "Test"
        # 2 panels expected
        assert len(app.config.panels) == 2
        await pilot.press("q")


@pytest.mark.asyncio
async def test_app_refresh_binding() -> None:
    app = PanelizeApp(_mini_config())
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        await pilot.press("q")


@pytest.mark.asyncio
async def test_auto_refresh_callback_is_callable() -> None:
    """Guard the cause: every interval must receive a real callable.

    `DOMNode.__init__` sets an *instance* attribute `_auto_refresh`, which
    shadows any method of that name on a subclass. A handler named
    `_auto_refresh` therefore resolves to None, `set_interval` gets None
    instead of a callback, and the timer fires into the void.
    """
    app = PanelizeApp(_mini_config(refresh=1))
    captured: list[object] = []
    real_set_interval = app.set_interval

    def spy(interval, callback=None, *args, **kwargs):  # type: ignore[no-untyped-def]
        captured.append(callback)
        return real_set_interval(interval, callback, *args, **kwargs)

    app.set_interval = spy  # type: ignore[method-assign]

    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("q")

    assert captured, "on_mount registered no interval at all"
    assert all(callable(cb) for cb in captured), (
        f"interval registered with a non-callable callback: {captured}"
    )


@pytest.mark.asyncio
async def test_auto_refresh_actually_ticks() -> None:
    """Guard the behaviour: a live dashboard must refresh on its own."""
    app = PanelizeApp(_mini_config(refresh=1))
    calls = {"n": 0}
    real_refresh_all = app.refresh_all

    def counting() -> None:
        calls["n"] += 1
        real_refresh_all()

    app.refresh_all = counting  # type: ignore[method-assign]

    async with app.run_test() as pilot:
        await pilot.pause()
        calls["n"] = 0          # discard the initial refresh done by on_mount
        await pilot.pause(1.3)  # one full period at refresh=1
        await pilot.press("q")

    assert calls["n"] >= 1, "auto-refresh interval never fired"


@pytest.mark.asyncio
async def test_app_pause_binding() -> None:
    app = PanelizeApp(_mini_config())
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.paused is False
        await pilot.press("p")
        await pilot.pause()
        assert app.paused is True
        await pilot.press("q")


@pytest.mark.asyncio
async def test_app_help_binding() -> None:
    app = PanelizeApp(_mini_config())
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("question_mark")
        await pilot.pause()
        await pilot.press("q")


@pytest.mark.asyncio
async def test_panel_widget_updates_on_snapshot() -> None:
    config = _mini_config()
    app = PanelizeApp(config)
    async with app.run_test() as pilot:
        await pilot.pause()
        widget = app._panel_widgets["p1"]
        assert isinstance(widget, PanelWidget)
        # Inject a successful snapshot
        snap = PanelSnapshot(panel_id="p1", rows=[["row1"], ["row2"]], ok=True)
        widget.update_snapshot(snap)
        await pilot.pause()
        # Inject an error snapshot
        snap_err = PanelSnapshot(panel_id="p1", rows=[], ok=False, error="boom")
        widget.update_snapshot(snap_err)
        await pilot.pause()
        # Inject an empty snapshot
        snap_empty = PanelSnapshot(panel_id="p1", rows=[], ok=True)
        widget.update_snapshot(snap_empty)
        await pilot.pause()
        await pilot.press("q")


@pytest.mark.asyncio
async def test_app_shows_actions_menu() -> None:
    config = DashboardConfig(
        app=AppConfig(title="Test", refresh=1),
        panels=[PanelConfig(id="p1", title="P1", command="echo x", parser="raw")],
    )
    app = PanelizeApp(config)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("a")
        await pilot.pause()
        await pilot.press("q")
