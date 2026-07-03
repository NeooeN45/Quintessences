---
description: Créer un nouveau RFC (Request for Comments) tracé dans 02_RFC/
argument-hint: <titre du RFC>
allowed-tools: Read, Glob, Grep, Write, Edit
---

Crée un nouveau RFC pour : **$ARGUMENTS**

Procédure (respecte la gouvernance GSIE — voir `CLAUDE.md`) :
1. Liste `02_RFC/` pour déterminer le prochain numéro `RFC-XXXX` (format 4 chiffres).
2. Lis un RFC existant comme gabarit ; réutilise sa structure exacte.
3. Rédige le RFC **en français**, avec au minimum : Contexte, Problème,
   Proposition, Alternatives considérées, Impact sur la Constitution/Architecture,
   Décisions (`RFC-XXXX-Dn`), Statut = `Draft`.
4. Si le RFC touche un document `Locked`, précise-le explicitement : c'est la
   seule voie légitime pour modifier un `Locked`.
5. Ne valide rien toi-même : le statut reste `Draft` en attente du fondateur.
6. Propose la mise à jour de `PROJECT_MEMORY.md` (section décisions) — ne
   l'applique qu'après confirmation.
