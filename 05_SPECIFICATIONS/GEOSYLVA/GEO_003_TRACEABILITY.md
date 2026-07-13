# GEO-003 — Matrice de traçabilité GeoSylva

| Champ | Valeur |
|---|---|
| **Document** | GEO-003 |
| **Dossier** | 05_SPECIFICATIONS/GEOSYLVA/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | CON-004, CON-005 |
| **Documents connexes** | `GEO_001_SPECIFICATION.md`, `GEO_002_NON_FUNCTIONAL.md`, `HUB_002_INTERFACE_CONTRACT.md` |

---

## 1. Objet

Matrice complète de traçabilité GeoSylva : exigence → architecture →
dataset → moteur → ontologie → contrat Hub.

---

## 2. Matrice exigences fonctionnelles (GEO-F-01 à F-23)

| Exig. | Description | Arch. | Datasets | Moteur | Ontologie S-6 | Couche Hub |
|---|---|---|---|---|---|---|
| F-01 | LiDAR HD MNT/MNS/MNH | 212 | DS-002 | GIS | DOM-DEN | geosylva.pcg_vegetation |
| F-02 | Segmentation PyCrown→SegmentAnyTreeV2 | 212 | DS-002 | Forest Dyn. | DOM-DEN | geosylva.arbres |
| F-03 | Dendrométrie (hauteur, DBH, G, densité) | 212 | DS-002, DS-003 | Forest Dyn. | DOM-DEN | geosylva.arbres |
| F-04 | Essences (BD Forêt + Crown-BERT) | 212 | DS-001 | Botanical | DOM-ECO | geosylva.essences |
| F-05 | Cartographie peuplements | 212 | DS-001 | GIS | DOM-SYL | geosylva.peuplements |
| F-06 | Types de peuplement et structure | 212 | DS-001 | Forest Dyn. | DOM-SYL | geosylva.peuplements |
| F-07 | Cartes dendrométriques ONF 700 m² | 212 | DS-002 | Forest Dyn. | DOM-DEN | geosylva.peuplements |
| F-08 | Biomasse locale LiDAR HD | 212 | DS-002 | Forest Dyn. | DOM-DYN | geosylva.biomasse |
| F-09 | Biomasse spatiale GEDI + ESA | 212 | DS-025, DS-026 | Forest Dyn. | DOM-DYN | geosylva.biomasse |
| F-10 | Suivi changements inter-annuels | 212 | DS-026 | Forest Dyn. | DOM-DYN | geosylva.biomasse |
| F-11 | Diagnostic sylvicole | 201 | DS-001/002/003 | Diagnostic | DOM-SYL | geosylva.diagnostics |
| F-12 | Recommandations gestion | 201 | — | Recommendation | DOM-SYL | geosylva.recommandations |
| F-13 | Validation forestier (CON-001) | — | — | — | — | — |
| F-14 | Couches geosylva.* (HUB-002) | 211 | — | — | — | geosylva.* |
| F-15 | PCG végétation procédurale | 212 | DS-001/002 | — | DOM-ECO | geosylva.pcg_vegetation |
| F-16 | Gradient de fidélité | 212 | — | — | — | geosylva.* |
| F-17 | Gaussian Splats arbres remarquables | 211 | — | — | — | geosylva.pcg_vegetation |
| F-18 | Offline-first mobile (RFC-0003) | 201 | — | — | — | — |
| F-19 | Saisie inventaire terrain | — | — | — | DOM-DEN | — |
| F-20 | Sync différée | 201 | — | — | — | — |
| F-21 | GPS + cartographie embarquée | — | — | GIS | — | — |
| F-22 | État réel vs simulé (CON-010) | 212 | — | Simulation | — | simulated.geosylva.* |
| F-23 | Convention simulated. (HUB-002) | 211 | — | — | — | simulated.geosylva.* |

---

## 3. Matrice exigences non fonctionnelles (GEO-NF-01 à NF-12)

| Exig. | Description | Cible | Source | Loi |
|---|---|---|---|---|
| NF-01 | Performance mobile | Carte < 3s | apps/GeoSylva | T-2 |
| NF-02 | Performance Hub | 60 FPS orbite | HUB-NF-09 | T-2 |
| NF-03 | Segmentation PyCrown | < 30s / km² | Livrable 212 | — |
| NF-04 | Offline-first | Cache < 2 GB | RFC-0003 | T-10 |
| NF-05 | Sync différée | Au retour réseau | RFC-0003 | CON-010 |
| NF-06 | Sécurité (JWT, TLS) | Standard | Global rules | CON-004 |
| NF-07 | Interopérabilité | GeoJSON/3D Tiles | HUB-002 | CON-007 |
| NF-08 | Souveraineté | IGN/NASA/ESA | §7 licences | CON-008 |
| NF-09 | Explicabilité | Trace diagnostic | CON-004 | CON-004 |
| NF-10 | Scalabilité | 1 massif → national | — | — |
| NF-11 | Accessibilité mobile | Contrastes, gants | Standard | — |
| NF-12 | App Android existante | Kotlin, interop | apps/GeoSylva | — |

