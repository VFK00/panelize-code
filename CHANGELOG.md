# Changelog

All notable changes to **panelize-code** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-19

First public release.

### Added

- TOML configuration loader with pydantic v2 validation (`config.py`).
- 6 output parsers: `raw`, `lines`, `tsv`, `csv`, `json` (with templates + dotted paths), `regex`.
- Subprocess provider with timeout, exit-code, and `command-not-found` handling.
- Generic Textual application (`PanelizeApp`) that iterates over panels declared in config.
- Generic `PanelWidget` that renders rows in a `DataTable` with status line.
- Auto grid layout: panel count → optimal `cols × rows` (1×1 / 2×1 / 2×2 / 3×2 / 3×3 / 4×3 / 4×N).
- Per-panel refresh intervals (override the global interval).
- Custom actions bound to single-key shortcuts.
- Built-in `panelize` theme + cycle through tokyo-night / monokai / gruvbox / nord / flexoki.
- Two CLI modes:
  - `panelize run` — interactive Textual TUI (default).
  - `panelize show` — one-shot rich snapshot (exit code 0 OK / 2 if any panel failed).
- `panelize init` — write a sample `panelize.toml`.
- `panelize validate` — validate a config file without running.
- Config lookup order: `./panelize.toml` → `./.panelize.toml` → `~/.config/panelize/config.toml` → `~/.panelize.toml`.
- 4 example configs: `dev-toolkit`, `devops`, `k8s`, `system`.
- 62 tests, 86% coverage, ruff clean, mypy strict.
- GitHub Actions CI matrix on Python 3.11 / 3.12 / 3.13.

### Notes

- Requires Python **3.11+** (uses stdlib `tomllib`).
- MIT-licensed.
- No daemon, no DB, no agent — just `bash` + `python`.

[Unreleased]: https://github.com/VFK00/panelize-code/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/VFK00/panelize-code/releases/tag/v0.1.0

## [Unreleased]

### Changed

- `panelize show` now runs panels concurrently (bounded thread pool, declaration
  order preserved in the output). Serial execution paid the sum of every panel's
  latency — measured on four 0.4s commands: **1.6s → 0.63s**. The TUI already ran
  one worker per panel; only the snapshot mode was affected.
