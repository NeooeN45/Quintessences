---
name: gsie-governance
description: Workflow de gouvernance GSIE. À utiliser dès qu'on rédige, modifie ou valide un document du projet GSIE (constitution, RFC, directive, décision, article, architecture, spécification, moteur, mémoire) ou qu'on touche à un statut, un identifiant tracé ou la hiérarchie documentaire. Garantit primauté constitutionnelle, respect des statuts Locked, traçabilité et langue française.
---

# Gouvernance GSIE

GSIE est une **fondation scientifique** en **Phase 1 (Foundation)** : le produit
est la **documentation**, pas le code. Cette skill impose la gouvernance du
projet à toute production documentaire. Réf. : `CLAUDE.md`, `00_CONSTITUTION/`.

## Règle d'entrée (toujours, avant d'écrire)

1. Lis le `README.md` du dossier cible + les documents parents dans la hiérarchie.
2. Ouvre l'en-tête du fichier cible → note son **identifiant réel** et son **statut**.
3. Applique la checklist ci-dessous.

## Hiérarchie (ne jamais contredire un niveau supérieur)

```
Vision → Constitution → RFC → Directive → Décision
→ Architecture → Spécification → Implémentation → Code
```

## Checklist non négociable

- [ ] **Primauté** : rien ne contredit `00_CONSTITUTION/` (`GSIE-CON-000`).
- [ ] **Locked** : ne JAMAIS modifier un `Locked` directement → passer par un RFC
      (`/rfc`). Le hook `guard-locked` bloque techniquement toute tentative.
- [ ] **Pas de code métier** en Phase 1 (aucun moteur exécutable, API, SDK, app).
- [ ] **Français** partout (doc, titres, commits).
- [ ] **Traçabilité** : toute décision structurante reçoit un `DEC-`/`RFC-` ;
      toute affirmation scientifique cite une source (`06_RESEARCH/`, `08_DATASETS/`).
- [ ] **Statut** : un nouveau document reste `Draft` ; ne jamais s'auto-attribuer
      `Validated`/`Locked`.
- [ ] **L'IA assiste, ne décide jamais** — recommandations explicables et contournables.

## Cycle de vie

`Draft` → `Review` → `Validated` → `Locked` (RFC seulement pour rouvrir un `Locked`).
Invariant ROADMAP : un livrable passe en `Review` seulement si le précédent est
au minimum en `Review`.

## Identifiants tracés

`GSIE-FND-xxx` · `GSIE-CON-xxx` · `GSIE-DIR-xxxx` · `RFC-xxxx` · `DEC-xxxxxx` ·
`GSIE-PROMPT-xxxx`. ⚠ Nommage : un `ARTICLE_0XX.md` porte l'identifiant
`GSIE-CON-0XX` — vérifier l'en-tête, signaler toute incohérence.

## Après écriture (sortie mémoire)

Si l'état du projet change, synchronise `PROJECT_MEMORY.md`, `ROADMAP.md`,
`CHANGELOG.md` (voir `/sync-memory` ou l'agent `memory-keeper`). Aucune décision
perdue.

## Outils dédiés du dépôt

- Commandes : `/rfc`, `/decision`, `/article`, `/engine-doc`, `/sync-memory`,
  `/constitution-audit`.
- Sous-agents : `constitution-guardian` (audit), `doc-redactor` (rédaction),
  `memory-keeper` (mémoire).

## En cas de doute

Entre « avancer vite » et « respecter la gouvernance », choisis **toujours** la
gouvernance. Signale le conflit plutôt que de le contourner.
