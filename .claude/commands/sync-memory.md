---
description: Synchroniser la mémoire du projet (PROJECT_MEMORY, ROADMAP, CHANGELOG)
allowed-tools: Read, Glob, Grep, Edit, Bash(git log:*), Bash(git diff:*)
---

Synchronise l'état du projet. Contexte optionnel : $ARGUMENTS

1. Inspecte les changements récents (`git log --oneline -15`, statuts des
   livrables, nouveaux RFC/décisions/articles).
2. Mets à jour, en cohérence stricte entre eux :
   - `PROJECT_MEMORY.md` — état courant, avancement des 12 livrables, décisions.
   - `ROADMAP.md` — statuts des livrables (`Draft`→`Review`→`Validated`→`Locked`).
   - `CHANGELOG.md` — nouvelle entrée datée des évolutions.
3. Vérifie l'invariant ROADMAP : un livrable ne passe en `Review` que si le
   précédent est au minimum en `Review`.
4. Résume les écarts détectés (compteurs Validated/Locked/Draft/Review) et
   confirme que les trois fichiers racontent la même histoire.
