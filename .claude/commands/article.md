---
description: Rédiger ou compléter un article constitutionnel (00_CONSTITUTION/)
argument-hint: <numéro et/ou titre de l'article>
allowed-tools: Read, Glob, Grep, Write, Edit
---

Rédige/complète l'article constitutionnel : **$ARGUMENTS**

⚠️ Garde-fous :
- Un article `Locked` (ex. `GSIE-CON-000`, `GSIE-FND-001/002`) ne se modifie
  QUE via un RFC. Le hook `guard-locked` bloquera toute tentative directe.
- Un article ne peut jamais contredire la Constitution existante.

1. Ouvre l'article cible (`ARTICLE_0XX.md`) ; vérifie son **en-tête** pour
   l'identifiant réel (`GSIE-CON-0XX`) et le **statut**.
2. Rédige **en français**, dans le style constitutionnel sobre du projet :
   Énoncé, Portée, Justification, Implications, Références croisées.
3. Conserve le statut `Draft` (ou `Review` si explicitement demandé). Ne passe
   jamais un article en `Validated`/`Locked` toi-même.
4. Signale toute incohérence de nommage fichier↔identifiant que tu rencontres.
