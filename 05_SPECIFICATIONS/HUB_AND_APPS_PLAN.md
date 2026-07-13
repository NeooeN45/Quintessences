# Plan — Hub Centre de Commandement + Spécifications des apps

| Champ | Valeur |
|---|---|
| **Document** | HUB_AND_APPS_PLAN |
| **Dossier** | 05_SPECIFICATIONS/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft — plan de travail, à valider par le Fondateur |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-003 (connaissance avant code), GSIE-CON-007 (modularité) |
| **Directives liées** | GSIE-DIR-0005 (jumeau numérique vivant), GSIE-DIR-0009 (restructuration écosystème) |
| **Décisions liées** | DEC-000010 (UE 5.8 + Cesium), DEC-000013 (restructuration GSIE) |
| **Documents connexes** | `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (211), `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` (212), `GSIE/ARCHITECTURE/GSIE_IGNIS_ARCHITECTURE.md` (208), `ROADMAP.md` |

> **Rappel gouvernance :** le code métier reste interdit en Phase 3
> (CLAUDE.md §2.3). Ce plan prépare la **Phase 4 (Implémentation)** en
> structurant les spécifications du Hub et des apps prioritaires. Aucun
> code n'est produit ici — uniquement des spécifications fonctionnelles
> et non fonctionnelles, conformément au `05_SPECIFICATIONS/README.md`.

---

## 1. Vision d'ensemble

```
                    API GSIE (livrable 207)
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    Sorties GeoSylva  Sorties Ignis   Sorties Artemis
    Sorties Hydro     Sorties Flora
          │                │                │
          └────────────────┼────────────────┘
                           │
                    WebSocket / JSON
                           │
                           ▼
          ┌────────────────────────────────────┐
          │    HUB — CENTRE DE COMMANDEMENT      │
          │         (Unreal Engine 5.8)         │
          │                                     │
          │  Cesium for Unreal (globe 3D)       │
          │  ├── Couche forêt (GeoSylva)        │
          │  ├── Couche incendie (Ignis)        │
          │  ├── Couche faune (Artemis)         │
          │  ├── Couche eau (Hydro)             │
          │  └── Couche végétation (Flora)      │
          │  Niagara (effets feu/eau/fumée)     │
          │  PCG (génération procédurale forêt) │
          └────────────────────────────────────┘
