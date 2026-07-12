# Architecture GSIE-Ignis — Système d'aide à la décision pour la surveillance et l'analyse des incendies de forêt

| Champ | Valeur |
|---|---|
| **ID document** | GSIE-ARCH-FEU-001 |
| **Statut** | Draft |
| **Phase** | 2 — Architecture |
| **Créé le** | 2026-07-12 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **RFC d'origine** | RFC-0004 (ADOPTÉ) |
| **Décisions liées** | DEC-000003 (adoption RFC-0004 + garde-fous), DEC-000005 (archive banc) |
| **Documents connexes** | `GSIE_IGNIS_DATA_PIPELINE.md`, `GSIE_IGNIS_DRONE_ARCHITECTURE.md`, `22_PROJECT_MEMORY/GSIE-Ignis.md` (registre d'idées), `22_PROJECT_MEMORY/GSIE-Ignis/Phase0_comparatif_moteurs_simulation.md` |

---

## 1. Objet et périmètre

Ce document décrit l'architecture du système cible GSIE-Ignis : un système
d'aide à la décision pour la surveillance, la détection précoce, la
caractérisation et l'analyse opérationnelle des incendies de forêt, destiné
au COS (Commandant des Opérations de Secours) et au CODIS.

GSIE-Ignis est une **application cliente** de l'écosystème GSIE — ce n'est ni
un 15ᵉ moteur central, ni un système de commandement (DEC-000003,
RFC-0004 §4, Option C hybride).

L'architecture décrite ici est celle du **système opérationnel cible**. Le
banc de simulation actuel (`~/GSIE-Ignis/` WSL2, Jalon 0–2) en est une
sous-tranche de validation, pas l'inverse.

---

## 2. Vue d'ensemble

### 2.1 Positionnement

```
┌─────────────────────────────────────────────────────────────────┐
│ ÉCOSYSTÈME GSIE — 14 moteurs (fondation scientifique)           │
│                                                                 │
│  Evidence → Knowledge → Correlation → Reasoning → Diagnostic    │
│  → Recommendation → Validation                                  │
│  Domaine : GIS, Climate, Pedology, Botanical, Forest Dynamics   │
│  Transverses : Learning, Simulation                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │ API GSIE (interfaces documentées)
┌──────────────────────────┴──────────────────────────────────────┐
│ GSIE-Ignis — Application cliente dédiée risque incendie           │
│                                                                 │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Drone   │  │  Jumeau   │  │ Analyse  │  │   GCS-Lite    │  │
│  │ (edge)   │→ │ numérique │→ │ d'enjeux │→ │  (présentation│  │
│  │          │  │ (serveur) │  │ (serveur)│  │    COS/CODIS) │  │
│  └──────────┘  └───────────┘  └──────────┘  └───────────────┘  │
│       ↕ MAVLink        ↕ API temps réel      ↕ WebSocket/gRPC  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Deux dimensions temporelles

| Dimension | Horizon | Fréquence | Sortie principale |
|---|---|---|---|
| **Préventive** (pré-feu) | Saisonnier → horaire | Carte de risque dynamique heure par heure | « Ce versant est une allumette aujourd'hui » (J-09) |
| **Réactive** (pendant feu) | Secondes → ~5 min | Boucle perception → assimilation → prédiction | Front prédit + enjeux menacés + délais (J-03, J-06) |
| **Post-feu** | Heures → jours | Validation satellite + RETEX | Contours validés, rapport comparatif (J-08, J-10, S-07) |

### 2.3 Banc de simulation vs système cible

Le banc de simulation (Jalon 0–2) est une **sous-tranche de validation** du
système cible. Il valide les briques critiques (ForeFire, PX4 SITL, Gazebo,
MAVSDK, détecteur virtuel, boucle d'assimilation, GCS-Lite) sans matériel
réel. Le système cible ajoute : drones réels, capteurs physiques, liaisons
radio terrain, orchestrateur multi-drones, GCS-Cinéma, intégration SDIS.

```
Banc de simulation (actuel)          Système cible
─────────────────────────            ─────────────────────────────
ForeFire (feu vérité + prédiction)   ForeFire (prédiction opérationnelle)
PX4 SITL (simulé)                    PX4 (drone réel, Jetson)
Gazebo (monde virtuel)               Capteurs réels (RGB, thermique, atmosphère)
Détecteur virtuel bruité             YOLO quantisé + VLM sur Jetson
GCS-Lite (MapLibre)                  GCS-Lite + GCS-Cinéma (Unreal/Cesium)
Boucle d'assimilation (test)         Boucle d'assimilation (opérationnelle)
—                                    Orchestrateur multi-drones
—                                    Communications terrain (LoRa/4G/5G)
—                                    Intégration SDIS (SITAC, NexSIS)
```

---

## 3. Composants architecturaux

### 3.1 ForeFire — moteur de propagation

**Rôle** : simuler la propagation du front de feu à partir d'un point
d'ignition, d'un paysage (MNT, combustible, vent) et de modèles de vitesse
(Rothermel, Balbi).

**Nature** : open source, C++, GPL v3, développé par le CNRS / Université
de Corse (UMR SPE 6134). Dépôt : `github.com/forefireAPI/forefire`.

**Intégration architecturale** : ForeFire s'exécute comme **service
séparé** (interface HTTP embarquée `listenHTTP` ou interpréteur
scriptable). Notre code propriétaire communique par messages — il n'est
pas une œuvre dérivée au sens GPL. Cette frontière de processus est un
garde-fou juridique à formaliser en ADR (voir
`Phase0_comparatif_moteurs_simulation.md` §1.1).

**Performance** : 1 000 ha simulés en < 10 s à résolution métrique —
compatible avec la boucle d'assimilation à recalage ~5 min (des dizaines
de scénarios par cycle envisageables sans émulateur).

**Double rôle sur le banc** : sur le banc de simulation, ForeFire joue
deux rôles : (1) feu « vérité » caché au système, et (2) moteur de
prédiction du jumeau numérique, avec des paramètres volontairement
différents — c'est ce qui rend le test d'assimilation honnête.

**Moteur secondaire (hors MVP)** : Cell2Fire (C2F-W) pour les campagnes
probabilistes massives hors ligne (cartes de risque, entraînement de
l'émulateur). Non bloquant pour le démonstrateur.

**Sources** : Filippi et al., ForeFire, RSFF'18 / 2014 ; Allaire, Filippi &
Mallet (2020), ensembles de simulations, *Int. J. Wildland Fire* ;
déploiement opérationnel FireCasterAPI / OpenDFCI / Entente Valable
(depuis juin 2020).

### 3.2 PX4 Autopilot — pilote de vol

**Rôle** : autopilote du drone — stabilisation, navigation, plans de vol
automatiques, décollage/atterrissage autonomes, fail-safe, RTH (Return To
Home).

**Nature** : open source, licence BSD (permissive — cohérent avec un
produit commercial). Dépôt : `github.com/PX4/PX4-Autopilot`.

**Intégration** : PX4 gère le vol de bas niveau. GSIE-Ignis ne réinvente
jamais l'autopilote (V-01). La couche mission (MAVSDK) est isolée de la
couche autopilote — portabilité ArduPilot préservée (ADR à écrire).

**Simulation** : PX4 SITL (Software In The Loop) + Gazebo pour le banc.
Mode headless pour les campagnes automatisées. Variables
`PX4_HOME_LAT/LON/ALT` pour géolocaliser le décollage (ex. Landiras).
`PX4_SIM_SPEED_FACTOR` pour accélérer le temps de simulation.

### 3.3 Gazebo — simulateur physique

**Rôle** : monde virtuel 3D pour la simulation drone — rendu, physique,
capteurs simulés (caméras, LiDAR, GPS), multi-véhicules.

**Nature** : open source, nouvelle génération (« Gz », ex-Ignition). Gazebo
Classic est rétrogradé en support communautaire — non retenu.

**Intégration** : Gazebo fournit l'environnement de perception pour le
détecteur virtuel bruité (qui interroge le feu « vérité » ForeFire et
renvoie des détections imparfaites). Le photoréalisme n'est pas dans
Gazebo : il vit dans le GCS-Cinéma (Unreal/Cesium), découplage sain.

> **AirSim archivé par Microsoft** — ne pas construire dessus. Le fork
> Colosseum n'offre pas de garantie de pérennité.

### 3.4 MAVSDK — API de mission

**Rôle** : interface haut niveau entre GSIE-Ignis et PX4 — définition de
missions, télémétrie, contrôle de vol, via le protocole MAVLink.

**Nature** : bibliothèque multi-langages (Python, Go, Swift, C++). API
moderne, asynchrone. Alternative : passerelle ROS 2 (uXRCE-DDS) si besoin
ultérieur.

**Intégration** : MAVSDK-Python est la couche mission du banc. L'API
envoie des intentions (waypoints, modes de mission) ; PX4 exécute. Le
télépilote peut reprendre la main à tout moment (V-04, exigence
réglementaire).

### 3.5 GCS-Lite — interface opérationnelle

**Rôle** : station de contrôle au sol métier — carte 3D, front de feu
vivants, polygones de propagation, enjeux menacés, incertitude affichée,
timeline de simulation, clic-carte → dispatch drone.

**Stack** : TypeScript, MapLibre GL 3D + MNT, WebSocket/gRPC vers l'API
temps réel. Base : QGroundControl/MAVLink pour la partie drone.

**Architecture double client** (G-11) : GCS-Lite (MapLibre, phases 2–3)
puis GCS-Cinéma (Unreal Engine 5.x + Cesium for Unreal, phase 4+), les
deux branchés sur la **même API temps réel**. Le contrat d'interface
WebSocket/gRPC est à spécifier tôt pour garantir la compatibilité.

**Principe d'incertitude** (G-03) : l'incertitude est affichée
explicitement (convergence/divergence des estimateurs). En cas de
divergence, le système signale l'incertitude au COS — jamais de fausse
certitude (J-04).

---

## 4. Pipeline de données — vue synthétique

Le pipeline détaillé fait l'objet de `GSIE_IGNIS_DATA_PIPELINE.md`. Vue
synthétique :

```
Capteurs drone (RGB, thermique, atmosphère)
    ↓ Edge processing (YOLO quantisé, VLM, estimation intensité)
Détections + vecteur de feu + métadonnées
    ↓ Liaison radio (LoRa critique / 4G télémétrie / large bande imagerie)
GCS-Lite (réception, visualisation temps réel)
    ↓ API temps réel
Jumeau numérique (assimilation → recalage ForeFire → prédiction)
    ↓
Analyse d'enjeux (intersection propagation × bâtiments/infra)
    ↓
Présentation COS (carte 3D, enjeux menacés, délais, incertitude)
```

**Boucle d'assimilation** (J-03, cœur du projet) : prédiction → observation
drone → recalage (~5 min). Filtre de Kalman d'ensemble ou filtre
particulaire. C'est la brique différenciante de GSIE-Ignis.

**Vecteur de feu multi-estimateurs** (J-04) : (1) géométrie du front
thermique entre passages drone, (2) inclinaison panache + vent, (3)
prédiction ForeFire → fusion pondérée par incertitudes.

---

## 5. Intégration avec les 14 moteurs GSIE

GSIE-Ignis est une application cliente : elle **sollicite** les moteurs GSIE
via leurs interfaces documentées. Elle n'en réimplémente aucun. L'approche
hybride (RFC-0004 Option C, actée par DEC-000003) prévoit des extensions
ciblées de certains moteurs, et réserve la question d'un moteur dédié à la
dynamique du feu à un second RFC après preuve de concept.

### 5.1 Moteurs sollicités et modalités d'intégration

| Moteur GSIE | Rôle dans GSIE-Ignis | Modalité | Idées liées |
|---|---|---|---|
| **Evidence Engine** | Évaluation de la preuve des détections drone, satellitaires et capteurs sol. Attribution d'un niveau de preuve à chaque observation avant intégration. | Consommation directe : chaque détection est soumise à l'Evidence Engine qui attribue un niveau de confiance. | P-01, P-03, J-08 |
| **Knowledge Engine** | Intégration des connaissances qualifiées (combustible, topographie, météo, enjeux) dans le graphe de connaissances. Base de doctrine DFCI, RETEX historiques. | Consommation + alimentation : GSIE-Ignis nourrit le graphe avec les observations terrain et la « boîte noire » du front (J-10). | J-10, D-04, M-21 |
| **Correlation Engine** | Croisement des observations multi-sources (drone × satellite × sol × météo) pour corroboration. Détection des divergences. | Consommation : fusion multi-estimateurs (J-04) s'appuie sur la corrélation des sources. | J-04, J-08, D-06 |
| **Reasoning Engine** | Inférence sur l'état du feu, les causes probables (hypothèse, jamais conclusion), les scénarios de propagation. | Consommation : le raisonnement sur la cause probable est une **hypothèse exploratoire** (garde-fou DEC-000003). | P-04, J-11 |
| **Diagnostic Engine** | Diagnostic de l'état du feu : intensité, régime de combustion, comportement (flamboyant/couvant), sautes probables. | Consommation : le diagnostic alimente la présentation COS. | P-03, P-07, J-11 |
| **Recommendation Engine** | Recommandations tactiques (zones à surveiller, pré-positionnement, délais d'arrivée aux enjeux). **Jamais un ordre** — une aide. | Consommation : les recommandations sont présentées au COS comme suggestions explicables et contournables (GSIE-CON-001). | J-06, J-09, V-05 |
| **Validation Engine** | Validation post-feu : comparaison prédictions vs contours réels (Copernicus EMS, BDIFF). Mesure de la qualité des modèles. | Consommation + boucle de rétroaction : alimente le réentraînement (D-03) et la crédibilité continue (J-10). | J-08, J-10, S-07 |
| **GIS Engine** | Couches géospatiales : MNT/MNH LiDAR HD, BD Forêt, BD TOPO, cadastre, DFCI, OpenStreetMap, BAN. Opérations spatiales (intersection, buffers). | Consommation intensive : l'analyse d'enjeux (J-06) est une opération GIS pure. Extension possible : couches feu spécifiques. | J-01, J-06, D-17 |
| **Climate Engine** | Données météo : AROME (vent, T°, hygrométrie), ERA5 (historique), modèles IA météo (CorrDiff, FourCastNet). Vent local = paramètre n°1 de la propagation. | Consommation + extension possible : descente d'échelle pour le vent sur relief français (M-09, M-12). | J-01, J-09, M-09 |
| **Pedology Engine** | Type de sol, humidité, profondeur — influence sur le combustible et la propagation souterraine. | Consommation secondaire : alimente la carte de combustible. | J-01 |
| **Botanical Engine** | Composition floristique, modèles de combustible (correspondance BD Forêt → modèles Rothermel/Balbi), état hydrique. | Consommation + extension possible : correspondance combustibles français (travail de calibration nécessaire, voir Phase0 §1.2). | J-01, P-06 |
| **Forest Dynamics Engine** | Dynamique de la végétation (succession, mortalité, régénération) → état du combustible disponible dans le temps. | Consommation : alimente la carte de risque dynamique pré-feu (J-09). | J-09 |
| **Learning Engine** | Apprentissage continu : réentraînement des détecteurs sur faux positifs signalés, entraînement de l'émulateur neuronal (J-02), datasets synthétiques (D-05). | Consommation + extension majeure : l'émulateur et l'apprentissage continu sont des briques différenciantes. | J-02, D-03, D-05 |
| **Simulation Engine** | Orchestration des simulations ForeFire, ensembles probabilistes, émulateur neuronal. Cœur du jumeau numérique. | Consommation + extension majeure : la boucle d'assimilation (J-03) est l'extension la plus structurante. | J-01, J-02, J-03 |

### 5.2 Extensions envisagées (à formaliser en ADR)

Les extensions suivantes sont identifiées mais **non actées** — elles
feront l'objet d'ADRs et potentiellement d'un second RFC si un moteur
dédié se justifie :

1. **Simulation Engine** : boucle d'assimilation temps réel, émulateur
   neuronal, ensembles probabilistes — l'extension la plus profonde.
2. **Climate Engine** : descente d'échelle météo pour le vent sur relief
   (CorrDiff-France, M-09/M-12).
3. **GIS Engine** : couches spécifiques feu (DFCI, combustible dynamique,
   surfaces brûlées).
4. **Learning Engine** : pipeline d'apprentissage continu sur données
   terrain drone + synthétiques.
5. **Botanical Engine** : correspondance BD Forêt → modèles de combustible
   calibrés pour la France.

### 5.3 Moteur dédié « Fire Dynamics » — question ouverte

RFC-0004 §9 Option B évoque un moteur `FIRE_DYNAMICS_ENGINE`. L'approche
hybride (Option C, actée) réserve cette question à un second RFC après
preuve de concept. Les fonctions spécifiques au feu (propagation,
assimilation, sautes de feu, pyroconvection) sont pour l'instant portées
par des extensions du Simulation Engine + ForeFire comme service externe.

---

## 6. Architecture offline-first

### 6.1 Principe directeur (C-06)

> **Le terrain reste opérationnel en mode dégradé. Le serveur enrichit
> mais ne conditionne pas.**

Les zones DFCI sont des zones blanches (pas de réseau cellulaire
garanti). L'architecture est conçue pour fonctionner en mode dégradé
lorsque la connexion avec le serveur est perdue ou intermittente.

### 6.2 Répartition edge / serveur

| Couche | Rôle | Mode dégradé |
|---|---|---|
| **Edge (drone + GCS terrain)** | Détection, messages compacts, cache tuiles, vol autonome, visualisation locale | **Fonctionne seul** — le drone continue sa mission, le GCS affiche les détections et le vol |
| **Serveur (jumeau numérique)** | Assimilation, prédiction ForeFire, ensembles, émulateur, analyse d'enjeux, réentraînement | **Suspendu** — reprend à la reconnexion ; les données edge sont synchronisées (file d'attente) |

### 6.3 Communications hiérarchiques par priorité (C-01)

| Priorité | Type de données | Techno | Latence cible |
|---|---|---|---|
| **Critique** | Alertes de détection, vecteur de feu, position | LoRa maillé (Meshtastic) | < 30 s |
| **Standard** | Télémétrie drone, état de mission, météo locale | 4G/5G avec file d'attente | < 5 s (si couverture) |
| **Large bande** | Imagerie, vidéo, VLM | Large bande ou stockage à bord | Différé (à la récupération ou si lien disponible) |

**Messages compacts** (C-02) : ~200 octets (détection, lat/lon, intensité,
vecteur, horodatage). Spécification à écrire en Phase 2.

### 6.4 Cache et synchronisation

- **Cache de tuiles** : le GCS-Lite pré-charge les tuiles ortho/MNT/DFCI
  de la zone d'intervention avant le déploiement. Le terrain dispose
  d'une carte complète sans connexion.
- **File d'attente** : les données edge (détections, télémétrie) sont
  stockées localement et synchronisées au serveur dès que la connexion
  rétablit. Aucune donnée n'est perdue.
- **Mode dégradé explicite** : le GCS affiche clairement l'état de
  connexion (vert/orange/rouge) et ce qui est en cache vs temps réel.

### 6.5 Souveraineté des données (S-11, M-05)

- Chiffrement des liaisons (MAVLink 2 signé — MAVLink par défaut est peu
  sécurisé).
- Authentification des nœuds mesh.
- Détection d'anomalies sur messages (fausses détections injectées).
- Résilience brouillage GPS.
- Modèles IA français hébergés UE (Mistral, Pixtral) pour les rapports
  RETEX et synthèses COS — argument DGSCGC/SDIS que les modèles US ne
  cochent pas.
- Anticipation qualification SecNumCloud/ANSSI pour vendre à la
  sécurité civile.

---

## 7. Garde-fous non négociables

*Rappel de DEC-000003 et de la Constitution GSIE. Ces garde-fous sont
architectureux : ils sont implémentés dans la conception, pas dans la
documentation seule.*

### 7.1 Outil d'aide à la décision, jamais commandement

> GSIE-Ignis est un **outil d'aide à la décision** du COS / CODIS, jamais
> un système de commandement (GSIE-CON-001, DEC-000003).

**Implications architecturales** :
- Toutes les sorties présentées au COS sont des **suggestions
  explicables et contournables**.
- Aucune action automatique sur le terrain (largage, marquage) —
  S-09 écarté.
- L'interface affiche l'incertitude, pas seulement la prédiction (G-03).
- Le système recommande, le COS décide.

### 7.2 Pas d'alerte population (FR-Alert)

> **Aucune alerte directe à la population** — prérogative régalienne
> (FR-Alert, DEC-000003, G-04).

**Implications architecturales** :
- Aucun canal d'alerte publique dans le système.
- Le système produit de l'information pour le COS, qui décide ou non
  de déclencher FR-Alert via sa chaîne de commandement.

### 7.3 Cause probable = hypothèse

> La sortie « cause probable » du feu reste une **hypothèse
> exploratoire**, jamais une conclusion (DEC-000003, RFC-0004 §8.2).

**Implications architecturales** :
- La sortie cause probable est présentée comme « hypothèse(s) possible(s) »
  avec un niveau d'incertitude explicite.
- L'interprétation RCCI de la fumée (P-04) est une **suggestion**, jamais
  une attribution de cause.
- Aucune présentation juridiquement contraignante.

### 7.4 « Autonome » = navigation uniquement

> Le terme « autonome » s'applique à la navigation drone, pas aux
> décisions opérationnelles (RFC-0004 §8.3).

**Implications architecturales** :
- L'autonomie du drone couvre : vol, navigation, plans de vol,
  décollage/atterrissage, fail-safe, RTH.
- Le télépilote peut reprendre la main à tout moment (V-04).
- Aucune autonomie de décision opérationnelle (alerte, intervention,
  reconfiguration de moyens).

### 7.5 Déconfliction aérienne (V-08)

> Un drone non coordonné = arrêt des largages. La déconfliction est une
> **obligation absolue** et un argument de vente.

**Implications architecturales** :
- Transpondeur / e-identification obligatoire.
- Intégration U-space.
- Règle absolue de dégagement automatique à l'arrivée d'aéronefs
  pilotés (Canadair, Dash, HBE).

### 7.6 RGPD sur détection de personnes (P-09, S-02)

> La détection de personnes/véhicules en zone est soumise au RGPD.

**Implications architecturales** :
- Les données de détection de personnes ne sont pas stockées
  durablement sans base légale.
- L'interface présente la présence de personnes comme une information
  tactique immédiate, pas comme un dispositif de surveillance.
- Purge automatique des données de détection après l'intervention.

---

## 8. Architecture technique — stack langages

| Couche | Langage | Justification |
|---|---|---|
| Orchestration (banc, pipelines, assimilation) | **Python** | Écosystème scientifique (NumPy, SciPy, GeoPandas), MAVSDK-Python, rapidité de prototypage |
| Cœur IP (assimilation, émulateur, futures briques embarquées) | **Rust** | Performance, sûreté mémoire, bindings Python via pyo3, cible embarquée Jetson |
| API temps réel (WebSocket/gRPC) | **Go** (optionnel) | Concurrence native, faible latence, typage strict |
| GCS-Lite (interface) | **TypeScript** | Écosystème web, MapLibre GL, WebSocket natif |
| GCS-Cinéma (visualisation, phase 4+) | **C++ / Unreal** | Unreal Engine 5.x, Cesium for Unreal, Niagara |
| ForeFire (service externe) | **C++** (non modifié) | Service GPL isolé, frontière de processus |

---

## 9. Jalons d'architecture

Les jalons GSIE-Ignis s'inscrivent dans les phases GSIE globales (voir
`22_PROJECT_MEMORY/GSIE-Ignis.md` §10) :

| Jalon | Contenu architectural | Phase GSIE |
|---|---|---|
| **Jalon 0** — Cartographie | Comparatifs sourcés (moteurs, simulation, capteurs, comms) | Phase 1 (documentaire) |
| **Jalon 1** — Architecture & spec | Ce document + pipeline + archi drone + ADRs + contrat API | Phase 2 (actuel) |
| **Jalon 2** — Banc intégral | ForeFire + PX4 SITL/Gazebo + détecteur virtuel + assimilation + GCS-Lite | Phase 2–3 |
| **Jalon 3** — Validation historique | Landiras 2022, comparaison Copernicus EMS | Phase 3 |
| **Jalon 4** — Hardware in the loop | Jetson réel + GCS-Cinéma (Unreal/Cesium) | Phase 3–4 |
| **Jalon 5** — Premier drone réel | Vol à vue | Phase 4 |
| **Jalon 6** — Pilote SDIS | Déploiement opérationnel | Phase 4+ |

---

## 10. Séquençage business (S-08)

> **Le MVP payable n'est PAS le drone.** C'est jumeau numérique + analyse
> d'enjeux sur données existantes (satellite, stations fixes, saisie
> manuelle position feu). Un COS qui clique un départ de feu et voit en
> 10 s la propagation + maisons menacées + délais → se vend SANS drone,
> finance la suite, et crée la relation SDIS qui fournira les données de
> la partie drone. Le drone est phase 2 du business.

**Implications architecturales** :
- L'architecture est modulaire : le jumeau numérique + analyse d'enjeux
  + GCS-Lite fonctionnent **sans le composant drone**.
- Le composant drone est une brique additionnelle, branchée sur la même
  API temps réel.
- Le MVP (sans drone) consomme : données satellite (Sentinel, FIRMS,
  MTG-FCI), saisie manuelle de position, AROME, couches GIS. Il produit :
  propagation ForeFire + enjeux + présentation COS.

---

## 11. Interopérabilité SDIS (S-12)

> Un système qui s'intègre s'achète ; un système qui veut tout remplacer
> se refuse.

**Implications architecturales** :
- Export dans les formats SDIS : symbologie SITAC normalisée, flux vers
  NexSIS 18-112, compatibilité SGA/SGO.
- L'architecture prévoit une couche d'export/adaptation de format,
  découplée du cœur.
- L'API temps réel est conçue pour être consommable par des systèmes
  tiers SDIS.

---

## 12. RETEX automatique (S-07)

> Rapport comparant prédictions vs réalité + décisions COS + évolution
> réelle. Nourrit le réentraînement ET devient un produit vendable.

**Implications architecturales** :
- La « boîte noire » du front (J-10) capture le flux temporel
  ultra-compact (position/intensité/vecteur à chaque pas) pour rejouer
  n'importe quel feu passé.
- Le RETEX automatique est un sous-produit de l'architecture, pas un
  module séparé.
- Chaque intervention rend le système plus crédible (réentraînement
  continu sur du réel).

---

## 13. Sources et références

### 13.1 Sources scientifiques

- Filippi et al., ForeFire, RSFF'18 / 2014 — méthode front-tracking DES
- Allaire, Filippi & Mallet (2020), ensembles de simulations, *Int. J.
  Wildland Fire*
- Pais et al. (2021), Cell2Fire, *Frontiers in Forests and Global Change*
- Kim, Pais & González (2025), optimisation contre contours réels, *Sci.
  Rep.*
- ForestFireVLM, *MDPI Drones* 2025 — VLM pour description de scène feu

### 13.2 Sources techniques

- ForeFire : `github.com/forefireAPI/forefire`, `forefire.univ-corse.fr`
  (FireCaster, OpenDFCI, Entente Valabre)
- PX4 : `docs.px4.io` (SITL, Gazebo, variables simulation)
- MAVSDK : `mavsdk.io` (API Python, MAVLink)
- Gazebo : `gazebosim.org` (nouvelle génération « Gz »)
- wildfire_ROS_models : `github.com/forefireAPI/wildfire_ROS_models`
  (substituts ANN, export C++)

### 13.3 Documents de gouvernance

- `00_CONSTITUTION/` — Constitution GSIE (prime sur tout)
- `02_RFC/RFC-0004.md` — RFC GSIE-Ignis (ADOPTÉ)
- `03_DECISIONS/DEC-000003.md` — Adoption RFC-0004 + garde-fous
- `03_DECISIONS/DEC-000005.md` — Archive du banc
- `22_PROJECT_MEMORY/GSIE-Ignis.md` — Registre d'idées (60+ idées, 9
  sections)
- `22_PROJECT_MEMORY/GSIE-Ignis/Phase0_comparatif_moteurs_simulation.md`
  — Comparatif sourcé Phase 0
- `22_PROJECT_MEMORY/GSIE-Ignis/guide_installation_banc.md` — Guide
  d'installation
- `22_PROJECT_MEMORY/GSIE-Ignis/journal.md` — Journal de bord

---

## 14. Questions ouvertes

1. **Moteur dédié Fire Dynamics** : justifié après preuve de concept ?
   (RFC-0004 §9, second RFC à ouvrir)
2. **Contrat d'interface API temps réel** : WebSocket vs gRPC vs
   hybride ? (G-11, à spécifier en Jalon 1)
3. **Frontière de processus ForeFire** : HTTP `listenHTTP` vs
   interpréteur scriptable vs Docker ? (ADR à écrire)
4. **CorrDiff-France** : fine-tuning du modèle météo IA sur le relief
   français — partenariat Météo-France ou CIFRE ? (M-09/M-12)
5. **Souveraineté matériel drone** : DJI Dock vs alternatives
   européennes pour la sécurité civile ? (V-09, S-11)
6. **U-space en France 2026** : procédures de coordination
   drone/aéronefs bombardiers d'eau ? (V-08)

---

> **Rappel final** : GSIE-Ignis est un outil d'aide à la décision. Le COS
> reste le décideur. L'architecture sert cette posture, elle ne la
> contourne pas.
