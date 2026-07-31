# Architecture — panelize-code

TUI générique config-driven. TOML → panels → commandes shell → rendu terminal.

## Vue d'ensemble

| Couche | Module | Rôle |
|--------|--------|------|
| CLI | `cli.py` | Entry point argparse, dispatch sous-commandes |
| Config | `config.py` | Chargement + validation TOML (pydantic) |
| Exécution | `provider.py` | Subprocess, capture stdout, snapshots |
| Parsing | `parsers.py` | 6 parsers stdout → rows |
| Layout | `layout.py` | Grille auto (cols × rows) |
| TUI live | `app.py` + `widgets/panel.py` | Mode `run` (Textual) |
| Snapshot | `render.py` | Mode `show` (Rich one-shot) |
| Thème | `theme.py` | Palette + thèmes built-in |

## Entry point

`panelize_code.cli:main` (déclaré `[project.scripts]`).

| Sous-commande | Fonction | Sortie |
|---------------|----------|--------|
| `run` (défaut) | `cmd_run` → `PanelizeApp.run()` | TUI Textual |
| `show` | `cmd_show` → `render_snapshot()` | Rich, exit `0`/`2` |
| `init` | `cmd_init` | Écrit `SAMPLE_CONFIG` |
| `validate` | `cmd_validate` | Liste panels/actions |

Sans sous-commande → fallback `run`. Helper `_load()` résout le chemin config (arg `-c` ou `find_config()`).

## Système config TOML

### Modèles pydantic (`config.py`)

| Modèle | Champs clés | Contraintes |
|--------|-------------|-------------|
| `AppConfig` | `title`, `refresh` `[1,3600]`, `theme`, `splash` | `extra="forbid"` |
| `PanelConfig` | `id`, `title`, `command`, `parser`, `refresh`, `timeout` `[1,300]`, `icon`, `columns`, `pattern`, `template`, `shell` | `extra="forbid"` |
| `ActionConfig` | `name`, `command`, `shortcut`, `confirm`, `shell`, `timeout` `[1,3600]` | `extra="forbid"` |
| `DashboardConfig` | `app`, `panels[]`, `actions[]` | root |

### Validateurs

| Cible | Règle |
|-------|-------|
| `PanelConfig.id` | Alphanumérique + `-` + `_` |
| `PanelConfig` (post) | `pattern` requis si `parser="regex"` |
| `DashboardConfig.panels` | IDs uniques (sinon erreur duplicate) |

### Chargement

- `load_config(path)` : `tomllib.load` → `DashboardConfig.model_validate`.
- `find_config()` : premier existant dans `default_config_paths()`.
- Ordre lookup : `./panelize.toml` → `./.panelize.toml` → `~/.config/panelize/config.toml` → `~/.panelize.toml`.

## 6 parsers (`parsers.py`)

Signature uniforme : `(stdout: str, panel: PanelConfig) -> list[Row]` où `Row = list[str]`. Dispatch via dict `PARSERS` + fonction `parse()`.

| Parser | Entrée | Sortie | Notes |
|--------|--------|--------|-------|
| `raw` | tout | 1 cellule (stdout complet) | `[]` si vide |
| `lines` | lignes | 1 row/ligne non vide, 1 colonne | — |
| `tsv` | tab-separated | split `\t` | — |
| `csv` | comma-separated | `csv.reader` stdlib | skip rows vides |
| `json` | JSON list/dict/primitive | via `template`, sinon `columns`, sinon dump compact | dict → wrap en liste |
| `regex` | lignes | groupes capturés → colonnes | `pattern` requis |

### Helpers

| Helper | Rôle |
|--------|------|
| `_deep_get(obj, "a.b.c")` | Accès dict imbriqué pointé, `""` si absent |
| `_render_template(tpl, item)` | Rend `{key}` (dotted via `_deep_get`) |

### Gestion erreurs parser

