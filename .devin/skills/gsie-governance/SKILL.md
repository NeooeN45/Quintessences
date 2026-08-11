---
name: gsie-governance
description: Gouvernance GSIE — statuts de documents, cycle de vie, traçabilité des décisions, RFC, hiérarchie constitutionnelle. Utiliser pour toute question sur le statut d'un livrable, la création d'une décision (DEC-xxxxxx), l'amendement d'une directive, ou la conformité d'un changement à la Constitution.
---

# Skill /gsie-governance — Gouvernance Quintessences / GSIE

## Quand invoquer cette skill

- Vérifier ou changer le **statut** d'un document (Draft / Review / Validated / Locked)
- Créer ou amender une **décision** (`DEC-xxxxxx`)
- Créer ou amender une **directive** (`GSIE-DIR-xxxx`)
- Ouvrir ou faire évoluer une **RFC** (`RFC-xxxx`)
- Vérifier la **hiérarchie documentaire** (Vision → Constitution → RFC → Directive → Decision → Architecture → Specification → Implementation → Code)
- Synchroniser la **mémoire** (`PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md`)
- Vérifier la conformité d'un changement à la **Constitution** (`00_CONSTITUTION/`)

## Sources d'autorité (ordre décroissant)

1. `00_CONSTITUTION/` — primauté constitutionnelle (`GSIE-CON-000` et articles `GSIE-CON-0XX`)
2. `01_DIRECTIVES/` — directives fondatrices (`GSIE-DIR-xxxx`)
3. `02_RFC/` — propositions d'évolution (`RFC-xxxx`)
4. `03_DECISIONS/` — décisions tracées (`DEC-xxxxxx`)
5. `05_SPECIFICATIONS/` — exigences transverses
6. `GSIE/ARCHITECTURE/` — architecture logicielle et scientifique
7. Code — dernier niveau, sert les niveaux supérieurs

**Règle** : un niveau ne contredit jamais un niveau supérieur. En cas de
conflit, le niveau supérieur prime. La Constitution prime toujours.

## Cycle de vie d'un document

| Statut | Signification | Éditable librement ? |
|---|---|---|
| `Draft` | Créé, contenu en cours | Oui |
| `Review` | Rédigé, en attente de validation du Fondateur | Oui, avec prudence |
| `Validated` | Validé par le Fondateur | Non sans raison tracée |
| `Locked` | Verrouillé | **Non — uniquement via RFC** |

**Ordre imposé** : un livrable ne passe en `Review` que si le précédent
est au minimum en `Review` (voir `ROADMAP.md`).

## Créer une décision (DEC-xxxxxx)

### Numérotation

- Numéro séquentiel à 6 chiffres : `DEC-000042`, `DEC-000043`, etc.
- Vérifier le numéro le plus élevé dans `03_DECISIONS/` avant de créer.
- En cas de collision (un DEC-000025 Validated existe déjà et un nouveau
  DEC-000025 est créé), renuméroter le nouveau (cf. DEC-000028).

### Template minimal

```markdown
# DEC-xxxxxx — [Titre court]

| Champ | Valeur |
|---|---|
| **ID** | DEC-xxxxxx |
| **Statut** | Draft |
| **Date** | YYYY-MM-DD |
| **Décideur** | Camille Perraudeau (Fondateur) |
| **RFC liée** | RFC-xxxx (si applicable) |
| **ADR liés** | ADR-xxx (si applicable) |
| **Supersède** | Aucun / DEC-xxxxxx |
| **Préserve** | DEC-xxxxxx (si applicable) |
| **Nature** | Décision d'architecture / d'organisation / technique |

## Décision

[Une à trois phrases — ce qui est décidé, pas pourquoi]

## Contexte

[Pourquoi cette décision — problème, options, contraintes]

## Conséquences

[Impact sur le code, la roadmap, les moteurs, les applications]
```

### Après création

1. Ajouter la décision à la section « Décisions actives » de
   `PROJECT_MEMORY.md`.
