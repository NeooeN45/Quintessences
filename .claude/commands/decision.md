---
description: Tracer une décision validée dans 03_DECISIONS/ (aucune décision perdue)
argument-hint: <résumé de la décision>
allowed-tools: Read, Glob, Grep, Write, Edit
---

Trace la décision : **$ARGUMENTS**

1. Détermine le prochain identifiant `DEC-XXXXXX` en inspectant `03_DECISIONS/`.
2. Rédige l'entrée **en français** : Contexte, Décision, Justification,
   Documents/RFC liés, Conséquences, Date, Statut.
3. Rattache la décision à sa source (RFC, Directive, Constitution) — une
   décision ne doit jamais contredire un niveau supérieur (`CLAUDE.md` §3).
4. Mets à jour `PROJECT_MEMORY.md` (section « Décisions actives ») et
   `CHANGELOG.md`. Confirme la cohérence avant d'écrire.
