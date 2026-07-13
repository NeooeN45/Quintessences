# Architecture drone Ignis — Stack embarqué, missions, communications et sécurité

| Champ | Valeur |
|---|---|
| **ID document** | GSIE-ARCH-FEU-003 |
| **Statut** | Draft |
| **Phase** | 2 — Architecture |
| **Créé le** | 2026-07-12 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **RFC d'origine** | RFC-0004 (ADOPTÉ) |
| **Décisions liées** | DEC-000003 (garde-fous), DEC-000005 (archive banc) |
| **Directives fondatrices** | GSIE-DIR-0005 (jumeau numérique vivant), GSIE-DIR-0006 (moteur cognitif) |
| **Document parent** | `GSIE_IGNIS_ARCHITECTURE.md` |
| **Document connexe** | `GSIE_IGNIS_DATA_PIPELINE.md` |

---

## 1. Objet

Ce document décrit l'architecture du sous-système drone de Ignis :
stack logicielle embarquée, types de missions, communications avec le
sol, contraintes d'autonomie et mesures de sécurité.

L'architecture décrite est celle du **système cible**. Le banc de
simulation actuel (PX4 SITL + Gazebo + MAVSDK, Jalon 0–2) valide les
briques logicielles sans matériel réel.

---

## 2. Vue d'ensemble du sous-système drone

