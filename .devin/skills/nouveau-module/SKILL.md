---
name: nouveau-module
description: Checklist complète pour créer un nouveau module GSIE en Phase 4
argument-hint: "[nom-du-module]"
triggers:
  - user
  - model
---

# Créer un nouveau module GSIE

## Checklist obligatoire

### 1. Vérification préalable (avant d'écrire une ligne)
- [ ] Lire le README.md du dossier cible
- [ ] Vérifier que le module est prévu dans la Phase 4 (ROADMAP.md)
- [ ] Identifier le moteur GSIE concerné (GSIE/ENGINES/)
- [ ] Lire le contrat d'interface du moteur (README.md du moteur)
- [ ] Vérifier qu'aucun document Locked ne contraint l'implémentation

### 2. Structure à créer

Pour un moteur GSIE :
```
GSIE/ENGINES/<NOM>_ENGINE/
├── engine.py          ← classe principale héritant de BaseEngine
├── models.py          ← InputModel + OutputModel (Pydantic v2)
├── exceptions.py      ← MoteurXError(GSIEBaseException)
├── __init__.py
└── tests/
    ├── conftest.py
    ├── test_unit.py   ← tests unitaires (mock des dépendances)
    └── test_integration.py
```

Pour une application cliente :
```
apps/<App>/src/
├── domain/            ← modèles métier purs
├── data/              ← implémentations des repositories
├── presentation/      ← UI / API layer
└── tests/
```

### 3. Tests en premier (TDD obligatoire)
Écrire `test_unit.py` avec au moins :
- Test nominal (input valide → output attendu)
- Test input vide/None
- Test input invalide (validation error)
- Test cas limite

### 4. Traçabilité
- Si décision structurante → créer DEC-xxxxxx dans 03_DECISIONS/
- Mettre à jour PROJECT_MEMORY.md après chaque livrable

### 5. Commit
Format : `feat(engine-name): description courte en français`
