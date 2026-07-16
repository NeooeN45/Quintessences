# RFC-0013 — Ingestion des données forestières ONF/CNPF/IGN dans GSIE

| Champ | Valeur |
|---|---|
| **ID** | RFC-0013 |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-16 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Impact** | `GSIE/API/` (moteurs ingestion), `GSIE/DATASETS/` (catalogue), `GSIE/ENGINES/` (GIS, Botanical, Forest Dynamics, Pedology), `03_DECISIONS/`, `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md` |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-002 (science), GSIE-CON-005 (traçabilité), GSIE-CON-007 (modularité), GSIE-CON-010 (historique) |
| **Décision liée** | DEC-000024 (à créer) |
| **RFC liées** | RFC-0011 (métamodèle v6.2 — 76 types), RFC-0012 (migration API v6.2) |
| **ADR liés** | ADR-001 (racine resource), ADR-002 (Temporal Engine) |
| **Datasets liés** | DS-001 (BD Forêt v2), DS-002 (LiDAR HD), DS-003 (IFN), DS-005 (ONF RPF), DS-012 (RPFR), DS-011 (BDAT) |

---

## 1. Objet

Cette RFC propose l'**ingestion structurée des datasets forestiers
français** (ONF, CNPF, IGN, INRAE) dans l'API GSIE via le métamodèle
v6.2. L'objectif est de fournir aux moteurs GSIE (GIS, Botanical,
Forest Dynamics, Pedology) un flux d'ingestion reproductible, tracé et
validé pour les données de référence forestières françaises.

### Datasets concernés

| DS | Nom | Producteur | Format | Priorité |
|---|---|---|---|---|
| DS-001 | BD Forêt v2 | IGN | Shapefile/GeoPackage | P0 |
| DS-002 | LiDAR HD | IGN | LAZ 1.4, GeoTIFF | P1 |
| DS-003 | Inventaire Forestier National (IFN) | IGN | CSV tabulaire | P0 |
| DS-005 | Référentiel Pédologique Forestier (RPF) | ONF/INRAE | PDF, shapefile | P1 |
| DS-011 | BDAT (Analyses de Terre) | INRAE/GIS Sol | CSV | P2 |
| DS-012 | RPFR (Référentiel Pédologique Forestier Régional) | ONF/INRAE | PDF, shapefile | P2 |

### Catalogues stations forestières (CNPF)

Le CNPF (Centre National de la Propriété Forestière) publie les
**catalogues des stations forestières** (typologie des stations,
groupes écologiques, potentialités sylvicoles). Ces catalogues sont
essentiels pour :

- Le moteur **Pedology Engine** (typologie des sols forestiers)
- Le moteur **Forest Dynamics Engine** (potentialités sylvicoles)
- Le moteur **Botanical Engine** (groupes écologiques indicateurs)

Sources CNPF :
- Catalogues des types de stations (par région forestière)
- Guides de sylviculture par station (CNPF/IDF)
- Référentiel des essences adaptées par station

---

## 2. Contexte et motivation

### 2.1 État actuel

Le catalogue de datasets (`DATASET_CATALOG.md`) référence 29 datasets
(Phase 3, clôturée). Cependant, **aucun pipeline d'ingestion n'existe
encore** — les datasets sont documentés mais pas intégrés à l'API GSIE.

### 2.2 Motivation

L'ingestion de ces datasets est critique pour la Phase 4 car :

1. **BD Forêt v2** (DS-001) est la carte de référence des peuplements
   forestiers français — sans elle, le moteur Forest Dynamics ne peut
   pas initialiser ses simulations
2. **L'IFN** (DS-003) fournit les données dendrométriques (diamètres,
   hauteurs, volumes) qui calibrent les modèles de croissance
3. **Les catalogues stations CNPF** définissent les relations
   sol-station-peuplement qui pilotent les recommandations sylvicoles
4. **Le RPF/RPFR** (DS-005/DS-012) fournit les types de sols forestiers
   pour le moteur Pedology

### 2.3 Contraintes

- **Licences** : Licence Ouverte 2.0 (IGN, data.gouv.fr) pour la
  plupart ; accords spécifiques ONF/INRAE pour les données non
  publiques
- **Volume** : BD Forêt v2 ≈ 50 Go (France entière) ; LiDAR HD ≈ 30 To
- **Fréquence de mise à jour** : BD Forêt v2 (annuelle) ; IFN
  (continu, publication annuelle) ; LiDAR HD (campagnes 2024-2026)
- **Projections** : Lambert-93 (EPSG:2154) pour la métropole

---

## 3. Architecture d'ingestion proposée

### 3.1 Pipeline générique

```
Source (API/FTP/Shapefile)
  → Téléchargement (Forge/)
  → Validation (schéma, géométrie, CRS)
  → Transformation (mapping métamodèle v6.2)
  → Insertion API GSIE (POST /api/v1/resources)
  → Traçabilité (Revision v1, Provenance)
  → Indexation PostGIS
```

### 3.2 Mapping datasets → types métamodèle v6.2

| Dataset | Type(s) métamodèle | Table(s) cible(s) |
|---|---|---|
| BD Forêt v2 | `place`, `observation`, `concept` | `place`, `observation`, `concept` |
| IFN | `observation`, `result`, `entity` | `observation`, `result`, `entity` |
| RPF/RPFR | `concept`, `place`, `assertion` | `concept`, `place`, `assertion` |
| BDAT | `observation`, `result` | `observation`, `result` |
| Catalogues stations CNPF | `concept`, `assertion`, `place` | `concept`, `assertion`, `place` |
| LiDAR HD | `place`, `observation` | `place` (MNT/MNS/MNH), `observation` |

### 3.3 Module d'ingestion

