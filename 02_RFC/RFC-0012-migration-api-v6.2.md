# RFC-0012 — Migration API GSIE vers le métamodèle v6.2

| Champ | Valeur |
|---|---|
| **ID** | RFC-0012 |
| **Statut** | Validated |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-16 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Impact** | `GSIE/API/` (ensemble du code API), `GSIE/ARCHITECTURE/ADR-007-api-v6.2.md`, `GSIE/SDK/`, `03_DECISIONS/DEC-000023.md`, `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md` |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-002 (science), GSIE-CON-005 (traçabilité), GSIE-CON-007 (modularité), GSIE-CON-010 (historique) |
| **Décision liée** | DEC-000023 (à créer) |
| **RFC liées** | RFC-0011 (métamodèle v6.2 — 73 types) |
| **ADR liés** | ADR-001 (racine resource), ADR-002 (Temporal Engine), ADR-007 (à créer — architecture API v6.2) |

---

## 1. Objet

Cette RFC propose la **migration complète de l'API GSIE** du schéma
v6.1 (12 tables, modèle `KnowledgeObject`) vers le métamodèle v6.2
(73 types noyau, table racine `resource`, GSIE Temporal & Provenance
Engine). Cette migration inclut :

1. **Table racine `resource`** (ADR-001) — tout type hérite de `resource`
2. **73 types SQLAlchemy** — un modèle par type du métamodèle
3. **Migration Alembic 0002** — création des 73 tables + enums + index
4. **CRUD générique** — endpoints REST pour tous les types via un router
   générique auto-généré, avec extensions spécifiques par moteur
5. **WebSocket** — canal temps réel pour le Hub (Centre de Commandement UE5.8)
6. **SDK** — génération OpenAPI → clients Python, Kotlin (GeoSylva), C++ (Hub)
7. **Migration des données existantes** — `knowledge_objects` → `assertions`

Cette RFC **supersède** l'architecture API actuelle (DEC-000019) pour la
partie persistance et endpoints, et **amende** la roadmap Phase 4.

---

## 2. Contexte et motivation

### 2.1 État actuel de l'API

L'API GSIE (FastAPI) a été implémentée en Vague 1 sur le schéma v6.1 :

- **12 tables** PostgreSQL : `knowledge_objects` + 5 satellites + 3
  botaniques + 3 écosystèmes
- **3 moteurs** : Evidence (Rust+PyO3), Knowledge (Python in-memory),
  GIS (placeholder)
- **11 endpoints** : auth (3), evidence (3), knowledge (5), gis (1)
- **Pipeline** : Evidence → Knowledge (tranche verticale)

### 2.2 Le gap

Le métamodèle v6.2 (RFC-0011, DEC-000022) définit **73 types noyau**
+ la table racine `resource` (ADR-001). L'API actuelle n'implémente
qu'environ 6 de ces types (via `KnowledgeObject` qui est supersédé par
`Assertion`). Le gap est structurel :

| Dimension | Métamodèle v6.2 | API actuelle | Écart |
|---|---|---|---|
| Types implémentés | 73 | ~6 | 67 manquants |
| Table racine `resource` | ADR-001 | Inexistante | Racine polymorphe absente |
| Modèle `Assertion` | Type 9 | `KnowledgeObject` (v6.1) | Migration breaking |
| Temporal Engine | Revision + Snapshot + ResourceDiff | `knowledge_history` | Bitemporel absent |
| PROV-O | Activity, ProvEntity, Agent, Source, Citation | Inexistant | Provenance absente |
| Observation/SOSA | 7 types | Inexistant | Modèle d'observation absent |
| Écologie | 8+ types | Inexistant | Cœur écologique absent |
| IA/ML | 7 types | Inexistant | Support modèles absent |
| Raisonnement | 6 types | Inexistant | Chaîne raisonnement absente |
| FAIR/RGPD | 7 types | Inexistant | Non conforme |
| WebSocket | Spécifié pour Hub | Inexistant | Hub déconnecté |
| SDK | 3 clients (Python, Kotlin, C++) | Aucun | Apps sans client |

### 2.3 Pourquoi une migration complète

Une migration incrémentale prolongerait l'incohérence entre le
métamodèle (référence) et l'API (implémentation). Chaque nouveau type
ajouté sans la racine `resource` créerait de la dette technique. La
migration complète aligne définitivement l'API sur le métamodèle et
évite le coût d'une double migration.

