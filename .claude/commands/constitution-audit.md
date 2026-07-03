---
description: Auditer la cohérence constitutionnelle et la traçabilité du dépôt
argument-hint: [dossier ou fichier à cibler, sinon tout le dépôt]
allowed-tools: Read, Glob, Grep, Task
---

Audit de conformité GSIE. Cible : ${ARGUMENTS:-tout le dépôt}

Délègue au sous-agent **constitution-guardian** si la portée est large.
Vérifie :
1. **Primauté** — aucun document ne contredit `00_CONSTITUTION/` (`GSIE-CON-000`).
2. **Hiérarchie** — aucune Architecture/Spec ne contredit une Décision/Directive.
3. **Statuts** — aucun `Locked` modifié hors RFC ; cohérence des statuts entre
   `PROJECT_MEMORY.md`, `ROADMAP.md` et les en-têtes de fichiers.
4. **Traçabilité** — chaque décision structurante possède un `DEC-`/`RFC-` ;
   pas de décision orpheline ; nommage fichier↔identifiant cohérent.
5. **Phase 1** — aucun code métier introduit.

Rends un rapport **en français** : conformités, écarts (classés par gravité),
et actions correctrices proposées. Ne corrige rien sans validation.