```
┌─────────────────────────────────────────────────────────────┐
│ DRONE (edge)                                                │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ PX4         │  │ Jetson       │  │ Capteurs          │  │
│  │ Autopilot   │  │ (edge AI)    │  │ RGB, thermique,   │  │
│  │ (vol, nav)  │  │ YOLO, VLM    │  │ atmosphère, GPS   │  │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬─────────┘  │
│         │  MAVLink 2     │  API locale         │            │
│         └────────────────┘                     │            │
│  ┌─────────────────────────────────────────────┘           │
│  │ Payloads modulaires (P-10)                               │
│  └─────────────────────────────────────────────────────────┘
└──────────────────────────┬──────────────────────────────────┘
                           │ MAVLink 2 (signé, chiffré)
┌──────────────────────────┴──────────────────────────────────┐
│ GCS-LITE (terrain)                                          │
│  ├── Télémétrie temps réel (position, attitude, batterie)   │
│  ├── Vidéo / détections (si lien large bande)               │
│  ├── Définition de mission (waypoints, modes)               │
│  ├── Reprise manuelle (télépilote, V-04)                    │
│  └── Relais vers serveur (jumeau numérique)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │ API temps réel (WebSocket/gRPC)
┌──────────────────────────┴──────────────────────────────────┐
│ SERVEUR (jumeau numérique)                                  │
│  ├── Assimilation des observations drone                    │
│  ├── Prédiction ForeFire recalée                            │
│  ├── Orchestrateur multi-drones (V-06)                      │
│  └── Analyse d'enjeux                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Stack embarqué

### 3.1 PX4 Autopilot — pilote de vol

**Rôle** : autopilote de bas niveau — stabilisation, navigation,
plans de vol, décollage/atterrissage autonomes, fail-safe, RTH.

**Licence** : BSD (permissive — cohérent avec un produit commercial).

**Justification du choix** (Phase0 §2.1) :
- Licence BSD vs GPL ArduPilot (liberté commerciale sur les modules
  embarqués).
- Alignement avec l'écosystème recherche vision/ROS 2 dont Ignis
  dépend (P-01, P-02).
- MAVSDK-Python comme API de mission propre et moderne.
- Cité dans des dossiers BVLOS de référence.
- ArduPilot reste un plan B viable : MAVLink étant commun, la couche
  mission est portable — l'isolation couche mission / couche autopilote
  est un ADR à écrire.

**Simulation** : PX4 SITL (Software In The Loop) + Gazebo pour le banc.
Mode headless pour les campagnes automatisées. Variables
`PX4_HOME_LAT/LON/ALT` pour géolocaliser le décollage.
`PX4_SIM_SPEED_FACTOR` pour accélérer le temps.

### 3.2 MAVSDK — API de mission

**Rôle** : interface haut niveau entre Ignis et PX4.

**Stack** : MAVSDK-Python (banc), MAVSDK multi-langages (production).

**Fonctions** :
- Connexion au drone (UDP/TCP/série).
- Définition de missions (waypoints, modes de vol).
- Télémétrie temps réel (position, attitude, batterie, état).
- Contrôle de vol (armement, décollage, atterrissage, RTH).
- Reprise manuelle (télépilote, V-04).

**Protocole** : MAVLink 2 (signé — sécurité S-11). MAVLink par défaut
est peu sécurisé ; l'authentification et la signature des messages
sont obligatoires.

**Alternative future** : passerelle ROS 2 (uXRCE-DDS) si intégration
robotique complexe nécessaire (multi-capteurs, VIO).

### 3.3 YOLO quantisé — détection embarquée (P-01)

**Rôle** : détection temps réel de fumée, flammes et anomalies
thermiques sur les flux vidéo du drone.

**Stack** : YOLO (ou RT-DETR / D-FINE) quantisé, optimisé TensorRT,
exécuté sur NVIDIA Jetson.

**Modèles candidats** (M-01, à benchmarker) :
- RT-DETR / RT-DETRv2 — forts sur petits objets (fumée naissante).
- D-FINE (Apache 2.0) — précision sur petits objets.
- YOLO11 (⚠️ AGPL Ultralytics → licence commerciale ou éviter).
- Fine-tunes existants : TommyNgx/YOLOv10-Fire-and-Smoke,
  kittendev/YOLOv8m-smoke.

**Critères de benchmark** : précision fumée fine × FPS sur Jetson ×
licence. La licence est un critère au même titre que les FPS.

**Datasets d'entraînement** : Pyro-SDIS, FLAME2, D-Fire, FASDD (D-01).

**Performance cible** : > 30 FPS sur Jetson Orin Nano pour le flux
RGB, détection en < 100 ms par frame.

### 3.4 VLM embarqué — description de scène (P-02)

**Rôle** : caractérisation contextuelle de scène — description
structurée (type de fumée, comportement, contexte) pour l'explicabilité
et la réduction des faux positifs.

**Modèles candidats** (M-02, à benchmarker) :
- SmolVLM2 (256M/500M/2.2B, Apache 2.0, vidéo, GGUF/ONNX) — candidat
  n°1 pour la base RCCI (P-04).
- Qwen2.5-VL-3B (grounding spatial).
- Moondream2 (~1.9B, pointage par requête).
- Florence-2 (MIT).
- Précédent prouvé : hiko1999/Qwen2-Wildfire-2B (+ GGUF).

**Intégration** : le VLM s'exécute sur le Jetson (edge) ou en mode
déporté (serveur, si liaison large bande disponible). En mode dégradé
(offline), le VLM edge assure un minimum de caractérisation.

**Référence** : ForestFireVLM, *MDPI Drones* 2025.

### 3.5 Outillage NVIDIA embarqué (M-03)

| Outil | Rôle |
|---|---|
| **TAO Toolkit** | Fine-tuning + export TensorRT des détecteurs |
| **DeepStream** | Pipeline vidéo temps réel multi-flux — ossature de la perception |
| **Metropolis / VSS** | Recherche vidéo par VLM |

**Cohérence** : tout parle TensorRT, du Jetson (edge) au serveur (GPU).
Un modèle entraîné et exporté via TAO s'exécute sur les deux.

### 3.6 Capteurs — payloads modulaires (P-10)

> Chaque capteur coûte de l'autonomie (poids, consommation). Les
> payloads sont modulaires selon la mission.

| Capteur | Priorité | Usage | P-xx |
|---|---|---|---|
| **RGB** | Haute (n°1) | Détection fumée/flamme, contexte visuel, VLM | P-01, P-02 |
| **Thermique LWIR radiométrique** | Haute (n°2) | T° par pixel → estimation intensité front (kW/m), détection nuit | P-03 |
| **Capteurs atmosphériques** (CO/CO₂, particules, T°, hygrométrie) | Moyenne | Régime de combustion, prédiction reprises | P-07 |
| **LiDAR embarqué** | Moyenne | Structure combustible, hauteur panache, post-feu | P-05 |
| **Multispectral / NIR** | Moyenne | État hydrique végétation, pénétration fumée légère | P-06 |
| **GPS / IMU** | Obligatoire | Navigation, anémométrie par dérive (P-08) | — |

**Matrice capteur × apport × coût × poids** : à produire en Phase 0
(livrable 2, P-10).

---

## 4. Missions

### 4.1 Types de mission (V-05)

| Mission | Description | Déclencheur | Capteurs requis |
|---|---|---|---|
| **Surveillance / patrouille** | Vol autonome sur un massif selon un plan de vol prédéfini. Détection de départs de feu. | Planifié (saison à risque) ou carte de risque (J-09) | RGB + thermique |
| **Reconnaissance ciblée** | Le COS clique sur la carte → le drone se rend sur la zone pour relevé ponctuel. | Clic GCS-Lite (G-02) | RGB + thermique + atmosphère |
| **Suivi de front** | Le drone suit le front de feu en cours pour alimentation continue du jumeau numérique. | COS (pendant feu) | RGB + thermique + atmosphère |
| **Recherche de personnes** | Recherche de personnes/véhicules dans un secteur donné. | COS (urgence) | RGB + thermique (P-09, RGPD) |
| **Post-feu** | Cartographie des surfaces brûlées, vérification des reprises. | COS (après feu) | RGB + thermique + LiDAR (optionnel) |
| **Relais radio** (V-07) | Le drone se positionne pour combler un trou de couverture radio. | Détection automatique (G-12) | Meshtastic (payload radio) |

### 4.2 Go / no-go météo (V-02)

Avant chaque mission, un moteur de règles évalue les conditions
météorologiques (vent, pluie, visibilité, température) depuis la
station météo locale (station d'accueil V-09 ou station portable).

**Règles** : seuils de vent maximal, visibilité minimale, pas de vol
par temps orageux. Simple moteur de règles, pas d'IA.

### 4.3 Orchestrateur multi-drones (V-06)

> L'interface envoie l'intention, l'orchestrateur décide.

**Principe** : le COS clique une zone → l'orchestrateur choisit le
drone le plus adapté (batterie, distance, capteurs, mission en cours)
et réorganise les patrouilles.

**Algorithmes** : type enchères / CBBA (Consensus-Based Bundle
Algorithm).

**Statut** : 🔍 à étudier (Haute priorité). Testable en simulation
(PX4 SITL multi-véhicules, Gazebo).

### 4.4 Rotation de flotte (V-03)

Relève entre drones pour patrouille continue. Un drone rentre se
recharger (station d'accueil V-09) pendant qu'un autre prend le relais.
L'orchestrateur (V-06) gère la transition.

### 4.5 Stations d'accueil automatiques (V-09)

> Drone-in-a-box : abri + recharge auto + météo locale, déployées sur
> massif → relève de flotte sans humain = infrastructure de
> surveillance permanente.

**Marché mature** (DJI Dock et alternatives). Stratégie : acheter la
station, construire le reste.

**Question ouverte** : souveraineté des données avec du matériel chinois
pour la sécurité civile (S-11, V-09). Alternatives européennes à auditer.

---

## 5. Communication — MAVLink → GCS-Lite → COS

### 5.1 Chaîne de communication

```
Drone (PX4 + Jetson)
  ├── MAVLink 2 (signé) → GCS-Lite (télémétrie, mission)
  ├── LoRa maillé (Meshtastic) → GCS-Lite (alertes critiques)
  ├── 4G/5G → GCS-Lite / serveur (télémétrie, si couverture)
  └── Large bande → GCS-Lite / stockage à bord (imagerie)
      ↓
