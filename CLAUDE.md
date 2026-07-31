# CLAUDE.md

Guide pour Claude Code sur ce repo. Lire avant toute edition.

## Nature du projet

- **TUI generique config-driven**. Declare des panels en TOML, point chacun sur une commande shell, obtient un dashboard terminal live.
- **Zero code requis cote user** : tout ce qui imprime sur stdout devient une tuile.
- Outil **open-source MIT**, public : `github.com/VFK00/panelize-code`.
- Binaire : `panelize`. Package : `panelize_code`.

## Stack

| Composant | Choix | Version |
|-----------|-------|---------|
| TUI engine | **Textual** | `>=0.80` |
| Rendu snapshot | **Rich** | `>=13.7` |
| Validation config | **pydantic v2** | `>=2.9` |
| Parsing TOML | `tomllib` (stdlib) | Python 3.11+ |
| CLI | `argparse` (stdlib) | — |
| Subprocess | `subprocess` (stdlib) | — |
| Build | **hatchling** | — |
| Gestion deps | **uv** | — |
| Python | **3.11+** (testé 3.11/3.12/3.13) | — |
| Tests | **pytest** + `pytest-cov` + `pytest-asyncio` | gate **70%** |
| Lint / type | **ruff** + **mypy strict** | — |

## Structure

```
panelize-code/
├── src/panelize_code/
│   ├── __init__.py        # __version__
│   ├── cli.py             # entry point argparse: run|show|init|validate
│   ├── config.py          # pydantic models + load_config + find_config
│   ├── parsers.py         # 6 parsers + dispatch parse()
│   ├── provider.py        # subprocess run_panel/run_action -> snapshots
│   ├── layout.py          # grid_dimensions(n) -> (cols, rows)
│   ├── app.py             # PanelizeApp (Textual App) — mode `run`
│   ├── render.py          # render_snapshot (rich) — mode `show`
│   ├── theme.py           # DEFAULT_THEME + BUILTIN_THEMES + COLORS
│   └── widgets/panel.py   # PanelWidget (DataTable) — une tuile TUI
├── tests/                 # 62 tests (7 fichiers)
├── examples/              # dev-toolkit / devops / k8s / system .toml
├── pyproject.toml
├── README.md · CHANGELOG.md · CONTRIBUTING.md · LICENSE (MIT)
└── .github/workflows/ci.yml
```

Detail flux + parsers : `docs/architecture.md`. Choix techniques : `docs/decisions.md`.

## Commandes courantes

```bash
uv sync --all-extras                          # install deps + extras dev
uv run pytest                                 # 62 tests, gate coverage 70%
uv run ruff check .                           # lint
uv run mypy src/                              # type check strict
uv tool install .                             # binaire global `panelize`
```

### CLI `panelize`

| Sous-commande | Role | Exit codes |
|---------------|------|------------|
| `panelize run` (defaut) | TUI Textual live, auto-refresh | — |
| `panelize show` | Snapshot rich one-shot (CI/cron) | `0` OK · `2` un panel a échoué |
| `panelize init [path]` | Ecrit un sample `panelize.toml` (`--force` pour écraser) | `0` · `1` si fichier existe |
| `panelize validate` | Valide config sans run | `0` OK · `1` invalide |

```bash
panelize init                                 # genere ./panelize.toml
panelize run -c examples/dev-toolkit.toml     # TUI
panelize show -c examples/system.toml         # snapshot CI-friendly
panelize validate -c my.toml
```

### Ordre lookup config (si pas de `-c`)

1. `./panelize.toml`
2. `./.panelize.toml`
3. `~/.config/panelize/config.toml`
4. `~/.panelize.toml`

## Conventions code observées

- `from __future__ import annotations` en tête de **chaque** module.
- Type hints partout. **mypy strict** + `warn_unreachable`.
- pydantic : tous les modèles en `extra="forbid"` (config stricte, clé inconnue = erreur).
- Bornes sur les ints config : `refresh` `[1, 3600]`, `timeout` panel `[1, 300]`, `timeout` action `[1, 3600]`.
- Parsers : signature uniforme `(stdout: str, panel: PanelConfig) -> list[Row]` où `Row = list[str]`. Dispatch via dict `PARSERS`.
- Erreurs parser **inline** dans les rows (`[json error] ...`, `[regex error] ...`), pas d'exception remontée.
- Provider : capture toutes les exceptions subprocess (`TimeoutExpired`, `FileNotFoundError`, générique) → `snap.ok = False` + `snap.error`. Un panel KO ne casse pas les autres.
- Textual : workers threadés par panel (`run_worker(..., thread=True)`), retour UI via `call_from_thread`.
- ruff select : `E, F, I, N, W, UP, B, C4, SIM`. Line-length **100**.
- Docstrings module + fonction systématiques.

## Pieges connus

- **`shell=True` par defaut** pour les commandes string : exécution shell réelle (pipes, `awk`, `curl` OK dans les exemples). Commande en `list[str]` → `shell=False` (pas d'interprétation shell). Outil destiné à un usage **local**, pas à exécuter des configs non fiables.
- **Coverage gate 70%** hardcodé dans `pyproject.toml` (`--cov-fail-under=70`). `pytest` échoue sous le seuil même si tous les tests passent.
- **`pytest-asyncio` mode `auto`** : tests async sans décorateur explicite. Combo `pytest 9.x` + `pytest-asyncio` ancien = conflit de résolution ; rester sur versions du lock.
- **CI mypy `continue-on-error: true`** : le type check ne bloque pas la CI (`.github/workflows/ci.yml`). Lint et tests bloquent.
- **Parser `regex`** : `pattern` obligatoire (model_validator rejette sinon). Groupes nommés priment sur positionnels si `columns` défini.
- **Parser `json`** : `columns` supporte les chemins pointés (`meta.name`) via `_deep_get`. `template` rend `{key}` (dotted OK).
- **`id` panel** : alphanumerique + `-` + `_` uniquement. IDs dupliqués → erreur de validation.
- **Theme `panelize`** enregistré au mount ; `t` cycle dans `BUILTIN_THEMES`. Échec thème = warning, pas de crash.

## Doc projet

Structure : `CLAUDE.md` (racine) + `docs/{architecture,decisions,fixes}.md`. MAJ doc dans le **même commit** que le code concerné.

## Style

Anglais pour le code, docstrings, README, commits (projet public). Conventional commits.
