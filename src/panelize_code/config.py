"""TOML config loader + validator (pydantic).

Schema example::

    [app]
    title = "My Dashboard"
    refresh = 30
    theme = "default"

    [[panels]]
    id = "git"
    title = "Git Status"
    command = "git status --short"
    parser = "lines"

    [[actions]]
    name = "Deploy"
    command = "make deploy"
    shortcut = "d"
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ParserType = Literal["raw", "lines", "tsv", "csv", "json", "regex"]


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = "panelize"
    refresh: int = Field(default=30, ge=1, le=3600)
    theme: str = "default"
    splash: bool = True


class PanelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=64)
    title: str
    command: str | list[str]
    parser: ParserType = "raw"
    refresh: int | None = Field(default=None, ge=1, le=3600)
    timeout: int = Field(default=10, ge=1, le=300)
    icon: str = ""
    columns: list[str] = Field(default_factory=list)
    pattern: str = ""
    template: str = ""
    shell: bool = True

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("id must be alphanumeric (- and _ allowed)")
        return v

    @model_validator(mode="after")
    def _check_regex_pattern(self) -> PanelConfig:
        if self.parser == "regex" and not self.pattern:
            raise ValueError("pattern is required when parser='regex'")
        return self


class ActionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    command: str | list[str]
    shortcut: str = ""
    confirm: bool = False
    shell: bool = True
    timeout: int = Field(default=60, ge=1, le=3600)


class DashboardConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: AppConfig = Field(default_factory=AppConfig)
    panels: list[PanelConfig] = Field(default_factory=list)
    actions: list[ActionConfig] = Field(default_factory=list)

    @field_validator("panels")
    @classmethod
    def validate_unique_panel_ids(cls, v: list[PanelConfig]) -> list[PanelConfig]:
        ids = [p.id for p in v]
        if len(ids) != len(set(ids)):
            dupes = {x for x in ids if ids.count(x) > 1}
            raise ValueError(f"duplicate panel ids: {sorted(dupes)}")
        return v


def load_config(path: Path) -> DashboardConfig:
    """Load + validate TOML config file."""
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {path}")
    with path.open("rb") as fh:
        raw = tomllib.load(fh)
    return DashboardConfig.model_validate(raw)


def default_config_paths() -> list[Path]:
    """Default lookup order for config file."""
    return [
        Path.cwd() / "panelize.toml",
        Path.cwd() / ".panelize.toml",
        Path.home() / ".config" / "panelize" / "config.toml",
        Path.home() / ".panelize.toml",
    ]


def find_config() -> Path | None:
    """Return first existing config from default paths, or None."""
    for p in default_config_paths():
        if p.exists():
            return p
    return None
