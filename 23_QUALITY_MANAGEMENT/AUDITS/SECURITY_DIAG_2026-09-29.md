# SECURITY_DIAG_2026-09-29 — Premier cycle du diagnostic sécurité continu

| Champ | Valeur |
|---|---|
| Date | 2026-09-29 |
| Périmètre | Dépôt parent Quintessences + repos externes `apps/GeoSylva`, `apps/QGISIA`, `Forge` |
| Outil | `tools/security_diag.py` (DEC-000091) : secrets (diff stagé, arborescence), checks config ciblés, Bandit, pip-audit, cargo-audit, npm-audit |
| Exécution | Devin CLI — scans `quick` et `full` sur les quatre dépôts |

---

## 0. Synthèse

Premier cycle complet du dispositif instauré par `DEC-000091`. La posture
initiale était déjà saine côté secrets (aucune clé réelle dans l'historique —
les deux alertes antérieures étaient des corpus de test marqués `TEST-ONLY` ou
des assertions sur clés générées à la volée). Les findings réels étaient des
durcissements de code et des dépendances vulnérables.

| Dépôt | Avant (quick) | Après corrections | Reste |
|---|---|---|---|
| Parent | P0:11 P1:8 P2:21 (dont ~30 faux positifs) | P0:0 P1:0 P2:7 | 7 P2 acceptés, 0 CVE pip-audit |
| GeoSylva | P0:0 P1:2 P2:13 | P0:0 P1:0 P2:0 | — |
| QGISIA | P0:0 P1:3 P2:48 | P0:0 P1:0 P2:0 | 5 highs npm (transitives, non bloqués au fix) |
| Forge | P0:0 P1:1 P2:5 | P0:0 P1:0 P2:0 (full : 2 CVE restantes) | `diskcache`, `idna` |

## 1. Findings réels corrigés

### Code

| Réf | Fichier | Correction |
|---|---|---|
| `shell=True` (P1) | `apps/QGISIA/QGISIA2/geoai_assistant.py:5437` | Invocation structurée `[npm_cmd, "run", "dev"]` via `shutil.which` — plus d'interpréteur de commande |
| `http://` arXiv (P2) | `Forge/src/dataset_forge/discovery/search.py:34`, `documents/connectors/arxiv_connector.py:17` | `https://export.arxiv.org/api/query` |
| XXE B314 (P2) | `Forge/src/dataset_forge/discovery/search.py`, `arxiv_connector.py` | `xml.etree.ElementTree` → `defusedxml.ElementTree` (déjà en dépendance), types mypy strict préservés |
| Bind B104 (P2) | `Forge/src/dataset_forge/ui/app.py` | `FORGE_UI_HOST`/`FORGE_UI_PORT` env-configurables, `0.0.0.0` justifié `nosec` (Docker Compose) |
| SHA1 B324 (P1) | `tools/test_check_governance_consistency.py:147` | `usedforsecurity=False` — hash d'objet blob Git, pas de donnée sensible (commit `602f226`) |
| httpx B113 (P2) | `GSIE/API/src/gsie_api/data/soilgrids_wcs_client.py:135` | `nosec B113` justifié — timeout client explicite |

### Dépendances (Forge — pip-audit : 33 CVE → 2)

| Paquet | Avant | Après | CVE |
|---|---|---|---|
| gitpython | 3.1.51 | 3.1.62 | 21 → 0 |
| aiohttp | 3.14.1 | 3.14.3 | 3 → 0 |
| anyio | 4.14.1 | 4.15.1 | 3 → 0 |
| cryptography | 49.0.0 | 50.0.1 | 1 → 0 |
| datasets | 5.0.0 | 5.0.1 | 1 → 0 |
| soupsieve | 2.8.4 | 2.10 | 2 → 0 |

## 2. Risques acceptés et documentés

