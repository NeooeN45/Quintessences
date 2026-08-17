# PROJECT_MEMORY — Archive historique arrêtée au 2026-08-12

| Champ | Valeur |
|---|---|
| **État documentaire** | Archive |
| **Archivé le** | 2026-08-14 |
| **Superseded by** | [PROJECT_MEMORY.md canonique](../PROJECT_MEMORY.md) |
| **Usage autorisé** | Contexte historique uniquement |

> Cette copie n'est plus une vue courante. Son contenu historique est conservé
> sans réalignement rétroactif ; toute information actuelle doit être lue dans
> la mémoire canonique à la racine du dépôt.

---

# PROJECT_MEMORY — Mémoire du projet GSIE

| Champ | Valeur |
|---|---|
| **Créé le** | 2026-07-01 |
| **Phase** | 4 — Implémentation |
| **Directive courante** | GSIE-DIR-0003 |
| **Dernière mise à jour** | 2026-08-12 |

---

## État de référence courant — 2026-08-12

L'audit reproductible de `E:\Documents` produit la version 2.0.0 de
`GSIE/DATASETS/CANDIDATES_RESSOURCES_EDOCUMENTS.md` et un manifeste CSV/JSON.
Sur 41 215 fichiers vus, 15 014 restent après exclusions et forment 3 077
ressources logiques : les GeoTIFF ne sont plus comptés comme images et les
sidecars de 46 shapefiles sont repliés. L'audit détecte 143 groupes de doublons
exacts, 489 ressources potentiellement sensibles et 23 PDF probablement soumis
à OCR. Toutes restent au statut de **candidat** : aucune ingestion, promotion
canonique ou copie n'est autorisée sans provenance, droits, licence et qualité.

Les documents ONF et les données IGN/BRGM/PNR sont soumis à des droits
spécifiques. Leur utilisation dans GSIE nécessite un régime d'accès formalisé
(`NOMENCLATURE_SOURCES.md`). Les productions personnelles (diagnostics,
fiches de terrain, GeoPackages de peuplements) pourront être proposées comme
`FieldIntake` après quarantaine, schéma, droits, provenance et évaluation de
qualité.

## État de référence courant — 2026-08-11

La PR #28 est fusionnée dans `main` au commit
`22a1818471055d9f136a98c666b09bf58232780c`. Les contrôles post-fusion HA
Linux/TLS, CI complète, Data Registry, migrations, Docker, couverture,
mutations, Bandit, Rust, Trivy et gouvernance sont verts. La preuve distante
établit 6 000/6 000 réponses HTTP 200, zéro erreur, 276,3 req/s, p95 175,58 ms
et p99 252,82 ms. La couverture fusionnée est de 16 086/16 386 instructions
(98,17 %) et 70/70 mutations sont détectées. Aucun SLO de production ni FETCH
global n'est autorisé par cette preuve seule.

La veille GSIE-Bench reste la base de recherche. RFC-0039 et DEC-000067 sont
désormais validées et adoptées. La sélection des trois diagnostics Gold, la
qualification des références, l'implémentation du runner déterministe et les
baselines non-IA sont autorisées, avec métriques par tâche et veto critiques.
Aucune intégration IA, ingestion non qualifiée ou promotion automatique n'est
autorisée par cette validation.

La veille `GSIE/RESEARCH/VEILLE_LLM_ET_RD_GSIE_2026-08-12.md` enregistre les
candidats LLM locaux et partenaires pour la normalisation, les conditions de
NVIDIA NIM, les réserves de licences et de quotas, ainsi que les pistes R&D
IGNIS, Hydro, GeoAI, QGIS/IGN, Mesh et financements. `GSIE-Norm-Bench` est
retenu comme sous-benchmark à définir avant tout fine-tuning ou intégration IA.
Les éléments non vérifiés restent des candidats ou des pistes Draft ; aucune
ingestion, dépense, candidature ou implémentation n'en découle.