```

Le **Hub** (Centre de Commandement) est la couche de visualisation
immersive qui surplombe toutes les apps. Il ne calcule rien — il
**reflète** l'état calculé par les moteurs GSIE (CON-007, ADR-001
livrable 208).

Les **apps** sont des clientes de GSIE qui exposent leurs données via
l'API GSIE (livrable 207). Le Hub consomme ces mêmes sorties validées.

---

## 2. Plan de production — ordre et priorités

### 2.1 Principe : le Hub d'abord, les apps ensuite

Le Hub est l'**infrastructure commune**. Si on spécifie les apps d'abord,
on risque de produire des silos incompatibles. En spécifiant le Hub
d'abord, on fixe le **contrat d'interface** (format de données, couches,
conventions géospatiales) auquel toutes les apps devront se conformer.

### 2.2 Ordre de production

| Étape | Livrable | Statut | Priorité |
|---|---|---|---|
| **1** | **Hub — Spécification du Centre de Commandement** | À créer | **P0 — bloquant** |
| 2 | **Ignis — Spécification fonctionnelle** | À créer | **P1 — priorité 1** (MVP visé) |
| 3 | **GeoSylva — Spécification fonctionnelle** | À créer | **P1 — priorité 1** (app principale) |
| 4 | Hydro — Spécification fonctionnelle | À créer | P2 |
| 5 | Flora — Spécification fonctionnelle | À créer | P2 |
| 6 | Artemis — Spécification fonctionnelle | À créer | P3 (stub Phase 4) |
| 7 | QGISIA — Spécification fonctionnelle | À créer | P3 (plugin QGIS, repo externe) |

> **Justification de l'ordre Ignis avant GeoSylva :** `DEC-000010` acte
> qu'Ignis (livrable 211) est priorité 1 avec MVP visé, et que
> GeoSylva-Unreal (livrable 212) est en **attente volontaire** jusqu'à
> ce que l'Ignis MVP soit fonctionnel (règle S-08). Les spécifications
> peuvent cependant être rédigées en parallèle — c'est le **code** qui
> attend.

---

## 3. Étape 1 — Spécification du Hub (Centre de Commandement)

### 3.1 Périmètre de la spécification

La spécification du Hub décrit **ce que le système doit faire**, pas
comment (rôle de l'architecture, déjà couvert par le livrable 211).

#### Spécifications fonctionnelles

| ID | Exigence | Source |
|---|---|---|
| HUB-F-01 | Le Hub doit afficher un globe 3D géoréférencé (WGS84) avec streaming de terrain et imagerie | Livrable 211 §2 (Cesium) |
| HUB-F-02 | Le Hub doit ingérer des données temps réel via WebSocket/JSON natif (C++) | Livrable 211 §3 |
| HUB-F-03 | Le Hub doit supporter l'activation/désactivation de couches par app (forêt, feu, faune, eau, flore) | Livrable 211 §0.3 |
| HUB-F-04 | Le Hub doit permettre le croisement visuel de couches de différentes apps dans la même scène 3D | Livrable 211 §0.3 |
| HUB-F-05 | Le Hub doit afficher des effets de feu/fumée/eau via Niagara, pilotés par les données du jumeau | Livrable 211 §4 |
| HUB-F-06 | Le Hub doit ingérer des Gaussian Splats géoréférencés via le pipeline Cesium ion (3D Tiles) | Livrable 211 §2 (validé avril 2026) |
| HUB-F-07 | Le Hub doit générer de la végétation procédurale pilotée par des couches scientifiques (PCG + landscape data layers) | Livrable 212 §4 |
| HUB-F-08 | Le Hub doit refléter l'état du jumeau numérique, jamais le calculer (client de visualisation uniquement) | ADR-001 livrable 208, CON-007 |
| HUB-F-09 | Le Hub doit séparer strictement l'état réel (source de vérité) de l'état simulé (scénario) | CON-010, livrable 212 §6 |
| HUB-F-10 | Le Hub doit permettre la navigation immersive (orbite, vol, marche) sur le globe et dans les scènes | Livrable 211 §0.3 |

#### Spécifications non fonctionnelles

| ID | Exigence | Source |
|---|---|---|
| HUB-NF-01 | Le Hub doit fonctionner sur Unreal Engine 5.8 (dernière version majeure UE5) | DEC-000010 |
| HUB-NF-02 | Le Hub doit utiliser Cesium for Unreal (plugin open source, Bentley Systems) comme socle géospatial | DEC-000010 |
| HUB-NF-03 | Le Hub doit être modulaire : architecture en plugins internes (CON-007), pas en monolithe | DEC-000010 §architecture partagée |
| HUB-NF-04 | Le Hub doit supporter World Partition + Data Layers pour le streaming de grands territoires | Recherche UE 5.8 |
| HUB-NF-05 | Le Hub ne doit pas dépendre de Mesh Terrain (experimental) ni PVE (bugs signalés) pour le MVP | Recherche UE 5.8 |
| HUB-NF-06 | Le Hub doit être interopérable avec l'API GSIE (livrable 207) via WebSocket/JSON | Livrable 211 §3 |
| HUB-NF-07 | Le Hub doit respecter les conventions de données françaises (Lambert 93, WGS84) | DEC-000010 |
| HUB-NF-08 | Le Hub ne doit jamais commander une action critique sans validation humaine (COS/forestier) | RFC-0004 §8, CON-001 |

#### Contrat d'interface Hub ↔ Apps

Le Hub consomme les sorties validées de chaque app via l'API GSIE. Chaque
app doit exposer :

| Champ | Format | Exigence |
|---|---|---|
| Identifiant de couche | `string` (ex. `geosylva.peuplements`, `ignis.front_de_feu`) | Unique par app |
| Type de géométrie | `point` / `line` / `polygon` / `raster` / `point_cloud` / `gaussian_splat` | Détermine le mode de rendu |
| SRS | `EPSG:XXXX` ou `WGS84` | Système de référence spatial |
| Format payload | GeoJSON / 3D Tiles / GeoTIFF / PLY | Standard ouvert |
| Fréquence de mise à jour | `temps réel` / `quotidien` / `statique` | Détermine WebSocket vs HTTP |
| Métadonnées | `EXT_structural_metadata` (3D Tiles 1.1) | Attributs requêtables au runtime |

### 3.2 Livrables de spécification du Hub

| # | Document | Dossier | Statut |
|---|---|---|---|
| HUB-001 | Spécification fonctionnelle du Centre de Commandement | `05_SPECIFICATIONS/HUB/` | À créer |
| HUB-002 | Contrat d'interface Hub ↔ Apps | `05_SPECIFICATIONS/HUB/` | À créer |
| HUB-003 | Spécification des couches (une fiche par app) | `05_SPECIFICATIONS/HUB/` | À créer |

---

## 4. Étape 2 — Spécification Ignis (priorité 1)

### 4.1 Périmètre

Ignis est le **premier cas d'usage** du Centre de Commandement — le plus
exigeant en temps réel. La spécification fonctionnelle décrit ce que
Ignis doit faire, en s'appuyant sur :

- `GSIE/ARCHITECTURE/GSIE_IGNIS_ARCHITECTURE.md` (livrable 208)
- `GSIE/ARCHITECTURE/GSIE_IGNIS_DATA_PIPELINE.md` (livrable 209)
- `GSIE/ARCHITECTURE/GSIE_IGNIS_DRONE_ARCHITECTURE.md` (livrable 210)
- `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211)
- `apps/Ignis/REGISTRE.md` (60+ idées, 9 sections)
- `02_RFC/RFC-0004.md` (garde-fous §8)

