---
description: Documenter un moteur GSIE dans 09_ENGINES/ (sans l'implémenter)
argument-hint: <nom du moteur, ex. REASONING>
allowed-tools: Read, Glob, Grep, Write, Edit
---

Documente le moteur : **$ARGUMENTS**

⚠️ Phase 1 = documentation uniquement. **N'écris aucun code exécutable.**

1. Ouvre `09_ENGINES/<NOM>_ENGINE/` et son `README.md`.
2. Vérifie la place du moteur dans la chaîne (`04_ARCHITECTURE/GSIE_DATA_FLOW.md`).
3. Documente **en français** : Responsabilité unique, Entrées, Sorties,
   Dépendances (moteurs amont/aval), Contrats d'interface (conceptuels),
   Contraintes d'explicabilité et de traçabilité, Points ouverts.
4. Assure la cohérence avec `GSIE_MASTER_ARCHITECTURE.md` et
   `GSIE_CORE_BLUEPRINT.md`. Signale toute contradiction plutôt que la masquer.