Les applications clientes sont aussi des producteurs de données : observations
terrain, capteurs, corrections, annotations, résultats d'actions et retours
utilisateur. Le guide d'architecture impose une boucle d'entrée par quarantaine,
schéma, droits, provenance et qualité avant tout enrichissement du Data Registry,
des productions dérivées, de GSIE-Bench ou des modèles IA. Aucune application
n'écrase directement la vérité canonique.

`GSIE/ARCHITECTURE/GSIE_EVOLUTION_AND_AI_INTEGRATION.md` passe en v1.2.0 après
audit d'intégrité. QualityAssessment, DatasetHealth et FieldIntake sont alignés
sur le code ; l'implémenté est séparé de la cible ; les zones `DATA_*`, le
resolver hors des 14 moteurs, la frontière Benchmark/Model Registry, la
readiness fournisseur et la sécurité sont clarifiés. Le guide reste `Draft` en
attente de validation par le fondateur.

Les sections historiques ci-dessous sont conservées sans réécriture.

## État opérationnel récent

- Data Registry Phase 2, QualityAssessment et FETCH fail-closed validés.
- Micro-extrait SoilGrids unique certifié par DEC-000061, sans promotion.
- API locale redéployée et chaîne PostgreSQL/Redis/MinIO vérifiée par
  DEC-000062.
- Profilage DEC-000063 : le port Docker Desktop explique le plafond hôte ;
  recyclage Gunicorn désynchronisé à 5000/5000. La capacité de production doit
  encore être qualifiée sous Linux avec plusieurs réplicas.
- DEC-000064 et DEC-000065 : banc à deux replicas puis workflow Ubuntu/TLS
  validés. Le run distant `31479643460` passe 6 000/6 000 requêtes sans erreur,
  à 298,03 req/s, p95 164,71 ms et p99 245,58 ms. Les requêtes longues,
  l'idempotence HTTP et les SLO de production restent hors preuve. Le run
  `31488527136` confirme le banc sur `e9743d8` après un unique rejeu dû à une
  coupure GitHub Releases antérieure aux tests. Deux coupures Debian parallèles
  sur `8a531ed` ont conduit à borner les reprises `apt`/`curl`, sans affaiblir
  TLS ni SHA-256 ; les images DB et API corrigées sont reconstruites et
  smoke-testées localement. La preuve distante de la tête finale reste requise.
- DEC-000066 : couverture Python multicouche obligatoire. Les suites finales
  passent 2 873 unités et 349 intégrations ; la fusion atteint 98,18 %, les
  49 contrats publics sont à 100 %, métier/application à 96,80 % et
  infrastructure à 99,97 %. Le job distant du run `31488527209` confirme
  98,169 %, 49/49 contrats, 96,80 % métier et 99,90 % infrastructure. Le premier
  run complet a aussi révélé puis fait corriger l'isolation S3/JWT du harnais
  Data Registry et un motif de mutation périmé. La sortie du brouillon reste
  conditionnée à un run complet vert sur la tête courante. Le run de PR
  `31492339317` sur `8a531ed` confirme 70/70 mutations, 98,17 % combinés,
  Registry, intégration, Docker, sécurité et gate final verts. La tête finale
  doit encore reproduire cette preuve après le durcissement réseau.
- DEC-000067 / RFC-0039 : GSIE-Bench v0.1 adopté. La tranche active est
  strictement limitée aux scénarios Gold, références qualifiées, runner
  déterministe et baselines non-IA. IA, ingestion non qualifiée et promotion
  automatique restent interdites.
- Le contrat FieldIntake stationnel v0.1 est implémenté et intégré sans
  migration au JSONB existant. Il contrôle unités et formules, conserve la
  mesure brute et signale les contradictions sans réécriture. Le scénario
  `quarantine.farges.dendrometry.001` reste Silver/quarantaine jusqu'à revue.
