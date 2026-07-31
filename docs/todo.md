# Todo — panelize-code

> Backlog technique persistant. Une entree = une tache livrable.
> Cocher `[x]` a la livraison, purger les entrees cochees au commit suivant.
> Ne pas dupliquer les issues GitHub — referencer (`#142`).
>
> Priorites : `P0` bloquant prod · `P1` prochaine iteration · `P2` opportuniste · `P3` idee.
> Ajout via `/doc todo "<task>"`. Ne jamais reordonner les entrees existantes.
>
> Format d'une entree :
>
> ```
> - [ ] **TODO-001** — <tache, verbe d'action> — `P1` — YYYY-MM-DD
>   - **Contexte** : pourquoi cette tache existe (bug lie, ADR, dette).
>   - **Critere de sortie** : comment on sait que c'est fini.
>   - **Fichiers** : `path/vers/fichier.py`
> ```

## En cours

- [ ] **TODO-001** — Publier sur PyPI — `P1` — 2026-08-01
  - **Contexte** : le depot est public, MIT, `pyproject.toml` complet (keywords, classifiers,
    `[project.urls]`), packaging hatchling fonctionnel — et **absent de PyPI**. Personne ne peut
    l'installer sans cloner. **0 etoile, 0 fork** : ce n'est pas un probleme de qualite, c'est
    un probleme de decouvrabilite. Aucune amelioration technique ne compense ce point.
  - **Prerequis raisonnable** : traiter TODO-002 d'abord, pour ne pas figer une premiere
    version publique avec 6 erreurs de typage connues.
  - **Critere de sortie** : `pip install panelize-code` fonctionne depuis une machine tierce ;
    le README documente cette voie d'installation en premier, avant le clone.
  - **Fichiers** : `pyproject.toml`, `README.md`, `.github/workflows/`

- [ ] **TODO-002** — Remettre `mypy --strict` au vert — `P1` — 2026-08-01
  - **Contexte** : **6 erreurs** dans 4 fichiers, toutes anterieures. `parsers.py:107,118`
    (`dict` sans parametres de type), `render.py:45` et `widgets/panel.py:44` x2 (`object`
    passe la ou Rich/Textual attendent un type precis), `app.py:74` (`_auto_refresh` incompatible
    avec la signature de `DOMNode`). La CI les tolere via `continue-on-error: true` — le type
    check ne bloque donc rien aujourd'hui.
  - **Critere de sortie** : `uv run mypy src/` sans erreur, et `continue-on-error` retire du
    workflow pour que la regression soit impossible.
  - **Fichiers** : `src/panelize_code/{parsers,render,app}.py`, `widgets/panel.py`,
    `.github/workflows/ci.yml`

- [ ] **TODO-003** — Couvrir `app.py` et `cli.py` — `P2` — 2026-08-01
  - **Contexte** : couverture globale 86 %, mais `app.py` a **75 %** et `cli.py` **74 %** — les
    deux modules les moins testes sont le coeur TUI et l'entree CLI. Les lignes non couvertes
    sont les chemins d'erreur et les raccourcis clavier, precisement ce qu'un utilisateur
    rencontre quand quelque chose se passe mal.
  - **Critere de sortie** : les deux modules au-dessus de 85 %, en visant les chemins d'erreur
    plutot que le remplissage.
  - **Fichiers** : `tests/test_app.py`, `tests/test_cli.py`

- [ ] **TODO-004** — Trancher le positionnement face a `glint` — `P2` — 2026-08-01
  - **Contexte** : releve le 2026-08-01, [`glint`](https://github.com/ntrospect0/glint) occupe
    le meme creneau — dashboard TUI, config TOML, grille composable — avec **10 types de widgets
    predefinis** et un **live reload** que nous n'avons pas. Notre difference reelle est la
    genericite : n'importe quelle commande shell devient un panneau, via 6 parsers. C'est un
    angle defendable, mais il n'est enonce nulle part.
  - **Critere de sortie** : le README enonce cette difference des les premieres lignes.
    Decision consignee en ADR : suivre `glint` sur le live reload, ou assumer la genericite
    comme seul axe.
  - **Fichiers** : `README.md`, `docs/decisions.md`

## Livre

- [x] **TODO-000** — Executer les panneaux de `show` en parallele — `P1` — livre 2026-08-01
  - `panelize show` lancait les panneaux l'un apres l'autre, payant la somme de leurs latences.
    Ce mode alimente la CI et le cron, ou les panneaux interrogent typiquement Docker, kubectl
    ou un endpoint HTTP — les cas ou l'attente serie coute le plus.
  - Mesure sur 4 commandes de 0,4 s : **1,60 s → 0,63 s**. Ordre de declaration preserve dans
    le rendu, pool borne a 8 pour qu'une grosse config ne lance pas autant de subprocess que
    de panneaux.
  - Le TUI etait deja concurrent (un worker Textual par panneau) : seul le chemin snapshot
    etait serie. 1 test de regression. Commit `afa1946`, CI verte sur 3.11/3.12/3.13.
