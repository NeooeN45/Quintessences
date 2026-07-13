# IGNIS-002 — Spécification non fonctionnelle Ignis

| Champ | Valeur |
|---|---|
| **Document** | IGNIS-002 |
| **Dossier** | 05_SPECIFICATIONS/IGNIS/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | CON-001, CON-004, CON-005, CON-007, CON-010 |
| **Constitutions liées** | Technique (T-2, T-8, T-10) |
| **Directives liées** | GSIE-DIR-0005, GSIE-DIR-0006 |
| **RFC de référence** | RFC-0004 (§8 garde-fous) |
| **Documents connexes** | `IGNIS_001_SPECIFICATION.md`, `HUB_001_SPECIFICATION.md`, `HUB_002_INTERFACE_CONTRACT.md` |

---

## 1. Objet

Spécification non fonctionnelle d'Ignis : performance, latence,
résilience, sécurité, interopérabilité, souveraineté, explicabilité.
Étend et quantifie les exigences IGNIS-NF-01 à NF-10 de la spec
fonctionnelle (IGNIS-001 §4).

---

## 2. Performance

### 2.1 Latence temps réel

| Flux | Cible | Source |
|---|---|---|
| Front de feu (ForeFire → Hub) | < 1s | Livrable 209, HUB-NF-10 |
| Hotspots FIRMS/VIIRS → Hub | < 30s | DS-024, FIRMS latency |
| Météo (vent, humidité) → Hub | < 5 min | DS-009, DS-010 |
| Position drones → Hub | < 1s (10 Hz) | Livrable 210, HUB-NF-10 |
| Périmètre brûlé (Sentinel-2) | < 24h (quotidien) | DS-023, EFFIS |

### 2.2 Débit

| Flux | Débit estimé | Canal |
|---|---|---|
| Front de feu | 1-10 messages/s selon granularité | WebSocket |
| Drones (télémétrie) | 10 Hz par drone × N drones | WebSocket |
| Vidéo drone | Flux séparé (RTSP/WebRTC) | Non-WebSocket |
| Hotspots | 1 message / 30s (batch) | WebSocket |

### 2.3 Capacité

| Ressource | Cible initiale | Justification |
|---|---|---|
| Drones simultanés | 10 | Estimation opérationnelle |
| Hotspots simultanés | 1 000 | Saison haute, multi-incendies |
| Tileset combustible | ~1 GB / département | LiDAR HD 3 strates, DS-002 |
| Scénarios simultanés | 5 | COS + adjoints |

---

## 3. Résilience et offline (T-10)

| ID | Exigence | Cible |
|---|---|---|
| IGNIS-NF-RES-01 | Reconnexion WebSocket automatique | < 5s, retry exponentiel |
| IGNIS-NF-RES-02 | Buffer dernières données connues | 5 min de données en mémoire |
| IGNIS-NF-RES-03 | Mode dégradé satellite coupé | Hotspots + météo indisponibles, front de feu continue sur dernière simulation |
| IGNIS-NF-RES-04 | Mode dégradé drone coupé | Positions figées, vidéo coupée, front de feu continue |
| IGNIS-NF-RES-05 | Persistance locale cache | Combustible + terrain en cache disque (3D Tiles) |

---

## 4. Sécurité

| ID | Exigence | Source |
|---|---|---|
| IGNIS-NF-SEC-01 | Authentification API GSIE (JWT, 15min access / 7d refresh) | Global rules §Security |
| IGNIS-NF-SEC-02 | Chiffrement TLS 1.3 sur tous les canaux | Standard |
| IGNIS-NF-SEC-03 | Rôles : COS (lecture + validation), télépilote (lecture + commande drone), lecteur (lecture seule) | RFC-0004 §8 |
| IGNIS-NF-SEC-04 | Audit trail : toute action journalisée (qui, quand, quoi, résultat) | CON-004 |
| IGNIS-NF-SEC-05 | RGPD : images drones floutées si individus identifiables, rétention < 30j | Standard RGPD |
| IGNIS-NF-SEC-06 | Pas de secret en clair dans le code ou les logs | Global rules |