- Les candidats spatiaux et la bibliothèque scientifique sont enregistrés
  metadata-only ; aucune copie, ingestion ou promotion n'est autorisée.
- Le dossier de relecture Farges et la garde `assess_gold_qualification`
  imposent deux avis indépendants, la qualification scientifique et juridique,
  les tolérances, alternatives et vetos avant toute proposition Gold.
- La tranche 1 GSIE-Bench est implémentée : 30 scénarios candidats générés,
  runner Closed fail-closed, checksums, baseline naïve et baseline pédologique
  déterministe. Les quatre tests ciblés passent, Ruff et mypy strict sont
  verts. La relecture a corrigé la référence bibliographique vers *Tree
  Physiology* et séparé les sources pédologiques. La tentative Closed officielle
  est bloquée par `QualificationRequiredError` ; la référence Parelle 2007 reste
  en attente de relecture experte indépendante avant toute mesure complète.

---

## État du projet

GSIE est en **Phase 1 : Foundation**, lancée officiellement par
**GSIE-DIR-0003**. Aucun développement métier.

> **La documentation est désormais considérée comme le produit principal
> de la Phase 1.** Le code viendra en son temps, subordonné aux
> fondations documentaires.

La Phase 1 est composée de **12 livrables obligatoires**, produits dans
l'ordre strict. Aucun développement ne commencera avant leur validation.

### Avancement des livrables

| # | Livrable | Statut |
|---|---|---|
| 001 | Structure documentaire et arborescence | Validated |
| 002 | Préambule Constitutionnel | Locked |
| 003 | Préambule Philosophique | Locked |
| 004 | Article 000 — Primauté de la Constitution | Locked |
| 005 | Pacte pour les IA | Draft (rédigé, à valider) |
| 006 | Philosophie de conception | Draft (rédigé, à valider) |
| 007 | Constitution scientifique | Draft |
| 008 | Constitution technique | Draft |
| 009 | Constitution de l'IA | Draft |
| 010 | Articles constitutionnels 001-100 | Draft (003-010 rédigés) |
| 011 | Système de documentation et guides | Draft |
| 012 | Mémoire du projet complète et snapshots | Draft |

## Décisions fondatrices

- **DEC-000001** — GSIE est une Fondation scientifique. Le moteur est
  le produit principal. Les applications ne sont que des interfaces.
- **DEC-000002** — Phase 1 : Fondation. Aucun développement métier
  autorisé.
- **RFC-0001-D1** — Distinction entre Préambule constitutionnel et
  Préambule philosophique.
- **RFC-0001-D2** — Introduction de l'Article 000 « Primauté de la
  Constitution ».
- **RFC-0001-D3** — Classification des lois : Lois Immuables et Lois
  Évolutives.
- **RFC-0001-D4** — Hiérarchie documentaire officielle
  (Vision → Constitution → RFC → Directive → Décision → Architecture →
  Spécification → Code).
- **DIR-0003-D1** — La documentation devient le cœur du projet.
- **DIR-0003-D2** — 12 livrables obligatoires, produits dans l'ordre.
- **DIR-0003-D3** — Aucun développement métier avant validation des
  12 livrables.

## Documents structurants

- **GSIE-DIR-0001** — Directive fondatrice (ACTIVE)
- **GSIE-DIR-0003** — Lancement officiel Phase 1 Foundation (ACTIVE)
- **GSIE-DIR-0004** — GSIE Genesis Directive (ACTIVE)
- **RFC-0001** — Méthodologie de rédaction de la Constitution (ADOPTÉ)
- **RFC-0002** — Unification du système d'articles constitutionnels (Proposé)
- **RFC-0003 à RFC-0010** — Réservés, non ouverts

## Documents fondateurs de la Constitution

- `GSIE-FND-002.md` — Préambule Constitutionnel (Locked — livrable 002)
- `GSIE-FND-001.md` — Préambule Philosophique (Locked — livrable 003)
- `GSIE-CON-000.md` — La Primauté de la Constitution (Locked — livrable 004)

