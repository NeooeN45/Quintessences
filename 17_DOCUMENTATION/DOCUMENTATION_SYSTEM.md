# Système de documentation — GSIE

Livrable : 011 — Système de documentation
Statut : Validated
Version : 1.0
Date : 2026-07-12

## Objet

Décrire comment la documentation GSIE est organisée, versionnée et maintenue.
En Phase 1, **la documentation est le produit** : ce système en est la colonne
vertébrale.

## Principe « docs-as-code »

Toute la documentation vit dans le dépôt, en Markdown UTF-8, versionnée avec
Git. Elle se lit sans outil propriétaire et se dérive en `.docx`/`.pdf`.

## Organisation

La documentation suit l'arborescence numérotée `00_` à `23_`. Chaque dossier
possède un `README.md` qui définit son objet, ce qui est autorisé et ce qui est
interdit. Le `README.md` fait autorité sur le contenu de son dossier.

## Hiérarchie documentaire

```
Vision → Constitution → RFC → Directive → Décision
→ Architecture → Spécification → Implémentation → Code
```

Aucun niveau ne contredit un niveau supérieur.

## Types de documents

| Type | Dossier | Identifiant |
|---|---|---|
| Fondateurs | `00_CONSTITUTION/` | `GSIE-FND-xxx` |
| Articles constitutionnels | `00_CONSTITUTION/` | `GSIE-CON-xxx` |
| Directives | `01_DIRECTIVES/` | `GSIE-DIR-xxxx` |
| Propositions | `02_RFC/` | `RFC-xxxx` |
| Décisions | `03_DECISIONS/` | `DEC-xxxxxx` |
| ADR | `17_DOCUMENTATION/` | via `ADR_TEMPLATE.md` |

## Cycle de vie et statuts

`Draft` → `Review` → `Validated` → `Locked`. Un `Locked` ne se rouvre que par
RFC. Un livrable ne passe en `Review` que si le précédent l'est au minimum.

## Maintenance

Après tout changement d'état du projet : mise à jour de `PROJECT_MEMORY.md`,
`ROADMAP.md` et `CHANGELOG.md`. Le `CHANGELOG.md` journalise chaque évolution.

## Voir aussi

- `WRITING_GUIDELINES.md` — règles de rédaction.
- `CONTRIBUTING_GUIDE.md` — comment contribuer.
- `ADR_TEMPLATE.md` — gabarit de décision d'architecture.
