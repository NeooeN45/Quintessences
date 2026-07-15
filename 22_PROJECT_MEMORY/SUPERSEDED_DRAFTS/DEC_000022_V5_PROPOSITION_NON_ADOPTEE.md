# Archive — DEC-000022 — Métamodèle v5 de l'Écosystème GSIE

| Champ | Valeur |
|---|---|
| **Statut** | Proposition historique non adoptée |
| **Source originale** | `03_DECISIONS/DEC-000022.md` |
| **Date d'archivage** | 2026-07-15 |
| **Motif** | Brainstorming v5 supersédé par la convergence v6/v6.1 avant adoption |
| **Valeur normative** | Aucune |

> Le contenu ci-dessous est conservé intégralement pour retracer le
> cheminement intellectuel. Ses mentions « Validated », « acté » ou
> « décisions validées » décrivent une erreur de gouvernance historique
> et ne doivent pas être interprétées comme un état réel du projet.

---

# DEC-000022 — Métamodèle v5 de l'Écosystème GSIE (Environmental Knowledge Operating System)

| Champ | Valeur |
|---|---|
| **ID** | DEC-000022 |
| **Date** | 2026-07-15 |
| **Phase** | 4 — Implémentation |
| **Vague** | 1 — Fondations (préparation) |
| **Statut** | Validated |
| **Décision précédente** | DEC-000021 (Semaine 4 — pipeline intégré Evidence → Knowledge) |
| **Livré par** | DEC-000022 → livrable GSIE-ARCH-213 (`ECOSYSTEM_METAMODEL.md`, Draft) |
| **RFC à créer** | RFC pour réviser le livrable 304 (`KNOWLEDGE_GRAPH_SPECIFICATION.md`, Validated) |

---

## Contexte

À l'issue de la Vague 1 (Fondations) — clôturée par DEC-000021 avec 166
tests et le pipeline intégré Evidence → Knowledge — une session de
conception interactive entre le Fondateur et l'architecte Devin a
produit le **métamodèle conceptuel v5** de l'Encyclopédie de
l'Écosystème GSIE. Cette décision acte l'ensemble des choix validés
durant cette session et ouvre la voie à la Vague 2 (Domaine) et à la
formalisation du métamodèle dans un livrable d'architecture.

### Problème initial

Le dépôt contenait **deux métamodèles concurrents non réconciliés** :

- **Livrable 205** (`SCIENTIFIC_DATA_MODEL.md`, *Draft*) — métamodèle
  logique orienté entités-domaine.
- **Livrables 303/304/309** (*Validated*) — métamodèle encyclopédique
  orienté KnowledgeObject + graphe Neo4j.
- **Code implémenté** — troisième voie non tracée : PostgreSQL +
  Apache AGE, source JSONB, UUID v4.

Le métamodèle v5 réconcilie ces trois voies sous une architecture
cohérente respectant tous les invariants constitutionnels
(CON-001, CON-002, CON-004, CON-005, CON-007, CON-010, S-1 à S-7).

## Décision

Valider le **métamodèle v5 — Environmental Knowledge Operating System**,
caractérisé par :

- **~110 classes** organisées en **8 couches** (Fondation,
  Connaissances, Acquisition, Analyse, Simulation, Décision,
  Applications, Event Bus + Scheduler) + **6 registres transverses**
  (Connector, Model, Capability, Ontology, Workflow, Plugin).
- **PostgreSQL 17** comme **seule source de vérité canonique**
  (PostGIS + Apache AGE + pgvector + TimescaleDB). DuckDB + Parquet +
  Elasticsearch en phase 2 (projections reconstructibles). Jena/Neo4j
  en phase 3 (uniquement si nécessaire).
- **5 vagues d'implémentation** incrémentales.
- **Relation** comme classe de premier niveau (n-aire, contextualisée,
  temporelle, spatiale, sourcée).