---

## 3. Architecture proposée

### 3.1 Table racine `resource` (ADR-001)

```sql
CREATE TABLE resource (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type        VARCHAR(50) NOT NULL,  -- 'assertion', 'observation', 'concept', etc.
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    gsie_id     VARCHAR(100) UNIQUE,   -- identifiant lisible (ex. "assertion:stress_hetre_2024")
    CONSTRAINT ck_resource_type CHECK (type IN (/* 73 valeurs */))
);
```

Tout type du métamodèle a une ligne dans `resource` avec son `id` et
son `type`. Les tables spécifiques (assertion, observation, concept,
etc.) référencent `resource.id` comme clé primaire ou étrangère.

### 3.2 Structure des modèles SQLAlchemy

```
src/gsie_api/infrastructure/models/
├── __init__.py              # registry — auto-enregistrement des 73 types
├── base.py                  # Resource base + TimestampMixin + mixins
├── enums.py                 # Tous les enums PostgreSQL (§3 du métamodèle)
├── provenance.py            # Types 1-8 : Entity, EntityAlias, Concept, ConceptVersion,
│                            #   Vocabulary, VocabularyRelease, ControlledTerm, Instance
├── assertion.py             # Types 9-13 : Assertion, AssertionParticipant,
│                            #   AssertionQualifier, Predicate, EvidenceAssessment
├── observation.py           # Types 14-19 : Observation, Result, Method, Instrument,
│                            #   Uncertainty, QualityAssessment
├── prov.py                  # Types 20-24 : Activity, ProvEntity, Agent, Source, Citation
├── spatial_temporal.py      # Types 25-28 : Unit, Place, TemporalContext, Media
├── temporal_engine.py       # Types 29-30, 61 : Revision, Snapshot, ResourceDiff
├── models_ai.py             # Types 31-36 : Model, ModelRun, ModelVersion, Dataset,
│                            #   Feature, FeatureSet (types 50-52 aussi)
├── ecology.py               # Types 43-49 : ScaleContext, Phenomenon, EcologicalProcess,
│                            #   RelationType, SamplingEvent, TraitDefinition, TraitValue
├── reasoning.py             # Types 53-60 : Question, Hypothesis, Decision, Recommendation,
│                            #   Scenario, Correlation, EcosystemService, Capability
├── governance.py            # Types 37-40, 42 : RightsStatement, AccessPolicy,
│                            #   SensitivityClassification, SpatialDisclosurePolicy, ConflictCluster
├── dynamics.py              # Types 66-73 : Flow, ConfidenceGraph, Goal, Constraint,
│                            #   KnowledgeLineage, Experiment, TerrainSession, EcologicalState
├── fair_rgpd.py             # Types 62-65 : Sample, Consent, DataSubject, PersistentIdentifier
└── inference.py             # Types 50-52 : Feature, FeatureSet, Inference (séparé pour clarté)
```

### 3.3 CRUD générique

Puisque tous les types héritent de `resource`, un **router générique**
gère le CRUD pour les 73 types :

```
GET    /api/v1/resources?type=assertion&paginate     # liste filtrée par type
POST   /api/v1/resources                              # créer (type dans le body)
GET    /api/v1/resources/{id}                         # détail
PUT    /api/v1/resources/{id}                         # mise à jour (crée une Revision)
DELETE /api/v1/resources/{id}                         # suppression (marque transaction_time_end)
GET    /api/v1/resources/{id}/revisions               # historique des révisions
GET    /api/v1/resources/{id}/snapshot                # snapshot à une date donnée
```

Les endpoints spécialisés par moteur s'ajoutent au-dessus :

```
POST   /api/v1/evidence/evaluate                      # existant — conserve
POST   /api/v1/knowledge/ingest                       # migré vers Assertion
POST   /api/v1/engines/correlation/detect             # nouveau
POST   /api/v1/engines/reasoning/infer                # nouveau
POST   /api/v1/engines/diagnostic/diagnose            # nouveau
POST   /api/v1/engines/recommendation/recommend       # nouveau
GET    /api/v1/engines/gis/wms                        # nouveau — WMS proxy
POST   /api/v1/engines/simulation/run                 # nouveau
```

### 3.4 WebSocket pour le Hub

