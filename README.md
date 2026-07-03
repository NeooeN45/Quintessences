# GeoSylva Intelligence Engine (GSIE)

> **Fondation scientifique** — système expert forestier open-source français.
> La connaissance avant le code. La science avant l'opinion.

---

## Qu'est-ce que GSIE ?

**GSIE** (GeoSylva Intelligence Engine) est une **plateforme
scientifique, technique et logicielle** destinée à devenir un système
expert d'aide au diagnostic forestier.

GSIE n'est **pas une application**. GSIE n'est **pas un simple
logiciel**. C'est une fondation scientifique dont le produit principal
est un **moteur d'intelligence forestière** modulaire, traçable et
explicable.

GSIE doit devenir le **premier système expert forestier open-source
français**, capable de :

- Réaliser des diagnostics stationnels
- Analyser les sols et interpréter la flore
- Corréler des centaines de paramètres écologiques, pédologiques,
  climatiques et géographiques
- Fournir des recommandations **explicables**
- Fonctionner **entièrement hors ligne**
- Servir de base à plusieurs interfaces

---

## GSIE et ses interfaces

**GeoSylva Mobile n'est qu'une interface.** Le produit principal est
GSIE. Les applications ne sont que des clients du moteur.

| Interface | Rôle |
|---|---|
| **GeoSylva Mobile** | Client Android terrain |
| **GeoSylva Desktop** | Poste fixe d'analyse |
| **GeoSylva Web** | Interface en ligne |
| **API GSIE** | Intégration dans des workflows tiers |
| **SDK** | Bibliothèques clientes (Kotlin, Python, TypeScript) |
| **Plugins** | Intégrations SIG tiers (QGIS, ArcGIS) |

Aucune application ne contient de logique métier. Toute l'intelligence
réside dans les moteurs de GSIE.

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

L'IA **assiste** le forestier. Elle ne décide **jamais** à sa place.

---

## Méthodologie documentaire

Toute documentation GSIE suit la hiérarchie suivante. Le code est
toujours le **dernier niveau**.

```
Vision → Constitution → RFC → Directive → Decision
→ Architecture → Specification → Implementation → Code
```

---

## Organisation du projet

```
GSIE/
├── 00_CONSTITUTION/        Principes intangibles et garde-fous
├── 01_DIRECTIVES/          Directives fondatrices (ACTIVE / ARCHIVED)
├── 02_RFC/                 Request for Comments
├── 03_DECISIONS/           Décisions tracées et validées
├── 04_ARCHITECTURE/        Architecture logicielle et scientifique
├── 05_SPECIFICATIONS/      Exigences fonctionnelles et non fonctionnelles
├── 06_RESEARCH/            Travaux scientifiques et bibliographie
├── 07_KNOWLEDGE/           Base de connaissances structurée
├── 08_DATASETS/            Jeux de données référencés et sourcés
├── 09_ENGINES/             Moteurs exécutables indépendants
├── 10_ALGORITHMS/          Procédures computationnelles formelles
├── 11_MODELS/              Modèles scientifiques et d'apprentissage
├── 12_APPLICATIONS/        Interfaces utilisateurs
├── 13_API/                 Contrats d'interface exposés
├── 14_SDK/                 Bibliothèques clientes
├── 15_TESTS/               Tests unitaires, intégration et non-régression
├── 16_TOOLS/               Utilitaires et chaînes de construction
├── 17_DOCUMENTATION/       Documentation officielle
├── 18_FINANCING/           Modèle économique et traçabilité financière
├── 19_LEGAL/               Licences, conformité, propriété intellectuelle
├── 20_PARTNERSHIPS/        Partenariats scientifiques et institutionnels
├── 21_EXPERIMENTS/         Prototypes et recherches exploratoires
└── 22_PROJECT_MEMORY/      Mémoire du projet (décisions, visions, idées)
```

Chaque dossier possède un README expliquant son objectif, ses
responsabilités, ce qui peut y être ajouté, ce qui est interdit, et ses
liens avec les autres dossiers.

---

## État du projet

**Phase 1 : Fondation.** Aucun développement métier.

