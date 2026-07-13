# IGNIS-003 — Matrice de traçabilité Ignis

| Champ | Valeur |
|---|---|
| **Document** | IGNIS-003 |
| **Dossier** | 05_SPECIFICATIONS/IGNIS/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | CON-004, CON-005 |
| **Documents connexes** | `IGNIS_001_SPECIFICATION.md`, `IGNIS_002_NON_FUNCTIONAL.md`, `HUB_002_INTERFACE_CONTRACT.md` |

---

## 1. Objet

Matrice complète de traçabilité : chaque exigence Ignis est tracée vers
son architecture, ses datasets, ses moteurs GSIE, ses idées registre, et
le contrat Hub.

---

## 2. Matrice exigences fonctionnelles (IGNIS-F-01 à F-26)

| Exigence | Description | Arch. | Datasets | Moteur | Registre | Couche Hub |
|---|---|---|---|---|---|---|
| F-01 | Hotspots FIRMS/VIIRS | 209 | DS-024 | — | P-01 | ignis.hotspots |
| F-02 | Périmètres brûlés EFFIS | 209 | DS-023 | Simulation | P-02 | ignis.perimetre_brule |
| F-03 | Historique Prométhée | 209 | DS-022 | Correlation | P-03 | — |
| F-04 | Détection multi-source | 209 | DS-023/024 | — | P-04 | ignis.hotspots |
| F-05 | LiDAR HD 3 strates | 212 | DS-002 | GIS | — | ignis.combustible |
| F-06 | Continuité 0-3m, CCF | 212 | DS-002 | Simulation | — | ignis.combustible |
| F-07 | BD Forêt type peuplement | 212 | DS-001 | GIS | — | ignis.combustible |
| F-08 | Vent Météo-France | 209 | DS-009 | Climate | — | ignis.meteo_vent |
| F-09 | Température + humidité | 209 | DS-009/010 | Climate | — | ignis.meteo_humidite |
| F-10 | FWI | 209 | DS-009 | Climate | — | — |
| F-11 | Simulation ForeFire | 208 | — | Simulation | J-01 | ignis.front_de_feu |
| F-12 | Mise à jour temps réel front | 208 | — | Simulation | J-02 | ignis.front_de_feu |
| F-13 | Scénarios hypothétiques | 208 | — | Simulation | J-03 | simulated.ignis.* |
| F-14 | Orchestration PX4 | 210 | — | — | V-01 | ignis.drones |
| F-15 | Pattern lawnmower | 210 | — | — | V-02 | ignis.drones |
| F-16 | Capture GPS + RTH | 210 | — | — | V-03 | ignis.drones |
| F-17 | Streaming vidéo/thermique | 210 | — | — | V-04 | — (RTSP) |
| F-18 | Front Niagara | 211 | — | — | G-06 | ignis.front_de_feu |
| F-19 | Hotspots/météo/drones Hub | 211 | — | — | G-07 | ignis.* |
| F-20 | Respect contrat HUB-002 | 211 | — | — | — | ignis.* |
| F-21 | Supervision humaine | 208 | — | — | S-06 | — |
| F-22 | Reprise manuelle | 208 | — | — | S-07 | — |
| F-23 | Pas commande sans COS | 208 | — | — | S-09 | — |
| F-24 | Journalisation actions | 208 | — | — | S-11 | — |
| F-25 | Données entraînement synthétiques | 208 | — | Learning | D-05 | — |
| F-26 | Capteurs simulés | 208 | — | — | D-08 | — |

---

## 3. Matrice exigences non fonctionnelles (IGNIS-NF-01 à NF-10)

| Exigence | Description | Cible | Source | Loi |
|---|---|---|---|---|
| NF-01 | Latence front feu | < 1s | Livrable 209 | T-8 |
| NF-02 | Performance Hub | 60 FPS orbite | HUB-NF-09 | T-2 |
| NF-03 | Temps réel WebSocket | < 1s | Livrable 211 §3 | T-8 |
| NF-04 | Offline / résilience | Buffer 5 min | T-10 | T-10 |
| NF-05 | Sécurité (auth, TLS) | JWT + TLS 1.3 | Global rules | CON-004 |
| NF-06 | Souveraineté données | IGN/NASA/EU | §6 licences | CON-008 |
| NF-07 | Interopérabilité | GeoJSON/3D Tiles | HUB-002 | CON-007 |
| NF-08 | Déconfliction drones | Anti-collision | Livrable 210 | RFC-0004 §8 |
| NF-09 | Explicabilité | Trace complète | CON-004 | CON-004 |
| NF-10 | RGPD | Images floutées, < 30j | Standard | — |