```
WS     /api/v1/ws/hub                                  # canal temps réel Hub
WS     /api/v1/ws/events                               # events système (resource.created, etc.)
```

Le Hub (Unreal Engine 5.8) se connecte en WebSocket et reçoit :
- `resource.created` — nouvelle ressource (observation, assertion, etc.)
- `resource.updated` — ressource modifiée
- `phenomenon.detected` — phénomène écologique détecté
- `model.completed` — exécution de modèle terminée
- `recommendation.ready` — recommandation disponible
- `alert.fire_risk` — alerte risque incendie (Ignis)
- `alert.drought` — alerte sécheresse

Implémentation : Redis Pub/Sub → fan-out vers les clients WebSocket
connectés. Un client peut s'abonner à des canaux par type, par zone
géographique, ou par moteur.

### 3.5 SDK

Génération depuis le schéma OpenAPI de FastAPI :

| Client | Langage | Consommateur | Générateur |
|---|---|---|---|
| `gsie-sdk-python` | Python | Scripts, Forge, moteurs | `openapi-generator-cli` |
| `gsie-sdk-kotlin` | Kotlin | GeoSylva (Android) | `openapi-generator-cli` |
| `gsie-sdk-cpp` | C++ | Hub (Unreal Engine 5.8) | `openapi-generator-cli` ou manuel |

Les SDK sont générés dans `GSIE/SDK/` et versionnés avec l'API.

### 3.6 Migration des données existantes

La migration Alembic 0002 :

1. Crée la table `resource` et les 73 tables spécifiques
2. Migre `knowledge_objects` → `resource` + `assertion` (type=assertion)
3. Migre `knowledge_history` → `revision` (Temporal Engine)
4. Migre `knowledge_relations` → `predicate` + `assertion_participant`
5. Migre `knowledge_conflits` → `conflict_cluster` + table de jonction
6. Migre `botanical_*` → `concept` + `concept_version` + `vocabulary`
7. Migre `ecosystem_*` → `place` + `controlled_term`
8. Supprime les anciennes tables (après validation)

La migration est **réversible** (downgrade recrée l'ancien schéma).

---

## 4. Impact

### 4.1 Breaking changes

- `KnowledgeObject` → `Assertion` : tous les endpoints `/knowledge/*`
  changent de schéma de réponse
- `knowledge_objects` table → supprimée après migration
- Les seeds botaniques et écosystèmes doivent être re-chargés dans les
  nouvelles tables

### 4.2 Compatibilité

- L'endpoint `/evidence/evaluate` est conservé (pas de breaking change)
- L'auth JWT RS256 est conservée
- Les middlewares (TraceId, CORS, rate limiting) sont conservés
- Le pipeline Evidence → Knowledge devient Evidence → Assertion

### 4.3 Consommateurs impactés

| Consommateur | Impact | Mitigation |
|---|---|---|
| GeoSylva (Android) | SDK Kotlin requis | Génération `gsie-sdk-kotlin` |
| QGISIA (QGIS) | SDK Python requis | Génération `gsie-sdk-python` |
| Hub (UE5.8) | WebSocket + SDK C++ requis | WebSocket + `gsie-sdk-cpp` |
| Ignis | Endpoints phénomène/alerte requis | Router `/phenomena` + `/alerts` |
| Forge | SDK Python requis | `gsie-sdk-python` |

---

## 5. Plan d'implémentation

### Phase 1 — Fondation (cette session)

1. ADR-007 — architecture API v6.2
2. Table `resource` + base model + enums PostgreSQL
3. 73 modèles SQLAlchemy (groupés par domaine)
4. Migration Alembic 0002
5. Schemas Pydantic génériques + spécifiques
6. Router générique CRUD + endpoints spécialisés
7. WebSocket pour Hub
8. Tests

### Phase 2 — SDK (session suivante)

1. Génération OpenAPI
2. `gsie-sdk-python`
3. `gsie-sdk-kotlin` (pour GeoSylva)
4. `gsie-sdk-cpp` (pour Hub)

### Phase 3 — Moteurs (vagues suivantes)

Implémentation des 14 moteurs sur le nouveau schéma :
- Correlation Engine, Reasoning Engine, Diagnostic Engine,
  Recommendation Engine, Climate Engine, Pedology Engine,
  Botanical Engine, Forest Dynamics Engine, Learning Engine,
  Simulation Engine

---

## 6. Risques et mitigations

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Migration Alembic cassée | Moyenne | Élevé | Tests upgrade + downgrade sur DB de test |
| Performance 73 tables | Faible | Moyen | Index sur FK + `resource.type` + pagination |
| Trop d'endpoints à maintenir | Moyenne | Moyen | CRUD générique réduit le boilerplate à ~1 router |
| SDK généré incompatible | Faible | Moyen | Tests d'intégration SDK ↔ API |
| WebSocket scaling | Faible | Moyen | Redis Pub/Sub — scaling horizontal natif |

---

## 7. Décision demandée

Approuver la migration complète de l'API GSIE vers le métamodèle v6.2,
avec création de DEC-000023 et ADR-007.

---

## 8. Annexes

- `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md` — métamodèle v6.2 (73 types)
- `GSIE/ARCHITECTURE/ADR-001-racine-resource.md` — table racine resource
- `GSIE/ARCHITECTURE/ADR-002-pg-temporal.md` — Temporal & Provenance Engine
- `GSIE/ARCHITECTURE/ADR-007-api-v6.2.md` — architecture API v6.2 (à créer)

---

## 9. Amendement de cohérence avec ADR-004 (2026-07-16)

### Constat

RFC-0012 décrivait à l'origine une migration big bang (migration 0002
unique créant les 73 tables + migrant les données + supprimant les
anciennes tables). ADR-004 prescrivait parallèlement une migration
progressive en 4 étapes (0002-0005) avec rollback sûr à chaque étape.
Les deux documents coexistaient sans réconciliation.

