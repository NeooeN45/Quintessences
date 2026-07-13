# GEO-002 — Spécification non fonctionnelle GeoSylva

| Champ | Valeur |
|---|---|
| **Document** | GEO-002 |
| **Dossier** | 05_SPECIFICATIONS/GEOSYLVA/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | CON-001, CON-004, CON-005, CON-007, CON-010 |
| **Constitutions liées** | Technique (T-2, T-8, T-10) |
| **Directives liées** | GSIE-DIR-0007, GSIE-DIR-0009 |
| **RFC de référence** | RFC-0003 (offline-first) |
| **Documents connexes** | `GEO_001_SPECIFICATION.md`, `HUB_001_SPECIFICATION.md`, `HUB_002_INTERFACE_CONTRACT.md` |

---

## 1. Objet

Spécification non fonctionnelle de GeoSylva : performance, offline-first,
résilience, sécurité, interopérabilité, souveraineté, explicabilité,
accessibilité mobile. Étend GEO-NF-01 à NF-12 de la spec fonctionnelle.

---

## 2. Performance

### 2.1 App mobile Android

| Métrique | Cible | Source |
|---|---|---|
| Chargement carte | < 3s | apps/GeoSylva existant |
| Rendu 3D Hub (orbite) | 60 FPS (RTX 4070) | HUB-NF-09 |
| Rendu 3D Hub (marche sol) | 30 FPS (RTX 4070) | HUB-NF-09 |
| Segmentation PyCrown (1 km²) | < 30s | Livrable 212 §3.2 |
| Segmentation SegmentAnyTreeV2 (1 km²) | < 2 min (GPU) | Livrable 212 §3.2 |

### 2.2 Capacité

| Ressource | Cible | Justification |
|---|---|---|
| Tileset peuplements | ~500 MB / département | BD Forêt v2 (DS-001) |
| Arbres individuels / scène Hub | 100k | PCG instanced meshes |
| GeoTIFF biomasse | ~100 MB / département | GEDI + ESA CCI (DS-025/026) |
| Gaussian Splats parcelle | ~50 MB / parcelle | Reconstruction drone |

---

## 3. Offline-first (RFC-0003)

| ID | Exigence | Cible |
|---|---|---|
| GEO-NF-OFF-01 | Cache local mobile (cartes, inventaires, GPS) | < 2 GB pour un massif |
| GEO-NF-OFF-02 | Synchronisation différée | Au retour réseau, conflits résolus par version (CON-010) |
| GEO-NF-OFF-03 | Conflits de sync | Dernière version gagne + notification forestier |
| GEO-NF-OFF-04 | GPS embarqué | Précision < 5m (GPS Android + correction si dispo) |

---

## 4. Résilience

| ID | Exigence | Cible |
|---|---|---|
| GEO-NF-RES-01 | Reconnexion API GSIE | < 5s, retry exponentiel |
| GEO-NF-RES-02 | Mode dégradé LiDAR partiel | Zones ZICAD (nodata) affichées en gris |
| GEO-NF-RES-03 | Persistance locale | Cache disque 3D Tiles + GeoJSON |

---

## 5. Sécurité

| ID | Exigence | Source |
|---|---|---|
| GEO-NF-SEC-01 | Authentification JWT (15min access / 7d refresh) | Global rules |
| GEO-NF-SEC-02 | Chiffrement TLS 1.3 | Standard |
| GEO-NF-SEC-03 | Rôles : forestier (lecture + saisie), ONF (lecture + gestion), chercheur (lecture + export), public (lecture synthèses) | CON-001 |
| GEO-NF-SEC-04 | RGPD : géolocalisation forestier anonymisée, photos terrain sans individus | Standard |
| GEO-NF-SEC-05 | Pas de secret en clair | Global rules |

---

## 6. Interopérabilité

| ID | Exigence | Standard |
|---|---|---|
| GEO-NF-INT-01 | Géométrie temps réel | GeoJSON (RFC 7946) |
| GEO-NF-INT-02 | Données volumineuses | 3D Tiles 1.1 (OGC) |
| GEO-NF-INT-03 | Nuages de points | LAZ/LAS (ASPRS) |
| GEO-NF-INT-04 | Rasters | GeoTIFF COG |
| GEO-NF-INT-05 | SRS | EPSG:2154, EPSG:4326 |
| GEO-NF-INT-06 | API GSIE | Livrable 207 |
| GEO-NF-INT-07 | Contrat Hub | HUB-002 (couches geosylva.*) |
| GEO-NF-INT-08 | App Android existante | Kotlin, offline, interopérable via API GSIE |

---

## 7. Souveraineté et licences

| Donnée | Licence | Souveraineté |
|---|---|---|
| LiDAR HD IGN (DS-002) | Licence Ouverte 2.0 | France ✅ |
| BD Forêt v2 (DS-001) | Licence Ouverte 2.0 | France ✅ |
| IFN (DS-003) | Licence Ouverte 2.0 | France ✅ |
| GEDI (DS-025) | Domaine public (NASA) | USA, libre ✅ |
| ESA Biomass CCI (DS-026) | CC-BY 4.0 (ESA) | EU ✅ |

---

## 8. Explicabilité (CON-004)

| ID | Exigence | Source |
|---|---|---|
| GEO-NF-EXP-01 | Diagnostic tracé : moteur → source → niveau de preuve | CON-005, livrable 306 |
| GEO-NF-EXP-02 | Recommandation contournable par le forestier | CON-001 |
| GEO-NF-EXP-03 | Journalisation des actions (saisie, validation, export) | CON-004 |

---

## 9. Scalabilité

| Dimension | Cible initiale | Évolution |
|---|---|---|
| Massifs | 1 (pilote) | National |
| Départements | 1 | France métropole + Corse |
| Archive historique | IFN (DS-003) | Séries longues 1958-présent |

---

## 10. Accessibilité mobile

| ID | Exigence | Source |
|---|---|---|
| GEO-NF-ACC-01 | Contrastes suffisants (usage en forêt, lumière forte) | Standard |
| GEO-NF-ACC-02 | Tailles de texte configurables | Standard |
| GEO-NF-ACC-03 | Navigation par gestes (usage avec gants) | UX terrain |
| GEO-NF-ACC-04 | Résistant à la pluie (écran tactile sous gouttes) | UX terrain |

---

## 11. Critères d'acceptation

- [x] Performance quantifiée (mobile + Hub + segmentation)
- [x] Offline-first défini (RFC-0003, cache < 2 GB)
- [x] Résilience et mode dégradé (ZICAD)
- [x] Sécurité : auth, TLS, rôles, RGPD
- [x] Interopérabilité : standards, SRS, API, contrat Hub, app Android
- [x] Souveraineté : licences par dataset
- [x] Explicabilité : traçabilité diagnostics (CON-004)
- [x] Scalabilité définie
- [x] Accessibilité mobile (terrain)

---

> Statut : *Draft — spec non fonctionnelle Phase 3. Aucun code (CON-003).*
