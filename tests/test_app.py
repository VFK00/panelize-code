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