### Décision

Le Fondateur tranche en faveur d'ADR-004 (migration progressive). La
migration 0002 actuelle (big bang) est marquée comme non exécutable
contre des données réelles et sera réécrite selon le plan suivant :

| Migration | Action | Rollback |
|---|---|---|
| 0002 | Créer `resource` + 73 tables v6.2 (vides) + index + enums | DROP tables v6.2 |
| 0003 | Copier données : knowledge_objects → resource + assertion + participants + qualifiers + evidence_assessment + citation. Mapper toutes les colonnes (titre, description, contenu, source, evidence_level). | DELETE FROM tables v6.2 (anciennes tables intactes) |
| 0004 | Bascule moteurs : repository PG sur schéma v6.2. Tests adaptés. | Repli sur store in-memory (feature flag) |
| 0005 | Supprimer anciennes tables après validation complète | Restaurer depuis backup |

### Tables à migrer (mapping complet)

| Table ancienne | Tables cibles v6.2 | Colonnes à mapper |
|---|---|---|
| knowledge_objects | resource + assertion + assertion_participant + assertion_qualifier + evidence_assessment + citation | connaissance_id, type, titre, description, domaine_scientifique, contenu, evidence_level, source, statut, version, date_integration, moteurs_consommateurs |
| knowledge_history | revision | connaissance_id, version, auteur, date_modification, description |
| knowledge_relations | predicate + assertion_participant | source_id, target_id, relation_type, poids |
| knowledge_conflits | conflict_cluster + assertion (conflit) | connaissance_id, source_a, source_b, description |
| knowledge_mots_cles | controlled_term + resource (tag) | connaissance_id, mot_cle |
| knowledge_domaines_validite | assertion_qualifier | connaissance_id, domaine |
| botanical_familles | resource + controlled_term (vocabulary) | nom_scientifique, nom_commun, source_reference |
| botanical_genres | resource + controlled_term (vocabulary) | nom_scientifique, nom_commun, famille_id |
| botanical_essences | resource + instance + controlled_term | nom_scientifique, nom_vernaculaire, famille_id, genre_id, description, source_reference |
| ecosystem_habitats | resource + place + controlled_term | code_eur28, nom_habitat, description, categorie, interet_patrimonial, source_reference, attributs |
| ecosystem_stations | resource + place + controlled_term | code_station, nom_station, description, coordonnees, altitude, exposition, source_reference |
| ecosystem_groupes_ecologiques | resource + controlled_term + assertion (relation) | nom_groupe, description, especes, habitats |

### Superseding

ADR-004 n'est pas supersédée — elle est confirmée. La section de
RFC-0012 qui décrivait le big bang est implicitement supersédée par
cet amendement.
