# Botanical Engine

Moteur de **flore, taxonomie et autécologie des espèces**.

## Périmètre

- Gérer la taxonomie et la nomenclature botanique (référentiels
  officiels : Tela Botanica, GBIF, BDNFF)
- Stocker les caractéristiques autécologiques de chaque essence
  (optimum, amplitude, exigences)
- Fournir les données d'identification et de classification
- Gérer les synonymes et les évolutions taxonomiques

## Principe fondamental

**Toute donnée botanique est sourcée et versionnée.** Les évolutions
taxonomiques sont tracées — un taxon peut changer de nom, mais
l'historique est conservé (CON-010).

## Frontières

- Consomme les données du `Species Repository` et de l'`Ontology`
- Fournit des données botaniques à `DIAGNOSTIC_ENGINE`,
  `CORRELATION_ENGINE` et `RECOMMENDATION_ENGINE`
- Ne produit pas de diagnostic — fournit des données taxonomiques et
  autécologiques

> Statut : *implémentation en cours (Phase 4)* — code livré, voir BOTANICAL_ENGINE.md et PROJECT_MEMORY.md

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/botanical/router.py`. Périmètre
v1 restreint à la taxonomie et à la nomenclature (pas d'autécologie,
`EspeceData.autecologie` reste `None` tant qu'aucune donnée sourcée
n'est ingérée — RFC-0016 tranche 1/10).

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/botanical/status` | aucune | — | Statut du moteur (`router.py:38`) |
| GET | `/botanical/version` | aucune | — | Version et backend (`router.py:49`) |
| POST | `/botanical/query` | `engine:write` | `30/minute` | Résout une essence vers son taxon accepté (GBIF Backbone Taxonomy) (`router.py:62`) |
| POST | `/botanical/indigenat` | `engine:read` | `30/minute` | Statut d'indigénat réel d'une essence pour une sylvoécorégion (dataset Bellifa et al., 2026) (`router.py:93`) |
| POST | `/botanical/taxref` | `engine:read` | `30/minute` | Résout un nom scientifique vers son entrée TAXREF (miroir GBIF) (`router.py:125`) |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/botanical/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `BotanicalQuery` | Entrée de `/botanical/query` | `type` (par_essence/par_taxon), `essence` (nom scientifique) |
| `EspeceData` | Élément de sortie | `gbif_taxon_key`, `nom_scientifique`, `synonymes`, `statut` (`TaxonStatus`), `autecologie` (toujours `None` en v1) |
| `BotanicalData` | Sortie de `/botanical/query` | liste de `EspeceData`, `source` |
| `IndigenatQuery`/`IndigenatResult` | Entrée/sortie `/botanical/indigenat` | taxon, code sylvoécorégion, statut d'indigénat |
| `TaxrefQuery`/`TaxrefResult` | Entrée/sortie `/botanical/taxref` | nom scientifique, `cd_nom` |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/botanical/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `BotanicalEngineError` | API GBIF/TAXREF indisponible, dataset local d'indigénat introuvable, ou valeur de statut inattendue | 502 (400 pour un statut inattendu dans le dataset d'indigénat) |

### 4. Dépendances

- **Amont** : `Species Repository`, `Ontology`.
- **Aval (chaîne principale)** : `DIAGNOSTIC_ENGINE`, `CORRELATION_ENGINE`,
  `RECOMMENDATION_ENGINE`.
- **Clients API externes** : GBIF Backbone Taxonomy (`gbif_client.py`),
  TAXREF via miroir GBIF (`taxref_client.py`), Treekipedia
  (`treekipedia_client.py`), Wikimédia (`wikimedia_client.py`), dataset
  local d'indigénat Bellifa et al. (2026, DOI 10.57745/DHJHGS,
  `indigenat_loader.py`).
- **Persistance** : PostgreSQL (resource `entity`, dédupliquée par clé GBIF).