GCS-Lite (terrain)
  ├── Visualisation temps réel
  ├── Reprise manuelle (télépilote)
  └── API temps réel → serveur (jumeau numérique)
      ↓
Serveur (jumeau numérique)
  └── Prédiction + enjeux → GCS-Lite → COS
```

### 5.2 Architecture hiérarchique par priorité (C-01)

| Priorité | Type | Techno | Bande passante | Latence |
|---|---|---|---|---|
| **Critique** | Détection, vecteur, position | LoRa maillé (Meshtastic) | ~200 octets/message | < 30 s |
| **Standard** | Télémétrie, état mission | 4G/5G (file d'attente) | ~1 KB/s | < 5 s (si couverture) |
| **Large bande** | Imagerie, vidéo | Large bande ou stockage à bord | ~Mbps | Différé |

**Justification** : les zones DFCI sont des zones blanches. Le bas
débit (LoRa) passe toujours ; le haut débit (4G/5G) n'est pas garanti.

### 5.3 Messages compacts (C-02)

~200 octets : détection, lat/lon, intensité, vecteur, horodatage.
Spécification détaillée à écrire en Phase 2 (voir
`GSIE_IGNIS_DATA_PIPELINE.md` §3.3.3).

### 5.4 Mesh radio renforçable (C-03)

Chaque nœud (drone, station, véhicule pompier) relaie le mesh → le
réseau se renforce en opération. Effet réseau vertueux : plus il y a de
moyens sur zone, meilleure est la couverture.

### 5.5 Mission relais (V-07)

Un drone se positionne automatiquement pour combler un trou de
couverture détecté (G-12). Le drone devient un nœud Meshtastic volant.

> **Garde-fou régalien** : relayer LoRa libre = OK ; retransmettre
> ANTARES (fréquences pompiers) = régalien, interdit. On visualise,
> on ne relaie pas.

### 5.6 Alternatives de communication (C-05, à évaluer Phase 0)

| Techno | Avantage | Inconvénient | Statut |
|---|---|---|---|
| **LoRa / Meshtastic** | Bas débit, maillé, bon marché | Débit très limité | ✅ Retenu (critique) |
| **Wi-Fi HaLow 802.11ah** | ~Mbps sub-GHz, challenger sérieux | Écosystème émergent | 🔍 |
| **Satellite IoT Kinéis** (🇫🇷) | Souveraineté, couverture totale | Latence, débit | 🔍 |
| **Iridium SBD** | Filet de sécurité ultime | Coût, débit | 🔍 |
| **4G/5G privée ARCEP** | Haut débit | Déploiement fixe à terme | 🔍 |
| **MANET tactiques (Silvus)** | Haut débit maillé | Très cher, cible « version pro » | 🔍 |

---

## 6. Autonomie et contraintes

### 6.1 Batterie

| Paramètre | Cible | Notes |
|---|---|---|
| Autonomie par vol | 30–45 min | Dépend du payload et des conditions |
| Temps de recharge | 60–90 min | Station d'accueil V-09 |
| Patrouille continue | Rotation de flotte (V-03) | Minimum 2 drones par massif |
| Seuil de retour | 25–30 % batterie | RTH automatique (fail-safe) |
| Monitoring | Temps réel via télémétrie | Affiché sur GCS-Lite |

### 6.2 Payload

> Chaque capteur coûte de l'autonomie (poids + consommation). La
> matrice capteur × apport × coût × poids (P-10) détermine la
> configuration optimale par mission.

**Configuration type (surveillance)** : RGB + thermique = minimum
viable. ~200–400 g de payload.

**Configuration type (reconnaissance)** : RGB + thermique + capteurs
atmosphériques. ~400–600 g.

**Configuration type (post-feu)** : RGB + thermique + LiDAR
(optionnel). ~600–900 g.

### 6.3 Contraintes météo

| Condition | Seil | Action |
|---|---|---|
| Vent | > seuil (ex. 12 m/s) | No-go (V-02) |
| Pluie | Forte pluie | No-go |
| Visibilité | < minimum | No-go |
| Orage | Activité électrique | No-go + surveillance post-orage (D-13) |
| Température | Hors plage batterie/capteurs | No-go |

### 6.4 Contraintes réglementaires

| Cadre | Description | Statut |
|---|---|---|
| **EASA catégorie spécifique** | Cadre européen pour les drones spécifiques | Conformité obligatoire |
| **SORA** (Specific Operations Risk Assessment) | Analyse de risque par opération | À produire par mission type |
| **BVLOS** (Beyond Visual Line of Sight) | Vol hors vue — patrouilles automatisées | Verrou principal (S-01) |
| **DGAC** | Autorité française | Démarrer en vol à vue, cadre simple |
| **U-space** | Intégration espace aérien européen | Procédures de coordination (V-08, Q12 ouverte) |

> **Verrou principal** : BVLOS / SORA / DGAC pour les patrouilles
> automatisées (S-01). Démarrer en vol à vue, cadre simple.

---

## 7. Sécurité

### 7.1 RGPD — détection de personnes (P-09, S-02)

> La détection de personnes/véhicules en zone est soumise au RGPD.

**Mesures architecturales** :
- Les données de détection de personnes sont des **informations
  tactiques immédiates**, pas un dispositif de surveillance.
- **Purge automatique** des données de détection après l'intervention.
- Pas de stockage durable sans base légale.
- L'interface présente la présence de personnes comme une alerte
  tactique (« personnes détectées dans la zone »), sans identification.
- Les images RGB contenant des personnes ne sont pas archivées sauf
  nécessité légale explicite.

### 7.2 Fail-safe et RTH (Return To Home)

| Scénario | Action automatique |
|---|---|
| Perte de liaison radio (MAVLink) | RTH automatique (PX4 fail-safe) |
| Batterie critique (< seuil) | RTH automatique |
| Perte GPS | Mode stabilisé + descente lente (ou atterrissage d'urgence) |
| Détection d'anomalie vol | RTH ou atterrissage d'urgence |
| Arrivée aéronef piloté (V-08) | **Dégagement automatique immédiat** |

**RTH** : le drone retourne à son point de décollage (ou station
d'accueil V-09) de manière autonome. Le télépilote peut annuler le RTH
et reprendre la main (V-04).

### 7.3 Déconfliction aérienne (V-08)

> Un drone non coordonné = arrêt des largages (cas réels). La
> déconfliction est une **obligation absolue** et un argument de vente.

**Mesures** :
- **Transpondeur / e-identification** : obligatoire.
- **Intégration U-space** : procédures de coordination.
- **Règle absolue** : dégagement automatique à l'arrivée d'aéronefs
  pilotés (Canadair, Dash, HBE). Le drone libère l'espace aérien
  immédiatement — pas de négociation, pas de délai.
- **Affichage GCS-Lite** : position des aéronefs pilotés connus sur la
  carte, zones de largage, couloirs aériens.

### 7.4 Cybersécurité by design (S-11)

> Le système est une cible. Anticiper coûte 10× moins que rattraper.

| Menace | Mesure |
|---|---|
| Écoute / injection MAVLink | MAVLink 2 signé (authentification des messages) |
| Fausse détection injectée | Détection d'anomalies sur messages (score aberrant, position impossible, fréquence anormale) |
| Brouillage GPS | Résilience : odométrie visuelle (VIO), RTH sur position estimée |
| Compromission nœud mesh | Authentification des nœuds, chiffrement des communications LoRa |
| Accès non autorisé GCS | Authentification forte, journalisation, RBAC |
| Exfiltration de données | Chiffrement au repos, réseau isolé, pas d'accès Internet direct sur le terrain |

**Anticipation** : qualification SecNumCloud/ANSSI pour vendre à la
sécurité civile (S-11).

### 7.5 Reprise manuelle (V-04)

> Exigence réglementaire : le télépilote peut reprendre la main à tout
> moment.

**Architecture** :
- Le GCS-Lite dispose d'un mode de contrôle manuel (joystick / RC).
- Le passage auto → manuel est immédiat et prioritaire sur toute
  mission automatique.
- L'autopilote PX4 supporte nativement ce basculement.
- Le télépilote est sous supervision humaine (V-04).

---

## 8. Simulation vs réel — correspondance

| Composant | Banc (simulation) | Cible (réel) |
|---|---|---|
| Autopilote | PX4 SITL | PX4 sur hardware de vol |
| Environnement | Gazebo (monde virtuel, headless) | Terrain réel |
| Capteurs | Capteurs simulés Gazebo | RGB, thermique, atmosphère, LiDAR |
| Détection | Détecteur virtuel bruité (interroge le feu « vérité ») | YOLO quantisé + VLM sur Jetson |
| Communication | UDP local (MAVLink) | LoRa + 4G/5G + large bande |
| GCS | GCS-Lite (MapLibre) | GCS-Lite + GCS-Cinéma (phase 4) |
| Multi-drones | PX4 SITL multi-véhicules | Flotte réelle + orchestrateur |
| Stations | — | Drone-in-a-box (V-09) |

> Le banc de simulation est conçu pour que le code de mission (MAVSDK)
> et la logique d'orchestration soient **identiques** entre simulation
> et réel. Seuls les capteurs et l'environnement changent.

---

## 9. Questions ouvertes

1. **Châssis drone** : build custom vs plateforme existante ? Critères :
   payload, autonomie, IP rating (backlog registre Q1).
2. **Liaison vidéo large bande** : quelle techno quand 4G absente ?
   Relais drone ? Antenne directionnelle ? (Q2, C-05).
3. **Patrouille nocturne** : thermique seul suffit-il ? Les feux
   nocturnes existent (Q3).
4. **Multi-drones** : à partir de combien ? Complexité coordination vs
   valeur (Q4, V-06).
5. **Drone-in-a-box** : DJI Dock vs alternatives européennes ?
   Souveraineté (Q8, V-09, S-11).
6. **U-space 2026** : procédures de coordination drone/aéronefs
   bombardiers d'eau (Q9, V-08).
7. **Drone-relais radio** : quelles fréquences a-t-on le droit
   d'émettre/relayer ? (Q7, V-07).

---

## 10. Sources et références

### 10.1 Sources techniques

- PX4 : `docs.px4.io` (SITL, Gazebo, fail-safe, RTH, BVLOS)
- MAVSDK : `mavsdk.io` (API Python, MAVLink 2)
- Gazebo : `gazebosim.org` (capteurs simulés, multi-véhicules)
- NVIDIA Jetson / TensorRT / TAO / DeepStream : `developer.nvidia.com`
- Meshtastic : `meshtastic.org` (LoRa maillé)

### 10.2 Sources scientifiques

- ForestFireVLM, *MDPI Drones* 2025 — VLM pour description de scène feu
- hiko1999/Qwen2-Wildfire-2B — VLM feu fine-tuné (précédent prouvé)

### 10.3 Cadre réglementaire

- EASA : règlements délégués catégorie spécifique
- SORA : JARUS Specific Operations Risk Assessment
- DGAC : autorité française aviation civile
- U-space : règlement européen 2021/664
- RGPD : règlement UE 2016/679

### 10.4 Documents de gouvernance

- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0005.md` — Vision GCS / jumeau numérique
  vivant (le drone alimente le jumeau, interactions immersives)
- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0006.md` — Vision moteur cognitif (drone
  comme observateur, intelligence distribuée, curiosité artificielle)
- `02_RFC/RFC-0004.md` — RFC Ignis (ADOPTÉ), §3.1, §3.5, §5.3, §8
  (garde-fous : autonomie limitée à la navigation, reprise manuelle,
  alerte humaine)
- `03_DECISIONS/DEC-000003.md` — Adoption + garde-fous (RGPD, autonomie)
- `apps/Ignis/REGISTRE.md` — Registre d'idées (sections 1, 3, 4, 7)
- `apps/Ignis/Phase0_comparatif_moteurs_simulation.md`
  — Comparatif PX4/ArduPilot, Gazebo, MAVSDK

---

## 11. Alignement sur les directives fondatrices

> Cette section explicite l'articulation du sous-système drone avec les
> directives fondatrices GSIE-DIR-0005 (jumeau numérique vivant) et
> GSIE-DIR-0006 (moteur cognitif). Les garde-fous RFC-0004 §8
> (autonomie limitée à la navigation, reprise manuelle, alerte humaine)
> sont déjà intégrés au §5.2 et au rappel final — ils ne sont pas
> dupliqués ici, mais référencés.

### 11.1 Le drone comme observateur du terrain (DIR-0006)

Au sens de la directive GSIE-DIR-0006, le drone n'est pas seulement un
capteur volant : c'est un **observateur du terrain**. Chaque drone apporte
une partie de la vérité, au même titre que les satellites, les caméras
fixes, les stations météo ou les rapports SDIS. Le moteur cognitif ne
choisit jamais une source unique : il construit un **consensus
probabiliste** multi-observateurs.

Chaque type de capteur drone est caractérisé par quatre dimensions
(DIR-0006, §« Principe d'assimilation permanente ») :

| Capteur drone | Précision | Latence | Fiabilité | Incertitude |
|---|---|---|---|---|
| **RGB** | Détection fumée/flamme à ~30 FPS ; résolution sub-mètre à 100 m AGL | < 100 ms par frame (edge) ; différé si large bande indisponible | Dépendante de l'éclairage, de la fumée, de la couverture nuageuse | Élevée sur détection précoce (faux positifs possibles) ; réduite par fusion VLM |
| **Thermique LWIR radiométrique** | T° par pixel (±1–2 °C typique) ; estimation intensité/front | < 1 s (traitation edge) ; différé si liaison limitée | Bonne pénétration fumée ; insensible à l'éclairage | Étalonnage radiométrique requis ; confusion sources thermiques parasites |
| **Capteurs atmosphériques** (CO/CO₂, particules, T°, hygrométrie) | Concentration gazeuse ± seuil capteur ; T° ±0,5 °C | Quelques secondes (acquisition + transmission) | Bonne répétabilité ; dérive capteur à étalonner | Représentativité ponctuelle (mesure in-situ, non spatialisée) |
| **LiDAR embarqué** | Structure 3D combustible, hauteur panache (cm–dm) | Post-traitement (différé) | Haute précision géométrique | Dépend de la densité de points et de la végétation |
| **Multispectral / NIR** | État hydrique végétation (indices NDVI/NDWI) | Différé (post-traitement) | Bonne pour suivi temporel | Sensible à l'atmosphère et à l'éclairage |

Le drone s'intègre dans le **consensus probabiliste multi-observateurs**
du moteur cognitif (DIR-0006, §« Les observateurs ») : ses observations
sont fusionnées avec celles des satellites (Copernicus, Sentinel, NASA
FIRMS), des caméras fixes, des stations météo (Météo-France), des capteurs
LoRa et des rapports SDIS. Aucune source n'est considérée comme une
vérité absolue ; chacune est pondérée par sa précision, sa latence, sa
fiabilité et son incertitude.

### 11.2 Le drone dans l'intelligence distribuée (DIR-0006)

La directive GSIE-DIR-0006 définit une architecture d'agents
spécialisés, chacun raisonnant indépendamment. Le **drone est un agent
spécialisé** dans cette architecture (DIR-0006, §« Intelligence
distribuée » : « Agent drone »).

**Responsabilités de l'agent drone** :
- **Navigation** : raisonnement local sur la trajectoire, l'optimisation
  de route, la gestion d'énergie (batterie, RTH).
- **Détection** : traitement embarqué (YOLO, VLM) et production de
  conclusions structurées (type de fumée, comportement, contexte).
- **Optimisation de trajectoire** : adaptation en vol selon les
  observations (repositionnement sur zone d'intérêt, suivi de front).

L'agent drone raisonne **indépendamment** sur ces domaines. Le moteur
cognitif (serveur) **fusionne** ses conclusions avec celles des autres
agents (agent météo, agent propagation, agent végétation, agent RCCI,
etc.). La fusion reste explicable et tracée (GSIE-CON-004, GSIE-CON-005) :
chaque conclusion drone est accompagnée de son niveau de confiance et des
observations qui l'ont produite.

> **Modularité** (GSIE-CON-007) : l'agent drone est une responsabilité
> unique, documentée et testée. Il n'empiète pas sur le raisonnement de
> l'agent propagation ou de l'agent météo — il leur fournit des
> observations et des conclusions locales.

### 11.3 Curiosité artificielle et propositions d'observation (DIR-0006)

La directive GSIE-DIR-0006 (§« Curiosité artificielle ») prévoit que,
lorsque l'incertitude devient trop importante sur une zone, le système
**propose spontanément** d'envoyer un drone observer, de demander une
mesure thermique ou de repositionner un capteur.

**Application au sous-système drone** :
- Le moteur cognitif détecte une **zone d'incertitude élevée** (front de
  feu mal contraint, détection non confirmée, divergence entre sources).
- Il génère une **proposition d'observation** : envoyer un drone sur la
  zone, activer la thermique, repositionner un drone en patrouille.
- Cette proposition est présentée au COS / télépilote via le GCS-Lite ou
  l'interface immersive.

> **Garde-fou — RFC-0004 §8.3 et §8.4 (prioritaires sur DIR-0006)** : la
> curiosité artificielle produit des **propositions**, jamais un
> déclenchement automatique. La décision de missionner un drone reste
> **humaine** (télépilote, COS / CODIS). Le système peut suggérer un
> repositionnement, mais la décision finale appartient à l'opérateur. La
> reprise manuelle reste toujours possible et prioritaire (§5.2, §7.5).

### 11.4 Sources de données externes pertinentes pour le drone

> Le détail exhaustif des sources de données figure dans le document
> parent (`GSIE_IGNIS_ARCHITECTURE.md`, livrable 209). Cette section ne
> liste que les sources directement pertinentes pour le sous-système
> drone.

| Source | Usage drone | Référence |
|---|---|---|
| **IGN** (LiDAR HD, MNT/MNH) | Navigation (terrain following), optimisation de trajectoire, contexte relief pour plan de vol | `ign.fr` — RGE Alti®, LiDAR HD |
| **Météo-France** | Go/no-go météo pré-mission (§4.2), recalage des conditions de vol, prévision de vent pour optimisation de route | `meteofrance.fr` — ARPEGE/AROME |
| **Copernicus** (Sentinel) | Contexte satellite pour corrélation avec observations drone (consensus multi-observateurs) | `copernicus.eu` — Sentinel-2, EMS |

### 11.5 Lien avec DIR-0005 — alimentation du jumeau numérique vivant

La directive GSIE-DIR-0005 définit Ignis comme un **jumeau numérique
vivant** des opérations de lutte contre les incendies. Le drone en est un
capteur actif : ses observations (RGB, thermique, environnementaux) sont
**projetées sur le terrain** dans l'interface immersive.

**Projection des observations drone dans le jumeau** :
- Les détections (fumée, flamme, front) sont projetées à leur position
  géographique sur le terrain 3D.
- Les mesures thermiques alimentent l'intensité du front affiché.
- Les capteurs atmosphériques enrichissent le contexte local (régime de
  combustion, qualité de l'air).

**Interactions immersives (DIR-0005, §« Exemples d'interactions »)** :
lorsque l'utilisateur clique sur un drone dans l'interface immersive, il
voit apparaître sans quitter la scène principale :
- le **flux vidéo** en temps réel (si liaison large bande disponible) ;
- la **caméra thermique** (LWIR radiométrique) ;
- la **batterie** et l'état des capteurs ;
- la **mission** en cours ;
- la possibilité de **reprendre le contrôle** (V-04).

Le drone n'est donc pas seulement un moyen d'observation : c'est un
**élément vivant du jumeau numérique**, visible et interagissable dans
l'interface immersive. Le flux vidéo et la caméra thermique apparaissent
au clic, conformément à DIR-0005 §« Exemples d'interactions ».

---

> **Rappel** : le drone est un capteur volant et un nœud de
> communication. Il est autonome en navigation (V-01), jamais en
> décision opérationnelle. Le télépilote et le COS restent les
> décideurs (DEC-000003, GSIE-CON-001).
