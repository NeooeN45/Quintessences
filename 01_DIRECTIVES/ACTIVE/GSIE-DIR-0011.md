# ============================================================================
# GSIE KNOWLEDGE DIRECTIVE
# Directive ID : GSIE-DIR-0011
# Version : 1.0
# Statut : ACTIVE
# Priorité : CRITIQUE
# Classification : PHASE
# Auteur : Camille Perraudeau
# Date : 2026-07-13
# ============================================================================

# Titre : Lancement officiel de la Phase 4 — Implémentation

## Résumé exécutif

La Phase 4 « Implémentation » est officiellement lancée. Elle transforme
les fondations (Phase 1), l'architecture (Phase 2) et la base de
connaissances (Phase 3) en **code métier opérationnel** : les 14 moteurs
GSIE, l'API GSIE, le Hub (Centre de Commandement Unreal Engine 5.8) et
les applications clientes (GeoSylva, Ignis en priorité).

## Contexte

- **Phase 1 (Foundation)** : clôturée — 12 livrables Validated/Locked.
- **Phase 2 (Architecture)** : 12 livrables Draft (201-212), contrats
  d'interface définis (livrable 206).
- **Phase 3 (Connaissance)** : clôturée (DEC-000017) — 10 livrables
  Validated (301-310), base de connaissances structurée, 26 datasets
  catalogués, 25 connaissances validées.
- **Spécifications Phase 4** : 9 specs Draft produites (HUB-001/002/003,
  IGNIS-001/002/003, GEO-001/002/003) + plan `HUB_AND_APPS_PLAN.md`.
- **Bancs de validation** : ForeFire (propagation incendie), PX4 SITL
  (5 vols drone réussis) — validés en Phase 1/2, prêts pour intégration.

## Périmètre de la Phase 4

### 4.1 — Socle technique et API GSIE (P0, bloquant)

| Livrable | Description |
|---|---|
| 401 | API GSIE — implémentation REST/WebSocket (livrable 207) |
| 402 | Pipeline d'ingestion datasets (PDAL, GDAL, PostGIS) |
| 403 | Base de connaissances — implémentation (PostgreSQL + Neo4j + ES + Jena, livrable 309) |

### 4.2 — Moteurs GSIE (P0/P1)

| Livrable | Description |
|---|---|
| 410 | GIS Engine — ingestion LiDAR HD, MNT/MNS/MNH, vectorisation |
| 411 | Forest Dynamics Engine — segmentation (PyCrown/SegmentAnyTreeV2), dendrométrie |
| 412 | Climate Engine — ingestion Météo-France, FWI |
| 413 | Simulation Engine — ForeFire intégration, propagation |
| 414 | Botanical Engine — essences (BD Forêt + Crown-BERT) |
| 415 | Diagnostic Engine — diagnostics sylvicoles |
| 416 | Recommendation Engine — recommandations contournables |
| 417 | Evidence Engine — filtre amont, niveaux de preuve |
| 418 | Knowledge Engine — graphe de connaissances |
| 419 | Correlation Engine — corrélations multi-sources |
| 420 | Reasoning Engine — raisonnement multi-échelle |
| 421 | Validation Engine — validation sorties |
| 422 | Learning Engine — entraînement, datasets synthétiques |
| 423 | Pedology Engine — sols (Phase 4 tardive) |

### 4.3 — Hub (Centre de Commandement) (P0)

| Livrable | Description |
|---|---|
| 430 | Hub Unreal Engine 5.8 — socle Cesium + 3D Tiles |
| 431 | Hub — couches temps réel (WebSocket, Ignis) |
| 432 | Hub — couches statiques (REST, GeoSylva/Hydro/Flora/Artemis) |
| 433 | Hub — PCG végétation + Gaussian Splats |

### 4.4 — Applications clientes (P1)

| Livrable | Description |
|---|---|
| 440 | Ignis — implémentation (ForeFire + PX4 + GCS) |
| 441 | GeoSylva — implémentation (app Android + Hub) |
| 442 | Hydro — implémentation (Phase 4 tardive) |
| 443 | Flora — implémentation (Phase 4 tardive) |
| 444 | Artemis — implémentation (Phase 4 tardive) |

### 4.5 — Encyclopédie de l'Écosystème (P1, DEC-000012)

| Livrable | Description |
|---|---|
| 450 | Encyclopédie — implémentation (base graphe, pipelines, API) |

## Ordre de production

```
4.1 API GSIE (P0, bloquant)
  ↓
4.2 Moteurs (P0 : GIS, Forest Dyn., Climate, Simulation)
  ↓ (parallèle)
4.3 Hub (P0)     4.4 Ignis (P1)     4.4 GeoSylva (P1)
  ↓
4.2 Moteurs (P1 : Botanical, Diagnostic, Recommendation, Evidence, Knowledge...)
  ↓
4.4 Hydro/Flora/Artemis (P2)     4.5 Encyclopédie (P1)
```

## Garde-fous

1. **CON-001** : l'IA assiste, ne décide jamais. Toute décision
   opérationnelle reste humaine.
2. **CON-004** : toute sortie de moteur doit être explicable (source,
   niveau de preuve, traçabilité).
3. **CON-005** : toute donnée consommée doit être tracée (DS-xxx).
4. **CON-007** : modularité obligatoire — un moteur = une
   responsabilité, interfaces entre moteurs via contrats (livrable 206).
5. **CON-008** : souveraineté des données — pas de cloud non-souverain
   pour les données critiques sans accord explicite.
6. **RFC-0004 §8** : garde-fous Ignis (reprise manuelle, supervision
   humaine, autonomie = navigation uniquement).
7. **RFC-0003** : architecture distribuée offline-first (GeoSylva).
8. **Tests** : tout code doit être testé (global rules §Testing).
9. **Sécurité** : JWT, TLS 1.3, pas de secret en clair (global rules).
10. **Commits** : Conventional Commits, français, PRs focalisées.

## Critères de validation des livrables Phase 4

- Code implémente la spec correspondante (HUB-xxx, IGNIS-xxx, GEO-xxx)
- Tests passent (couverture ≥ 80% sur logique métier)
- API GSIE respectée (livrable 207)
- Contrat Hub respecté (HUB-002)
- Traçabilité datasets (CON-005)
- Garde-fous respectés (CON-001, CON-004, RFC-0004 §8)

---

> Statut : *ACTIVE — Phase 4 lancée par DEC-000017 le 2026-07-13.*
