<div align="center">

# Quintessences

### Écosystème d'intelligence environnementale

**Un moteur. Des spécialisations. Zéro décision opaque.**

GSIE (General System Intelligence Engine) est un moteur d'aide à la
décision modulaire, traçable et explicable — conçu pour la forêt, le feu,
le climat et les territoires.

[![Phase](https://img.shields.io/badge/phase-2%20Architecture-blue)](ROADMAP.md)
[![Licence](https://img.shields.io/badge/licence-proprietary-red)](LICENSE)
[![Constitution](https://img.shields.io/badge/constitution-10%20articles%20%2B%203%20sectorielles-green)](00_CONSTITUTION/)
[![Moteurs](https://img.shields.io/badge/moteurs-14%20documentés-orange)](09_ENGINES/)
[![Décisions tracées](https://img.shields.io/badge/décisions%20tracées-6%20DEC-yellow)](03_DECISIONS/)
[![CI](https://github.com/NeooeN45/Quintessences/actions/workflows/ci.yml/badge.svg)](https://github.com/NeooeN45/Quintessences/actions/workflows/ci.yml)

</div>

---

## Pourquoi Quintessences existe

La gestion environnementale repose sur des **décisions qui engagent des
décennies** : choix d'essences, interventions sylvicoles, lutte contre
les incendies, adaptation climatique. Ces décisions sont prises par des
professionnels de terrain avec des outils **inadaptés** :

- **Données fragmentées** — sol, climat, flore, satellite éparpillés
  dans des silos incompatibles.
- **Outils d'IA opaques** — boîtes noires qui produisent des
  recommandations sans explication, sans source, sans traçabilité.
- **Pas de hors-ligne** — les outils existants supposent une
  connexion permanente, impossible en forêt ou en zone isolée.
- **Pas de gouvernance** — aucun cadre ne garantit que l'IA reste un
  outil d'aide et non une autorité qui décide à la place de l'humain.

**Quintessences résout ces quatre problèmes** avec une approche
radicalement différente : un moteur d'intelligence **fondé sur une
Constitution**, où chaque recommandation est sourcée, explicable et
contournable.

---

## Ce qui différencie Quintessences

| Critère | Concurrents (SilvIA, ForestNet, EcoAudit-AI…) | Quintessences |
|---|---|---|
| **Gouvernance** | Aucun cadre formel | Constitution de 10 articles + 3 sectorielles |
| **Traçabilité** | Décisions non tracées | Chaque décision a un identifiant (DEC-xxx) et un historique |
| **Explicabilité** | Boîte noire | Chaque recommandation cite ses sources et son raisonnement |
| **Hors-ligne** | Supposent une connexion | Conçu pour le terrain isolé (offline-first) |
| **Périmètre** | Un domaine (forêt OU feu OU carbone) | Multi-spécialisations (forêt + feu + futur climat/eau) |
| **Architecture** | Monolithique | 14 moteurs indépendants, responsabilité unique |
| **Méthodologie** | Ad hoc | Hiérarchie documentaire formelle (Vision → Code) |
| **Rôle de l'IA** | Décide ou suggère | **Assiste, ne décide jamais** (GSIE-CON-001) |

---

## Architecture

```
Quintessences (écosystème)
└── GSIE (General System Intelligence Engine — moteur)
    │
    ├── 14 moteurs communs (chaîne d'intelligence)
    │   Evidence → Knowledge → Correlation → Reasoning
    │   → Diagnostic → Recommendation → Validation → Utilisateur
    │
    ├── Moteurs domaine (alimentent le raisonnement)
    │   GIS · Climate · Pedology · Botanical · Forest Dynamics
    │
    ├── Moteurs transverses
    │   Learning (apprentissage encadré) · Simulation (scénarios)
    │
    └── Spécialisations (applications clientes)
        ├── GeoSylva        — app forestière (diagnostics sylvicoles)
        ├── GSIE-Ignis      — spécialisation incendie (surveillance, propagation)
        ├── Myhunt          — suivi cynégétique (faune, territoires)
        ├── QGISIA          — agent IA QGIS (SIG desktop, analyses géospatiales)
        └── [futures]       — climat, eau, biodiversité…
```

---

## Spécialisations

### GeoSylva — application forestière

La première spécialisation de Quintessences. Diagnostics stationnels,
analyse des sols, interprétation de la flore, recommandations de gestion
adaptées au terrain.

| Interface | Rôle |
|---|---|
| GeoSylva Mobile | Client Android terrain (offline) |
| GeoSylva Desktop | Poste fixe d'analyse |
| GeoSylva Web | Interface en ligne |
| API GSIE | Intégration dans des workflows tiers |
| SDK | Bibliothèques clientes (Kotlin, Python, TypeScript) |
| Plugins SIG | Intégrations QGIS, ArcGIS |

### GSIE-Ignis — spécialisation incendie

Système d'aide à la décision pour la surveillance et l'analyse des feux
de forêt. Jumeau numérique de propagation (ForeFire), assimilation de
données temps réel par drone, détection par vision embarquée. Positionné
comme **application cliente** de GSIE (RFC-0004, ADOPTÉ).

**Garde-fous non négociables** : outil d'aide à la décision du COS/CODIS,
jamais un système de commandement. Aucune alerte directe à la population
(prérogative régale FR-Alert). La sortie « cause probable » reste une
hypothèse exploratoire, jamais une conclusion.

### Myhunt — suivi cynégétique

Plateforme de suivi cynégétique premium orientée terrain. Application
Android native, API NestJS et backoffice Next.js. Gestion des
observations, zones, espèces et synchronisation hors-ligne.

- **Repo** : [github.com/NeooeN45/Myhunt](https://github.com/NeooeN45/Myhunt)
- **Lien GSIE** : moteurs GIS, Knowledge, Correlation, Learning (analyse
  des populations, prédiction de présence, gestion durable).

### QGISIA — agent IA QGIS (« GeoSylva AI »)

Agent IA intelligent pour QGIS. Route les demandes en langage naturel
vers le meilleur modèle, appelle les outils QGIS, interroge le web et
l'imagerie satellite, génère et exécute du PyQGIS. Interface desktop
du moteur GSIE pour les professionnels SIG.

- **Repo** : [github.com/NeooeN45/QGISIAPRO](https://github.com/NeooeN45/QGISIAPRO)
- **Lien GSIE** : moteurs GIS, Climate, Pedology, Botanical, Reasoning
  (analyses environnementales expertes dans QGIS).

### Futures spécialisations

L'architecture modulaire de GSIE permet d'étendre Quintessences à
d'autres domaines : climat, eau, biodiversité, sols. Chaque nouvelle
spécialisation fait l'objet d'un RFC dédié.

---

## Les 14 moteurs GSIE

Chaque moteur a une **responsabilité unique**. Aucun moteur ne connaît
les détails internes d'un autre. Cette modularité garantit la
maintenabilité, la testabilité et l'extensibilité.

### Chaîne d'intelligence (7 moteurs)

| Moteur | Rôle |
|---|---|
| Evidence Engine | Évalue la preuve scientifique en amont |
| Knowledge Engine | Centralise les connaissances qualifiées |
| Correlation Engine | Détecte les corrélations multiparamètres |
| Reasoning Engine | Raisonne sur les connaissances et corrélations |
| Diagnostic Engine | Produit les diagnostics (stationnels, sylvicoles, risque) |
| Recommendation Engine | Génère des recommandations **contournables** |
| Validation Engine | Valide les sorties avant présentation à l'utilisateur |

### Moteurs domaine (5 moteurs)

| Moteur | Rôle |
|---|---|
| GIS Engine | Données géospatiales (MNT, parcels, infra) |
| Climate Engine | Données climatiques et bioclimatiques |
| Pedology Engine | Données pédologiques (sols, texture, drainage) |
| Botanical Engine | Flore, taxonomie, autécologie |
| Forest Dynamics Engine | Dynamique des peuplements, croissance, mortalité |

### Moteurs transverses (2 moteurs)

| Moteur | Rôle |
|---|---|
| Learning Engine | Apprentissage encadré (retours terrain, feedback) |
| Simulation Engine | Simulation de scénarios (interventions, évolutions) |

---

## Gouvernance

Quintessences est gouverné par une **Constitution** — un ensemble de
principes intangibles qui s'imposent à tout le projet, y compris au
Fondateur. Aucun autre projet d'IA environnementale n'a ce niveau de
garde-fou formel.

### Les 10 articles constitutionnels

| Article | Principe |
|---|---|
| CON-000 | La Constitution prime sur tout (Locked) |
| CON-001 | Le forestier reste le décideur — l'IA assiste, ne décide jamais |
| CON-002 | La science avant tout |
| CON-003 | La Connaissance avant le Code |
| CON-004 | Toute décision doit être explicable |
| CON-005 | Toute connaissance doit être traçable |
| CON-006 | La Documentation fait partie du Produit |
| CON-007 | La Modularité est obligatoire |
| CON-008 | Le Projet appartient à sa Vision |
| CON-009 | GSIE est un patrimoine scientifique vivant |
| CON-010 | Toute connaissance doit pouvoir évoluer sans perdre son historique |

### Hiérarchie documentaire

Le code est toujours le **dernier niveau**. Aucun niveau ne contredit
un niveau supérieur.

```
Vision → Constitution → RFC → Directive → Décision
→ Architecture → Spécification → Implémentation → Code
```

### Traçabilité

Chaque décision structurante reçoit un identifiant (`DEC-xxxxxx`) et est
archivée dans `03_DECISIONS/`. Les propositions d'évolution passent par
des RFC (`02_RFC/`). **Aucune décision n'est perdue.**

| Decision | Sujet |
|---|---|
| DEC-000001 | GSIE est une fondation scientifique |
| DEC-000002 | Phase 1 : aucun développement métier |
| DEC-000003 | Adoption RFC-0004 : branche fonctionnelle GSIE-Ignis |
| DEC-000004 | Entrée en Phase 2 : Architecture |
| DEC-000005 | Archivage du code du banc GSIE-Ignis (Jalon 0) |
| DEC-000006 | Restructuration identité : Quintessences > GSIE > GeoSylva |

---

## Philosophie

1. La connaissance avant le code.
2. La science avant l'opinion.
3. Le terrain avant la théorie.
4. L'architecture avant les fonctionnalités.
5. La documentation avant l'implémentation.
6. La qualité avant la vitesse.
7. La cohérence avant l'optimisation.
8. La transparence avant la complexité.
9. L'explicabilité avant la performance.
10. La modularité avant le confort de développement.

---

## Roadmap

| Phase | Statut | Description |
|---|---|---|
| **Phase 1 — Foundation** | Clôturée | Constitution, 14 moteurs documentés, gouvernance, mémoire |
| **Phase 2 — Architecture** | **Active** | Contrats d'interface, schémas de données, RFC d'architecture |
| Phase 3 — Specification | À venir | Spécifications techniques détaillées par moteur |
| Phase 4 — Implementation | À venir | Code métier des moteurs |
| Phase 5 — Applications | À venir | GeoSylva, GSIE-Ignis et interfaces |

Voir `ROADMAP.md` pour le détail des livrables.

---

## Organisation du dépôt

```
Quintessences/
├── 00_CONSTITUTION/        Principes intangibles et garde-fous
├── 01_DIRECTIVES/          Directives fondatrices (ACTIVE / ARCHIVED)
├── 02_RFC/                 Request for Comments
├── 03_DECISIONS/           Décisions tracées et validées
├── 04_ARCHITECTURE/        Architecture logicielle et scientifique
├── 05_SPECIFICATIONS/      Exigences fonctionnelles et non fonctionnelles
├── 06_RESEARCH/            Travaux scientifiques et bibliographie
├── 07_KNOWLEDGE/           Base de connaissances structurée
├── 08_DATASETS/            Jeux de données référencés et sourcés
├── 09_ENGINES/             14 moteurs GSIE (documentés, non implémentés)
├── 10_ALGORITHMS/          Procédures computationnelles formelles
├── 11_MODELS/              Modèles scientifiques et d'apprentissage
├── 12_APPLICATIONS/        Interfaces utilisateurs (GeoSylva, GSIE-Ignis, …)
├── 13_API/                 Contrats d'interface exposés
├── 14_SDK/                 Bibliothèques clientes
├── 15_TESTS/               Tests unitaires, intégration et non-régression
├── 16_TOOLS/               Utilitaires et chaînes de construction
├── 17_DOCUMENTATION/       Documentation officielle et guides contributeurs
├── 18_FINANCING/           Modèle économique et traçabilité financière
├── 19_LEGAL/               Licences, conformité, propriété intellectuelle
├── 20_PARTNERSHIPS/        Partenariats scientifiques et institutionnels
├── 21_EXPERIMENTS/         Prototypes et recherches exploratoires
├── 22_PROJECT_MEMORY/      Mémoire du projet (décisions, visions, idées)
└── 23_QUALITY_MANAGEMENT/  Qualité : manuel, politique, KPI, audits, revues
```

Chaque dossier possède un `README.md` expliquant son objectif, ses
responsabilités, ce qui peut y être ajouté, ce qui est interdit.

---

## Contribuer

Quintessences est un projet à gouvernance constitutionnelle. Toute
contribution respecte la hiérarchie documentaire et la Constitution.

1. **Lire la Constitution** (`00_CONSTITUTION/`) avant toute proposition.
2. **Ouvrir un RFC** (`02_RFC/`) pour toute évolution structurante.
3. **Sourcer** toute affirmation scientifique (`06_RESEARCH/`,
   `08_DATASETS/`).
4. **Tracer** toute décision (`03_DECISIONS/`).
5. **Rédiger en français** — documentation, commentaires, commits.

Voir `17_DOCUMENTATION/CONTRIBUTING_GUIDE.md` pour le guide complet.

---

## Licence

**Licence propriétaire — All Rights Reserved.**

Copyright (c) 2026 Camille Perraudeau — Quintessences / GSIE.

Le code source est public pour transparence et évaluation. Toute
utilisation commerciale nécessite une licence séparée.

Contact : `fondateur@gsie.fr`

Voir `LICENSE` pour le texte complet.

---

<div align="center">

*Quintessences — la connaissance est le véritable produit.*
*Le code n'est qu'un moyen.*

</div>

---

## Contact

Pour toute question, réclamation ou collaboration :

**5jvw9s5zj@mozmail.com**

