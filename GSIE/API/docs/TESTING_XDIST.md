# Parallélisation pytest (pytest-xdist) — état et contraintes

> P2-1 (tooling). Statut : `pytest-xdist` **installé et activé par
> défaut** avec `-n auto --dist=loadfile` dans `pyproject.toml` →
> `[tool.pytest.ini_options]` → `addopts`.
>
> **Sur le poste de développement Windows, poser
> `PYTEST_XDIST_AUTO_NUM_WORKERS=2`** — voir contrainte 1. Sans cette
> variable, `auto` vaut le nombre de cœurs et la collecte échoue.

## Constat initial

La suite complète (748 tests à l'origine, 1621 tests en août 2026)
prenait environ 13 minutes en exécution séquentielle. À mesure que la
suite grossissait, l'exécution séquentielle a commencé à crasher :
segfault Pydantic (`Windows fatal exception`) après ~1600 tests dans le
même processus, et 14 échecs par pollution d'event loop asyncio fermée
entre fichiers de test. `pytest-xdist==3.6.1` a été ajouté aux
dépendances de développement pour permettre la parallélisation et
isoler chaque fichier dans son propre processus worker.

## Ce qui a été testé

| Configuration | Résultat |
|---|---|
| Séquentiel (sans `-n`) | 14 failed + segfault Pydantic (pollution event loop) |
| `-n auto` (8 workers) | **Échec de collecte** — voir contrainte 1 |
| `-n 2 --dist=loadfile` | Référence courante — voir résultat CI |
| `-n 2 --dist=loadfile` (fichier migration seul) | 2 passed |

## Contrainte 1 — `-n auto` sature la mémoire de la machine

Avec 8 workers, chaque processus worker importe indépendamment la pile
scientifique lourde (`scipy`, `xarray`, `cfgrib`, `eccodes`). Sur cette
machine de développement, le fichier de pagination Windows est
insuffisant pour supporter 8 imports simultanés de `scipy.linalg`
(erreur `DLL load failed... Le fichier de pagination est insuffisant`).
Ce n'est pas un bug de code — c'est une contrainte de ressources locale.

C'est pourquoi le plafond ne vit pas dans `pyproject.toml` : un `-n 2`
en dur dans le dépôt exporterait la limite d'une machine à toutes les
autres, bridant une CI Linux et restant hors d'atteinte d'un poste plus
contraint. `addopts` porte `-n auto`, et la machine déclare son propre
plafond :

```bash
# Poste de développement Windows — deux workers, pas davantage.
export PYTEST_XDIST_AUTO_NUM_WORKERS=2
```

xdist lit cette variable pour résoudre `auto`. Sur une CI dimensionnée,
ne rien poser : `auto` prend le nombre de cœurs.

## Contrainte 2 — fuite d'état partagé entre fichiers de test (résolue)

Historiquement, `--dist=loadfile` faisait échouer
`test_migration_baseline.py` car un autre module de test exécuté avant
dans le même worker enregistrait une classe déclarative additionnelle
(`test_model`) sur le registre global SQLAlchemy. Ce problème a été
résolu : `tests/unit/test_models.py` utilise désormais une
`LocalBase(DeclarativeBase)` isolée (pas le `Base` du projet) pour ne
pas polluer `Base.metadata`.

## Contrainte 3 — fuite d'event loop asyncio sur Windows (résolue)

pytest-asyncio (mode `auto`, scope `function`) ferme l'event loop après
chaque test async mais ne la remet pas à `None`. Les tests synchrones
utilisant `TestClient` (qui appelle `asyncio.get_event_loop()` en
interne via httpx) récupèrent alors une loop fermée et lèvent
`RuntimeError: Event loop is closed`.

Ce problème est résolu par la fixture autouse `_ensure_fresh_event_loop`
dans `tests/conftest.py` : avant chaque test, si la loop courante est
fermée, une nouvelle est créée. Pour les tests async, pytest-asyncio
crée sa propre loop (qui remplace celle-ci). Le coût est négligeable.

## Décision

- `pytest-xdist` est **activé par défaut** avec `-n auto --dist=loadfile`
  dans `addopts` (pyproject.toml), le plafond étant déclaré par la
  machine via `PYTEST_XDIST_AUTO_NUM_WORKERS` (2 sur le poste Windows).
  Chaque fichier de test s'exécute dans son propre processus worker,
  isolant les fuites d'état.
- La parallélisation manuelle reste disponible :
  ```bash
  pytest -n 4 --dist=loadfile          # plus de workers si RAM suffisante
  pytest -n 2 --dist=loadfile -k "not test_migration_baseline"
  ```
- Le marqueur `serial` est déclaré dans `pyproject.toml`
  (`markers = ["serial: ..."]`) et appliqué automatiquement, à la
  collecte, aux tests de `tests/integration/test_outbox_concurrence.py`
  via `tests/conftest.py::pytest_collection_modifyitems` (le fichier de
  test lui-même n'est pas modifié). Ces tests sont aussi regroupés sur
  un seul worker xdist via `pytest.mark.xdist_group`.

## Installation

`pytest-xdist` est une dépendance de l'extra `dev` (PEP 621). Pour
disposer de l'outil dans le venv du projet :

```bash
cd GSIE/API
uv sync --extra dev
```

> Note : `uv sync --dev` ne fonctionne pas ici car le projet utilise
> `[project.optional-dependencies]` (PEP 621) et non
> `[dependency-groups]` (PEP 735) — `--dev` d'uv cible ce second
> mécanisme, absent de ce dépôt.
