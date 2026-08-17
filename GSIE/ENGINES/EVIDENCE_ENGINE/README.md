# Evidence Engine

Moteur d'**évaluation de la preuve scientifique**.

## Périmètre

- Évaluer la qualité scientifique de chaque connaissance intégrée à GSIE
- Attribuer un niveau de preuve
- Tracer l'historique, les sources et le consensus scientifique
- Détecter les conflits bibliographiques

## Principe fondamental

**Aucune connaissance n'est utilisée sans niveau de preuve.**

## Frontières

- N'évalue pas la pertinence opérationnelle (rôle des moteurs de
  raisonnement)
- Filtre et qualifie les connaissances avant leur entrée dans
  `KNOWLEDGE_ENGINE`

## Position dans la chaîne

```
Sources → Import → Validation → Evidence Engine → Knowledge Engine
```

> État d’implémentation : une API v1 et deux backends (Rust/PyO3 et
> repli Python) sont présents. Le backend Rust reste optionnel en
> développement local ; le contrat effectif est décrit ci-dessous.

## Build local du module Rust (PyO3)

Le cœur du moteur est écrit en Rust et exposé à Python via PyO3
(maturin). En dev local, le module n'est pas installé par défaut —
l'API utilise un fallback Python et émet le warning
`evidence_engine_rust_not_available_fallback_python`.

Pour construire et installer la wheel Rust localement :

```powershell
# Prérequis : Rust toolchain (rustup), Python 3.12 dans GSIE/API/.venv
cd E:\Projets\Quintessences\GSIE\API
uv pip install maturin==1.9.6

cd E:\Projets\Quintessences\GSIE\ENGINES\EVIDENCE_ENGINE\rust
..\..\..\..\GSIE\API\.venv\Scripts\maturin.exe build --release
# → target/wheels/gsie_evidence-0.1.0-cp312-cp312-win_amd64.whl

uv pip install --force-reinstall `
  "target\wheels\gsie_evidence-0.1.0-cp312-cp312-win_amd64.whl"
```

Vérification :

```powershell
.\.venv\Scripts\python.exe -c "from gsie_api.engines.evidence.wrapper import is_rust_available; print(is_rust_available())"
# → True, log: evidence_engine_rust_loaded version=0.1.0
```

En production (Docker), le build est automatique (stage builder du
`Dockerfile` de l'API).

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/evidence/router.py`

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/evidence/status` | aucune | — | Statut du moteur (actif / dégradé selon disponibilité du module Rust) |
| POST | `/evidence/evaluate` | rôle `engine:write` (`EngineWriteUser`) | `30/minute` | Évalue une soumission de connaissance brute et attribue un niveau de preuve A-F |
| GET | `/evidence/version` | aucune | — | Version du moteur et backend utilisé (rust+pyo3 ou python-fallback) |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/evidence/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `RawKnowledgeSubmission` | Entrée de `/evidence/evaluate` | `soumission_id`, `type_contenu` (publication/referentiel/expert/observation), `contenu` (structure libre), `source_candidate` (`SourceReference`), `soumetteur` |
| `SourceReference` | Sous-objet source | `type_source` (peer_reviewed/referentiel_officiel/expert_identifie/observation_terrain), `auteur`, `reference` (DOI/URL/citation), `version_source` |
| `QualifiedKnowledge` | Sortie de `/evidence/evaluate` | `connaissance_id`, `evidence_level` (A-F), `statut` (accepte/quarantine/refuse), `conflits` (liste de `ConflitBibliographique`), `version` |
| `EvidenceStatementCreate` / `EvidenceStatementRecord` | Assertion atomique sourcée (RFC-0016 §3.1) | `claim`, `page_or_table` (localisation obligatoire), `evidence_level`, `source` |

### 3. Exceptions

Aucune exception métier dédiée n'est levée par ce moteur : les erreurs
d'entrée sont couvertes par la validation Pydantic native (HTTP 422),
et les erreurs du cœur Rust sont interceptées (`except Exception`)
avec repli automatique sur l'implémentation Python
(`wrapper.py:_evaluate_rust`, log `rust_engine_evaluation_failed` puis
`falling_back_to_python_evaluation`) plutôt que propagées à l'appelant.

### 4. Dépendances

- **Aval (chaîne principale)** : `KNOWLEDGE_ENGINE` — toute connaissance
  au statut `accepte` est ingérée par le Knowledge Engine
  (`gsie_api.engines.pipeline`, DEC-000021).
- **Amont** : aucun moteur GSIE — reçoit directement les soumissions
  brutes (import, ingestion documentaire).
- **Clients API externes** : aucun.
- **Dépendance technique** : module Rust `gsie_evidence` (crate compilée
  via PyO3/maturin) ; fallback Python intégré si absent.
