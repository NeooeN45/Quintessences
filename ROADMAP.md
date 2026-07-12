# ROADMAP — GSIE

## Phase 1 — Foundation (courante)

> Lancée officiellement par **GSIE-DIR-0003**.
> La documentation est le produit principal de cette phase.
> Aucun développement métier avant validation des 12 livrables.

### Foundation Roadmap — 12 livrables obligatoires

Les livrables sont produits dans l'ordre. Un livrable ne peut passer en
**Review** que lorsque le précédent est au minimum en **Review**.

| # | Livrable | Fichier / Dossier | Statut |
|---|---|---|---|
| 001 | Structure documentaire et arborescence officielle | `GSIE/` (ensemble) | Validated |
| 002 | Préambule Constitutionnel | `00_CONSTITUTION/GSIE-FND-002.md` | Locked |
| 003 | Préambule Philosophique | `00_CONSTITUTION/GSIE-FND-001.md` | Locked |
| 004 | Article 000 — Primauté de la Constitution | `00_CONSTITUTION/GSIE-CON-000.md` | Locked |
| 005 | Pacte pour les IA | `00_CONSTITUTION/PACT_FOR_AI_AGENTS.md` | Validated |
| 006 | Philosophie de conception | `00_CONSTITUTION/GSIE-DESIGN-PHILOSOPHY.md` | Validated |
| 007 | Constitution scientifique | `00_CONSTITUTION/SCIENTIFIC_CONSTITUTION.md` | Validated |
| 008 | Constitution technique | `00_CONSTITUTION/TECHNICAL_CONSTITUTION.md` | Validated |
| 009 | Constitution de l'IA | `00_CONSTITUTION/AI_CONSTITUTION.md` | Validated |
| 010 | Articles constitutionnels 000-100 | `00_CONSTITUTION/GSIE-CON-000.md` à `GSIE-CON-010.md` (source réelle) ; gabarit `ARTICLE_0xx` en attente (cf. **RFC-0002**) | Validated (000 Locked, 001-010 Validated) |
| 011 | Système de documentation et guides contributeurs | `17_DOCUMENTATION/` | Validated |
| 012 | Mémoire du projet complète et snapshots | `22_PROJECT_MEMORY/` | Validated |

### Légende des statuts

| Statut | Définition |
|---|---|
| **Draft** | Fichier créé, contenu non rédigé ou en cours |
| **Review** | Contenu rédigé, en attente de validation du fondateur |
| **Validated** | Contenu rédigé et validé par le fondateur |
| **Locked** | Validé et verrouillé — modification uniquement par RFC |

### Avancement global

- **Validated** : 9 / 12 (001, 005, 006, 007, 008, 009, 010, 011, 012)
- **Locked** : 3 / 12 (002, 003, 004)
- **Draft** : 0 / 12

### Articles constitutionnels rédigés (livrable 010)

| Article | Fichier | Titre | Statut |
|---|---|---|---|
| 000 | `GSIE-CON-000.md` | La Primauté de la Constitution | Locked |
| 001 | `GSIE-CON-001.md` | Le forestier reste le décideur | Validated |
| 002 | `GSIE-CON-002.md` | La science avant tout | Validated |
| 003 | `GSIE-CON-003.md` | La Connaissance avant le Code | Validated |
| 004 | `GSIE-CON-004.md` | Toute décision doit être explicable | Validated |
| 005 | `GSIE-CON-005.md` | Toute connaissance doit être traçable | Validated |
| 006 | `GSIE-CON-006.md` | La Documentation fait partie du Produit | Validated |
| 007 | `GSIE-CON-007.md` | La Modularité est obligatoire | Validated |
| 008 | `GSIE-CON-008.md` | Le Projet appartient à sa Vision | Validated |
| 009 | `GSIE-CON-009.md` | GSIE est un patrimoine scientifique vivant | Validated |
| 010 | `GSIE-CON-010.md` | Toute connaissance doit pouvoir évoluer sans perdre son historique | Validated |

### Documents transverses rédigés

| Fichier | Titre | Statut |
|---|---|---|
| `PACT_FOR_AI_AGENTS.md` | Pacte des Agents IA (livrable 005) | Validated |
| `GSIE-DESIGN-PHILOSOPHY.md` | GSIE Design Philosophy (livrable 006) | Validated |

### Documents méthodologiques rédigés

| Fichier | Dossier | Titre |
|---|---|---|
| `ARCHITECTURE_PRINCIPLES.md` | `04_ARCHITECTURE/` | Architecture Principles |
| `RESEARCH_METHOD.md` | `06_RESEARCH/` | GSIE Research Method |
| `KNOWLEDGE_METHOD.md` | `07_KNOWLEDGE/` | GSIE Knowledge Method |

### Documents d'architecture rédigés

| Fichier | Dossier | Titre |
|---|---|---|
| `GSIE_MASTER_ARCHITECTURE.md` | `04_ARCHITECTURE/` | GSIE Master Architecture |
| `GSIE_CORE_BLUEPRINT.md` | `04_ARCHITECTURE/` | GSIE Core Blueprint |
| `GSIE_DATA_FLOW.md` | `04_ARCHITECTURE/` | GSIE Data Flow |