- JSON invalide → `[["[json error] ..."]]`.
- Regex invalide → `[["[regex error] ..."]]`.
- Parser inconnu → `[["[unknown parser: X]"]]`.
- **Jamais d'exception remontée** : erreur inline dans les rows.

## Provider subprocess (`provider.py`)

### Dataclasses

| Dataclass | Champs |
|-----------|--------|
| `PanelSnapshot` | `panel_id`, `rows`, `ok`, `error`, `duration_ms`, `exit_code` |
| `ActionResult` | `name`, `ok`, `stdout`, `stderr`, `exit_code` |

### Flux `run_panel`

1. `_to_args(command, shell)` : `list` → `shell=False` ; `str`+shell → shell réel ; `str`+no-shell → `shlex.split`.
2. `subprocess.run` (`capture_output`, `text`, `timeout`, `check=False`).
3. Exceptions captées : `TimeoutExpired`, `FileNotFoundError`, générique → `ok=False` + `error`.
4. `returncode != 0` → `ok=False`, `error` = 1ère ligne stderr/stdout (tronquée 200).
5. Sinon → `parse(stdout, panel)`.

`run_action` : même logique, retourne `ActionResult` (stdout/stderr/exit).

## Auto grid layout (`layout.py`)

`grid_dimensions(n) -> (cols, rows)` :

| n panels | (cols, rows) |
|----------|--------------|
| 1 | (1, 1) |
| 2 | (2, 1) |
| 3 | (3, 1) |
| 4 | (2, 2) |
| 5–6 | (3, 2) |
| 7–9 | (3, 3) |
| 10–12 | (4, 3) |
| >12 | (4, ⌈n/4⌉) |

## Flux rendu — mode `run` (TUI Textual)

`PanelizeApp` (`app.py`) :

1. `compose` : `Header` + `Grid` (cols via `grid_dimensions`) + 1 `PanelWidget`/panel + `Footer`.
2. `on_mount` : enregistre thème, `refresh_all`, `set_interval` global + intervals per-panel.
3. `refresh_panel(id)` : worker threadé → `run_panel` → `call_from_thread(_apply_snapshot)`.
4. `PanelWidget.update_snapshot` : reconstruit la `DataTable` (colonnes config sinon `col1..N`).

### Bindings

| Touche | Action |
|--------|--------|
| `r` | Refresh all |
| `a` | Menu actions |
| `t` | Cycle thème (`BUILTIN_THEMES`) |
| `p` | Pause/resume auto-refresh |
| `q` / `Ctrl+C` | Quit |
| `?` / `F1` | Aide |
| autre | Action dont `shortcut` matche (`on_key`) |

Action OK → notify + `refresh_all`. Action KO → notify error (stderr tronqué).

## Flux rendu — mode `show` (Rich one-shot)

`render_snapshot(config, console)` (`render.py`) :

1. `run_panel` sur chaque panel.
2. KO → `[red]✗ error[/red]`. Vide → `no output`. Sinon → `rich.Table` (header si `columns`).
3. Wrap en `rich.Panel` (titre `icon title`, subtitle `Nms`).
4. `console.print(Group(...))`.
5. Exit : `0` tous OK, `2` ≥1 échec.

Usage : `watch -n 30 panelize show`, cron, CI.

## Thème (`theme.py`)

- `DEFAULT_THEME` : `Theme` Textual nommé `panelize` (palette tokyo-night-like).
- `BUILTIN_THEMES` : `panelize`, `tokyo-night`, `monokai`, `gruvbox`, `nord`, `flexoki`.
- `COLORS` : map sémantique (`ok`/`warn`/`error`/`info`/`muted`) pour Rich markup.

## Tests

62 tests, 7 fichiers (`test_app`, `test_cli`, `test_config`, `test_layout`, `test_parsers`, `test_provider`, `test_render`). Gate coverage **70%**. Matrice CI : Python 3.11/3.12/3.13.