---

## 5. Interopérabilité

| ID | Exigence | Standard |
|---|---|---|
| IGNIS-NF-INT-01 | Format géométrie temps réel | GeoJSON (RFC 7946) |
| IGNIS-NF-INT-02 | Format données volumineuses | 3D Tiles 1.1 (OGC) |
| IGNIS-NF-INT-03 | Transport temps réel | WebSocket (RFC 6455) |
| IGNIS-NF-INT-04 | SRS | EPSG:2154 (Lambert 93), EPSG:4326 (WGS84) |
| IGNIS-NF-INT-05 | API GSIE | Livrable 207 |
| IGNIS-NF-INT-06 | Contrat Hub | HUB-002 (couches ignis.*) |

---

## 6. Souveraineté et licences

| Donnée | Licence | Souveraineté |
|---|---|---|
| LiDAR HD IGN (DS-002) | Licence Ouverte 2.0 (etalab-2.0) | France ✅ |
| BD Forêt v2 (DS-001) | Licence Ouverte 2.0 | France ✅ |
| FIRMS/VIIRS (DS-024) | Domaine public (NASA) | USA, accès libre ✅ |
| EFFIS (DS-023) | CC-BY 4.0 (Commission EU) | EU ✅ |
| Météo-France (DS-009/010) | Conditions Météo-France | France ✅ |
| Prométhée (DS-022) | Licence Ouverte 2.0 | France ✅ |

> **Principe :** aucune donnée critique ne transite par un cloud
> non-souverain sans accord explicite (CON-008).

---

## 7. Explicabilité (CON-004)

| ID | Exigence | Source |
|---|---|---|
| IGNIS-NF-EXP-01 | Toute prédiction ForeFire tracée : source, version, paramètres, niveau de preuve | CON-005, livrable 306 |
| IGNIS-NF-EXP-02 | Toute action opérateur journalisée | CON-004 |
| IGNIS-NF-EXP-03 | Cause probable d'un incendie = hypothèse, jamais certitude | RFC-0004 §8.2 |
| IGNIS-NF-EXP-04 | Recommandations contournables par le COS | CON-001, RFC-0004 §8.4 |

---

## 8. Déconfliction et sécurité opérationnelle

| ID | Exigence | Source |
|---|---|---|
| IGNIS-NF-OPS-01 | Déconfliction drones : anti-collision, zones d'exclusion | Livrable 210 |
| IGNIS-NF-OPS-02 | Reprise manuelle obligatoire à tout moment | RFC-0004 §8.3 |
| IGNIS-NF-OPS-03 | Autonomie drone = navigation uniquement, pas de décision offensive | RFC-0004 §8.4 |
| IGNIS-NF-OPS-04 | Pas d'alerte population automatisée | RFC-0004 §8.2 |

---

## 9. Scalabilité

| Dimension | Cible initiale | Évolution |
|---|---|---|
| Incendies simultanés | 3 | 10+ (multi-régions) |
| Départements | 1 (pilote) | National (France métropole) |
| Archive post-saison | 1 saison | Historique complet (Prométhée DS-022) |

---

## 10. Critères d'acceptation

- [x] Latence temps réel quantifiée par flux
- [x] Capacité maximale estimée (drones, hotspots, tilesets)
- [x] Résilience et mode dégradé définis (T-10)
- [x] Sécurité : auth, chiffrement, rôles, audit, RGPD
- [x] Interopérabilité : standards, SRS, API, contrat Hub
- [x] Souveraineté : licences par dataset
- [x] Explicabilité : traçabilité, transparence (CON-004)
- [x] Garde-fous RFC-0004 §8 couverts
- [x] Scalabilité définie

---

> Statut : *Draft — spec non fonctionnelle Phase 3 (préparation Phase 4).
> À valider par le Fondateur. Aucun code métier (CON-003).*
