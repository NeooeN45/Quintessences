# PROJECT_MEMORY — Vue courante du projet Quintessences

| Champ | Valeur |
|---|---|
| **Écosystème** | Quintessences |
| **Moteur** | GSIE (General System Intelligence Engine) |
| **Phase** | 3 — Connaissance |
| **Directive courante** | GSIE-DIR-0010 (Réorganisation arborescence) |
| **Dernière mise à jour** | 2026-07-13 |

---

## État

**Quintessences** est un écosystème d'applications environnementales
fondé sur le moteur **GSIE** (General System Intelligence Engine).
Spécialisations : GeoSylva (forêt), Artemis (faune), Ignis (incendies),
Hydro (eau), Flora (végétation), QGISIA (plugin QGIS). Centre de
Commandement GSIE (Unreal Engine 5.8) — poste de pilotage immersif où
toutes les données convergent.

Repos externes intégrés : `apps/GeoSylva/` (GitHub: NeooeN45/GeoSylva),
`apps/QGISIA/` (GitHub: NeooeN45/QGISIAPRO), `Forge/` (usine de données,
pas de remote). Ces repos ont leur propre `.git` et sont ignorés par le
repo parent.

Le projet est en **Phase 3 : Connaissance**, lancée officiellement par
**DEC-000011** (GSIE-DIR-0007) le 2026-07-13. La Phase 1 (Foundation)
est **clôturée** — les 12 livrables sont Validated (9/12) ou Locked
(3/12). La Phase 2 (Architecture) a produit 12 livrables Draft
(201-212), prêts pour Review.

La Phase 3 transforme les fondations scientifiques et l'architecture en
une **base de connaissances structurée, sourcée et versionnée** — le
véritable produit de GSIE (CON-003). Elle est composée de 8 livrables
(301-308). Le code métier dans le dépôt reste interdit jusqu'en Phase 4.

### Avancement des livrables

- **Validated** : 9 / 12 (001, 005, 006, 007, 008, 009, 010, 011, 012)
- **Locked** : 3 / 12 (002 — Préambule Constitutionnel, 003 — Préambule Philosophique, 004 — Article 000)
- **Draft** : 0 / 12

### Articles constitutionnels rédigés

