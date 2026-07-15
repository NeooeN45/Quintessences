---
name: handoff-moteur
description: Délègue l'implémentation complète d'un moteur GSIE au Devin Cloud via /handoff
argument-hint: "[nom-du-moteur]"
triggers:
  - user
---

# Handoff moteur vers Devin Cloud

Cette skill prépare et lance un `/handoff` optimisé pour l'implémentation d'un moteur GSIE.

## Préparation

1. **Lire le contrat d'interface** du moteur : `GSIE/ENGINES/[nom]_ENGINE/README.md`
2. **Vérifier les dépendances** : quels moteurs amont doivent être implémentés
3. **Préparer le prompt de handoff** avec :
   - Le nom du moteur
   - Le contrat d'interface complet (coller le README.md)
   - Les conventions de code (référence : skill /architecture-gsie)
   - Les tests requis (référence : skill /tests-gsie)
   - Les dépendances amont/aval
   - Le modèle de réponse standard `{data, confidence, trace_id, engine}`

## Prompt de handoff

Utilise `/handoff` avec un prompt structuré :

```
/handoff Implémenter le moteur [NOM]_ENGINE de GSIE Phase 4.

Contrat d'interface : [coller le README.md du moteur]

Conventions :
- Python 3.11+ avec mypy strict
- Pydantic v2 pour les modèles entrée/sortie
- Exceptions typées héritant de GSIEBaseException
- Tests TDD : écrire les tests AVANT l'implémentation
- Réponse standard : {"data": ..., "confidence": float, "trace_id": "uuid4", "engine": "nom"}
- Logging structuré JSON avec trace_id + engine + latency_ms

Structure à créer :
- engine.py (logique principale)
- models.py (InputModel + OutputModel Pydantic)
- exceptions.py (exceptions typées)
- tests/test_unit.py (tests unitaires)
- tests/test_integration.py (tests d'intégration)

Critères d'acceptation :
1. mypy --strict passe sans erreur
2. ruff check passe sans erreur
3. pytest --cov couverture ≥ 80% sur la logique métier
4. Tous les cas de test documentés dans /tests-gsie sont couverts
5. Le moteur respecte le contrat d'interface du README.md
```

## Après le handoff

1. Noter l'ID de session cloud retourné
2. Ajouter une entrée dans PROJECT_MEMORY.md : "Moteur [nom] — handoff cloud session [ID]"
3. Surveiller la progression sur app.devin.ai
4. À la fin, récupérer le résultat et faire un code review local
