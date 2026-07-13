# IGNIS-001 — Spécification fonctionnelle Ignis

| Champ | Valeur |
|---|---|
| **Document** | IGNIS-001 |
| **Dossier** | 05_SPECIFICATIONS/IGNIS/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-001 (décideur humain), GSIE-CON-003 (connaissance avant code), GSIE-CON-004 (explicabilité), GSIE-CON-005 (traçabilité), GSIE-CON-007 (modularité), GSIE-CON-010 (versionnement) |
| **Constitutions liées** | Technique (T-2 interchangeabilité, T-8 traçabilité, T-10 offline) |
| **Directives liées** | GSIE-DIR-0005 (jumeau numérique vivant), GSIE-DIR-0006 (moteur cognitif), GSIE-DIR-0009 (restructuration écosystème) |
| **Décisions liées** | DEC-000003 (adoption RFC-0004 + garde-fous), DEC-000010 (UE 5.8 + Cesium), DEC-000013 (Centre de Commandement) |
| **RFC de référence** | RFC-0004 (Ignis, §8 garde-fous — ADOPTÉ) |
| **Architecture de référence** | `GSIE/ARCHITECTURE/IGNIS_ARCHITECTURE.md` (livrable 208), `GSIE/ARCHITECTURE/IGNIS_DATA_PIPELINE.md` (livrable 209), `GSIE/ARCHITECTURE/IGNIS_DRONE_ARCHITECTURE.md` (livrable 210), `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211) |
| **Documents connexes** | `HUB_001_SPECIFICATION.md`, `HUB_002_INTERFACE_CONTRACT.md`, `apps/Ignis/REGISTRE.md` (registre d'idées v0.7.3), `GSIE/DATASETS/DATASET_CATALOG.md` |

> Cette spécification décrit **ce que Ignis doit faire**, pas comment
> (rôle de l'architecture, livrables 208–210). Aucun code métier n'est
> produit ici (CON-003, Phase 3). Les identifiants d'idées du registre
> (P-xx, J-xx, V-xx, C-xx, G-xx, D-xx, S-xx, M-xx) et de datasets
> (DS-xxx) sont cités pour assurer la traçabilité (CON-005, T-8).

---

## 1. Objet et périmètre

### 1.1 Définition

**Ignis** est un système autonome de surveillance et d'analyse des
incendies de forêt, application cliente de l'écosystème GSIE. Il fournit
au COS (Commandant des Opérations de Secours) et au CODIS une aide à la
décision fondée sur un jumeau numérique vivant du feu, alimenté par des
drones autonomes, des satellites libres et des données open data
françaises.

Ignis n'est ni un moteur central GSIE, ni un système de commandement
(DEC-000003, RFC-0004 §4, Option C hybride). Il sollicite les 14 moteurs
GSIE via leurs interfaces documentées et publie ses sorties vers le
Centre de Commandement (Hub) selon le contrat d'interface HUB-002.

### 1.2 Principe fondamental

> **Ignis construit un jumeau numérique vivant des opérations de lutte
> contre les incendies.** (GSIE-DIR-0005)

Le terrain devient l'interface. Toutes les données — observations,
prédictions, enjeux, moyens, météo — se projettent dans un même espace
géographique. Le moteur 3D (Unreal Engine 5.8 + Cesium for Unreal) est
interchangeable : aucune logique métier ne vit dans le client 3D
(ADR-001, livrable 208). L'intelligence reste dans le serveur Ignis ;
le rendu n'est qu'une fenêtre ouverte sur cette intelligence.

Le système ne répond jamais « cela arrivera ». Il répond « voici les
scénarios les plus probables » avec un niveau de confiance, une
justification et les observations utilisées (GSIE-CON-004, livrable 208
§2ter.6).

### 1.3 Périmètre inclus

- Détection précoce multi-source (satellite + drone + capteurs sol)
- Caractérisation du combustible et du terrain (LiDAR HD, BD Forêt)
- Ingestion météo temps réel (vent, température, humidité, FWI)
- Simulation de propagation (ForeFire) avec assimilation temps réel
- Scénarios hypothétiques de propagation (ensembles probabilistes)
- Surveillance par drones autonomes (PX4, missions, streaming)
- Analyse d'enjeux (intersection propagation × bâtiments/infrastructures)
- Visualisation dans le Centre de Commandement (couches `ignis.*`)
- Carte de risque dynamique pré-feu (horizonte horaire)
- Génération de données synthétiques pour l'entraînement (FIRETWIN)
- Validation post-feu et RETEX automatique

### 1.4 Périmètre exclu

- **Commande directe des pompiers** — Ignis est un outil d'aide à la
  décision, jamais un système de commandement (GSIE-CON-001, RFC-0004
  §8.4, DEC-000003)
- **Décision COS** — le COS décide, Ignis recommande (GSIE-CON-001)
- **Alerte directe à la population** — prérogative régalienne FR-Alert
  (RFC-0004 §8, G-04, S-06)
- **Retransmission sur fréquences ANTARES** — régalien, interdit. On
  visualise, on ne relaie pas (V-07, S-06)
- **Largage / action physique par drone** — écarté (S-09, reporté)
- **Attribution de cause du feu comme conclusion** — la cause probable
  reste une hypothèse exploratoire, jamais une conclusion juridiquement
  contraignante (RFC-0004 §8.2, DEC-000003)
- **App mobile pompiers terrain** — hors périmètre Ignis (interface
  COS/CODIS via GCS-Lite et Centre de Commandement)

---

## 2. Acteurs et rôles

| Acteur | Rôle dans Ignis | Niveau d'interaction |
|---|---|---|
| **COS (Commandant des Opérations de Secours)** | Supervise le suivi opérationnel, valide les actions, reçoit les recommandations tactiques | Lecture + validation (RFC-0004 §8) |
| **CODIS** | Coordination départementale, reçoit les prédictions et l'analyse d'enjeux | Lecture + validation |
| **Télépilote drone** | Définit les missions, reprend la main en cas de besoin (V-04), supervise les vols | Contrôle vol + reprise manuelle |
| **Opérateur GCS-Lite** | Visualise le front, les drones, les détections en temps réel ; clique carte → dispatch drone (G-02) | Lecture + contrôle des missions |
| **Forestier / DFCI** | Consulte la carte de risque dynamique pré-feu, les données combustible | Lecture + annotation |
| **Chercheur** | Valide les modèles sur feux historiques, exporte pour publication | Lecture + export + RETEX |
| **API GSIE** | Fournit les données aux moteurs et au Hub (source de vérité) | Producteur |
| **Drones PX4** | Exécutent les missions de surveillance, capturent les observations | Acteur physique (edge) |

---

## 3. Exigences fonctionnelles

### 3.1 Détection et surveillance (IGNIS-F-01 à IGNIS-F-04)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| IGNIS-F-01 | Ignis doit ingérer les hotspots FIRMS/VIIRS (détections thermiques satellitaires quasi temps réel, API gratuite, latence ~3 h) comme pré-alerte large échelle et corroboration des détections drone | P0 | DS-024, J-08, D-11 |
| IGNIS-F-02 | Ignis doit ingérer les périmètres brûlés EFFIS (recensement satellitaire temps réel des feux UE, danger prévisionnel) comme cadre européen et vérité terrain de validation | P1 | DS-023, D-10, J-08 |
| IGNIS-F-03 | Ignis doit ingérer l'historique Prométhée/BDIFF (base officielle des incendies de forêt en France depuis 2006, causes renseignées) comme colonne vertébrale des feux historiques pour le RETEX et l'apprentissage continu | P1 | DS-022, D-08, J-10 |
| IGNIS-F-04 | Ignis doit assurer une détection active multi-source fusionnant satellite (FIRMS, MTG-FCI), drone (RGB, thermique) et capteurs sol (CO/CO₂, particules) — aucune source unique, consensus probabiliste | P0 | J-08, P-01, P-03, P-07, livrable 208 §2ter.1 |

### 3.2 Combustible et terrain (IGNIS-F-05 à IGNIS-F-07)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| IGNIS-F-05 | Ignis doit ingérer le LiDAR HD IGN en 3 strates (MNT, MNS, MNH) comme couches 3D Tiles géoréférencées pour le terrain et la structure de canopée | P0 | DS-002, J-01, livrable 209 §4.5.1 |
| IGNIS-F-06 | Ignis doit caractériser le combustible (continuité verticale 0–3 m, accessibilité CCF) à partir du LiDAR HD et de BD Forêt v2 — cas d'usage SDIS 63 (Puy-de-Dôme) | P1 | DS-002, DS-001, P-05, J-05 |
| IGNIS-F-07 | Ignis doit ingérer BD Forêt v2 (IGN) pour le type de peuplement et la correspondance avec les modèles de combustible (Rothermel/Balbi) calibrés pour la France | P1 | DS-001, J-01, livrable 208 §5.1 (Botanical Engine) |

### 3.3 Météo temps réel (IGNIS-F-08 à IGNIS-F-10)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| IGNIS-F-08 | Ignis doit ingérer le vent (direction + force) depuis les modèles AROME/ARPEGE de Météo-France, avec descente d'échelle possible (CorrDiff) pour le vent sur relief français — le vent local étant le paramètre n°1 de la propagation | P0 | DS-009, J-01, M-09, M-12, livrable 208 §5.1 (Climate Engine) |
| IGNIS-F-09 | Ignis doit ingérer la température et l'humidité depuis Météo-France (modèles + observations sol) pour alimenter la carte de risque dynamique pré-feu et les paramètres ForeFire | P0 | DS-009, DS-010, J-09, livrable 209 §4.5.1 |
| IGNIS-F-10 | Ignis doit intégrer le Fire Weather Index (FWI) si disponible, comme indicateur composite de danger météorologique | P2 | DS-009, J-09 |

### 3.4 Propagation (IGNIS-F-11 à IGNIS-F-13)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| IGNIS-F-11 | Ignis doit simuler la propagation du feu avec ForeFire (ou équivalent) — banc WSL2 validé, 1 000 ha en < 10 s à résolution métrique — comme service séparé (frontière de processus GPL) | P0 | J-01, J-03, livrable 208 §3.1, DEC-000005 |
| IGNIS-F-12 | Ignis doit mettre à jour le front de feu en temps réel via la boucle d'assimilation (prédiction → observation drone → recalage, cycle ~5 min) avec filtre de Kalman d'ensemble ou particulaire | P0 | J-03, J-04, livrable 209 §4.1 |
| IGNIS-F-13 | Ignis doit supporter les scénarios hypothétiques de propagation (vent 60 km/h, changement de combustible, sautes de feu) avec ensembles probabilistes (10–50 scénarios par cycle) — l'état simulé est distingué de l'état réel (préfixe `simulated.`) | P1 | J-02, J-11, CON-010, HUB-002 §7, livrable 209 §4.3 |

### 3.5 Drones (IGNIS-F-14 à IGNIS-F-17)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| IGNIS-F-14 | Ignis doit orchestrer les drones via PX4 SITL + Gazebo (banc WSL2, 5 vols validés) puis PX4 réel (Jetson) — plans de vol auto, décollage/atterrissage auto, fail-safe, RTH | P0 | V-01, V-04, livrable 210 §3.1, DEC-000005 |
| IGNIS-F-15 | Ignis doit supporter le pattern de surveillance lawnmower (patrouille autonome sur un massif selon un plan de vol prédéfini) pour la détection de départs de feu | P0 | V-05, livrable 210 §4.1 |
| IGNIS-F-16 | Ignis doit assurer la capture GPS et le retour RTH (Return To Home) automatique à 25–30 % de batterie, avec reprise manuelle par télépilote à tout moment (V-04, exigence réglementaire) | P0 | V-04, livrable 210 §6.1 |
| IGNIS-F-17 | Ignis doit supporter le streaming vidéo RGB et thermique depuis le drone, avec inférence embarquée YOLO quantisé (détection fumée/flamme, > 30 FPS sur Jetson) et VLM (description structurée de scène) | P1 | P-01, P-02, P-03, livrable 210 §3.3–3.4 |

### 3.6 Visualisation Hub (IGNIS-F-18 à IGNIS-F-20)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| IGNIS-F-18 | Ignis doit publier le front de feu vers le Hub via la couche `ignis.front_de_feu` (WebSocket, temps réel < 1 s), avec effets Niagara pilotés par les données du jumeau (position, intensité, direction du vent) | P0 | HUB-F-11, HUB-002 §2, G-06, J-07, livrable 211 §4 |
| IGNIS-F-19 | Ignis doit publier les hotspots, la météo (vent, humidité) et les positions drones en temps réel vers le Hub selon les couches définies dans le contrat HUB-002 | P0 | HUB-002 §2 (registre des couches ignis.*), J-08, C-01 |
| IGNIS-F-20 | Ignis doit respecter le contrat d'interface HUB-002 pour toutes les couches `ignis.*` : format de payload WebSocket/JSON, métadonnées requises (CON-005), `evidence_level` par feature, `source_datasets` listés | P0 | HUB-002 §3–5, CON-005, CON-002 |

### 3.7 Garde-fous (IGNIS-F-21 à IGNIS-F-24)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| IGNIS-F-21 | Ignis doit garantir la supervision humaine de toutes les actions — le système recommande, le COS décide. Aucune action critique sans validation humaine explicite (COS/télépilote) | P0 | RFC-0004 §8, GSIE-CON-001, DEC-000003, G-04 |
| IGNIS-F-22 | Ignis doit assurer la reprise manuelle obligatoire par télépilote à tout moment (V-04) — l'autonomie du drone couvre uniquement la navigation, jamais les décisions opérationnelles | P0 | RFC-0004 §8.3, V-04, livrable 208 §7.4 |
| IGNIS-F-23 | Ignis ne doit jamais commander d'action critique sans validation COS — aucune alerte population (FR-Alert = régalien), aucune attribution de cause comme conclusion, aucune action physique par drone | P0 | RFC-0004 §8.2/§8.4, G-04, S-06, S-09 |
| IGNIS-F-24 | Ignis doit journaliser toutes les actions (décisions COS horodatées, observations, prédictions, recalages) pour le RETEX automatique et la validation continue des modèles (boîte noire du front) | P0 | J-10, S-07, CON-010, livrable 209 §5 |

### 3.8 Génération données synthétiques (IGNIS-F-25 à IGNIS-F-26)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| IGNIS-F-25 | Ignis doit générer des données d'entraînement synthétiques annotées par le simulateur (Unreal/Niagara géoréférencé) — milliers d'images aériennes de feu avec vérité terrain automatique (angles, lumières, végétations, fumées variés). Entraînement mixte synthétique + réel validé par la recherche (FIRETWIN) | P1 | D-05, G-06, livrable 211 §4 (FIRETWIN) |
| IGNIS-F-26 | Ignis doit simuler les capteurs drone (RGB, thermique, profondeur) dans le banc Gazebo pour valider les détecteurs virtuels bruités avant déploiement matériel — le détecteur interroge le feu « vérité » ForeFire et renvoie des détections imparfaites | P1 | D-05, livrable 208 §3.3, livrable 210 §3.6 |

---

## 4. Exigences non fonctionnelles

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| IGNIS-NF-01 | **Latence boucle complète** : détection drone → présentation COS < 5 min (boucle d'assimilation J-03). Inférence edge < 100 ms, message critique LoRa < 30 s, cycle ForeFire + filtre < 60 s | P0 | J-03, livrable 209 §3.2 |
| IGNIS-NF-02 | **Performance simulation** : ForeFire 1 000 ha en < 10 s à résolution métrique. Ensembles probabilistes (10–50 scénarios) < 60 s sans émulateur, < 10 s avec émulateur V1 | P0 | J-01, J-02, livrable 209 §4.4 |
| IGNIS-NF-03 | **Temps réel Hub** : couches `ignis.front_de_feu` et `ignis.drones` en WebSocket < 1 s ; `ignis.hotspots` < 30 s ; `ignis.meteo_vent` et `ignis.meteo_humidite` < 5 min | P0 | HUB-002 §2, C-01 |
| IGNIS-NF-04 | **Offline-first** : le terrain reste opérationnel en mode dégradé (perte de connexion serveur). Le drone continue sa mission, le GCS affiche les détections et le vol. Le serveur reprend à la reconnexion avec synchronisation des données edge (file d'attente, aucune donnée perdue) | P0 | C-06, T-10, livrable 208 §6 |
| IGNIS-NF-05 | **Sécurité liaisons** : MAVLink 2 signé (authentification + signature des messages obligatoires), chiffrement des liaisons, authentification des nœuds mesh, détection d'anomalies sur messages (fausses détections injectées), résilience brouillage GPS | P0 | S-11, livrable 208 §6.5, livrable 210 §5.1 |
| IGNIS-NF-06 | **Souveraineté des données** : modèles IA français hébergés UE (Mistral, Pixtral) pour les rapports RETEX et synthèses COS. Anticipation qualification SecNumCloud/ANSSI pour la sécurité civile | P1 | S-11, M-05, livrable 208 §6.5 |
| IGNIS-NF-07 | **Interopérabilité** : respect du contrat d'interface HUB-002 (couches `ignis.*`, format WebSocket/JSON, 3D Tiles, GeoJSON, GeoTIFF). SRS par défaut EPSG:2154 (Lambert 93) ou EPSG:4326 (WGS84) | P0 | HUB-002, CON-007 |
| IGNIS-NF-08 | **Déconfliction aérienne** : transpondeur / e-identification obligatoire, intégration U-space, règle absolue de dégagement automatique à l'arrivée d'aéronefs pilotés (Canadair/Dash/HBE) — un drone non coordonné = arrêt des largages | P0 | V-08, livrable 208 §7.5, livrable 210 §7 |
| IGNIS-NF-09 | **Explicabilité** : chaque sortie (prédiction, recommandation, alerte) est accompagnée d'un niveau de confiance, d'une justification (observations et raisonnements) et des observations utilisées. L'incertitude est affichée explicitement (convergence/divergence des estimateurs) | P0 | GSIE-CON-004, G-03, J-04, livrable 208 §2ter.6 |
| IGNIS-NF-10 | **RGPD** : la détection de personnes/véhicules en zone (P-09) impose des garde-fous RGPD obligatoires — anonymisation, pas de stockage d'images identifiantes, finalité strictement opérationnelle | P0 | P-09, S-02, RFC-0004 §5.3 |

---

## 5. Cas d'usage prioritaires

### 5.1 CU-01 — Surveillance temps réel d'un incendie actif

| Champ | Description |
|---|---|
| **Acteur principal** | COS |
| **Acteurs secondaires** | Télépilote drone, opérateur GCS-Lite, API GSIE |
| **Préconditions** | Un incendie est confirmé. Les drones sont déployés sur zone. La connexion serveur est disponible (ou mode dégradé). |
| **Scénario nominal** | 1. Le drone survole le front en mission « suivi de front » (V-05). 2. Les capteurs RGB + thermique capturent le front. 3. L'edge processing détecte fumée/flamme (YOLO, P-01) et estime l'intensité (thermique radiométrique, P-03). 4. Le vecteur de feu est calculé par fusion multi-estimateurs (J-04). 5. Les observations sont transmises (LoRa critique / 4G télémétrie). 6. Le jumeau numérique assimile les observations et recale ForeFire (~5 min, J-03). 7. La prédiction recalée (front + intensité + incertitude) est publiée au Hub (`ignis.front_de_feu`, `ignis.propagation`). 8. L'analyse d'enjeux intersecte la propagation avec les bâtiments/infra (J-06) → liste des enjeux menacés + délais (30 min / 1 h / 2 h). 9. Le COS visualise le front, les enjeux et les recommandations dans le Centre de Commandement. 10. Le COS décide des actions. |
| **Scénario alternatif** | Perte de connexion serveur → mode dégradé (C-06) : le GCS-Lite affiche les détections et le vol en local, les données sont synchronisées au retour de connexion. |
| **Post-conditions** | Le COS dispose d'une prédiction recalée, d'une liste d'enjeux menacés avec délais, et de recommandations tactiques explicables. Toutes les actions sont journalisées (J-10). |

### 5.2 CU-02 — Préparation d'un scénario de propagation

| Champ | Description |
|---|---|
| **Acteur principal** | COS |
| **Acteurs secondaires** | API GSIE, Simulation Engine |
| **Préconditions** | Un incendie est actif ou un départ de feu est simulé. Les données de terrain (LiDAR HD, BD Forêt, AROME) sont préchargées. |
| **Scénario nominal** | 1. Le COS sélectionne un point d'ignition ou un front existant sur la carte. 2. Le COS configure les paramètres du scénario (vent 60 km/h, combustible modifié, horizon 2 h). 3. ForeFire exécute le scénario (< 10 s, J-01). 4. Les ensembles probabilistes (10–50 scénarios) produisent une carte de probabilité (< 60 s, J-02). 5. Le résultat est publié au Hub avec le préfixe `simulated.ignis.front_de_feu` (état simulé distingué de l'état réel, CON-010). 6. Le COS visualise la propagation minute par minute (timeline G-10) et les enjeux menacés. 7. Le COS évalue les options tactiques. |
| **Post-conditions** | Le COS dispose d'un ou plusieurs scénarios hypothétiques avec probabilités, enjeux menacés et délais. L'état simulé est visuellement distingué de l'état réel. |

### 5.3 CU-03 — Patrouille drone autonome

| Champ | Description |
|---|---|
| **Acteur principal** | Télépilote drone |
| **Acteurs secondaires** | Orchestrateur multi-drones (V-06), API GSIE |
| **Préconditions** | Saison à risque. Les drones sont stationnés en station d'accueil (V-09) ou déployés sur zone. Le go/no-go météo est validé (V-02). |
| **Scénario nominal** | 1. La carte de risque dynamique (J-09) identifie un massif à surveiller. 2. Le télépilote ou l'orchestrateur (V-06) assigne un drone (batterie, distance, capteurs). 3. Le drone décolle et exécute le pattern lawnmower sur le massif (V-05). 4. Les capteurs RGB + thermique capturent en continu. 5. L'edge processing détecte fumée/flamme (P-01) et anomalies thermiques (P-03). 6. En cas de détection, un message critique est envoyé via LoRa (< 30 s, C-01). 7. Le GCS-Lite affiche la détection et la position du drone en temps réel. 8. Le COS est notifié et décide d'une reconnaissance ciblée (G-02) ou d'un suivi de front. 9. À 25–30 % de batterie, le drone rentre en RTH automatique (V-04). Un drone de relève prend le relais (V-03). |
| **Scénario alternatif** | Détection d'aéronefs pilotés → dégagement automatique (V-08, déconfliction aérienne). |
| **Post-conditions** | Le massif a été survolé. Toute détection est reportée au COS. Les données de vol sont journalisées. |

---

## 6. Couches Ignis exposées au Hub

Ignis publie ses données vers le Centre de Commandement selon le
contrat d'interface HUB-002. Les couches `ignis.*` sont les suivantes :

| `layer_id` | `display_name` | Canal | Fréquence | `geometry_type` | Source |
|---|---|---|---|---|---|
| `ignis.front_de_feu` | Front de feu | WebSocket | Temps réel (< 1 s) | `polygon` | ForeFire + assimilation (J-03) |
| `ignis.hotspots` | Hotspots (FIRMS/VIIRS) | WebSocket | Temps réel (< 30 s) | `point` | DS-024, J-08 |
| `ignis.meteo_vent` | Vent (vecteurs) | WebSocket | Temps réel (< 5 min) | `line` | DS-009, M-09 |
| `ignis.meteo_humidite` | Humidité | WebSocket | Temps réel (< 5 min) | `raster` | DS-009, DS-010 |
| `ignis.combustible` | Combustible (3 strates) | REST (3D Tiles) | Statique | `point_cloud` | DS-002, DS-001 |
| `ignis.drones` | Positions drones | WebSocket | Temps réel (< 1 s) | `point` | PX4 télémétrie, V-01 |
| `ignis.propagation` | Propagation prédite | WebSocket | Temps réel (< 1 s) | `polygon` | ForeFire ensembles, J-02 |
| `ignis.perimetre_brule` | Périmètre brûlé | REST (GeoJSON) | Quotidien | `polygon` | DS-023, J-08 |

> **Convention état réel vs simulé** (HUB-002 §7) : les scénarios
> hypothétiques utilisent le préfixe `simulated.` — ex.
> `simulated.ignis.front_de_feu` (scénario vent 60 km/h). Le Hub
> affiche l'état simulé avec une teinte bleutée / hachurée pour le
> distinguer visuellement de l'état réel.

Chaque couche expose un document de métadonnées JSON à l'URL
`metadata_url` incluant : `source_datasets` (liste des DS-xxx consommés,
CON-005), `license`, `evidence_framework`, `quality` (précision
géométrique, temporelle, modèle de confiance), `version` (CON-010) et
`knowledge_ids` si applicable.

---

## 7. Matrice de traçabilité (exigence → source)

| Exigence | Architecture (livrable) | Dataset(s) | Moteur GSIE | Idée(s) registre | Contrat Hub |
|---|---|---|---|---|---|
| IGNIS-F-01 | 208 §2ter.2, 209 §3 | DS-024 | Simulation Engine | J-08, D-11 | `ignis.hotspots` |
| IGNIS-F-02 | 209 §5 | DS-023 | Validation Engine | J-08, D-10 | `ignis.perimetre_brule` |
| IGNIS-F-03 | 209 §5 | DS-022 | Validation Engine, Learning Engine | J-10, D-08 | — |
| IGNIS-F-04 | 208 §2ter.1 | DS-024, DS-009 | Evidence Engine, Simulation Engine | J-08, P-01, P-03, P-07 | `ignis.hotspots` |
| IGNIS-F-05 | 208 §3, 209 §4.5.1 | DS-002 | GIS Engine | J-01 | `ignis.combustible` |
| IGNIS-F-06 | 208 §5.1 | DS-002, DS-001 | GIS Engine, Botanical Engine | P-05, J-05 | `ignis.combustible` |
| IGNIS-F-07 | 208 §5.1 | DS-001 | Botanical Engine, GIS Engine | J-01 | `ignis.combustible` |
| IGNIS-F-08 | 208 §5.1, 209 §4.5.1 | DS-009 | Climate Engine | J-01, M-09, M-12 | `ignis.meteo_vent` |
| IGNIS-F-09 | 209 §4.5.1 | DS-009, DS-010 | Climate Engine | J-09 | `ignis.meteo_humidite` |
| IGNIS-F-10 | 208 §5.1 | DS-009 | Climate Engine | J-09 | — |
| IGNIS-F-11 | 208 §3.1, 209 §4 | DS-002, DS-001, DS-009 | Simulation Engine | J-01, J-03 | `ignis.front_de_feu` |
| IGNIS-F-12 | 209 §4.1 | DS-002, DS-009 | Simulation Engine, Evidence Engine | J-03, J-04 | `ignis.front_de_feu` |
| IGNIS-F-13 | 209 §4.3 | DS-002, DS-009 | Simulation Engine, Learning Engine | J-02, J-11 | `simulated.ignis.front_de_feu` |
| IGNIS-F-14 | 210 §3.1 | — | — | V-01, V-04 | `ignis.drones` |
| IGNIS-F-15 | 210 §4.1 | — | — | V-05 | `ignis.drones` |
| IGNIS-F-16 | 210 §6.1 | — | — | V-04 | `ignis.drones` |
| IGNIS-F-17 | 210 §3.3–3.4 | D-01 | Learning Engine | P-01, P-02, P-03 | — |
| IGNIS-F-18 | 211 §4 | DS-002, DS-009 | Simulation Engine | G-06, J-07 | `ignis.front_de_feu` |
| IGNIS-F-19 | 211 §0.3, HUB-002 §2 | DS-024, DS-009 | — | J-08, C-01 | `ignis.hotspots`, `ignis.meteo_vent`, `ignis.drones` |
| IGNIS-F-20 | HUB-002 §3–5 | — | Evidence Engine | — | Toutes couches `ignis.*` |
| IGNIS-F-21 | 208 §7.1 | — | — | G-04, S-06 | HUB-002 §7 |
| IGNIS-F-22 | 208 §7.4, 210 §5 | — | — | V-04 | — |
| IGNIS-F-23 | 208 §7.2–7.3 | — | — | G-04, S-06, S-09 | HUB-002 §7 |
| IGNIS-F-24 | 209 §5 | DS-022, DS-023 | Validation Engine, Learning Engine | J-10, S-07 | — |
| IGNIS-F-25 | 211 §4 | — | Learning Engine | D-05, G-06 | — |
| IGNIS-F-26 | 208 §3.3, 210 §3.6 | D-01 | Learning Engine | D-05 | — |

---

## 8. Critères d'acceptation

La spécification IGNIS-001 est considérée **complète** quand :

- [x] Toutes les exigences fonctionnelles (IGNIS-F-01 à IGNIS-F-26) sont
  tracées vers une source (architecture, dataset, registre, RFC)
- [x] Toutes les exigences non fonctionnelles (IGNIS-NF-01 à
  IGNIS-NF-10) sont quantifiées (performance, latence, sécurité)
- [x] Les cas d'usage prioritaires couvrent la surveillance temps réel
  (CU-01), la préparation de scénarios (CU-02) et la patrouille drone
  (CU-03)
- [x] Les garde-fous RFC-0004 §8 sont respectés (supervision humaine,
  reprise manuelle, pas de commande critique sans COS, journalisation)
- [x] Les couches `ignis.*` exposées au Hub sont définies selon le
  contrat HUB-002 (8 couches temps réel + REST)
- [x] La convention état réel vs simulé est spécifiée (préfixe
  `simulated.`, CON-010)
- [x] La matrice de traçabilité relie chaque exigence à son architecture,
  ses datasets, son moteur GSIE, ses idées registre et son contrat Hub
- [x] Les datasets sont cités par leur identifiant (DS-001, DS-002,
  DS-009, DS-010, DS-022, DS-023, DS-024)
- [x] Les idées du registre sont citées par leur identifiant (P-xx,
  J-xx, V-xx, C-xx, G-xx, D-xx, S-xx, M-xx)
- [ ] Les fiches couches détaillées (IGNIS-002) sont définies — **à
  produire**
- [ ] Le contrat d'interface API temps réel (WebSocket/gRPC) est
  spécifié — **à produire (Jalon 1)**

---

## 9. Glossaire

| Terme | Définition |
|---|---|
| **Ignis** | Système autonome de surveillance et d'analyse des incendies, application cliente de GSIE |
| **COS** | Commandant des Opérations de Secours — décideur humain sur le terrain (GSIE-CON-001) |
| **CODIS** | Centre Opérationnel Départemental d'Incendie et de Secours |
| **Jumeau numérique vivant** | Représentation dynamique et recalée en temps réel du feu et de son environnement (GSIE-DIR-0005) |
| **Assimilation** | Boucle prédiction → observation → recalage (~5 min) qui corrige l'état du jumeau à partir des observations drone (J-03) |
| **ForeFire** | Moteur de propagation du feu open source (CNRS / Univ. Corse), GPL v3, service séparé (J-01) |
| **PX4** | Autopilote open source (BSD) pour drones — vol, navigation, plans de vol (V-01) |
| **Gazebo** | Simulateur physique 3D pour le banc de simulation drone (PX4 SITL) |
| **GCS-Lite** | Station de contrôle au sol métier (MapLibre GL 3D) — interface opérationnelle COS/télépilote (G-11) |
| **GCS-Cinéma** | Client 3D immersif (Unreal Engine 5.8 + Cesium for Unreal) — Centre de Commandement GSIE (G-05) |
| **Edge** | Traitement embarqué sur le drone (NVIDIA Jetson) — YOLO, VLM, estimation intensité |
| **Hotspot** | Détection thermique satellitaire (FIRMS/VIIRS) indiquant un point de chaleur actif |
| **FWI** | Fire Weather Index — indicateur composite de danger météorologique d'incendie |
| **RTH** | Return To Home — retour automatique du drone à son point de décollage (fail-safe) |
| **BVLOS** | Beyond Visual Line Of Sight — vol hors champ visuel du télépilote (cadre réglementaire EASA/SORA) |
| **DFCI** | Défense de la Forêt Contre l'Incendie — doctrine et infrastructure françaises |
| **RCCI** | Reading Crown Fire Indicators — lecture des indicateurs de fumée pour caractériser le combustible (P-04, suggestion) |
| **RETEX** | Retour d'expérience post-incident — rapport comparatif prédictions vs réalité (S-07) |
| **BDIFF** | Base de Données des Incendies de Forêt en France (depuis 2006, causes renseignées) |
| **EFFIS** | European Forest Fire Information System (JRC, Commission européenne) |
| **FIRMS** | Fire Information for Resource Management System (NASA) — détections thermiques MODIS/VIIRS |
| **Meshtastic** | Protocole LoRa maillé open source pour communications critiques en zone blanche (C-01) |
| **MAVLink 2** | Protocole de communication drone-sol, signé et authentifié (sécurité S-11) |
| **Niagara** | Système de particules/fluides d'Unreal Engine — effets feu/fumée pilotés par les données (G-06) |
| **FIRETWIN** | Référence de recherche pour la visualisation scientifique du feu par Niagara (livrable 211 §4) |

---

> Statut : *Draft — spécification fonctionnelle Phase 3 (préparation
> Phase 4). À valider par le Fondateur. Aucun code métier produit
> (CON-003).*