La Constitution est en place : 11 articles (CON-000 à CON-010), deux
préambules verrouillés (FND-001, FND-002), trois constitutions
sectorielles (scientifique, technique, IA). Les 14 moteurs officiels
sont documentés dans `09_ENGINES/`. L'architecture est en cours de
consolidation.

---

## Moteurs GSIE

GSIE est composé de **14 moteurs indépendants**, chacun ayant une
responsabilité unique. La chaîne principale est :

```
Evidence Engine → Knowledge Engine → Correlation Engine
→ Reasoning Engine → Diagnostic Engine → Recommendation Engine
→ Validation Engine → Utilisateur
```

Les moteurs spécialisés (GIS, Climate, Pedology, Botanical, Forest
Dynamics) alimentent les moteurs de raisonnement en données
domaine-spécifiques. Les moteurs Learning et Simulation enrichissent et
projettent.

| Moteur | Rôle | Dossier |
|---|---|---|
| Evidence Engine | Évaluation de la preuve scientifique | `09_ENGINES/EVIDENCE_ENGINE/` |
| Knowledge Engine | Centralisation des connaissances qualifiées | `09_ENGINES/KNOWLEDGE_ENGINE/` |
| Correlation Engine | Corrélations multiparamètres | `09_ENGINES/CORRELATION_ENGINE/` |
| Reasoning Engine | Raisonnement sur les connaissances | `09_ENGINES/REASONING_ENGINE/` |
| Diagnostic Engine | Diagnostics stationnels et sylvicoles | `09_ENGINES/DIAGNOSTIC_ENGINE/` |
| Recommendation Engine | Recommandations contournables | `09_ENGINES/RECOMMENDATION_ENGINE/` |
| Validation Engine | Validation des sorties avant présentation | `09_ENGINES/VALIDATION_ENGINE/` |
| GIS Engine | Données géospatiales | `09_ENGINES/GIS_ENGINE/` |
| Climate Engine | Données climatiques et bioclimatiques | `09_ENGINES/CLIMATE_ENGINE/` |
| Pedology Engine | Données pédologiques | `09_ENGINES/PEDOLOGY_ENGINE/` |
| Botanical Engine | Flore, taxonomie, autécologie | `09_ENGINES/BOTANICAL_ENGINE/` |
| Forest Dynamics Engine | Dynamique des peuplements | `09_ENGINES/FOREST_DYNAMICS_ENGINE/` |
| Learning Engine | Apprentissage encadré | `09_ENGINES/LEARNING_ENGINE/` |
| Simulation Engine | Simulation de scénarios | `09_ENGINES/SIMULATION_ENGINE/` |

---

## Bases spécialisées

GSIE ne repose pas sur une seule base. Les 9 bases spécialisées sont :

| Base | Rôle |
|---|---|
| Knowledge Graph | Graphe de connaissances structurées |
| Scientific Database | Données scientifiques sourcées |
| Spatial Database | Données géospatiales |
| Ontology | Ontologies et taxonomies |
| Document Repository | Documents et publications |
| Evidence Repository | Preuves et niveaux de preuve |
| Climate Repository | Données climatiques |
| Species Repository | Espèces et caractéristiques |
| Station Repository | Stations forestières |

---

## Gouvernance et traçabilité

- **Constitution** (`00_CONSTITUTION/`) — principes intangibles
- **Directives** (`01_DIRECTIVES/`) — décisions fondatrices versionnées
- **RFC** (`02_RFC/`) — propositions d'évolution débattues
- **Décisions** (`03_DECISIONS/`) — décisions tracées et validées
- **Mémoire** (`22_PROJECT_MEMORY/`) — aucune décision perdue

Les prompts de pilotage sont eux-mêmes versionnés :

```
GSIE-PROMPT-0001  →  Fondation du projet
GSIE-PROMPT-0002  →  Constitution
GSIE-PROMPT-0003  →  Architecture générale
…
```

---

## Fichiers racine

| Fichier | Rôle |
|---|---|
| `README.md` | Présentation du projet (ce fichier) |
| `PROJECT_MEMORY.md` | Vue courante de l'état du projet |
| `CHANGELOG.md` | Journal des évolutions |
| `ROADMAP.md` | Feuille de route |

---

## Licence

À définir par un RFC dédié.

---

*GSIE — la connaissance est le véritable produit. Le code n'est qu'un
moyen.*