- **Séparation Concept / Instance** (Concept référentiel non versionné,
  Instance physique versionnée).
- **Provenance W3C PROV** (Activity/Entity/Agent) + Data Lineage avec
  version et checksum.
- **Versioning Git-like** complet dès la Vague 1 (Revision + Snapshot +
  Branch + Merge).
- **Ontology explicite** (le système se connaît lui-même) en Vague 4.
- **Auto-apprentissage partiel** : E-F sans validation humaine, A-D avec
  validation humaine obligatoire (CON-001).
- **Registry Architecture** comme brique différenciante : les modules
  annoncent leurs Capability et le GSIE orchestre automatiquement.

## Décisions validées en session (25 décisions)

| # | Décision | Choix retenu |
|---|---|---|
| D1 | Architecture organisatrice | 7 couches initialement, devenue 8 avec Event Bus |
| D2 | Séparation ontologique | Concept (non versionné) / Instance (versionné) |
| D3 | Relation | Classe de 1er niveau enrichie (n-aire, contextualisée) |
| D4 | Provenance | W3C PROV (Activity/Entity/Agent) |
| D5 | Stockage canonique | PostgreSQL 17 + PostGIS + AGE + pgvector + TimescaleDB (phase 1). DuckDB + Parquet + ES (phase 2). Jena/Neo4j (phase 3 si nécessaire). PostgreSQL = seule source de vérité. |
| D6 | Source | FK vers table sources dédiée |
| D7 | Attributs | 3 niveaux : colonnes natives (fréquent) + AttributeDefinition/AttributeValue (rare) + JSONB metadata (variable). Tables dédiées par domaine. |
| D8 | Identifiant | UUID seul — réviser GSIE-DIR-0008 §2.2 |
| D9 | Versioning | Git-like complet dès vague 1 (Revision + Snapshot + Branch + Merge) |
| D10 | Learning | Auto-apprentissage partiel : E-F sans humain, A-D avec validation humaine |
| D11 | Ontology explicite | Concevoir maintenant, implémenter vague 4 |
| D12 | Vagues | 5 vagues fines incrémentales |
| D13 | Confidentialité | 3 niveaux + RLS PostgreSQL |
| D14 | Raster | Federated First + ConnectorRegistry. Copie locale seulement si nécessaire. |
| D15 | TimeSeries | TimescaleDB |
| D16 | Formalisation | RFC pour réviser 304 + nouveau livrable Draft (213) |
| D17 | ConnectorRegistry | Couche Fondation |
| D18 | Modules GeoSylva | 11 modules en vague 2 |
| D19 | DigitalTwin + Mesh | Plus tard (quand Unreal en phase active) |
| D20 | DuckDB + Parquet | Vague 2 (analytique massif) |
| D21 | Registry Architecture | 6 registres transverses (couche différenciante) |
| D22 | Event Bus | LISTEN/NOTIFY en phase 1, Redis/NATS si besoin |
| D23 | FeatureStore | Vague 3 (quand premiers modèles IA en production) |
| D24 | SemanticLayer | Couche Analyse, vague 2 |
| D25 | DataQuality | Couche Connaissances, vague 2 |

## Invariants constitutionnels respectés