### 4.2 Spécifications fonctionnelles (structure)

| ID | Exigence | Source |
|---|---|---|
| IGNIS-F-01 | Ignis doit ingérer les données de combustible depuis LiDAR HD IGN (3 strates, continuité 0-3m) | DS-002, SDIS 63 |
| IGNIS-F-02 | Ignis doit ingérer les hotspots temps réel depuis FIRMS (MODIS/VIIRS) | DS-024 |
| IGNIS-F-03 | Ignis doit ingérer les périmètres brûlés depuis EFFIS (Sentinel-2) | DS-023 |
| IGNIS-F-04 | Ignis doit ingérer les données météo temps réel (vent, température, humidité) depuis Météo-France | DS-009, DS-010 |
| IGNIS-F-05 | Ignis doit simuler la propagation du feu (ForeFire ou équivalent) | Livrable 208, banc WSL2 |
| IGNIS-F-06 | Ignis doit afficher le front de feu en temps réel dans le Hub (Niagara) | Livrable 211 §4 |
| IGNIS-F-07 | Ignis doit orchestrer des drones de surveillance (PX4 SITL + Gazebo validés) | Livrable 210, banc WSL2 |
| IGNIS-F-08 | Ignis doit générer des données d'entraînement synthétiques (idée D-05) | Registre, FIRETWIN |
| IGNIS-F-09 | Ignis doit respecter les garde-fous RFC-0004 §8 (supervision humaine, reprise manuelle) | RFC-0004 |
| IGNIS-F-10 | Ignis doit exposer ses sorties via l'API GSIE au format contrat Hub ↔ Apps | HUB-002 |

### 4.3 Livrables de spécification Ignis

| # | Document | Dossier | Statut |
|---|---|---|---|
| IGNIS-001 | Spécification fonctionnelle Ignis | `05_SPECIFICATIONS/IGNIS/` | À créer |
| IGNIS-002 | Spécification non fonctionnelle Ignis (performance, latence, offline) | `05_SPECIFICATIONS/IGNIS/` | À créer |
| IGNIS-003 | Matrice de traçabilité exigence → moteur → dataset | `05_SPECIFICATIONS/IGNIS/` | À créer |

---

## 5. Étape 3 — Spécification GeoSylva (priorité 1)

### 5.1 Périmètre

GeoSylva est l'**application principale** de l'écosystème (forêt). La
spécification s'appuie sur :

- `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` (livrable 212)
- `apps/GeoSylva/` (repo externe, Android Kotlin — existant)
- `GSIE/KNOWLEDGE/FOREST_ONTOLOGY.md` (livrable 303)
- `GSIE/DATASETS/DATASET_CATALOG.md` (DS-001 à DS-026)

### 5.2 Spécifications fonctionnelles (structure)

| ID | Exigence | Source |
|---|---|---|
| GEO-F-01 | GeoSylva doit ingérer le LiDAR HD IGN (MNT, MNS, MNH) pour le terrain et la canopée | DS-002, livrable 212 §2 |
| GEO-F-02 | GeoSylva doit segmenter les arbres individuels (PyCrown puis SegmentAnyTreeV2) | Livrable 212 §3.2 |
| GEO-F-03 | GeoSylva doit identifier les essences (fusion LiDAR + hyperspectral, Crown-BERT) quand la donnée est disponible | Livrable 212 §3.2, Crown-BERT |
| GEO-F-04 | GeoSylva doit générer de la végétation procédurale pilotée par la science (PCG + landscape data layers) | Livrable 212 §4 |
| GEO-F-05 | GeoSylva doit appliquer le gradient de fidélité (contexte / procédural / haute fidélité) | Livrable 212 §1 |
| GEO-F-06 | GeoSylva doit séparer l'état réel (versionné) de l'état simulé (scénario) | CON-010, livrable 212 §6 |
| GEO-F-07 | GeoSylva doit ingérer BD Forêt v2 pour les essences dominantes et types de peuplement | DS-001 |
| GEO-F-08 | GeoSylva doit ingérer l'Inventaire Forestier National pour la calibration dendrométrique | DS-003 |
| GEO-F-09 | GeoSylva doit estimer la biomasse (LiDAR HD + GEDI + ESA Biomass CCI) | DS-002, DS-025, DS-026 |
| GEO-F-10 | GeoSylva doit exposer ses sorties via l'API GSIE au format contrat Hub ↔ Apps | HUB-002 |
| GEO-F-11 | GeoSylva (app Android) doit fonctionner offline-first sur le terrain | RFC-0003, apps/GeoSylva existant |
| GEO-F-12 | GeoSylva doit permettre la saisie d'inventaire terrain (mobile) avec synchronisation différée | apps/GeoSylva existant |

