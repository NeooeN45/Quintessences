# HUB-001 — Spécification fonctionnelle du Centre de Commandement GSIE

| Champ | Valeur |
|---|---|
| **Document** | HUB-001 |
| **Dossier** | 05_SPECIFICATIONS/HUB/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-001 (décideur humain), GSIE-CON-003 (connaissance avant code), GSIE-CON-007 (modularité) |
| **Constitutions liées** | Technique (T-2 interchangeabilité, T-8 traçabilité, T-10 offline) |
| **Directives liées** | GSIE-DIR-0005 (jumeau numérique vivant), GSIE-DIR-0009 (restructuration écosystème) |
| **Décisions liées** | DEC-000010 (UE 5.8 + Cesium), DEC-000013 (Centre de Commandement) |
| **Architecture de référence** | `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211) |
| **Documents connexes** | `HUB_002_INTERFACE_CONTRACT.md`, `HUB_AND_APPS_PLAN.md`, `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` (livrable 212) |

> Cette spécification décrit **ce que le Centre de Commandement doit
> faire**, pas comment (rôle de l'architecture, livrable 211). Aucun
> code métier n'est produit ici (CON-003, Phase 3).

---

## 1. Objet et périmètre

### 1.1 Définition

Le **Centre de Commandement GSIE** est la couche de visualisation
immersive de l'écosystème Quintessences. Construit sur Unreal Engine
5.8 + Cesium for Unreal, il affiche dans une scène 3D géoréférencée
unique les données produites par les 14 moteurs GSIE et exposées par
les applications clientes (GeoSylva, Ignis, Artemis, Hydro, Flora).

### 1.2 Principe fondamental

> **Le Centre de Commandement reflète l'état du jumeau numérique, il ne
> le calcule jamais.** (CON-007, ADR-001 livrable 208)

Toute logique métier (propagation du feu, segmentation d'arbres,
diagnostic sylvicole, corrélations) est calculée par les moteurs GSIE.
Le Hub est un **client de visualisation** qui consomme les sorties
validées via l'API GSIE (livrable 207).

### 1.3 Périmètre inclus

- Affichage 3D géoréférencé d'un globe terrestre (France + monde)
- Streaming de terrain, imagerie, photogrammétrie, Gaussian Splats
- Ingestion temps réel de données via WebSocket/JSON
- Activation/désactivation de couches par application
- Croisement visuel de couches multi-apps dans la même scène
- Effets visuels (feu, fumée, eau) via Niagara
- Génération procédurale de végétation pilotée par la science (PCG)
- Navigation immersive (orbite, vol, marche)
- Séparation état réel / état simulé (scénarios)

### 1.4 Périmètre exclu

- Calcul métier (propagation, segmentation, diagnostic) → moteurs GSIE
- Stockage persistant des données → API GSIE / base de connaissances
- Décision opérationnelle (COS, forestier) → CON-001, l'humain décide
- Commande directe d'acteurs physiques (drones, vannes) → apps dédiées
- Interface mobile terrain → apps mobiles (GeoSylva Android, etc.)

---

## 2. Acteurs et rôles

| Acteur | Rôle dans le Hub | Niveau d'interaction |
|---|---|---|
| **Opérateur Centre de Commandement** | Visualise l'état global, active/désactive les couches, lance des scénarios | Lecture + contrôle des couches |
| **COS (incendie)** | Supervise le suivi opérationnel Ignis, valide les actions | Lecture + validation (RFC-0004 §8) |
| **Forestier / sylviculteur** | Consulte les diagnostics GeoSylva, les recommandations | Lecture + annotation |
| **Chercheur** | Explore les corrélations, exporte des données pour publication | Lecture + export |
| **Décideur public** | Visualise les synthèses pour la communication institutionnelle | Lecture seule |
| **API GSIE** | Fournit les données au Hub (source de vérité) | Producteur |

---

## 3. Exigences fonctionnelles

### 3.1 Globe et terrain (HUB-F-01 à HUB-F-03)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| HUB-F-01 | Le Hub doit afficher un globe 3D géoréférencé (WGS84) avec streaming de terrain et imagerie par niveaux de détail (LOD) | P0 | Livrable 211 §2 |
| HUB-F-02 | Le Hub doit ingérer les données de terrain françaises (LiDAR HD IGN MNT/MNS/MNH, BD Ortho) comme couches 3D Tiles géoréférencées | P0 | DS-002, DS-004, livrable 211 §2 |
| HUB-F-03 | Le Hub doit supporter l'imagerie globale (Google 3D Tiles, Cesium World Terrain) comme contexte large avant zoom sur données haute résolution | P1 | Livrable 211 §2 |

### 3.2 Ingestion temps réel (HUB-F-04 à HUB-F-06)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| HUB-F-04 | Le Hub doit se connecter à l'API GSIE via WebSocket natif (C++ `FWebSocketsModule`/`IWebSocket` + module `Json`) pour recevoir les mises à jour temps réel | P0 | Livrable 211 §3 |
| HUB-F-05 | Le Hub doit supporter deux modes de mise à jour : temps réel (WebSocket, < 1s) et différé (HTTP REST, quotidien/à la demande) | P0 | Livrable 211 §3 |
| HUB-F-06 | Le Hub doit gérer la reconnexion automatique en cas de perte de connexion WebSocket, avec buffer des dernières données connues | P1 | T-10 (offline) |

### 3.3 Couches et multi-app (HUB-F-07 à HUB-F-10)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| HUB-F-07 | Le Hub doit gérer un système de couches activables/désactivables, une couche par app (forêt, feu, faune, eau, flore) | P0 | Livrable 211 §0.3 |
| HUB-F-08 | Le Hub doit permettre le croisement visuel de couches de différentes apps dans la même scène 3D (ex : couche forêt + couche incendie superposées) | P0 | Livrable 211 §0.3 |
| HUB-F-09 | Le Hub doit supporter l'opacité réglable par couche (pour permettre la superposition sans occlusion totale) | P1 | Standard visualisation |
| HUB-F-10 | Le Hub doit afficher les métadonnées d'un objet cliqué (source, date, niveau de preuve, identifiant GSIE) via `EXT_structural_metadata` (3D Tiles 1.1) | P1 | CON-005 (traçabilité) |

### 3.4 Effets visuels (HUB-F-11 à HUB-F-13)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| HUB-F-11 | Le Hub doit afficher des effets de feu et fumée via Niagara, pilotés par les données du jumeau (position du front, intensité, direction du vent) | P0 (Ignis) | Livrable 211 §4 |
| HUB-F-12 | Le Hub doit afficher des effets d'eau (écoulement, zones inondées) via Niagara, pilotés par les données Hydro | P2 | Extension 211 |
| HUB-F-13 | Le Hub doit synchroniser les effets Niagara avec les mises à jour temps réel (pas d'animation loop arbitraire — les données pilotent) | P0 | Livrable 211 §4, FIRETWIN |

### 3.5 Reconstruction 3D et Gaussian Splats (HUB-F-14 à HUB-F-16)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| HUB-F-14 | Le Hub doit ingérer des Gaussian Splats géoréférencés via le pipeline Cesium ion (3D Tiles, LOD hiérarchique) | P1 | Livrable 211 §2 (validé avril 2026) |
| HUB-F-15 | Le Hub doit ingérer de la photogrammétrie classique (mesh 3D Tiles) comme alternative aux Gaussian Splats | P2 | Livrable 211 §2 |
| HUB-F-16 | Le Hub doit permettre le passage progressif (fade) entre imagerie aérienne, photogrammétrie et Gaussian Splats sur un même secteur | P2 | Standard UX 3D |

### 3.6 Génération procédurale (HUB-F-17 à HUB-F-19)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| HUB-F-17 | Le Hub doit générer de la végétation procédurale pilotée par des couches scientifiques (PCG + landscape data layers) — essence, densité, hauteur | P1 (GeoSylva) | Livrable 212 §4 |
| HUB-F-18 | Le Hub doit appliquer un gradient de fidélité : contexte (imagerie) → procédural (PCG) → haute fidélité (Gaussian Splats par arbre) | P1 | Livrable 212 §1 |
| HUB-F-19 | Le Hub doit séparer l'état réel (versionné, source de vérité) de l'état simulé (scénario hypothétique) — couleurs ou calques distincts | P0 | CON-010, livrable 212 §6 |

### 3.7 Navigation et interaction (HUB-F-20 à HUB-F-23)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| HUB-F-20 | Le Hub doit supporter trois modes de navigation : orbite (globe), vol (traverse un massif), marche (niveau sol) | P0 | Standard 3D |
| HUB-F-21 | Le Hub doit permettre le zoom continu du globe (1:10M) au niveau sol (1:1) sans transition visible (LOD streaming) | P0 | Cesium 3D Tiles |
| HUB-F-22 | Le Hub doit permettre la sélection d'objets (clic → métadonnées) et la mesure de distances/surfaces | P1 | Standard GIS 3D |
| HUB-F-23 | Le Hub doit supporter le mode plein écran pour la projection en salle de commandement | P1 | Usage COS |

### 3.8 Sécurité et garde-fous (HUB-F-24 à HUB-F-26)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| HUB-F-24 | Le Hub ne doit jamais commander une action critique sans validation humaine explicite (COS/forestier) | P0 | RFC-0004 §8, CON-001 |
| HUB-F-25 | Le Hub doit distinguer visuellement les données validées (source officielle) des données en quarantaine (non vérifiées) | P1 | CON-005, DS quarantaine |
| HUB-F-26 | Le Hub doit journaliser toutes les actions de l'opérateur (activation couche, lancement scénario, export) pour traçabilité | P1 | CON-004 (explicabilité) |

---

## 4. Exigences non fonctionnelles

| ID | Exigence | Cible | Source |
|---|---|---|---|
| HUB-NF-01 | Moteur graphique | Unreal Engine 5.8 (dernière version majeure UE5) | DEC-000010 |
| HUB-NF-02 | Socle géospatial | Cesium for Unreal (plugin open source, Bentley Systems) | DEC-000010 |
| HUB-NF-03 | Architecture | Modulaire en plugins internes (CON-007), pas en monolithe | DEC-000010 |
| HUB-NF-04 | Streaming grands territoires | World Partition + Data Layers (UE 5.8) | Recherche UE 5.8 |
| HUB-NF-05 | Exclusions MVP | Pas de Mesh Terrain (experimental), pas de PVE (bugs signalés) | Recherche UE 5.8 |
| HUB-NF-06 | Interopérabilité | API GSIE (livrable 207) via WebSocket/JSON natif | Livrable 211 §3 |
| HUB-NF-07 | Systèmes de coordonnées | Lambert 93 (France métropole), WGS84 (global) | DEC-000010 |
| HUB-NF-08 | Supervision humaine | Toute action critique requiert validation humaine (CON-001) | RFC-0004 §8 |
| HUB-NF-09 | Performance cible | 60 FPS en orbite, 30 FPS en marche sol, sur GPU mid-range (RTX 4070) | Standard 3D temps réel |
| HUB-NF-10 | Latence ingestion | < 1s pour temps réel (WebSocket), < 5s pour différé (HTTP) | Livrable 211 §3 |
| HUB-NF-11 | Résilience | Reconnexion auto WebSocket, buffer dernières données, pas de crash sur perte de flux | T-10 (offline) |
| HUB-NF-12 | Accessibilité | Contrastes suffisants, tailles de texte configurables, navigation clavier | Standard accessibilité |
| HUB-NF-13 | Portabilité | Windows 11 (priorité), Linux (si UE 5.8 le supporte en production) | DEC-000010 |

---

## 5. Cas d'usage prioritaires

### 5.1 CU-01 — Surveillance incendie en temps réel (Ignis)

**Acteur :** COS (Commandant des Opérations de Secours)
**Scénario :**
1. Le COS ouvre le Hub en mode plein écran en salle de commandement.
2. La couche Ignis est active : front de feu (Niagara), hotspots (FIRMS),
   météo (vent, humidité), drones en vol.
3. Le COS visualise la propagation prédite (ForeFire) superposée au
   terrain LiDAR HD et à la végétation (combustible 3 strates).
4. Le COS lance un scénario « vent 60 km/h » — l'état simulé s'affiche
   en couleur distincte, l'état réel reste visible en transparence.
5. Le COS clique sur un hotspot → métadonnées (source FIRMS, timestamp,
   confiance, identifiant GSIE).
6. Le COS valide ou invalide une action recommandée (RFC-0004 §8).

### 5.2 CU-02 — Diagnostic sylvicole (GeoSylva)

**Acteur :** Forestier / sylviculteur
**Scénario :**
1. Le forestier navigue vers une parcelle (recherche ou coordonnées).
2. La couche GeoSylva est active : peuplements (BD Forêt), arbres
   individuels (segmentation LiDAR HD), essences, diagnostics.
3. Le forestier active la génération procédurale (PCG) — la végétation
   3D apparaît, pilotée par les couches scientifiques (essence, densité,
   hauteur).
4. Le forestier clique sur un arbre → métadonnées (essence, DBH,
   hauteur, biomasse, source, niveau de preuve).
5. Le forestier consulte les recommandations sylvicoles (moteur
   Recommendation) et les valide ou les rejette (CON-001).

### 5.3 CU-03 — Exploration recherche (multi-app)

**Acteur :** Chercheur
**Scénario :**
1. Le chercheur active les couches forêt (GeoSylva) + faune (Artemis) +
   eau (Hydro) sur un secteur.
2. Il visualise les corrélations (moteur Correlation) entre présence
   d'espèces, type de peuplement et régime hydrique.
3. Il exporte les données visualisées (JSON, GeoJSON) pour publication.

---

## 6. Couches du Hub (vue d'ensemble)

> Détail dans `HUB_003_LAYER_SHEETS.md` (à créer)

| Couche | App source | Type de géométrie | Fréquence | Mode de rendu |
|---|---|---|---|---|
| Terrain + imagerie | Cesium ion / IGN | Raster 3D Tiles | Statique | Cesium tileset |
| Peuplements | GeoSylva | Polygones | Statique | Mesh + matériau |
| Arbres individuels | GeoSylva | Points / instances | Statique | PCG + instanced meshes |
| Végétation procédurale | GeoSylva | Instances 3D | Statique | PCG (landscape data layers) |
| Gaussian Splats | GeoSylva / Ignis | Gaussian Splat 3D Tiles | Statique | Cesium GS tileset |
| Front de feu | Ignis | Polygones + particules | Temps réel (< 1s) | Niagara |
| Hotspots | Ignis | Points | Temps réel | Sprite / point cloud |
| Météo (vent) | Ignis | Vectors | Temps réel | Particules / flèches |
| Drones | Ignis | Points + trajectoires | Temps réel | Mesh + trail |
| Réseau hydro | Hydro | Lignes | Statique | Mesh + matériau |
| Zones humides | Hydro | Polygones | Quotidien | Mesh translucide |
| Observations faune | Artemis | Points | Événementiel | Sprite |
| Répartition flore | Flora | Polygones / points | Saisonnier | Mesh + couleur |

---

## 7. Matrice de traçabilité (exigence → source)

| Exigence | Architecture (livrable 211) | Dataset | Moteur GSIE | App |
|---|---|---|---|---|
| HUB-F-01 Globe 3D | §2 Cesium | — | GIS Engine | — |
| HUB-F-02 Terrain français | §2 Cesium | DS-002, DS-004 | GIS Engine | GeoSylva |
| HUB-F-04 WebSocket temps réel | §3 WebSockets natif | — | — | Ignis (priorité) |
| HUB-F-11 Feu Niagara | §4 Niagara | DS-022, DS-023, DS-024 | Simulation Engine | Ignis |
| HUB-F-14 Gaussian Splats | §2 (validé avril 2026) | — | — | GeoSylva, Ignis |
| HUB-F-17 PCG végétation | Livrable 212 §4 | DS-001, DS-002 | Forest Dynamics | GeoSylva |
| HUB-F-19 État réel vs simulé | Livrable 212 §6 | — | Simulation Engine | Toutes |

---

## 8. Critères d'acceptation

La spécification HUB-001 est considérée **complète** quand :

- [x] Toutes les exigences fonctionnelles sont tracées vers une source
  (architecture, dataset, moteur, app).
- [x] Toutes les exigences non fonctionnelles sont quantifiées
  (performance, latence, résilience).
- [x] Les cas d'usage prioritaires couvrent Ignis (P1) et GeoSylva (P1).
- [x] Les garde-fous constitutionnels sont respectés (CON-001, CON-005,
  CON-007, CON-010, RFC-0004 §8).
- [ ] Le contrat d'interface (HUB-002) est défini — **à produire**.
- [ ] Les fiches couches (HUB-003) sont définies — **à produire**.

---

## 9. Glossaire

| Terme | Définition |
|---|---|
| **Hub** | Centre de Commandement GSIE (Unreal Engine 5.8) |
| **Couche** | Ensemble de données géoréférencées d'une app, activable/désactivable |
| **État réel** | Données versionnées, source de vérité (ce qui s'est passé / ce qui est) |
| **État simulé** | Résultat d'un scénario hypothétique (ce qui pourrait se passer) |
| **3D Tiles** | Standard OGC pour le streaming de données 3D géoréférencées par LOD |
| **Gaussian Splat** | Représentation 3D par splats gaussiens (alternative à la photogrammétrie mesh) |
| **PCG** | Procedural Content Generation (système d'Unreal Engine pour la génération procédurale) |
| **Niagara** | Système de particules/fluides d'Unreal Engine |
| **Cesium ion** | Service cloud de Cesium pour le traitement et le streaming de données 3D |

---

> Statut : *Draft — spécification fonctionnelle Phase 3 (préparation
> Phase 4). À valider par le Fondateur. Aucun code métier produit
> (CON-003).*
