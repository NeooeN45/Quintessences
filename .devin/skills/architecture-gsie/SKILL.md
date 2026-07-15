---
name: architecture-gsie
description: Architecture patterns pour GSIE Phase 4 — 14 moteurs, API, Hub Unreal, apps clientes
triggers:
  - user
  - model
---

# Architecture GSIE — Patterns Phase 4

## Hiérarchie obligatoire

```
Vision → Constitution → RFC → Directive → Décision
→ Architecture → Spécification → Implémentation → Code
```

## Les 14 moteurs — responsabilités uniques

Chaîne principale : Evidence → Knowledge → Correlation → Reasoning → Diagnostic → Recommendation → Validation → Utilisateur

Moteurs domaine : GIS, Climate, Pedology, Botanical, ForestDynamics
Moteurs transverses : Learning, Simulation

Chaque moteur = une responsabilité unique. Interface : entrées typées → traitement → sorties typées + métadonnées de confiance.

## Principes d'architecture (ARCHITECTURE_PRINCIPLES.md)

- Modularité obligatoire (CON-007) : chaque moteur est indépendant, remplaçable
- Interfaces > implémentations : les moteurs communiquent via contrats
- Dependency injection : aucun moteur n'instancie directement un autre
- Fail fast : validation à l'entrée de chaque moteur
- Traçabilité complète : chaque décision porte son identifiant DEC-xxxxxx

## Structure d'un nouveau moteur (Phase 4)

```
GSIE/ENGINES/<NOM>_ENGINE/
├── README.md           ← responsabilité + contrat d'interface (existant, Draft)
├── engine.py           ← implémentation principale
├── models.py           ← modèles Pydantic entrées/sorties
├── exceptions.py       ← exceptions typées du moteur
└── tests/
    ├── test_unit.py
    └── test_integration.py
```

## API GSIE — conventions

- FastAPI + Pydantic v2
- Endpoints : `/v1/engines/{engine_name}/process`
- Auth : JWT Bearer (voir TECHNICAL_CONSTITUTION.md)
- Réponses : `{"data": ..., "confidence": float, "trace_id": "DEC-xxxxxx", "engine": "..."}`

## Avant de créer un composant Phase 4

1. Lire `GSIE/ENGINES/<NOM>_ENGINE/README.md` — le contrat d'interface est déjà défini
2. Vérifier qu'aucune décision (03_DECISIONS/) ne contraint l'implémentation
3. Respecter les entrées/sorties du contrat — ne pas les modifier sans RFC
4. Écrire les tests avant l'implémentation
