"""Tests for the CLI surface."""

from __future__ import annotations

from pathlib import Path

import pytest

from panelize_code.cli import build_parser, cmd_init, cmd_validate


def test_parser_has_subcommands() -> None:
    parser = build_parser()
    # Argparse exposes sub-actions; ensure parsing succeeds for each.
    for cmd in ["run", "show", "init", "validate"]:
        ns = parser.parse_args([cmd])
        assert ns.command == cmd


def test_cli_version_flag(capsys) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "panelize" in out


def test_init_writes_sample(tmp_path) -> None:
    target = tmp_path / "out.toml"
    ns = type("NS", (), {"path": str(target), "force": False})()
    code = cmd_init(ns)
    assert code == 0
    assert target.exists()
    content = target.read_text()
    assert "[app]" in content
    assert "[[panels]]" in content


def test_init_refuses_overwrite(tmp_path) -> None:
    target = tmp_path / "out.toml"
    target.write_text("existing")
    ns = type("NS", (), {"path": str(target), "force": False})()
    code = cmd_init(ns)
    assert code == 1
    assert target.read_text() == "existing"


def test_init_force_overwrites(tmp_path) -> None:
    target = tmp_path / "out.toml"
    target.write_text("existing")
    ns = type("NS", (), {"path": str(target), "force": True})()
    code = cmd_init(ns)
    assert code == 0
    assert "[app]" in target.read_text()


def test_validate_ok(tmp_path, capsys) -> None:
    cfg = tmp_path / "ok.toml"
    cfg.write_text(
        """
[app]
title = "X"

[[panels]]
id = "a"
title = "A"
command = "echo a"
parser = "raw"
"""
    )
    ns = type("NS", (), {"config": str(cfg)})()
    code = cmd_validate(ns)
    assert code == 0
    assert "OK" in capsys.readouterr().out


def test_validate_invalid(tmp_path) -> None:
    cfg = tmp_path / "bad.toml"
    cfg.write_text(
        """
[[panels]]
id = "bad id!"
title = "x"
command = "x"
"""
    )
    ns = type("NS", (), {"config": str(cfg)})()
    code = cmd_validate(ns)
    assert code == 1


def test_examples_are_valid() -> None:
    """Every shipped example must validate."""
    from panelize_code.config import load_config

    examples = Path(__file__).parent.parent / "examples"
    files = list(examples.glob("*.toml"))
    assert files, "examples directory must not be empty"
    for f in files:
        load_config(f)