---

## 4. Matrice datasets → exigences

| Dataset | Exigences | Moteur | Statut |
|---|---|---|---|
| DS-001 BD Forêt v2 | F-04, F-05, F-06, F-07, F-11, F-15 | GIS, Forest Dyn. | Planifié |
| DS-002 LiDAR HD IGN | F-01, F-02, F-03, F-07, F-08, F-11, F-15 | GIS, Forest Dyn. | Planifié |
| DS-003 IFN | F-03, F-11 | Forest Dyn. | Planifié |
| DS-025 GEDI | F-09 | Forest Dyn. | Planifié |
| DS-026 ESA Biomass CCI | F-09, F-10 | Forest Dyn. | Planifié |

---

## 5. Matrice moteurs → exigences

| Moteur | Exigences GeoSylva | Datasets |
|---|---|---|
| GIS Engine | F-01, F-05, F-21 | DS-001, DS-002 |
| Forest Dynamics | F-02, F-03, F-06, F-07, F-08, F-09, F-10 | DS-001/002/003/025/026 |
| Botanical Engine | F-04 | DS-001 |
| Diagnostic Engine | F-11 | DS-001/002/003 |
| Recommendation Engine | F-12 | — |
| Simulation Engine | F-22 | — |

---

## 6. Matrice ontologie → exigences

| Domaine S-6 | Concepts clés | Exigences |
|---|---|---|
| DOM-ECO (écologie forestière) | Essence, station, bioclimat | F-04, F-15 |
| DOM-DEN (dendrométrie) | Hauteur, DBH, surface terrière, biomasse | F-01, F-02, F-03, F-07, F-08, F-19 |
| DOM-SYL (sylviculture) | Peuplement, traitement, diagnostic | F-05, F-06, F-11, F-12 |
| DOM-DYN (dynamique) | Croissance, changement, mortalité | F-08, F-09, F-10 |

---

## 7. Matrice couches Hub → exigences

| layer_id | Exigences | Canal | Fréquence |
|---|---|---|---|
| geosylva.peuplements | F-05, F-06, F-07 | REST (3D Tiles) | Statique |
| geosylva.arbres | F-02, F-03 | REST (GeoJSON) | Statique |
| geosylva.essences | F-04 | REST (3D Tiles) | Statique |
| geosylva.diagnostics | F-11 | REST (GeoJSON) | Quotidien |
| geosylva.recommandations | F-12 | REST (GeoJSON) | Quotidien |
| geosylva.biomasse | F-08, F-09, F-10 | REST (GeoTIFF) | Annuel |
| geosylva.pcg_vegetation | F-01, F-15, F-17 | REST (metadata) | Statique |
| simulated.geosylva.* | F-22, F-23 | REST | À la demande |

---

## 8. Matrice précédents opérationnels → exigences

| Précédent | Méthode | Exigence validée |
|---|---|---|
| ONF | LiDAR HD + terrain → cartes 700 m²/pixel (G, DBH, H, densité, structure) | F-07 |
| SDIS 63 | 3 strates végétation 3m résolution, continuité 0-3m, CCF | F-06 (partagé Ignis) |
| Arbonaut SaniLidar | LiDAR + ortho + terrain → stress hydrique par arbre | F-03, F-08 |

> Source : `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` §3.3

---

## 9. Critères d'acceptation

- [x] Toutes les exigences F-01 à F-23 tracées
- [x] Toutes les exigences NF-01 à NF-12 tracées
- [x] Tous les datasets cités (DS-001/002/003/025/026)
- [x] Tous les moteurs identifiés (GIS, Forest Dyn., Botanical, Diagnostic, Recommendation, Simulation)
- [x] Domaines ontologie S-6 mappés (DOM-ECO/DEN/SYL/DYN)
- [x] Couches Hub mappées (geosylva.* + simulated.)
- [x] Précédents opérationnels tracés (ONF, SDIS, Arbonaut)

---

> Statut : *Draft — matrice de traçabilité Phase 3. Aucun code (CON-003).*
