---
name: documentation-gsie
description: Standards de documentation GSIE — markdown, sources, cycle de vie, mise à jour mémoire
triggers:
  - user
  - model
---

# Documentation GSIE — Standards

## Langue

**Tout en français.** Documentation, commentaires, titres, commits, messages d'erreur utilisateur.
Exception : les identifiants de code (variables, fonctions, classes) sont en anglais.

## Structure d'un document

```markdown
# TITRE — [Identifiant] [Version]

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-xxx-000 |
| **Statut** | Draft / Review / Validated / Locked |
| **Version** | 1.0.0 |
| **Date** | YYYY-MM-DD |
| **Auteur** | [nom] |

## 1. Résumé

[2-3 phrases maximum]

## 2. Contexte

## 3. Contenu principal

## 4. Sources et références

## 5. Historique des modifications
```

## Cycle de vie (OBLIGATOIRE)

| Statut | Signification | Modification libre ? |
|---|---|---|
| `Draft` | En cours de rédaction | Oui |
| `Review` | En attente validation fondateur | Oui, avec prudence |
| `Validated` | Validé | Non sans raison tracée |
| `Locked` | Verrouillé | **Jamais — RFC obligatoire** |

**Règle d'ordre** : un document passe en Review seulement si le précédent dans la ROADMAP est au moins en Review.

## Sources scientifiques

Toute affirmation factuelle doit citer une source traçable :
- Référence dans `GSIE/RESEARCH/` pour les études
- Identifiant dataset dans `GSIE/DATASETS/DATASET_CATALOG.md` (DS-001 à DS-029)
- Format : `[ONF, 2023]` avec entrée complète dans une section Sources

## Mise à jour de la mémoire (obligatoire après changement d'état)

Après tout changement structurant :
1. Mettre à jour `PROJECT_MEMORY.md` — état courant
2. Mettre à jour `ROADMAP.md` — si statut livrable change
3. Mettre à jour `CHANGELOG.md` — format `## [date] - description`

## Style markdown

- Titres hiérarchisés (pas de saut de niveau)
- Tables pour les listes de faits
- Blocs de code pour les schémas et exemples
- Ton sobre, scientifique, sans emphase commerciale
- Pas d'emojis sauf si demandé explicitement