| # | Invariant | Source |
|---|---|---|
| I1 | Aucune connaissance sans source identifiable | S-1, CON-002 |
| I2 | Toute connaissance porte son niveau de preuve (A-F) | S-2 |
| I3 | Les conflits sont conservés, jamais résolus arbitrairement | S-3 |
| I4 | Toute incertitude est explicite | S-5 |
| I5 | Toute connaissance est versionnée, historique immuable | CON-010, S-7 |
| I6 | Toute décision est explicable | CON-004 |
| I7 | L'IA assiste, ne décide jamais | CON-001 |
| I8 | Identité stable et citable | S-7, CON-010 |
| I9 | Tout objet versionné porte created_at, updated_at, created_by, validated_by, validation_level, review_status, deleted_at, version, checksum, uuid | CON-010, CON-005 |
| I10 | Toute Relation est traçable et sourcée | S-1, CON-005 |
| I11 | Concept vs Instance : un Concept est référentiel (non versionné), une Instance est un individu physique (versionné) | — |
| I12 | L'ontologie est explicite : le système connaît ses propres classes, propriétés, relations et contraintes | CON-007 |
| I13 | Identité découplée : toute entité a une Identity avec UUID + aliases externes + historique | S-7, CON-010 |
| I14 | Provenance W3C PROV : toute activité est tracée par Activity/Entity/Agent | CON-004, CON-005 |
| I15 | Niveaux d'observation : RawObservation → ValidatedObservation → ComputedObservation → Inference → Decision | S-2, CON-004 |
| I16 | Décision sous contraintes et objectifs : toute Recommendation respecte des Constraints et poursuit des Goals | CON-001 |

## Incompatibilités à résoudre

25 incompatibilités identifiées entre les métamodèles 205/304/309 et le
code implémenté. Voir section 16 du livrable GSIE-ARCH-213 pour le
détail complet et leur priorisation par vague.

Les plus critiques (Vague 1) :

1. Neo4j (304) vs Apache AGE (code) → RFC pour réviser 304
2. `connaissances_meta` (304) vs `knowledge_objects` (code) → renommer
3. Source JSONB (code) vs FK (304) → migrer vers FK
4. UUID v4 vs `GSIE-K-XXXXXXXXXX` → réviser GSIE-DIR-0008 §2.2
5. Entités versionnées (205) vs non (304) → adopter Concept/Instance
6. 4 couches (304) vs 1 (code) → acter PostgreSQL seul

## Garde-fous

1. 5 vagues incrémentales (pas tout d'un coup)
2. PostgreSQL 17 comme seule source de vérité, projections
   reconstructibles
3. Attributs 3 niveaux (colonnes natives + EAV + JSONB metadata)
4. Ontology explicite en vague 4 (pas avant que le cœur soit stable)
5. Auto-apprentissage partiel (E-F sans humain, A-D avec humain)
6. EventBus en LISTEN/NOTIFY en phase 1 (pas d'infra lourde avant le
   besoin)

## Actions consécutives

| # | Action | Responsable | Statut |
|---|---|---|---|
| A1 | Créer le livrable GSIE-ARCH-213 (`ECOSYSTEM_METAMODEL.md`, Draft) | Devin | ✅ Fait |
| A2 | Créer ce DEC-000022 (traçabilité) | Devin | ✅ Fait |
| A3 | Créer une RFC pour réviser le livrable 304 (Validated → révisé) | À faire | ⏳ |
| A4 | Réviser GSIE-DIR-0008 §2.2 (identifiants GSIE-K-XXXXXXXXXX → UUID) | À faire | ⏳ |
| A5 | Mettre à jour PROJECT_MEMORY.md | Devin | En cours |
| A6 | Mettre à jour CHANGELOG.md | Devin | En cours |
| A7 | Lancer la Vague 2 (Domaine : GIS + Climate + Botanical + Pedology + ForeFire) | À faire après RFC | ⏳ |

## Prochaine étape

1. **Court terme** : créer la RFC pour réviser le livrable 304 et
   réviser GSIE-DIR-0008 §2.2.
2. **Vague 2** : modules métier GeoSylva (11 agrégats DDD), Observation
   enrichie + DataQuality, OGC/STAC, SemanticLayer, EventBus, DuckDB +
   Parquet + Elasticsearch, TimescaleDB.
3. **Vague 3** : Simulation + Décision + Ignis + Artemis + FeatureStore.
4. **Vague 4** : Ontology explicite + KnowledgeGraph + Feedback +
   Learning + 4 registres restants.
5. **Vague 5** : DigitalTwin + Mesh + EcosystemService + projections
   Jena/Neo4j si nécessaire.
