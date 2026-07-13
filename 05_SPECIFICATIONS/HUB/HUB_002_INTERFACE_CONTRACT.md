# HUB-002 — Contrat d'interface Hub ↔ Apps

| Champ | Valeur |
|---|---|
| **Document** | HUB-002 |
| **Dossier** | 05_SPECIFICATIONS/HUB/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-005 (traçabilité), GSIE-CON-007 (modularité) |
| **Constitutions liées** | Technique (T-2 interchangeabilité, T-8 traçabilité) |
| **Documents connexes** | `HUB_001_SPECIFICATION.md`, `HUB_AND_APPS_PLAN.md`, `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211), `GSIE/ARCHITECTURE/ENGINE_COMMUNICATION_PROTOCOL.md` (livrable 203) |

> Ce document définit le **contrat d'interface** entre le Centre de
> Commandement (Hub) et les applications clientes. Toute app qui souhaite
> exposer ses données dans le Hub doit respecter ce contrat. Aucun code
> métier (CON-003, Phase 3).

---

## 1. Principe

Le Hub est un **consommateur passif** : il ne demande pas de données,
il **s'abonne** aux flux publiés par les apps via l'API GSIE. Chaque app
publie ses sorties sous forme de **couches** géoréférencées. Le Hub
décide quelles couches afficher, à quelle opacité, dans quel ordre.

```
App (GeoSylva/Ignis/...) → API GSIE (livrable 207) → WebSocket/JSON → Hub
                                                              ou