### 5.3 Livrables de spécification GeoSylva

| # | Document | Dossier | Statut |
|---|---|---|---|
| GEO-001 | Spécification fonctionnelle GeoSylva | `05_SPECIFICATIONS/GEOSYLVA/` | À créer |
| GEO-002 | Spécification non fonctionnelle GeoSylva (offline, performance mobile, sync) | `05_SPECIFICATIONS/GEOSYLVA/` | À créer |
| GEO-003 | Matrice de traçabilité exigence → moteur → dataset | `05_SPECIFICATIONS/GEOSYLVA/` | À créer |

---

## 6. Étapes 4-7 — Apps secondaires (P2/P3)

| App | Priorité | Périmètre Phase 4 | Statut |
|---|---|---|---|
| Hydro | P2 | Réseau hydrographique, zones humides, régimes hydriques (DS LiDAR HD hydrographie + inondation) | Stub → spec |
| Flora | P2 | Cartographie végétale, phénologie, répartition floristique (DS GBIF, Tela Botanica, BDNFF) | Stub → spec |
| Artemis | P3 | Habitats faune, observations, corrélations flore-faune (DS INPN) | Stub Phase 4 |
| QGISIA | P3 | Plugin QGIS (repo externe GitHub: NeooeN45/QGISIAPRO) | Existant → spec interface |

---

## 7. Dépendances et ordre critique

```
HUB-001 (spec Hub) ──► HUB-002 (contrat interface)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        IGNIS-001        GEO-001        (autres apps)
        IGNIS-002        GEO-002
        IGNIS-003        GEO-003
              │               │
              └───────┬───────┘
                      ▼
              HUB-003 (fiches couches)
                      │
                      ▼
              Phase 4 — Implémentation
```

> **Blocage :** HUB-001 et HUB-002 doivent être validés avant que les
> specs app ne soient finalisées, car le contrat d'interface fixe le
> format que toutes les apps doivent respecter.

---

## 8. Calendrier indicatif (Phase 3 → Phase 4)

| Période | Activité | Livrables |
|---|---|---|
| Phase 3 (courante) | Finaliser specs Hub + Ignis + GeoSylva | HUB-001/002/003, IGNIS-001/002/003, GEO-001/002/003 |
| Transition Phase 3 → 4 | Validation des specs par le Fondateur | Décision `DEC-` d'entrée en Phase 4 |
| Phase 4 — Sprint 1 | Prototype Hub (Cesium + WebSocket + globe) | Code (Phase 4 autorise le code métier) |
| Phase 4 — Sprint 2 | MVP Ignis (combustible + météo + propagation + Niagara) | Code |
| Phase 4 — Sprint 3 | GeoSylva-Unreal (LiDAR + PCG + segmentation) | Code |
| Phase 4 — Sprint 4+ | Apps secondaires | Code |

> **Rappel :** aucune estimation de durée n'est donnée (CLAUDE.md). Ce
> calendrier est **indicatif et ordonné**, pas daté.

---

## 9. Critères d'acceptation

Une spécification est considérée **complète** quand :

- [ ] Toutes les exigences fonctionnelles sont tracées vers un moteur
  GSIE et un dataset (`GSIE/DATASETS/`).
- [ ] Toutes les exigences non fonctionnelles sont quantifiées
  (performance, latence, offline, sécurité).
- [ ] Le contrat d'interface avec le Hub est défini (format, SRS,
  fréquence).
- [ ] Les garde-fous constitutionnels sont respectés (CON-001 décideur
  humain, CON-002 science, CON-007 modularité, RFC-0004 §8 pour Ignis).
- [ ] La matrice de traçabilité exigence → moteur → dataset est complète.

---

## 10. Prochaines actions immédiates

1. **Valider ce plan** par le Fondateur (Camille).
2. Créer `05_SPECIFICATIONS/HUB/HUB_001_SPECIFICATION.md` (spec
   fonctionnelle du Hub).
3. Créer `05_SPECIFICATIONS/HUB/HUB_002_INTERFACE_CONTRACT.md` (contrat
   d'interface Hub ↔ Apps).
4. Créer `05_SPECIFICATIONS/IGNIS/IGNIS_001_SPECIFICATION.md`.
5. Créer `05_SPECIFICATIONS/GEOSYLVA/GEO_001_SPECIFICATION.md`.

---

> Statut : *Draft — plan de travail Phase 3 (préparation Phase 4). À
> valider par le Fondateur avant exécution. Aucun code métier produit
> (CON-003).*