Création d'un module `gsie_api.ingestion` avec :

```
gsie_api/ingestion/
├── __init__.py
├── base.py           # IngestionPipeline (classe abstraite)
├── bd_foret.py       # DS-001 — BD Forêt v2
├── ifn.py            # DS-003 — Inventaire Forestier National
├── rpf.py            # DS-005/DS-012 — RPF/RPFR
├── bdat.py           # DS-011 — BDAT
├── stations_cnpf.py  # Catalogues stations CNPF
├── lidar.py          # DS-002 — LiDAR HD (P1, post-Vague 2)
└── validators.py     # Validation géométrie, CRS, schéma
```

### 3.4 Endpoints API d'ingestion

```
POST /api/v1/ingestion/datasets/{ds_id}/run
  → Déclenche l'ingestion d'un dataset
  → Retourne un job_id (async, via Celery/worker)

GET /api/v1/ingestion/jobs/{job_id}
  → Statut du job (pending, running, completed, failed)

GET /api/v1/ingestion/datasets
  → Liste des datasets disponibles pour ingestion

GET /api/v1/ingestion/datasets/{ds_id}/status
  → Statut d'ingestion (dernier run, nombre de records, erreurs)
```

### 3.5 Traçabilité (CON-010)

Chaque record ingéré crée :
1. Une `resource` (table racine) avec `gsie_id` préfixé par le dataset
   (ex. `ds001:place:2026:abc123`)
2. Une `Revision` v1 avec justification `Ingestion DS-001 BD Forêt v2`
3. Un `Provenance` lié à l'`activity` d'ingestion (batch, date, source)

---

## 4. Plan d'implémentation

### Phase 1 — Vague 2 (P0, immédiat)

1. **Module `gsie_api.ingestion.base`** — pipeline abstrait
2. **DS-001 BD Forêt v2** — ingestion Shapefile → `place` + `observation`
3. **DS-003 IFN** — ingestion CSV → `observation` + `result` + `entity`
4. **Catalogues stations CNPF** — ingestion → `concept` + `assertion`
5. Tests unitaires (couverture 80%)
6. Endpoints API ingestion

### Phase 2 — Vague 3 (P1)

7. **DS-005 RPF / DS-012 RPFR** — ingestion → `concept` + `place` + `assertion`
8. **DS-011 BDAT** — ingestion CSV → `observation` + `result`
9. **DS-002 LiDAR HD** — ingestion LAZ/GeoTIFF → `place` (rasters)

### Phase 3 — Vague 4 (P2)

10. Monitoring ingestion (métriques, alertes)
11. Ingestion incrémentale (delta IFN annuel)
12. Cache Redis pour datasets fréquemment accédés

---

## 5. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| Volume BD Forêt v2 (50 Go) | OOM, timeout | Ingestion par batch (10 000 records), streaming |
| Qualité géométrique Shapefile | Géométries invalides | Validation PostGIS `ST_IsValid` avant insertion |
| Changements de schéma source | Mapping cassé | Tests de régression sur schéma source |
| Licences restrictives | Usage bloqué | Vérification licence avant ingestion (catalogue) |
| Projections multiples (Lambert-93, UTM) | Géométries décalées | Normalisation EPSG:2154 avant insertion |

---

## 6. Alternatives considérées

### 6.1 Ingestion manuelle (scripts ad hoc)

**Rejetée** — non reproductible, non tracée, non testée. Violation
CON-010 (traçabilité) et CON-005 (reproductibilité).

### 6.2 ETL externe (Apache Airflow, Prefect)

**Rejetée pour Vague 2** — ajoute une dépendance opérationnelle
complexe. L'ingestion est intégrée à l'API GSIE pour Vague 2.
Évaluation Airflow/Prefect possible en Vague 4 si le volume le
justifie.

### 6.3 Ingestion directe SQL (COPY, shp2pgsql)

**Rejetée** — contourne l'API GSIE, pas de traçabilité Revision, pas
de validation métier. Utilisable uniquement pour les benchmarks
initiaux (Forge/).

---

## 7. Conséquences

### 7.1 Positives

- Les moteurs GSIE disposent de données forestières réelles françaises
- Traçabilité complète (Provenance, Revision) pour chaque record
- Pipeline reproductible et testé
- Architecture extensible (nouveaux datasets ajoutés facilement)

### 7.2 Négatives

- Complexité supplémentaire (module ingestion + endpoints)
- Temps d'ingestion initial (BD Forêt v2 ≈ 2-4h sur machine de dev)
- Stockage PostgreSQL (estimation +20 Go pour P0)

### 7.3 Neutralisation des risques

- Tests de régression sur schéma source
- Monitoring ingestion (Phase 3)
- Rollback possible (soft-delete des resources ingérées)

---

## 8. Décision requise

**Décision** : Valider cette RFC et autoriser l'implémentation du
module `gsie_api.ingestion` en Vague 2 (P0 : BD Forêt v2, IFN,
catalogues stations CNPF).

**Décideur** : Camille Perraudeau (Fondateur)

---

## 9. Références

- `GSIE/DATASETS/DATASET_CATALOG.md` — catalogue des 29 datasets
- `GSIE/ARCHITECTURE/` — architecture GSIE
- `02_RFC/RFC-0011-metamodele-encyclopedie-v6.1.md` — métamodèle v6.2
- `02_RFC/RFC-0012-migration-api-v6.2.md` — migration API v6.2
- `00_CONSTITUTION/GSIE-CON-010.md` — traçabilité (append-only)
- `00_CONSTITUTION/GSIE-CON-005.md` — reproductibilité scientifique

---

## 10. Historique

| Date | Modification | Auteur |
|---|---|---|
| 2026-07-16 | Création — RFC-0013 Draft | Camille Perraudeau |
