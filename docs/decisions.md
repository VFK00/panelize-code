# Decisions — panelize-code

ADR append-only. Une entrée par décision technique. Reconstitué depuis le code.

## ADR-001 — Textual comme moteur TUI

### Contexte
Besoin d'un dashboard terminal live : multi-panneaux, auto-refresh, navigation clavier, thèmes. Alternatives : `curses` brut, `urwid`, `blessed`, Rich seul.

### Décision
**Textual** (`>=0.80`) pour le mode interactif. App = `PanelizeApp(App[int])`, layout `Grid`, tuiles = `PanelWidget(Vertical)` avec `DataTable`. Workers threadés par panel (`run_worker(thread=True)`) + `call_from_thread` pour le retour UI.

### Conséquences
- Refresh async par panel sans bloquer l'UI ; un panel lent ne fige pas les autres.
- Système de thèmes natif Textual réutilisé (`register_theme`, `self.theme`).
- CSS Textual pour le style des widgets (`DEFAULT_CSS`).
- Dépendance lourde vs curses. Acceptée pour la productivité.

## ADR-002 — Config TOML driven, zéro code

### Contexte
Cible : décrire un dashboard sans écrire de Python. Besoin format déclaratif lisible, versionnable, partageable.

### Décision
Dashboard **100% déclaré en TOML** : `[app]`, `[[panels]]`, `[[actions]]`. Parsing via `tomllib` (stdlib 3.11+). Validation stricte via **pydantic v2**, tous les modèles en `extra="forbid"` (clé inconnue = erreur). Lookup multi-chemins (`./panelize.toml` → `~/.config/panelize/config.toml` → …).

### Conséquences
- Une config = un dashboard versionnable et partageable.
- Erreurs de config détectées tôt (`panelize validate`).
- `extra="forbid"` empêche les typos silencieuses.
- Aucune logique custom possible côté user : tout passe par commandes shell + parsers.

## ADR-003 — 6 parsers stdout pluggables

### Contexte
Les commandes shell impriment des formats hétérogènes : texte brut, lignes, TSV, CSV, JSON, sorties à parser via regex. Besoin de transformer stdout en rows tabulaires.

### Décision
**6 parsers** : `raw`, `lines`, `tsv`, `csv`, `json`, `regex`. Signature uniforme `(stdout, panel) -> list[Row]`. Dispatch via dict `PARSERS` + `parse()`. JSON supporte `template` et `columns` dotted (`meta.name`). Regex : groupes nommés/positionnels → colonnes. **Erreurs inline** dans les rows (`[json error] …`), jamais d'exception remontée.

### Conséquences
- Tables structurées et recherchables (vs murs de texte de `watch`).
- Extensible : ajouter un parser = 1 fonction + 1 entrée dict.
- Erreur d'un parser visible dans la tuile, n'interrompt pas le dashboard.

## ADR-004 — Subprocess isolé par panel + dégradation gracieuse

### Contexte
Chaque panel exécute une commande externe pouvant échouer : binaire absent, exit non-zéro, timeout. Un échec ne doit pas tuer le dashboard.

### Décision
`provider.run_panel` capture **toutes** les exceptions subprocess (`TimeoutExpired`, `FileNotFoundError`, générique) → `PanelSnapshot(ok=False, error=...)`. Timeout par panel (défaut 10s). `_to_args` : `list[str]` → `shell=False`, string → shell réel (défaut) ou `shlex.split`. Mode `show` exit `2` si ≥1 panel échoue.

### Conséquences
- Un panel KO affiche son erreur, les autres continuent.
- Exit code `show` exploitable en CI/cron/monitoring.
- `shell=True` par défaut : pipes/awk/curl OK, mais usage local de confiance requis (pas de configs non fiables).

## ADR-005 — Deux modes : `run` (TUI) et `show` (snapshot)

### Contexte
Deux usages : cockpit interactif live + check ponctuel scriptable (CI, cron, `watch`).

### Décision
- **`run`** : `PanelizeApp` Textual, auto-refresh global + per-panel, actions live.
- **`show`** : `render_snapshot` (Rich), one-shot, exit `0`/`2`.
- Aussi `init` (sample config) et `validate` (check sans run). CLI via **argparse** (stdlib), pas click/typer.

### Conséquences
- Même config, deux consommations.
- `show` intégrable pipeline sans terminal interactif.
- argparse = zéro dépendance CLI supplémentaire.

## ADR-006 — Auto grid layout

### Contexte
Disposer N panels lisiblement sans config manuelle de grille.

### Décision
`grid_dimensions(n) -> (cols, rows)` : mapping codé (1→1×1, 4→2×2, 5-6→3×2, 7-9→3×3, 10-12→4×3, >12→4×⌈n/4⌉). Appliqué via `Grid.styles.grid_size_columns`.

### Conséquences
- Layout optimal automatique, zéro config layout côté user.
- Au-delà de 12 panels : 4 colonnes fixes, lignes calculées.

## ADR-007 — Packaging hatchling + uv

### Contexte
Distribution PyPI + dev local reproductible. Alternatives : setuptools, poetry, pdm.

### Décision
Build backend **hatchling** (`[build-system]`, wheel packages `src/panelize_code`). Layout `src/`. Gestion deps + lock + install via **uv** (`uv sync --all-extras`, `uv tool install .`). Extras `dev` : pytest, pytest-cov, pytest-asyncio, mypy, ruff. Coverage gate **70%** (`--cov-fail-under=70`). CI matrice Python 3.11/3.12/3.13.

### Conséquences
- `uv tool install .` → binaire global `panelize`.
- Lock reproductible (`uv.lock`).
- mypy strict + ruff (`E,F,I,N,W,UP,B,C4,SIM`, line 100) garde-fous qualité.
- CI : lint + tests bloquants, mypy `continue-on-error`.

## ADR-008 — Licence MIT, open-source public

### Contexte
Outil générique réutilisable, sans logique métier propriétaire. Issu d'un TUI projet-spécifique généralisé.

### Décision
Publication **open-source MIT** sur `github.com/VFK00/panelize-code`. README, CHANGELOG, CONTRIBUTING, classifiers PyPI (Beta, OS POSIX/MacOS). Aucune info privée/infra dans le repo.

### Conséquences
- Réutilisable et forkable librement.
- Contraintes : code/docs/commits en anglais, zéro donnée sensible commitée.
- Maintenance publique (issues, PRs).
