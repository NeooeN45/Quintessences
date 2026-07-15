---
name: rfc-gsie
description: Créer ou modifier une RFC GSIE — template + traçabilité + gouvernance
argument-hint: "[sujet-de-la-rfc]"
triggers:
  - user
  - model
---

# RFC GSIE — Workflow

## Quand créer une RFC ?

Une RFC est obligatoire pour :
- Modifier un document Locked (CON-000, FND-001, FND-002)
- Changer un contrat d'interface de moteur publié
- Introduire une nouvelle dépendance technologique majeure
- Modifier la hiérarchie documentaire

## Structure d'une RFC

Fichier : `02_RFC/RFC-xxxx-[titre-court].md`

```markdown
# RFC-xxxx — [Titre]

| Champ | Valeur |
|---|---|
| **Identifiant** | RFC-xxxx |
| **Statut** | Draft |
| **Auteur** | [nom] |
| **Date** | YYYY-MM-DD |
| **Motivation** | [pourquoi ce changement est nécessaire] |

## Problème

[Description du problème que cette RFC résout]

## Solution proposée

[Description de la solution]

## Impact

- Documents modifiés : [liste]
- Contrats d'interface affectés : [liste]
- Risques : [liste]

## Alternatives considérées

[Alternatives rejetées et pourquoi]
```

## Processus

1. Créer la RFC en statut `Draft`
2. Créer une DEC liée (DEC-xxxxxx) référençant la RFC
3. Mettre à jour PROJECT_MEMORY.md
4. Attendre la validation du fondateur avant d'appliquer le changement

## Important
Ne jamais modifier directement un Locked sans RFC validée. Le hook guard-locked bloque techniquement toute tentative.
