---
name: unreal-engine
description: Intégration Unreal Engine 5.8 + Cesium pour le Centre de Commandement GSIE
triggers:
  - user
  - model
---

# Centre de Commandement GSIE — Unreal Engine 5.8

## Environnement configuré

- **Projet UE** : `E:\GSIE-Centre-Commandement`
- **UE version** : 5.8.0
- **Cesium for Unreal** : v2.28.0 (globe 3D géoréférencé)
- **Unreal MCP** : v2.2.0 (pilotage IA éditeur via MCP)
- **Plugins natifs actifs** : GeoReferencing (PROJ/EPSG), Niagara, PythonScriptPlugin

## Architecture documentée

Voir `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211, v2.2.0).
Voir `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` (livrable 212, v1.1.0).

## Conventions de développement UE5.8

- **Blueprints** : pour la logique de présentation et les interactions UI
- **C++** : pour les systèmes de performance (streaming de données géo)
- **Python (PythonScriptPlugin)** : pour les scripts d'automatisation éditeur
- **Naming** : `BP_` pour Blueprints, `AC_` pour ActorComponents, `DT_` pour DataTables

## Intégration données géospatiales

```
Données IGN → PostGIS → API GSIE → Blueprint Data Table → Cesium Globe
LiDAR HD IGN → PDAL → Point Cloud → Unreal Point Cloud Plugin
```

- SRID de référence : WGS84 (EPSG:4326) côté données, converti en coordonnées Unreal via GeoReferencing plugin
- Zone de test Ignis : Landiras (Gironde) — config Cesium ion template existante

## Gaussian Splatting (DEC-000010 validé)

Technique validée pour la représentation forestière immersive. Pipeline :
```
Drone/LiDAR → Point Cloud → 3D Gaussian Splatting → Cesium Tileset → UE5.8
```

## Avant de modifier le projet UE

1. Lire `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` pour le contexte complet
2. Vérifier les plugins requis (voir §3 du doc)
3. Les plugins Fab (BlueprintWebSocket, FluidFlux) sont à installer manuellement
4. Tester dans la zone Landiras avant généralisation