### Moteurs documentés (`09_ENGINES/`)

| Moteur | Dossier | Statut |
|---|---|---|
| `EVIDENCE_ENGINE` | `09_ENGINES/EVIDENCE_ENGINE/` | Documenté (Phase 1) |
| `KNOWLEDGE_ENGINE` | `09_ENGINES/KNOWLEDGE_ENGINE/` | Documenté (Phase 1) |
| `CORRELATION_ENGINE` | `09_ENGINES/CORRELATION_ENGINE/` | Documenté (Phase 1) |
| `REASONING_ENGINE` | `09_ENGINES/REASONING_ENGINE/` | Documenté (Phase 1) |
| `DIAGNOSTIC_ENGINE` | `09_ENGINES/DIAGNOSTIC_ENGINE/` | Documenté (Phase 1) |
| `RECOMMENDATION_ENGINE` | `09_ENGINES/RECOMMENDATION_ENGINE/` | Documenté (Phase 1) |
| `VALIDATION_ENGINE` | `09_ENGINES/VALIDATION_ENGINE/` | Documenté (Phase 1) |
| `GIS_ENGINE` | `09_ENGINES/GIS_ENGINE/` | Documenté (Phase 1) |
| `CLIMATE_ENGINE` | `09_ENGINES/CLIMATE_ENGINE/` | Documenté (Phase 1) |
| `PEDOLOGY_ENGINE` | `09_ENGINES/PEDOLOGY_ENGINE/` | Documenté (Phase 1) |
| `BOTANICAL_ENGINE` | `09_ENGINES/BOTANICAL_ENGINE/` | Documenté (Phase 1) |
| `FOREST_DYNAMICS_ENGINE` | `09_ENGINES/FOREST_DYNAMICS_ENGINE/` | Documenté (Phase 1) |
| `LEARNING_ENGINE` | `09_ENGINES/LEARNING_ENGINE/` | Documenté (Phase 1) |
| `SIMULATION_ENGINE` | `09_ENGINES/SIMULATION_ENGINE/` | Documenté (Phase 1) |

**14/14 moteurs amorcés — niveau de documentation à qualifier.**

> Précision (audit 2026-07-06) : « amorcé » ne signifie pas « documenté en
> profondeur ». Sur les 14 moteurs, **3** possèdent un fichier de moteur dédié
> (`EVIDENCE`, `KNOWLEDGE`, `CORRELATION`, 14–18 lignes) et **11** ne disposent
> pour l'instant que d'un `README` de cadrage (26–35 lignes). Quatre brouillons
> (`DIAGNOSTIC`, `REASONING`, `RECOMMENDATION`, `VALIDATION`) subsistent dans
> `22_PROJECT_MEMORY/SUPERSEDED_DRAFTS/`. La documentation de moteur complète
> relève de la **Phase 2 (Architecture)**.

### Hors des 12 livrables (dossiers annexes substantiels)

Deux ensembles volumineux existent mais ne sont **rattachés à aucun** des 12
livrables de la Phase 1. Leur statut de gouvernance reste à statuer par le
Fondateur (livrable annexe ? anticipation de phase ultérieure ?) :

- `18_FINANCING/` — modèle et gouvernance financière (~1 060 lignes).
- `23_QUALITY_MANAGEMENT/` — manuel, politique et processus qualité (~1 370 l).

### RFC ouverts

**RFC-0003** — Architecture distribuée GSIE-Net : ouvert le 2026-07-07.
Capture la vision fondateur sur l'architecture offline-first, distribuée
et orientée données de GSIE. Activé en Phase 2. Voir `02_RFC/RFC-0003.md`.

**RFC-0004** — GSIE-FEU : Système autonome de surveillance et d'analyse des
incendies : **ADOPTÉ** le 2026-07-12 (DEC-000003). Nouvelle branche
fonctionnelle et application cliente de GSIE pour le risque incendie. Activé
en Phase 2+. Voir `02_RFC/RFC-0004.md` et `03_DECISIONS/DEC-000003.md`.

### Prochaine étape

**TOUS les livrables sont Validated ou Locked.** Phase 1 complète.

| Statut | Count | Livrables |
|---|---|---|
| Validated | 9 / 12 | 001, 005, 006, 007, 008, 009, 010, 011, 012 |
| Locked | 3 / 12 | 002, 003, 004 |

La Phase 1 est **clôturée**. Le projet peut entrer en Phase 2
(Architecture) après décision du Fondateur.

---

## Phase 2 — Architecture (active)

> Lancée officiellement par **DEC-000004** le 2026-07-12.
> Phase 1 clôturée — tous les livrables Validated ou Locked.

- Architecture détaillée des moteurs
- Contrats d'interface entre moteurs
- Schémas de données

## Phase 3 — Connaissance (à définir)

- Base de connaissances
- Ontologies et taxonomies
- Sourcing scientifique

## Phase 4 — Implémentation (à définir)

- Moteurs
- API
- SDK
- Applications

---

> Chaque phase fait l'objet d'une Directive dédiée.
> La Phase 1 ne se clôture que lorsque les 12 livrables sont au
> minimum **Validated**.