| Finding | Justification |
|---|---|
| `ws_allowed_origins=["*"]` (config.py:301) | Garde-fou double : le validateur de `Settings` **refuse `*` en prod** (`test_config.py::should_reject_wildcard_ws_origins_in_production`) et `_is_origin_allowed` n'honore `*` qu'en `environment == "development"`. Défaut dev assumé. |
| 6× `image: :latest` | `gsie-api`/`api-api` : images auto-buildées, surchargeables par `GSIE_HA_API_IMAGE`. Metabase/Superset/Dekart/SchemaSpy : stack viz **dev locale non exposée** — épinglage recommandé en durcissement ultérieur. |
| `diskcache 5.6.3` (Forge, PYSEC-2026-2447) | Aucun correctif publié à ce jour. |
| `idna 3.7` (Forge, PYSEC-2026-215) | ReDoS d'encodage, impact faible ; retenu par le resolver uv. |
| 5 highs npm QGISIA (`@xmldom/xmldom`, `browserslist`, `nanoid`, `postcss`, `pdfjs-dist`) | Dépendances transitives d'un dashboard React de plugin QGIS local (pas d'application web publique). `npm audit fix` recommandé ; `pdfjs-dist` exige un bump majeur 5→6 à valider manuellement. |
| `cargo-audit` absent | Binaire non installé sur le poste — le check est reporté sans bloquer. |

## 3. Faux positifs traités (calibration du scanner)

- Variables psql `:'password'` et env vars `$VAR`/`${VAR}` — injectées à
  l'exécution, jamais littérales (`init-roles.sql`, `04-comptes-de-connexion.sh`).
- Chaînes de connexion d'exemple (`user:pass`, `gsie_dev`, `secret`,
  `••••` masqués) dans les docs et `alembic.ini`.
- Noms de clés de préférences chiffrées (`KEY_ACCESS_TOKEN = "access_token"`)
  et placeholders `nvapi-...`.
- Namespaces XML/OGC/W3C : `opengis.net`, `w3.org`, `georss.org`,
  `topografix.com`, `sitemaps.org`, DTD QGIS… — jamais des communications
  réseau.
- `client.eval()` Redis (scripts Lua atomiques), `loop.exec()` Qt,
  `hashlib.sha1` HIBP k-anonymity (`usedforsecurity=False`).
- `exec()` dans `script_sandbox.py` (sandbox isolée `-I -S -B`, builtins
  réduits, kill OS au timeout — fonction du produit documentée), docstrings,
  chaînes d'audit de `build_release.py`, commentaires.
- Rapports d'audit (`url_report.json`, audits passés) — données, pas code.

## 4. Robustesse de l'outil

Corrections apportées pendant le cycle :

- Parsing `pip-audit` : recherche du `{` initial + `raw_decode` (rc=1 est
  normal en présence de vulns ; préfixe `Found N known vulnerabilities`
  toléré).
- Déduplication enrichie du message (les CVE d'un même projet n'étaient pas
  distinctes).
- Encodage UTF-8 forcé sur `stdout`/`stderr` (console Windows cp1252).
- Motif `eval|exec` : lookbehind `(?<![\w.])` (exclut `.exec()`/`.eval()`),
  exclusion des lignes commentaires `#`/`//`.
- `scan_secrets` : extraction de la valeur capturée + reconnaissance des
  placeholders à deux niveaux (correspondance entière / valeur seule).

### Limite connue

`subprocess.run(timeout)` ne tue que l'enfant direct sous Windows : un
`pip-audit` orphelin peut survivre à un timeout `uvx`. Un premier run à froid
(cache uvx/npm vides) peut durer >10 min ; les runs suivants sont rapides.

## 5. Dispositif installé

- Hooks actifs sur les 4 dépôts : `pre-commit` (secrets du diff stagé,
  bloquant — vérifié par sonde positive et négative), `post-commit`
  (diagnostic rapide en fond), `pre-push` (diagnostic complet bloquant).
- Installateur : `tools/install_hooks.sh` (idempotent).
- Rapports horodatés sous `output/security-diag/` dans chaque dépôt
  (gitignoré).

## 6. Prochaines actions recommandées

1. `npm audit fix` dans `apps/QGISIA` + bump manuel `pdfjs-dist` 6.x à valider.
2. Installer `cargo-audit` pour couvrir `GSIE/ENGINES/EVIDENCE_ENGINE/rust`.
3. Épingler les images de la stack viz (`docker-compose.viz.yml`).
4. Surveiller un correctif `diskcache` upstream.
