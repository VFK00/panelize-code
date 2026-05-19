"""Tests for config loader + validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from panelize_code.config import (
    ActionConfig,
    AppConfig,
    DashboardConfig,
    PanelConfig,
    load_config,
)


def test_default_app_config() -> None:
    app = AppConfig()
    assert app.title == "panelize"
    assert app.refresh == 30
    assert app.theme == "default"


def test_panel_minimal() -> None:
    p = PanelConfig(id="x", title="X", command="echo hi")
    assert p.id == "x"
    assert p.parser == "raw"
    assert p.timeout == 10


def test_panel_id_validation() -> None:
    PanelConfig(id="my-panel_1", title="x", command="x")
    with pytest.raises(ValidationError):
        PanelConfig(id="bad id!", title="x", command="x")


def test_panel_regex_requires_pattern() -> None:
    with pytest.raises(ValidationError):
        PanelConfig(id="r", title="r", command="x", parser="regex")
    p = PanelConfig(id="r", title="r", command="x", parser="regex", pattern=r"(\d+)")
    assert p.pattern == r"(\d+)"


def test_panel_refresh_bounds() -> None:
    with pytest.raises(ValidationError):
        PanelConfig(id="x", title="x", command="x", refresh=0)
    with pytest.raises(ValidationError):
        PanelConfig(id="x", title="x", command="x", refresh=99999)


def test_unique_panel_ids() -> None:
    with pytest.raises(ValidationError):
        DashboardConfig(
            panels=[
                PanelConfig(id="a", title="A", command="x"),
                PanelConfig(id="a", title="B", command="x"),
            ]
        )


def test_action_minimal() -> None:
    a = ActionConfig(name="x", command="x")
    assert a.confirm is False
    assert a.timeout == 60


def test_load_config_from_toml(tmp_path) -> None:
    cfg_file = tmp_path / "panelize.toml"
    cfg_file.write_text(
        """
[app]
title = "Test"
refresh = 5

[[panels]]
id = "p1"
title = "P1"
command = "echo hello"
parser = "lines"

[[actions]]
name = "do"
command = "true"
""",
        encoding="utf-8",
    )
    cfg = load_config(cfg_file)
    assert cfg.app.title == "Test"
    assert cfg.app.refresh == 5
    assert len(cfg.panels) == 1
    assert cfg.panels[0].id == "p1"
    assert len(cfg.actions) == 1


def test_load_config_missing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.toml")


def test_extra_keys_forbidden(tmp_path) -> None:
    cfg_file = tmp_path / "p.toml"
    cfg_file.write_text(
        """
[app]
title = "X"
unknown_key = "boom"
""",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_config(cfg_file)