App → API GSIE → HTTP REST (3D Tiles) → Hub
```

**Deux canaux :**
- **Temps réel** : WebSocket/JSON (positions, fronts, alertes, métriques)
- **Volumineux / statique** : HTTP REST → 3D Tiles / GeoJSON / GeoTIFF
  (terrain, peuplements, Gaussian Splats, réseaux)

---

## 2. Identifiant de couche

Chaque couche expose un identifiant stable et unique.

| Champ | Format | Exigence |
|---|---|---|
| `layer_id` | `<app>.<nom_couche>` (ex. `geosylva.peuplements`, `ignis.front_de_feu`) | Unique, stable, en snake_case |
| `app` | `geosylva` / `ignis` / `artemis` / `hydro` / `flora` | Un des 5 apps |
| `display_name` | Texte libre (FR) | Nom affiché dans l'UI du Hub |
| `description` | Texte libre (FR) | Description courte pour l'opérateur |

### Registre des couches (version initiale)

| `layer_id` | App | `display_name` | Canal | Fréquence |
|---|---|---|---|---|
| `geosylva.peuplements` | GeoSylva | Peuplements forestiers | REST (3D Tiles) | Statique |
| `geosylva.arbres` | GeoSylva | Arbres individuels | REST (GeoJSON) | Statique |
| `geosylva.essences` | GeoSylva | Essences dominantes | REST (3D Tiles) | Statique |
| `geosylva.diagnostics` | GeoSylva | Diagnostics sylvicoles | REST (GeoJSON) | Quotidien |
| `geosylva.recommandations` | GeoSylva | Recommandations | REST (GeoJSON) | Quotidien |
| `geosylva.biomasse` | GeoSylva | Biomasse (GEDI/ESA) | REST (GeoTIFF) | Annuel |
| `geosylva.pcg_vegetation` | GeoSylva | Végétation procédurale | REST (metadata) | Statique |
| `ignis.front_de_feu` | Ignis | Front de feu | WebSocket | Temps réel (< 1s) |
| `ignis.hotspots` | Ignis | Hotspots (FIRMS/VIIRS) | WebSocket | Temps réel (< 30s) |
| `ignis.meteo_vent` | Ignis | Vent (vecteurs) | WebSocket | Temps réel (< 5min) |
| `ignis.meteo_humidite` | Ignis | Humidité | WebSocket | Temps réel (< 5min) |
| `ignis.combustible` | Ignis | Combustible (3 strates) | REST (3D Tiles) | Statique |
| `ignis.drones` | Ignis | Positions drones | WebSocket | Temps réel (< 1s) |
| `ignis.propagation` | Ignis | Propagation prédite | WebSocket | Temps réel (< 1s) |
| `ignis.perimetre_brule` | Ignis | Périmètre brûlé | REST (GeoJSON) | Quotidien |
| `hydro.reseau` | Hydro | Réseau hydrographique | REST (3D Tiles) | Statique |
| `hydro.zones_humides` | Hydro | Zones humides | REST (GeoJSON) | Quotidien |
| `hydro.regimes` | Hydro | Régimes hydriques | REST (GeoTIFF) | Saisonnier |
| `flora.repartition` | Flora | Répartition floristique | REST (GeoJSON) | Saisonnier |
| `flora.phenologie` | Flora | Phénologie | REST (GeoTIFF) | Saisonnier |
| `artemis.observations` | Artemis | Observations faune | REST (GeoJSON) | Événementiel |
| `artemis.habitats` | Artemis | Habitats faune | REST (3D Tiles) | Statique |

---

## 3. Format de payload

### 3.1 Canal temps réel (WebSocket/JSON)

Chaque message WebSocket est un objet JSON avec les champs suivants :

```json
{
  "layer_id": "ignis.front_de_feu",
  "timestamp": "2026-07-13T14:30:00Z",
  "srs": "EPSG:2154",
  "geometry_type": "polygon",
  "features": [
    {
      "id": "front-001",
      "geometry": { "type": "Polygon", "coordinates": [[[...]]] },
      "properties": {
        "intensity": 0.75,
        "velocity": 1.2,
        "direction": 270,
        "confidence": "high",
        "source": "ForeFire",
        "evidence_level": "B"
      }
    }
  ],
  "metadata": {
    "source_engine": "Simulation Engine",
    "version": "2026-07-13T14:29:55Z",
    "knowledge_id": "GSIE-K-0000000123"
  }
}
```

| Champ | Type | Exigence |
|---|---|---|
| `layer_id` | string | Identifiant de couche (§2) |
| `timestamp` | ISO 8601 (UTC) | Date de production de la donnée |
| `srs` | string | Système de référence spatial (`EPSG:2154` Lambert 93, `EPSG:4326` WGS84) |
| `geometry_type` | string | `point` / `line` / `polygon` / `raster` / `point_cloud` / `gaussian_splat` |
| `features` | array | Liste de features GeoJSON (RFC 7946) |
| `features[].id` | string | Identifiant unique de la feature |
| `features[].geometry` | GeoJSON geometry | Géométrie au format RFC 7946 |
| `features[].properties` | object | Attributs spécifiques à la couche |
| `features[].properties.source` | string | Source de la donnée (CON-005) |
| `features[].properties.evidence_level` | string | Niveau de preuve A-F (livrable 306) |
| `metadata.source_engine` | string | Moteur GSIE producteur |
| `metadata.version` | ISO 8601 | Version de la donnée (CON-010) |
| `metadata.knowledge_id` | string | Identifiant GSIE-K si applicable |

### 3.2 Canal volumineux / statique (HTTP REST → 3D Tiles)

Pour les données volumineuses (terrain, peuplements, Gaussian Splats,
réseaux), l'app publie un **tileset 3D Tiles 1.1** accessible via URL.

| Champ | Format | Exigence |
|---|---|---|
| `tileset_url` | URL HTTP(S) | Point d'entrée du `tileset.json` (3D Tiles 1.1) |
| `srs` | string | SRS du tileset (généralement `EPSG:4978` WGS84 géocentrique) |
| `metadata_url` | URL HTTP(S) | URL des métadonnées JSON (source, licence, version) |
| `structural_metadata` | `EXT_structural_metadata` | Attributs requêtables au runtime (3D Tiles 1.1) |

### 3.3 Canal raster (HTTP REST → GeoTIFF)

Pour les rasters (biomasse, phénologie, régimes hydriques) :

| Champ | Format | Exigence |
|---|---|---|
| `raster_url` | URL HTTP(S) | GeoTIFF (COG de préférence) |
| `srs` | string | SRS du raster |
| `bands` | array | Description des bandes (nom, unité, type) |
| `metadata_url` | URL HTTP(S) | Métadonnées JSON |

---

## 4. Types de géométrie et mode de rendu

Le Hub détermine le mode de rendu à partir du `geometry_type` :

| `geometry_type` | Mode de rendu Hub | Exemples |
|---|---|---|
| `point` | Sprite / instanced mesh | Hotspots, observations faune, arbres |
| `line` | Mesh + matériau | Réseau hydro, trajectoires drones |
| `polygon` | Mesh + matériau (translucent possible) | Peuplements, périmètre brûlé, zones humides |
| `raster` | Texture sur terrain / draped | Biomasse, phénologie, régimes hydriques |
| `point_cloud` | Cesium point cloud tileset | LiDAR HD brut (si affiché) |
| `gaussian_splat` | Cesium Gaussian Splat tileset | Reconstruction drone (M-19) |
| `mesh_3dtiles` | Cesium 3D Tiles tileset | Photogrammétrie, bâtiments |

---

## 5. Métadonnées requises (CON-005)

Chaque couche doit exposer un document de métadonnées JSON à
l'URL `metadata_url` :

```json
{
  "layer_id": "ignis.front_de_feu",
  "app": "ignis",
  "producer_engine": "Simulation Engine",
  "source_datasets": ["DS-002", "DS-009", "DS-022"],
  "license": "Licence Ouverte 2.0 (etalab-2.0)",
  "evidence_framework": "GSIE/RESEARCH/EVIDENCE_FRAMEWORK.md",
  "update_frequency": "temps réel (< 1s)",
  "srs": "EPSG:2154",
  "quality": {
    "geometric_precision": "< 5m",
    "temporal_precision": "< 1s",
    "confidence_model": "ForeFire + Evidence Framework niveau B"
  },
  "contact": "GSIE — Simulation Engine",
  "version": "2026-07-13T14:29:55Z",
  "knowledge_ids": ["GSIE-K-0000000123"]
}
```

| Champ | Exigence | Loi |
|---|---|---|
| `source_datasets` | Liste des DS-xxx consommés | CON-005 |
| `license` | Licence effective | `19_LEGAL/` |
| `evidence_framework` | Référence au framework de preuve | CON-002, livrable 306 |
| `quality` | Indicateurs de qualité | CON-005 |
| `version` | Version datée | CON-010 |
| `knowledge_ids` | Identifiants GSIE-K liés | Livrable 302 |

---

## 6. Cycle de vie d'une couche

| État | Définition | Transition |
|---|---|---|
| `draft` | Couche déclarée mais données non publiées | → `active` quand les données sont disponibles |
| `active` | Couche publiée, le Hub peut s'y abonner | → `deprecated` quand remplacée |
| `deprecated` | Couche remplacée mais encore disponible | → `archived` après délai |
| `archived` | Couche retirée, plus accessible | Restauration par décision tracée |

> Toute transition d'état est journalisée (CON-010). Le Hub ne crash pas
> si une couche est indisponible — il affiche un avertissement.

---

## 7. Garde-fous

| Règle | Source | Sanction |
|---|---|---|
| Aucune couche sans `source_datasets` | CON-005 | Couche refusée par le Hub |
| Aucune couche sans `evidence_level` par feature | CON-002, livrable 306 | Feature marquée « non vérifiée » |
| Aucune action critique sans validation humaine | CON-001, RFC-0004 §8 | Bouton d'action désactivé par défaut |
| État réel et état simulé séparés | CON-010 | Préfixe `simulated.` dans le `layer_id` |
| Toute couche est modulaire et remplaçable | CON-007 | L'app peut être désactivée sans casser le Hub |

### Convention état réel vs simulé

| Type | Préfixe `layer_id` | Couleur Hub |
|---|---|---|
| État réel | `<app>.<couche>` | Couleurs naturelles |
| État simulé | `simulated.<app>.<couche>` | Teinte bleutée / hachurée |

Exemple : `ignis.front_de_feu` (réel) vs `simulated.ignis.front_de_feu`
(scénario vent 60 km/h).

---

## 8. Versionnement du contrat

| Version | Date | Changement |
|---|---|---|
| 1.0.0 | 2026-07-13 | Version initiale (Draft) |

> Toute modification du contrat (ajout de champ, changement de format)
> est versionnée ici et tracée dans `CHANGELOG.md`. Les apps doivent
> déclarer la version du contrat qu'elles supportent.

---

## 9. Critères d'acceptation

- [x] Identifiant de couche défini et registre initial établi (22 couches)
- [x] Format de payload temps réel (WebSocket/JSON) spécifié
- [x] Format de payload volumineux (3D Tiles, GeoTIFF) spécifié
- [x] Types de géométrie et modes de rendu mappés
- [x] Métadonnées requises définies (CON-005)
- [x] Cycle de vie d'une couche défini
- [x] Garde-fous constitutionnels respectés
- [x] Convention état réel vs simulé définie
- [x] Versionnement du contrat établi

---

> Statut : *Draft — contrat d'interface Phase 3 (préparation Phase 4).
> À valider par le Fondateur. Aucun code métier produit (CON-003).*
