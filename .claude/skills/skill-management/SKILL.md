---
name: skill-management
description: Gérer les skills Claude Code du projet GSIE — lister, évaluer, installer (vendorisation épinglée), tracer, mettre à jour et retirer des skills, y compris les skills communautaires externes. À utiliser dès qu'on veut ajouter, auditer, mettre à jour ou supprimer une skill, ou vérifier la conformité de l'outillage Claude Code.
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# Gestion des skills GSIE

Cette skill administre l'outillage Claude Code du dépôt en respectant la
gouvernance GSIE (traçabilité, licences, revue avant adoption). Réf. :
`CLAUDE.md`, `.claude/SKILLS_GSIE.md`, `GSIE-CON-005` (traçabilité).

## Inventaire

- **Skills projet** : `.claude/skills/<nom>/SKILL.md`
- **Commandes** : `.claude/commands/*.md`
- **Sous-agents** : `.claude/agents/*.md`
- **Sélection & recommandations** : `.claude/SKILLS_GSIE.md`

Pour lister l'existant : `ls .claude/skills .claude/commands .claude/agents`.

## Installer une skill communautaire (procédure obligatoire)

1. **Réviser avant de faire confiance.** Cloner dans un dossier temporaire, lire
   le `SKILL.md` et les scripts. Refuser tout comportement contraire à la
   Constitution (ex. écriture de code métier en Phase 1, contournement des `Locked`).
2. **Vérifier la licence.** Exiger une licence claire (MIT/Apache/BSD). Sans
   licence explicite → **ne pas installer**, documenter comme « licence à clarifier ».
3. **Vendoriser + épingler.** Copier le dossier de la skill dans
   `.claude/skills/<nom>/`. Créer un `PROVENANCE.md` : source, commit SHA,
   licence, date, réviseur. Ne jamais modifier localement le contenu vendorisé.
4. **Tracer.** Ajouter/mettre à jour la ligne correspondante dans
   `.claude/SKILLS_GSIE.md` et une entrée dans `CHANGELOG.md`.
5. **Vérifier.** Confirmer que le `SKILL.md` a un frontmatter valide
   (`name`, `description`) et que la skill apparaît bien à l'usage.

## Modèle de PROVENANCE.md

```
# Provenance — skill `<nom>`
| Source | <url> |
| Commit épinglé | <sha> |
| Licence | <type> |
| Date d'intégration | <AAAA-MM-JJ> |
| Révisé par | <qui> |
```

## Mettre à jour une skill vendorisée

Re-cloner la source, comparer (`diff`), remplacer le contenu, mettre à jour le
commit dans `PROVENANCE.md` et journaliser dans `CHANGELOG.md`.

## Retirer une skill

Supprimer `.claude/skills/<nom>/`, retirer sa ligne de `SKILLS_GSIE.md`, et
journaliser le retrait avec la raison dans `CHANGELOG.md`.

## Créer une skill GSIE sur-mesure

Créer `.claude/skills/<nom>/SKILL.md` avec frontmatter `name` + `description`
(déclencheurs clairs, en français). Garder la skill focalisée sur une
responsabilité unique. S'inspirer de `gsie-governance`.

## Garde-fous permanents

- Aucune skill ne doit produire de **code métier** en Phase 1.
- Le hook `guard-locked` et la skill `gsie-governance` restent actifs et
  prioritaires quelles que soient les skills installées.
- Toute skill externe non révisée est considérée comme non fiable.