## Articles constitutionnels rédigés

- `GSIE-CON-000.md` — La Primauté de la Constitution (Locked, Loi Fondamentale Immuable)
- `GSIE-CON-001.md` — Le forestier reste le décideur (Draft, à valider)
- `GSIE-CON-002.md` — La science avant tout (Draft, à valider)
- `GSIE-CON-003.md` — La Connaissance avant le Code (Draft, à valider)
- `GSIE-CON-004.md` — Toute décision doit être explicable (Draft, à valider)
- `GSIE-CON-005.md` — Toute connaissance doit être traçable (Draft, à valider)
- `GSIE-CON-006.md` — La Documentation fait partie du Produit (Draft, à valider)
- `GSIE-CON-007.md` — La Modularité est obligatoire (Draft, à valider)
- `GSIE-CON-008.md` — Le Projet appartient à sa Vision (Draft, à valider)
- `GSIE-CON-009.md` — GSIE est un patrimoine scientifique vivant (Draft, à valider)
- `GSIE-CON-010.md` — Toute connaissance doit pouvoir évoluer sans perdre son historique (Draft, à valider)

## Documents transverses et méthodologiques rédigés

- `PACT_FOR_AI_AGENTS.md` — Pacte des Agents IA (livrable 005, Draft)
- `GSIE-DESIGN-PHILOSOPHY.md` — Design Philosophy (livrable 006, Draft)
- `SCIENTIFIC_CONSTITUTION.md` — Constitution Scientifique (livrable 007, Draft)
- `TECHNICAL_CONSTITUTION.md` — Constitution Technique (livrable 008, Draft)
- `AI_CONSTITUTION.md` — Constitution IA (livrable 009, Draft)
- `GSIE/ARCHITECTURE/ARCHITECTURE_PRINCIPLES.md` — Architecture Principles
- `GSIE/RESEARCH/RESEARCH_METHOD.md` — GSIE Research Method
- `GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md` — GSIE Knowledge Method

## Documents d'architecture rédigés

- `GSIE/ARCHITECTURE/GSIE_MASTER_ARCHITECTURE.md` — Architecture globale
- `GSIE/ARCHITECTURE/GSIE_CORE_BLUEPRINT.md` — Blueprint (Evidence Engine repositionné en amont)
- `GSIE/ARCHITECTURE/GSIE_DATA_FLOW.md` — Flux de données (Evidence Engine repositionné en amont)

## Moteurs amorcés (14/14 — profondeur à qualifier)

> 3 moteurs ont un fichier dédié (EVIDENCE, KNOWLEDGE, CORRELATION) ; 11 n'ont
> qu'un README de cadrage. Documentation complète = Phase 2 (cf. `ROADMAP.md`).

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

## Vision courante

GSIE doit devenir le premier système expert forestier open-source
français. La connaissance est le véritable produit. Le code n'est qu'un
moyen.

**Durant la Phase 1**, la documentation est le produit principal.

## Prochaine étape

**Livrables 007 à 009** — Constitutions scientifique, technique et de
l'IA : à rédiger. Les livrables 005 et 006 sont rédigés en attente de
validation.

---

## Index de la mémoire

| Fichier | Rôle |
|---|---|
| `PROJECT_MEMORY.md` | Vue courante de l'état du projet (ce fichier) |
| `VISION_HISTORY.md` | Évolution de la vision au fil du temps |
| `DECISION_HISTORY.md` | Chronologie de toutes les décisions |
| `IDEA_BACKLOG.md` | Idées non encore transformées en décisions |
| `FOUNDER_JOURNAL.md` | Journal du fondateur |
| `ARCHITECT_JOURNAL.md` | Journal de l'architecte |
| `CONTEXT_SNAPSHOT_001.md` | Snapshot de contexte (à remplir à la 10e Directive) |
