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

> Statut : *implémentation en cours (Phase 4)* — code livré, voir EVIDENCE_ENGINE.md et PROJECT_MEMORY.md

## Build local du module Rust (PyO3)

Le cœur du moteur est écrit en Rust et exposé à Python via PyO3
(maturin). En dev local, le module n'est pas installé par défaut —
l'API utilise un fallback Python et émet le warning
`evidence_engine_rust_not_available_fallback_python`.

Pour construire et installer la wheel Rust localement :

```powershell
# Prérequis : Rust toolchain (rustup), Python 3.12 dans GSIE/API/.venv
cd A:\Quintessences\GSIE\GSIE\API
uv pip install maturin==1.9.6

cd A:\Quintessences\GSIE\GSIE\ENGINES\EVIDENCE_ENGINE\rust
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
