# Knowledge Engine

Moteur de **base de connaissances**.

## Périmètre

- Centraliser toutes les connaissances de GSIE
- Gérer les concepts, les relations et les ontologies
- Fournir les connaissances normalisées aux autres moteurs

## Entrées

Connaissances validées (par `EVIDENCE_ENGINE`).

## Sorties

Objets de connaissance normalisés.

## Frontières

- Source unique de vérité pour tous les moteurs de raisonnement
- Ne contient pas de logique d'inférence
- Ne valide pas lui-même les connaissances (rôle de `EVIDENCE_ENGINE`)

> Statut : *implémentation en cours (Phase 4)* — code livré, voir KNOWLEDGE_ENGINE.md et PROJECT_MEMORY.md

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/knowledge/router.py`

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/knowledge/status` | aucune | — | Statut du moteur (`router.py:47`) |
| GET | `/knowledge/version` | aucune | — | Version et backend (`router.py:58`) |
| POST | `/knowledge/ingest` | `engine:write` | `30/minute` | Ingère une connaissance qualifiée (statut `accepte` requis) dans le graphe (`router.py:71`) |
| POST | `/knowledge/query` | `engine:read` | `60/minute` | Interroge le graphe (par_concept/par_relation/par_domaine/par_essence/par_station), résultats paginés (`router.py:104`) |
| POST | `/knowledge/revise` | `engine:write` | `30/minute` | Révise une connaissance existante avec archivage de l'historique (CON-010) (`router.py:127`) |
| GET | `/knowledge/stats` | `engine:read` | — | Statistiques du graphe (nombre d'objets par type) (`router.py:162`) |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/knowledge/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `KnowledgeIngestRequest` | Entrée de `/knowledge/ingest` | `connaissance_id`, `contenu_normalise`, `type` (concept/relation/regle/seuil/modele/classification), `evidence_level`, `statut` |
| `KnowledgeObject` | Nœud du graphe (sortie principale) | `connaissance_id`, `type`, `domaine_scientifique`, `version`, `historique` (liste de `VersionEntry`), `relations` |
| `KnowledgeQuery` | Entrée de `/knowledge/query` | `type` (`QueryType`), `filtres` (dict libre), `evidence_min`, `page`, `page_size` |
| `KnowledgeQueryResult` | Sortie de `/knowledge/query` | `requete_id`, liste de `KnowledgeObject`, pagination |
| `KnowledgeRevisionRequest` | Entrée de `/knowledge/revise` | `connaissance_id`, champs modifiés, `justification`, `rfc_reference` |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/knowledge/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `KnowledgeEngineError` | Erreur générique du moteur (ex. connaissance déjà existante, statut ≠ `accepte`, aucun champ modifié en révision) | 400 |
| `KnowledgeNotFoundError` (hérite de `KnowledgeEngineError`) | Connaissance introuvable lors d'une révision | 404 |
| `TerritoireInconnuError` (hérite de `ValueError`) | Territoire référencé inconnu | non exposée directement par le router `/knowledge` |
| `SourceIncitableError` (hérite de `ValueError`) | Source non citable/incomplète | non exposée directement par le router `/knowledge` |

### 4. Dépendances

- **Amont (chaîne principale)** : `EVIDENCE_ENGINE` — seules les
  connaissances au statut `accepte` sont ingérées (pipeline
  `gsie_api.engines.pipeline`, DEC-000021).
- **Aval** : `CORRELATION_ENGINE`, `REASONING_ENGINE` et tous les moteurs
  de raisonnement — source unique de vérité pour les connaissances
  normalisées.
- **Clients API externes** : aucun.
- **Persistance** : PostgreSQL (aucune dépendance à un module Rust).
