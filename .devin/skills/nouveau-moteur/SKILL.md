---
name: nouveau-moteur
description: Orchestrateur — crée un moteur GSIE complet (structure + tests + docs + DEC) en une commande
argument-hint: "[nom-du-moteur]"
triggers:
  - user
  - model
---

# Créer un moteur GSIE complet

Tu es l'orchestrateur de création de moteurs. Quand l'utilisateur invoque `/nouveau-moteur [nom]`, tu exécutes les étapes suivantes **dans l'ordre**, en utilisant les skills existantes comme sous-agents.

## Étape 1 — Validation préalable

1. Vérifier que le moteur est prévu dans ROADMAP.md (Phase 4)
2. Lire `GSIE/ENGINES/[nom]_ENGINE/README.md` si le contrat d'interface existe déjà
3. Vérifier qu'aucun document Locked ne contraint l'implémentation
4. Si le moteur n'est pas prévu ou un Locked bloque → **arrêter et signaler**

## Étape 2 — Créer la structure (skill /nouveau-module)

Invoque la skill `/nouveau-module [nom]_ENGINE` pour créer :
```
GSIE/ENGINES/[NOM]_ENGINE/
├── engine.py
├── models.py
├── exceptions.py
├── __init__.py
└── tests/
    ├── conftest.py
    ├── test_unit.py
    └── test_integration.py
```

## Étape 3 — Générer les tests squelettes (skill /tests-gsie)

Invoque `/tests-gsie` pour générer les tests avec :
- Test nominal (input valide → output attendu)
- Test input vide/None → ValidationError
- Test input invalide → erreur explicite
- Test moteur amont indisponible → fallback
- Test confidence dans [0.0, 1.0]
- Test trace_id présent

## Étape 4 — Créer la documentation (skill /documentation-gsie)

Invoque `/documentation-gsie` pour mettre à jour :
- Le README.md du moteur (si non existant)
- Une entrée dans PROJECT_MEMORY.md
- Une entrée dans CHANGELOG.md

## Étape 5 — Tracer la décision

Crée un `DEC-xxxxxx` dans `03_DECISIONS/` référençant :
- Le moteur créé
- Le contrat d'interface
- Les dépendances amont/aval

## Étape 6 — Vérification finale

1. `mypy GSIE/ENGINES/[NOM]_ENGINE/ --strict` — aucune erreur
2. `ruff check GSIE/ENGINES/[NOM]_ENGINE/` — aucune erreur
3. `pytest GSIE/ENGINES/[NOM]_ENGINE/tests/ -v` — tests passent (squelettes)

## Résumé final

Retourne à l'utilisateur :
- Liste des fichiers créés
- Identifiant DEC attribué
- Commandes de vérification passées
- Prochaines étapes recommandées (implémenter la logique métier)