---

## 4. Matrice datasets → exigences

| Dataset | Exigences | Moteur | Statut |
|---|---|---|---|
| DS-001 BD Forêt v2 | F-07 | GIS | Planifié |
| DS-002 LiDAR HD IGN | F-05, F-06 | GIS, Simulation | Planifié |
| DS-009 ARPEGE/AROME | F-08, F-09, F-10 | Climate | Planifié (prioritaire) |
| DS-010 Météo-France obs | F-09 | Climate | Planifié |
| DS-022 Prométhée | F-03 | Correlation | Planifié |
| DS-023 EFFIS | F-02, F-04 | Simulation | Planifié |
| DS-024 FIRMS/VIIRS | F-01, F-04 | — | Planifié (prioritaire) |

---

## 5. Matrice moteurs → exigences

| Moteur | Exigences Ignis | Datasets |
|---|---|---|
| GIS Engine | F-05, F-07 | DS-001, DS-002 |
| Climate Engine | F-08, F-09, F-10 | DS-009, DS-010 |
| Simulation Engine | F-02, F-06, F-11, F-12, F-13 | DS-023 |
| Correlation Engine | F-03 | DS-022 |
| Learning Engine | F-25 | — |

---

## 6. Matrice idées registre → exigences

| Idée | Exigence | Statut |
|---|---|---|
| P-01 à P-04 | F-01 à F-04 | Planifiée |
| J-01 à J-03 | F-11 à F-13 | Banc WSL2 validé (ForeFire) |
| V-01 à V-04 | F-14 à F-17 | Banc WSL2 validé (PX4, 5 vols) |
| G-06, G-07 | F-18, F-19 | Architecture définie (211) |
| S-06, S-07, S-09, S-11 | F-21 à F-24 | Garde-fous RFC-0004 |
| D-05, D-08 | F-25, F-26 | Veille (FIRETWIN) |

---

## 7. Matrice couches Hub → exigences

| layer_id | Exigences | Canal | Fréquence |
|---|---|---|---|
| ignis.front_de_feu | F-11, F-12, F-18 | WebSocket | < 1s |
| ignis.hotspots | F-01, F-04 | WebSocket | < 30s |
| ignis.meteo_vent | F-08 | WebSocket | < 5 min |
| ignis.meteo_humidite | F-09 | WebSocket | < 5 min |
| ignis.combustible | F-05, F-06, F-07 | REST (3D Tiles) | Statique |
| ignis.drones | F-14, F-15, F-16 | WebSocket | < 1s (10 Hz) |
| ignis.propagation | F-12, F-13 | WebSocket | < 1s |
| ignis.perimetre_brule | F-02 | REST (GeoJSON) | Quotidien |
| simulated.ignis.* | F-13 | WebSocket | < 1s |

---

## 8. Couverture garde-fous RFC-0004 §8

| Garde-fou §8 | Exigence(s) | Vérification |
|---|---|---|
| §8.2 Cause = hypothèse | F-25, NF-09 | Libellé « hypothèse » dans l'UI |
| §8.3 Reprise manuelle | F-22, NF-08 | Bouton reprise toujours visible |
| §8.4 Supervision humaine | F-21, F-23 | Action critique désactivée sans COS |
| §8.2 Pas d'alerte population | NF-08 | Aucun module d'alerte publique |
| §8.4 Autonomie = navigation | F-14 | Drone = navigation uniquement |

---

## 9. Critères d'acceptation

- [x] Toutes les exigences F-01 à F-26 tracées
- [x] Toutes les exigences NF-01 à NF-10 tracées
- [x] Tous les datasets cités (DS-001/002/009/010/022/023/024)
- [x] Tous les moteurs identifiés (GIS, Climate, Simulation, Correlation, Learning)
- [x] Idées registre tracées (P/J/V/G/S/D)
- [x] Couches Hub mappées (ignis.* + simulated.)
- [x] Garde-fous RFC-0004 §8 couverts

---

> Statut : *Draft — matrice de traçabilité Phase 3. Aucun code (CON-003).*