- `GSIE-CON-000.md` — La Primauté de la Constitution (Locked, Loi Fondamentale Immuable)
- `GSIE-CON-001.md` — Le forestier reste le décideur (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-002.md` — La science avant tout (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-003.md` — La Connaissance avant le Code (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-004.md` — Toute décision doit être explicable (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-005.md` — Toute connaissance doit être traçable (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-006.md` — La Documentation fait partie du Produit (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-007.md` — La Modularité est obligatoire (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-008.md` — Le Projet appartient à sa Vision (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-009.md` — GSIE est un patrimoine scientifique vivant (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-010.md` — Toute connaissance doit pouvoir évoluer sans perdre son historique (Validated, Loi Fondamentale Immuable)

### Documents transverses et méthodologiques rédigés

- `PACT_FOR_AI_AGENTS.md` — Pacte des Agents IA (livrable 005, Validated)
- `GSIE-DESIGN-PHILOSOPHY.md` — Design Philosophy (livrable 006, Validated)
- `SCIENTIFIC_CONSTITUTION.md` — Constitution Scientifique (livrable 007, Validated)
- `TECHNICAL_CONSTITUTION.md` — Constitution Technique (livrable 008, Validated)
- `AI_CONSTITUTION.md` — Constitution IA (livrable 009, Validated)
- `GSIE/ARCHITECTURE/ARCHITECTURE_PRINCIPLES.md` — Architecture Principles
- `GSIE/RESEARCH/RESEARCH_METHOD.md` — GSIE Research Method (livrable 301, détaillé Phase 3)
- `GSIE/RESEARCH/EVIDENCE_FRAMEWORK.md` — Evidence Framework (livrable 306, Phase 3)
- `GSIE/RESEARCH/SOURCING_PLAN.md` — Sourcing Plan (livrable 307, Phase 3)
- `GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md` — GSIE Knowledge Method (livrable 302, détaillé Phase 3)
- `GSIE/KNOWLEDGE/FOREST_ONTOLOGY.md` — Forest Ontology (livrable 303, Phase 3)
- `GSIE/KNOWLEDGE/KNOWLEDGE_GRAPH_SPECIFICATION.md` — Knowledge Graph Spec (livrable 304, Phase 3)
- `GSIE/KNOWLEDGE/KNOWLEDGE_BASE_SEED.md` — Knowledge Base Seed (livrable 308, 25 connaissances)
- `GSIE/DATASETS/DATASET_CATALOG.md` — Dataset Catalog (livrable 305, 24 datasets)
- `GSIE/ARCHITECTURE/ENCYCLOPEDIA_DATABASE_SCHEMA.md` — Schéma DB Encyclopédie (livrable 309, PostgreSQL + Neo4j + ES + Jena)
- `GSIE/ARCHITECTURE/ENGINE_DATA_SOCLE.md` — Socle données 14 moteurs + liens apps (livrable 310)

### Documents d'architecture rédigés

- `GSIE/ARCHITECTURE/GSIE_MASTER_ARCHITECTURE.md` — Architecture globale
- `GSIE/ARCHITECTURE/GSIE_CORE_BLUEPRINT.md` — Blueprint du cœur système (Evidence Engine repositionné en amont)
- `GSIE/ARCHITECTURE/GSIE_DATA_FLOW.md` — Flux de données officiel (Evidence Engine repositionné en amont)
- `GSIE/ARCHITECTURE/GSIE_IGNIS_GCS_CINEMA_UNREAL.md` — GCS-Cinéma UE 5.8 (livrable 211, DEC-000010)
- `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` — GeoSylva-Unreal (livrable 212, en attente MVP Ignis)
- `GSIE/RESEARCH/UNREAL_ENGINE_PRECEDENTS.md` — Fiches scientifiques FIRETWIN, FIRE-VLM, IVSR

### Branche Ignis (RFC-0004)

- `apps/Ignis/REGISTRE.md` — Registre d'idées vivant (60+ idées, 9
  sections : perception, jumeau numérique, vol drone, communications, GCS,
  données, stratégie, modèles IA, veille concurrentielle). Version 0.7.x.
- `apps/Ignis/` — Livrables du Jalon 0 (comparatifs sourcés).
- **Banc de simulation Ignis** (WSL2, hors dépôt) :
  - ForeFire compilé + démo propagation.png ✓
  - PX4 SITL v1.18.0-beta1 + Gazebo Harmonic 8.14.0 opérationnels ✓
  - **5 tests de vol réussis** : premier vol (34 m), waypoint (carré 100 m),
    pattern carré (200 m × 200 m), RTH (partiel), surveillance incendie
    (pattern lawnmower + 15 captures GPS)
  - Scripts : `premier_vol.py`, `vol_waypoint.py`, `vol_pattern_carre.py`,
    `vol_rth.py`, `vol_surveillance_incendie.py`, `run_test.sh`
  - Visualisation : `trajectoire_surveillance.png`

### Moteurs amorcés (14/14 — profondeur à qualifier)

> 3 moteurs ont un fichier dédié (EVIDENCE, KNOWLEDGE, CORRELATION) ; 11 n'ont
> qu'un README de cadrage. Documentation complète = Phase 2. Détail : `ROADMAP.md`.

- `GSIE/ENGINES/EVIDENCE_ENGINE/` — Evidence Engine (filtre amont)
- `GSIE/ENGINES/KNOWLEDGE_ENGINE/` — Knowledge Engine
- `GSIE/ENGINES/CORRELATION_ENGINE/` — Correlation Engine
- `GSIE/ENGINES/REASONING_ENGINE/` — Reasoning Engine
- `GSIE/ENGINES/DIAGNOSTIC_ENGINE/` — Diagnostic Engine
- `GSIE/ENGINES/RECOMMENDATION_ENGINE/` — Recommendation Engine
- `GSIE/ENGINES/VALIDATION_ENGINE/` — Validation Engine
- `GSIE/ENGINES/GIS_ENGINE/` — GIS Engine
- `GSIE/ENGINES/CLIMATE_ENGINE/` — Climate Engine
- `GSIE/ENGINES/PEDOLOGY_ENGINE/` — Pedology Engine
- `GSIE/ENGINES/BOTANICAL_ENGINE/` — Botanical Engine
- `GSIE/ENGINES/FOREST_DYNAMICS_ENGINE/` — Forest Dynamics Engine
- `GSIE/ENGINES/LEARNING_ENGINE/` — Learning Engine
- `GSIE/ENGINES/SIMULATION_ENGINE/` — Simulation Engine

## RFC ouverts

- **RFC-0003** — Architecture distribuée GSIE-Net (Proposé — 2026-07-07) :
  capture la vision fondateur sur l'architecture offline-first, distribuée,
  multi-couches et orientée données. Activé en Phase 2.
- **RFC-0004** — Ignis : Système autonome de surveillance et d'analyse
  des incendies (**ADOPTÉ** — 2026-07-12, DEC-000003) : nouvelle branche
  fonctionnelle dédiée au risque incendie, positionnée comme application
  cliente de GSIE. Registre d'idées dans `apps/Ignis/REGISTRE.md` ;
  livrables Jalon 0 dans `apps/Ignis/`. Aucun développement
  métier en Phase 1. Voir `02_RFC/RFC-0004.md`.

---

## Décisions actives

- **DEC-000001** — GSIE est une Fondation scientifique
- **DEC-000002** — Phase 1 : Fondation, aucun développement métier
- **RFC-0001-D1** — Distinction Préambule constitutionnel / philosophique
- **RFC-0001-D2** — Article 000 « Primauté de la Constitution »
- **RFC-0001-D3** — Classification des lois (Immuables / Évolutives)
- **RFC-0001-D4** — Hiérarchie documentaire officielle (Vision → Code)
- **DIR-0003-D1** — La documentation devient le cœur du projet
- **DIR-0003-D2** — 12 livrables obligatoires, produits dans l'ordre
- **DIR-0003-D3** — Aucun développement métier avant validation des 12 livrables
- **DEC-000003** — Adoption RFC-0004 : branche fonctionnelle Ignis (application cliente)
- **DEC-000004** — Entrée en Phase 2 : Architecture (Phase 1 clôturée)
- **DEC-000005** — Amendement DEC-000003/000004 : archivage du code du banc Ignis (Jalon 0)
- **DEC-000006** — Restructuration identité : Quintessences (écosystème) > GSIE (moteur) > GeoSylva (app forestière)
- **DEC-000007** — Extension écosystème : Artemis + QGISIA (ancien Myhunt, renommé par DEC-000013)
- **DEC-000008** — Directive fondatrice Ignis (GCS / jumeau numérique vivant) — GSIE-DIR-0005
- **DEC-000009** — Vision du Moteur Cognitif Ignis — GSIE-DIR-0006
- **DEC-000010** — Adoption Unreal Engine 5.8 + Cesium comme moteur 3D du jumeau numérique
- **DEC-000011** — Entrée en Phase 3 : Connaissance (GSIE-DIR-0007)
- **DEC-000012** — L'Encyclopédie de l'Écosystème : la plus grande base de connaissances écologiques du marché (GSIE-DIR-0008)
- **DEC-000013** — Restructuration écosystème : Myhunt→Artemis, GSIE-Ignis→Ignis, +Hydro, +Flora, Centre de Commandement GSIE (GSIE-DIR-0009)
- **DEC-000014** — Réorganisation arborescence : GSIE/ + apps/ (GSIE-DIR-0010)

## Documents structurants

- **GSIE-DIR-0001** — Directive fondatrice (ACTIVE)
- **GSIE-DIR-0003** — Lancement officiel Phase 1 Foundation (ACTIVE)
- **GSIE-DIR-0004** — GSIE Genesis Directive (ACTIVE)
- **GSIE-DIR-0005** — Directive fondatrice Ignis (GCS / jumeau numérique vivant) (Draft — DEC-000008)
- **GSIE-DIR-0006** — Vision du Moteur Cognitif Ignis (Draft — DEC-000009)
- **GSIE-DIR-0007** — Lancement officiel Phase 3 Connaissance (ACTIVE — DEC-000011)
- **GSIE-DIR-0008** — L'Encyclopédie de l'Écosystème (ACTIVE — DEC-000012)
- **GSIE-DIR-0009** — Restructuration écosystème : apps, Centre de Commandement, organisation (ACTIVE — DEC-000013)
- **GSIE-DIR-0010** — Réorganisation arborescence : GSIE/ + apps/ (ACTIVE — DEC-000014)
- **RFC-0001** — Méthodologie de rédaction de la Constitution (ADOPTÉ)
- **RFC-0002** — Unification du système d'articles constitutionnels (Proposé, en attente de validation du Fondateur)
- **RFC-0003** — Architecture distribuée GSIE-Net (Proposé)
- **RFC-0004** — Branche fonctionnelle Ignis (ADOPTÉ — DEC-000003)
- **RFC-0005 à RFC-0010** — Réservés, non ouverts

## Documents fondateurs de la Constitution

- `GSIE-FND-002.md` — Préambule Constitutionnel (Locked — livrable 002)
- `GSIE-FND-001.md` — Préambule Philosophique (Locked — livrable 003)
- `GSIE-CON-000.md` — La Primauté de la Constitution (Locked — livrable 004)

## Vision courante

**Quintessences** = écosystème d'intelligence environnementale (marque
umbrella). **GSIE** = General System Intelligence Engine, le moteur
spécialisable par domaine. **GeoSylva** = app forestière (première
spécialisation). La connaissance est le véritable produit.

**Durant la Phase 1**, la documentation est le produit principal. Le
code viendra en son temps, subordonné aux fondations.

## Prochaine étape

**Phase 2 — Architecture : tous les livrables 201-210 sont Draft et
complets.** Les 10 livrables respectent DIR-0005/0006 et les garde-fous
RFC-0004 §8. Le projet peut passer à la revue Fondateur (Review) puis
à la Phase 3 (Connaissance).

> La mémoire détaillée vit dans `22_PROJECT_MEMORY/`.
> La roadmap complète vit dans `ROADMAP.md`.