2. Ajouter une entrée dans `CHANGELOG.md` à la date courante.
3. Si la décision modifie la roadmap, mettre à jour `ROADMAP.md`.

## Créer une RFC (RFC-xxxx)

### Numérotation

- Numéro séquentiel à 4 chiffres : `RFC-0031`, `RFC-0032`, etc.
- Vérifier le numéro le plus élevé dans `02_RFC/` avant de créer.

### Workflow

1. `Draft` → rédaction de la RFC
2. `Review` → soumission au Fondateur
3. `Adopté` / `Rejeté` → décision du Fondateur tracée par un `DEC-xxxxxx`
4. Si `Adopté` → implémentation autorisée (Phase 4)

### Template

Voir `02_RFC/README.md` et une RFC existante (ex. `RFC-0028`) pour le
format complet.

## Amender une directive (GSIE-DIR-xxxx)

- Les directives fondatrices (`GSIE-DIR-0001` à `GSIE-DIR-0011`) ne
  s'amendent que par une décision du Fondateur tracée par `DEC-xxxxxx`.
- L'amendement crée une nouvelle version de la directive (v1.0 → v1.1)
  et archive l'ancienne.
- Voir `01_DIRECTIVES/README.md` pour le format.

## Synchroniser la mémoire

Après **tout changement d'état** du projet :

1. `PROJECT_MEMORY.md` — champ « Dernière mise à jour » + section
   concernée (Vague, Décisions actives, Documents structurants, etc.)
2. `CHANGELOG.md` — nouvelle entrée à la date courante sous le titre
   approprié (ou création d'un nouveau titre si la date n'existe pas)
3. `ROADMAP.md` — si le changement affecte les phases ou livrables

## Vérifier la conformité à la Constitution

1. Lire `00_CONSTITUTION/GSIE-CON-000.md` (article fondateur)
2. Lire les articles `GSIE-CON-0XX` pertinents (CON-001 : l'IA assiste,
   CON-002 : source et niveau de preuve, CON-003 : pas de code métier
   hors phase, CON-004 : explicabilité, CON-005 : domaine de validité,
   CON-010 : pas d'UPDATE ni DELETE physique)
3. Vérifier que le changement ne contredit aucun article
4. Si contradiction → **arrêter** et ouvrir une RFC pour amendement
   constitutionnel

## Documents `Locked`

**Jamais modifier un `Locked`** — uniquement via RFC dédiée dans
`02_RFC/`. Ceci inclut : `GSIE-FND-001`, `GSIE-FND-002`, `GSIE-CON-000`.

## Fichiers de référence

| Fichier | Rôle |
|---|---|
| `PROJECT_MEMORY.md` | État courant, décisions actives |
| `ROADMAP.md` | Phases et livrables |
| `CHANGELOG.md` | Journal des évolutions |
| `03_DECISIONS/README.md` | Format des décisions |
| `02_RFC/README.md` | Format des RFC |
| `01_DIRECTIVES/README.md` | Format des directives |
| `00_CONSTITUTION/README.md` | Hiérarchie constitutionnelle |

## Intake des idées et ressources

Les skills `/ingestion-idee` et `/ingestion-ressource` préparent des
propositions, mais ne remplacent pas la gouvernance :

- une idée reste dans `22_PROJECT_MEMORY/IDEA_BACKLOG.md` tant qu'elle n'est
  pas qualifiée ;
- une ressource est routée vers `GSIE/RESEARCH/`, `GSIE/DATASETS/`,
  `GSIE/KNOWLEDGE/`, `21_EXPERIMENTS/` ou `19_LEGAL/` selon sa nature ;
- une licence inconnue interdit l'ingestion d'un dataset ;
- aucune skill d'intake ne crée seule de RFC, DEC ou code métier ;
- toute décision structurante reste soumise au Fondateur et aux sources
  canoniques.

## Phase courante

**Phase 4 — Implémentation** (lancée par `DEC-000017` / `GSIE-DIR-0011`
le 2026-07-13). Le code métier est autorisé. Voir `PROJECT_MEMORY.md`
pour l'état d'implémentation courant.
