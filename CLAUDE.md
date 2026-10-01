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
| Tests | **pytest** + `pytest-cov` + `pytest-asyncio` | gate : voir Pieges |
| Lint / type | **ruff** + **mypy strict** | — |

## Commandes courantes

```bash
uv sync --all-extras                          # install deps + extras dev
uv run pytest                                 # suite + gate coverage
uv run ruff check .                           # lint
uv run mypy src/                              # type check strict
uv tool install --force --reinstall .        # binaire global `panelize`, puis controle par contenu
```

⚠ `panelize --version` ne prouve pas que le binaire est a jour : le 2026-10-01 il affichait `0.2.0` comme la
source, mais venait du scratchpad d'une ancienne session, sans les correctifs de `952d196` (reinstalle depuis
ce depot le meme jour). Controle : hacher `src/panelize_code/*.py` contre la copie sous
`~/.local/share/uv/tools/panelize-code/`, ou comparer a `uv run panelize` sur le meme cas.

### CLI `panelize`

| Sous-commande | Role | Exit codes |
|---------------|------|------------|
| `panelize run` (defaut) | TUI Textual live, auto-refresh | — |
| `panelize show` | Snapshot rich one-shot (CI/cron) | `0` OK · `2` un panel a échoué · `1` config absente ou invalide (traceback) |
| `panelize init [path]` | Ecrit un sample `panelize.toml` (`--force` pour écraser) | `0` · `1` si fichier existe |
| `panelize validate` | Valide config sans run | `0` OK · `1` invalide |

```bash
panelize init                                 # genere ./panelize.toml
panelize run -c examples/dev-toolkit.toml     # TUI
panelize show -c examples/system.toml         # snapshot CI-friendly
panelize validate -c my.toml
```

Ordre de recherche de la config sans `-c` : `README.md`, section « Config lookup order ».

## Conventions code observées

- `from __future__ import annotations` en tête de chaque module, sauf les `__init__.py`.
- Type hints partout sauf 4 handlers de `app.py` (`type: ignore[no-untyped-def]`). **mypy strict** + `warn_unreachable`.
- pydantic : tous les modèles en `extra="forbid"` (config stricte, clé inconnue = erreur).
- Bornes sur les ints config : `refresh` `[1, 3600]`, `timeout` panel `[1, 300]`, `timeout` action `[1, 3600]`.
- Parsers : signature uniforme `(stdout: str, panel: PanelConfig) -> list[Row]` où `Row = list[str]`. Dispatch via dict `PARSERS`.
- Erreurs parser **inline** dans les rows (`[json error] ...`, `[regex error] ...`), pas d'exception remontée.
- Provider : capture toutes les exceptions subprocess (`TimeoutExpired`, `FileNotFoundError`, générique) → `snap.ok = False` + `snap.error`. Un panel KO ne casse pas les autres.
- Textual : workers threadés par panel (`run_worker(..., thread=True)`), retour UI via `call_from_thread`.
- ruff select : `E, F, I, N, W, UP, B, C4, SIM`. Line-length **100**.
- Docstring sur chaque module et sur les fonctions publiques de `parsers`, `provider`, `render`, `layout` ; `cli.py` et la plupart d'`app.py` n'en ont pas.

## Pieges connus

- **`shell=True` par defaut** pour les commandes string : exécution shell réelle (pipes, `awk`, `curl` OK dans les exemples). Commande en `list[str]` → `shell=False` (pas d'interprétation shell). Outil destiné à un usage **local**, pas à exécuter des configs non fiables.
- **Coverage gate 70%** hardcodé dans `pyproject.toml` (`--cov-fail-under=70`). `pytest` échoue sous le seuil même si tous les tests passent.
- **`pytest-asyncio` mode `auto`** : tests async sans décorateur explicite. Combo `pytest 9.x` + `pytest-asyncio` ancien = conflit de résolution ; rester sur versions du lock.
- **Noms `_prefixes` sur les classes Textual** : `DOMNode.__init__` pose des attributs d'instance (`_auto_refresh`, `_auto_refresh_timer`, ...) qui **masquent silencieusement** une methode de meme nom sur une sous-classe. `self.set_interval(n, self._auto_refresh)` passe alors `None`, et Textual cree un timer sans callback sans lever d'erreur. Verifier `dir(App())` — une instance, pas la classe : `dir(DOMNode)` ne montre pas ces attributs — avant de nommer un handler avec un underscore. Cas reel : `journal.md` FIX-1.
- **CI mypy bloquant** depuis le 2026-08-01 (`continue-on-error` retire). Lint, type check et tests bloquent tous les trois.
- **Parser `regex`** : `pattern` obligatoire (model_validator rejette sinon). Si `columns` est défini, seuls les groupes nommés comptent : un groupe positionnel donne une cellule vide. Les lignes non appariées sont sautées. `validate` ne compile pas le motif : une regex invalide n'apparait qu'au run, dans la tuile.
- **Parser `json`** : `columns` supporte les chemins pointés (`meta.name`) via `_deep_get`. `template` rend `{key}` (dotted OK).
- **`id` panel** : alphanumerique + `-` + `_` uniquement. IDs dupliqués → erreur de validation.
- **Theme `panelize`** enregistré au mount mais appliqué seulement si `[app] theme = "panelize"` : le défaut `"default"` (`config.py`, figé par `tests/test_config.py`) est refusé par Textual et retombe **en silence** sur `textual-dark`. `t` cycle dans `BUILTIN_THEMES` ; un échec de `t` = warning.
- **Raccourcis d'action** : `RESERVED_KEYS` (`config.py`) refuse au chargement tout `shortcut` pris par l'app ; un test vérifie qu'il couvre chaque touche de `PanelizeApp.BINDINGS` — ajouter un binding sans l'y ajouter casse la suite. Avant, une telle action se déclenchait **en plus** de la touche (`p` mettait en pause et lançait `docker system prune -f` dans `examples/devops.toml`).
- **`confirm = true`** ouvre `ConfirmScreen` (y / n / esc) avant l'action. Pendant la question, `on_key` ignore les raccourcis : sans cette garde, une seconde frappe relançait l'action.

## Doc projet

Docs embarquées : `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, ce `CLAUDE.md`. `docs/{architecture,decisions,journal,todo}.md`
est **local, hors VCS** depuis `d50d480` ; ses premières versions restent lisibles dans l'historique public (à partir de `9c55ef5`). MAJ doc dans le **meme commit** que le code concerne — pour `docs/`,
cela signifie au meme moment, meme si le contenu ne part pas dans le commit.

`docs/` etant hors VCS, il n'a pas le filet de git : sa seule sauvegarde est celle du poste.

## Style

Anglais pour le code, docstrings, README, commits (projet public). Conventional commits.
