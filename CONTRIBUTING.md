# Contributing to panelize-code

Thanks for your interest. This document describes how to set up a dev environment,
the contribution workflow, and the conventions the project follows.

## Quick links

- Issues: <https://github.com/VFK00/panelize-code/issues>
- Discussions are disabled. Use issues for proposals.
- License: [MIT](./LICENSE).

## Development setup

You need **Python 3.11+** and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/VFK00/panelize-code.git
cd panelize-code
uv sync --all-extras
```

That installs the package in editable mode with dev dependencies (`pytest`, `pytest-cov`,
`pytest-asyncio`, `mypy`, `ruff`).

### Common commands

```bash
uv run pytest                       # full test suite, 70% coverage gate
uv run pytest tests/test_parsers.py # one file
uv run pytest -k regex              # by keyword
uv run ruff check .                 # lint
uv run ruff check --fix .           # auto-fix
uv run mypy src/                    # type check (strict)
```

### Running the CLI from the source tree

```bash
uv run panelize init
uv run panelize validate -c panelize.toml
uv run panelize show -c examples/system.toml
uv run panelize run -c examples/dev-toolkit.toml
```

## Project layout

```
src/panelize_code/
  cli.py         # entrypoint: run | show | init | validate
  app.py         # Textual application (loops over config.panels)
  widgets/
    panel.py     # generic panel widget (DataTable + status line)
  config.py      # TOML loader + pydantic models
  provider.py    # subprocess execution + ActionResult / PanelSnapshot
  parsers.py     # raw / lines / tsv / csv / json / regex
  layout.py      # auto grid dimensions
  render.py      # rich snapshot (mode `show`)
  theme.py       # default Textual theme + palette
tests/           # pytest suite (62 tests, 86% coverage)
examples/        # ready-to-use TOML configs
```

## Contribution workflow

1. **Open an issue first** for non-trivial changes (new parser, breaking config change,
   architectural shift). For small fixes / docs / examples, you can skip and PR directly.
2. **Fork + branch.** Branch names: `feat/...`, `fix/...`, `docs/...`, `chore/...`.
3. **Write tests.** Any new behavior gets a test. The 70% coverage gate must hold.
4. **Keep PRs focused.** One concern per PR. Refactors separate from features.
5. **Update [CHANGELOG.md](./CHANGELOG.md)** under `[Unreleased]`.
6. **Run the checks locally** before pushing:
   ```bash
   uv run ruff check .
   uv run mypy src/
   uv run pytest
   ```
7. **Open the PR** against `main`. Reference the issue if one exists.

## Coding conventions

- **Python 3.11+** baseline. Use modern syntax (`str | None`, `list[int]`).
- **`from __future__ import annotations`** at the top of every module.
- **Ruff** is the source of truth for style. No separate formatter.
- **Mypy strict** for `src/`. Test code can be looser.
- **Pydantic v2** for all config models. `model_config = ConfigDict(extra="forbid")`.
- **No global state.** Pass config / dependencies explicitly.
- **Subprocess via `subprocess.run`** with `capture_output=True`, `text=True`, `timeout=…`.
  Always catch `TimeoutExpired` and `FileNotFoundError`.
- **Comments**: only when the *why* is non-obvious. Names should explain the *what*.

## Adding a new parser

1. Add a function `parse_<name>(stdout: str, panel: PanelConfig) -> list[Row]` in
   `parsers.py`.
2. Register it in the `PARSERS` dict and extend `ParserType` in `config.py`.
3. Add tests in `tests/test_parsers.py` covering happy path, empty input, malformed input.
4. Document it in `README.md` (parsers table) and add an example to `examples/` if useful.

## Adding a new example

1. Drop a `.toml` file under `examples/`.
2. The CI test `test_examples_are_valid` will validate it on every push.
3. Mention it in `README.md` under the "Examples" section.

## Releasing (maintainers)

1. Bump version in `pyproject.toml` and `src/panelize_code/__init__.py`.
2. Move `[Unreleased]` entries to a new `[X.Y.Z] - YYYY-MM-DD` section in `CHANGELOG.md`.
3. Commit: `chore: release vX.Y.Z`.
4. Tag: `git tag -a vX.Y.Z -m "panelize-code vX.Y.Z"`.
5. Push: `git push origin main --tags`.
6. Create release: `gh release create vX.Y.Z --title "vX.Y.Z" --notes-from-tag`.

## Reporting bugs

Open an issue with:

- Your Python version (`python --version`).
- Your OS.
- The minimal `panelize.toml` that reproduces the issue.
- The exact command you ran.
- The full traceback or error output.

## Reporting security issues

Don't open a public issue. Email <felis.virama07@gmail.com> with details.

## Code of conduct

Be kind. Assume good faith. Disagreement is fine — disrespect is not. Maintainers may
remove comments, commits, code, edits, and contributors that violate this norm.
