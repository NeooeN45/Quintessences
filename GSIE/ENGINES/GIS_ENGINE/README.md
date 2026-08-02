# GIS Engine

Moteur de **données géospatiales**.

## Périmètre

- Gérer les données géospatiales (parcelles, stations, relief,
  hydrographie)
- Fournir des services de cartographie et d'analyse spatiale
- Calculer les caractéristiques stationnelles liées à la géographie
  (pente, exposition, altitude, distance)
- Intégrer les données IGN et autres sources géographiques officielles

## Principe fondamental

**Toute donnée géospatiale est sourcée et datée.** Les couches
cartographiques portent leur origine et leur date de mise à jour.

## Frontières

- Consomme les données de la `Spatial Database`
- Fournit des données géospatiales à `DIAGNOSTIC_ENGINE` et
  `CORRELATION_ENGINE`
- Mode hors-ligne : cache local des données de référence (article T-8)
- Ne produit pas de diagnostic — fournit des données

> Statut : *implémentation en cours (Phase 4)* — code livré, voir GIS_ENGINE.md et PROJECT_MEMORY.md

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/gis/router.py`. Périmètre v1
restreint à deux couches réelles (cadastre, altitude) — les autres
couches du contrat (mnt, pente, exposition, hydrographie, orthophoto,
sol) sont hors périmètre v1 (aucune donnée simulée, ADR-009).

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/gis/status` | aucune | — | Statut du moteur (`router.py:38`) |
| GET | `/gis/version` | aucune | — | Version et backend (`router.py:49`) |
| POST | `/gis/cadastre/parcelle` | `engine:write` | `30/minute` | Récupère et persiste une parcelle cadastrale (API Carto IGN) — `null` si non trouvée (`router.py:62`) |
| POST | `/gis/altitude` | `engine:read` | `60/minute` | Récupère l'altitude d'un point (API de calcul altimétrique IGN, RGE ALTI) (`router.py:94`) |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/gis/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `ParcelleCadastraleRequest` | Entrée de `/gis/cadastre/parcelle` | `code_insee`, `section`, `numero` |
| `AltitudeRequest` | Entrée de `/gis/altitude` | `latitude`, `longitude` (WGS 84) |
| `GeoLayer` | Une couche géospatiale | `nom` (`CoucheGeo`), `type` (raster/vecteur/mesure), `valeurs`, `source`, `date_maj` |
| `GeoData` | Sortie de `/gis/cadastre/parcelle` | `requete_id`, `place_id` (resource `place` persistée), `couches` (liste de `GeoLayer`) |
| `StationCharacteristics` | Sortie de `/gis/altitude` | caractéristiques stationnelles dérivées de l'altitude |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/gis/engine.py` et `ign_client.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `GISEngineError` | Erreur générique du moteur (échec de l'API altimétrique) | 502 |
| `IGNClientError` | API Carto IGN (cadastre) indisponible ou en erreur | 502 |

### 4. Dépendances

- **Amont** : `Spatial Database` (PostGIS).
- **Aval (chaîne principale)** : `DIAGNOSTIC_ENGINE`, `CORRELATION_ENGINE`.
- **Clients API externes** : IGN — API Carto (module Cadastre,
  `apicarto.ign.fr`) et API de calcul altimétrique (RGE ALTI,
  `data.geopf.fr`), via `gsie_api.engines.gis.ign_client`.
- **Persistance** : PostGIS (resource `place`).
