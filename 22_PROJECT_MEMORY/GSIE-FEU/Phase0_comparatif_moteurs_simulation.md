# GSIE-Feu — Phase 0, Livrable 1
# Comparatif : moteurs de propagation & pile de simulation

> Version 1.0.0 — 2026-07-11
> Statut : recommandations à valider par Camille (décisions → ADRs en Phase 1)
> Périmètre : moteur de propagation du feu, émulation neuronale, pile de simulation drone. Les comparatifs capteurs et communications feront l'objet des livrables 2 et 3.

---

## Résumé exécutif (décisions proposées)

| Décision | Recommandation | Confiance |
|---|---|---|
| Moteur de propagation principal | **ForeFire** (CNRS / Université de Corse) | Haute |
| Moteur secondaire (probabiliste massif) | **Cell2Fire (C2F-W)** — à évaluer en phase 2, non bloquant | Moyenne |
| Émulateur neuronal | Partir du dépôt **forefireAPI/wildfire_ROS_models** (ANN surrogates + export C++) | Haute |
| Autopilote simulé (puis réel) | **PX4** | Haute |
| Simulateur de vol | **Gazebo (nouvelle génération "Gz")** — PAS Gazebo Classic | Haute |
| API de mission | **MAVSDK-Python** (+ passerelle ROS 2 uXRCE-DDS si besoin ultérieur) | Haute |
| Photoréalisme simulation | ⚠️ AirSim archivé par Microsoft → ne pas construire dessus. Photoréalisme via GCS-Cinéma (Cesium for Unreal) branché sur l'API temps réel, pas via le simulateur de vol | Haute |
| Point de vigilance juridique | ForeFire est **GPL v3** → l'intégrer comme **service séparé** (frontière de processus), jamais lié dans notre code propriétaire | Haute |

---

## 1. Moteurs de propagation du feu

### 1.1 ForeFire — recommandé comme moteur principal

**Fiche d'identité.** Moteur open source de simulation de propagation écrit en C++, développé par le CNRS à l'Université de Corse Pascal Paoli, utilisé pour la recherche et la prévision opérationnelle. Licence GPL v3. Dépôt : github.com/forefireAPI/forefire.

**Ce qui le distingue techniquement :**
- **Suivi de front (front-tracking)** par simulation à événements discrets : le front de feu est suivi par des marqueurs advectés en résolvant le problème inverse (distance fixée, durée calculée), ce qui rend la précision du front moins dépendante de la résolution des données d'entrée — par opposition aux automates cellulaires qui héritent de la grille.
- **Performance** : calibré grande échelle, 1 000 ha simulés en moins de 10 s à résolution métrique. C'est compatible avec notre boucle d'assimilation à recalage ~5 min (des dizaines de scénarios par cycle sont envisageables même sans émulateur).
- **Multi-modèles de vitesse (ROS)** : Rothermel, Balbi (développé par la même équipe), et modèles utilisateurs ajoutables — le moteur est conçu comme banc d'essai de nouvelles formulations. Pour nous : porte ouverte à des modèles calibrés sur combustibles français.
- **Couplage atmosphérique** : couplage bidirectionnel conçu avec Méso-NH (CNRS/Météo-France) pour les effets feu→atmosphère→feu (pyroconvection). Hors périmètre MVP, mais crucial pour le volet recherche (comportements extrêmes, J-11 sautes de feu).
- **Intégration** : bindings Python (pyForeFire), interpréteur scriptable, interface HTTP embarquée (listenHTTP), Docker fourni, MPI pour le parallélisme. Entrées : paysage NetCDF (altitude, vent, distribution de combustible) analogue au format Landscape de FARSITE.

**L'argument décisif (au-delà de la technique).** ForeFire n'est pas qu'un code de labo : via la plateforme FireCasterAPI (projet ANR FireCaster), il est **déployé en opérationnel depuis juin 2020 à l'échelle nationale au sein du système d'information OpenDFCI de l'Entente Valabre**, où il sert à croiser aléas et enjeux et à partager les données en temps réel entre structures de commandement de la zone Sud. Autrement dit :
1. Les SDIS de la zone Sud **connaissent déjà** cet outil → notre système parlera un langage de simulation déjà légitime chez nos clients.
2. L'Entente Valabre, que nous avions identifiée comme porte d'entrée (D-02), est **déjà partenaire** de l'équipe ForeFire → un partenariat scientifique avec l'Université de Corse (UMR SPE 6134, contact historique : J.-B. Filippi) nous raccorde au même écosystème.
3. La valorisation industrielle de FireCaster est portée par la SATT Sud-Est, l'usage sécurité civile restant gratuit — il existe donc un cadre connu pour un usage commercial à discuter (bureaux d'études et assurances explicitement cités comme cibles de valorisation).

**Points de vigilance :**
- **GPL v3** : toute œuvre dérivée liée à ForeFire doit être publiée en GPL. Parade architecturale standard : exécuter ForeFire comme **processus/service séparé** (son interface HTTP ou l'interpréteur s'y prêtent nativement) et communiquer par messages — notre code propriétaire n'est alors pas une œuvre dérivée. À formaliser en ADR avec, si besoin, un avis juridique avant commercialisation.
- La mise en données réelle (flux météo, combustible) est signalée par l'équipe elle-même comme fortement dépendante de l'infrastructure — la plateforme de scripting opérationnelle n'est pas open source. Nous devrons construire notre propre pipeline de préparation de données (c'était prévu : c'est notre valeur d'assemblage).
- Communauté plus petite que les outils US ; documentation académique. Compensé par la proximité géographique/linguistique de l'équipe et le cas d'usage identique au nôtre.

### 1.2 Cell2Fire / C2F-W — recommandé en second moteur (probabiliste)

Simulateur à base cellulaire (grille raster) en C++, open source, parallélisé. Validé contre Prometheus (le simulateur de référence canadien) : précision similaire (>90 %) pour un temps de calcul jusqu'à 30× inférieur, avec un temps d'exécution croissant linéairement là où Prometheus croît exponentiellement. La famille C2F-W supporte plusieurs systèmes de combustible (FBP canadien, Scott & Burgan US, KITRAL chilien) et inclut un modèle de feu de cime. Conçu pour les **simulations stochastiques massives et les cartes de risque** (burn probability maps) — exactement notre besoin J-09 (carte de risque dynamique) et les scénarios probabilistes.

Travaux récents (Kim, Pais & González, *Sci Rep* 2025) : optimisation sans dérivée des facteurs de propagation contre des contours réels (F1 de 0,74 → 0,83 sur le feu de Dogrib) — méthodologiquement très proche de notre boucle d'assimilation, à lire absolument.

**Positionnement chez nous** : ForeFire pour le front opérationnel temps réel (précision du front), Cell2Fire pour les grandes campagnes probabilistes hors ligne (risque, entraînement de l'émulateur). Non bloquant pour le démonstrateur Landiras ; évaluation en phase 2.

**Vigilance** : pas de système de combustible « France » natif (FBP/S&B/KITRAL) → travail de correspondance BD Forêt → modèles de combustible nécessaire quel que soit le moteur, mais calibration à prévoir. Certains dépôts de la famille portent des mentions « research use only » : vérifier la licence du dépôt précis retenu (C2F-W) avant tout usage commercial.

### 1.3 Alternatives évaluées et écartées (pour l'instant)

| Moteur | Nature | Verdict |
|---|---|---|
| **FARSITE / FlamMap** (US Forest Service) | Référence historique US, front elliptique de Huygens | ❌ comme moteur : orienté Windows/desktop, pas conçu pour l'intégration serveur ; ✅ comme **référence de validation** (formats, jeux de test, littérature immense) |
| **WRF-SFIRE** | Couplage complet feu-atmosphère (modèle météo WRF) | ⏸️ Trop lourd pour l'opérationnel temps réel (heures de calcul). Pertinent plus tard pour la recherche sautes de feu/pyroconvection, en concurrence avec ForeFire×Méso-NH |
| **ELMFIRE** | Level-set Eulérien, utilisé dans des chaînes opérationnelles US cloud | 🔍 Sérieux, mais écosystème US (Landfire, Scott & Burgan) ; à garder en veille, pas de bénéfice net vs ForeFire pour la France |
| **Prometheus** (Canada) | Référence canadienne (FBP) | ❌ Windows, fermé à l'intégration ; sert déjà d'étalon à Cell2Fire |
| Solveurs recherche (IGA/FEM, CFD type FIRETEC/QUIC-Fire) | Physique fine | ⏸️ Échelle parcelle/labo, pas territoire. QUIC-Fire à suivre pour le brûlage dirigé (marché secondaire) |

### 1.4 Émulateur neuronal — le chaînon vers le temps réel probabiliste

Constat clé de la recherche : l'équipe ForeFire maintient **wildfire_ROS_models**, une bibliothèque Python des modèles de vitesse de propagation avec implémentations de référence, suite de tests, **entraînement de substituts ANN (réseaux de neurones) et export C++ pour intégration ForeFire**. C'est exactement la brique J-02 (émulateur) — partiellement déjà construite par l'équipe qui fait référence.

Stratégie proposée en trois temps :
1. **MVP** : ForeFire brut (10 s / 1 000 ha suffisent largement au démonstrateur et aux premiers ensembles).
2. **V1** : substituts ANN au niveau du modèle de vitesse (via wildfire_ROS_models) pour accélérer les ensembles.
3. **V2 (recherche)** : émulateur du simulateur complet (U-Net/ConvLSTM entraîné sur des campagnes Cell2Fire/ForeFire massives) pour les centaines de scénarios en continu — publication possible, lien CIFRE.

La littérature du domaine (Allaire, Filippi & Mallet 2020, génération et évaluation d'ensembles de simulations ForeFire, *IJWF*) fournit la méthodologie d'ensembles probabilistes directement sur notre moteur retenu.

---

## 2. Pile de simulation drone

### 2.1 Autopilote : PX4 recommandé

Les deux candidats (PX4, ArduPilot) sont matures, éprouvés en production, et disposent de SITL solides. Critères discriminants pour GSIE-Feu :

| Critère | PX4 | ArduPilot |
|---|---|---|
| Licence | **BSD** (permissive — cohérent avec un produit commercial) | GPL (contraintes de diffusion sur les modifs firmware) |
| Simulation recommandée | Gazebo nouvelle génération, maintenu par l'équipe cœur | SITL très mature, multi-véhicules en un binaire |
| Écosystème vision/recherche | La pile PX4 SITL + Gazebo + VIO est la plus utilisée en recherche de navigation visuelle ; intégration ROS 2 native (uXRCE-DDS) | Très présent en académique aussi ; approche odométrie externe différente |
| API de mission | MAVSDK-Python (propre, moderne) | pymavlink/DroneKit (DroneKit vieillissant) |
| Dossiers réglementaires | Cité dans des dossiers BVLOS de référence (ex. Zipline aux US) | Dominant en agricole/heavy-lift |

**Recommandation : PX4**, pour la licence BSD (liberté commerciale sur nos modules embarqués), l'alignement avec l'écosystème recherche vision/ROS 2 dont nous dépendrons (P-01, P-02), et MAVSDK-Python comme API de mission propre. ArduPilot reste un plan B parfaitement viable : MAVLink étant commun, notre GCS et une grande partie de la logique de mission resteraient portables — c'est aussi un argument pour bien isoler la couche mission de la couche autopilote (ADR à écrire).

### 2.2 Simulateur : Gazebo (nouvelle génération)

Position officielle PX4 : **utiliser Gazebo (ex-« Ignition ») pour tout nouveau projet** ; Gazebo Classic est rétrogradé en support communautaire et n'est plus recommandé. Gazebo moderne apporte : rendu 3D, mondes personnalisés, caméras/LiDAR simulés, large bibliothèque de capteurs, plus grande communauté — tout ce qu'il faut pour nos étages 2 et 3 (drone simulé + perception).

Points pratiques utiles pour notre banc :
- Mode **headless** (sans UI) pour les campagnes automatisées.
- **PX4_HOME_LAT/LON/ALT** : positionner le décollage aux coordonnées réelles (ex. massif de Landiras) pour aligner simulation et couches SIG.
- **PX4_SIM_SPEED_FACTOR** : accélérer la simulation (tester des heures de patrouille en minutes).
- Multi-véhicules supporté → V-03/V-06 (rotation de flotte, orchestrateur) testables en simulation ; des frameworks communautaires récents (ROS 2, xacro, capteurs configurables) existent pour le multi-agents PX4/Gazebo.

**⚠️ AirSim : ne pas construire dessus.** AirSim (Microsoft, base Unreal, photoréaliste) a été archivé par Microsoft ; le fork communautaire Colosseum n'offre pas de garantie de pérennité. Conséquence architecturale heureuse : notre photoréalisme vit dans le **GCS-Cinéma (Cesium for Unreal)** branché sur l'API temps réel (G-11), pas dans le simulateur de vol. Le simulateur reste Gazebo (physique, capteurs), l'image cinéma reste Unreal (visualisation) — découplage sain. Pour la génération de données synthétiques (D-05), on évaluera en phase 4 : rendu Gazebo suffisant pour la fumée lointaine vs pipeline Unreal dédié (via le GCS-Cinéma) pour le photoréalisme.

*(Option future à garder en veille : NVIDIA Isaac Sim pour la synthèse photoréaliste massive de données — synergie avec l'écosystème Jetson — mais complexité et empreinte GPU élevées : rien pour le MVP.)*

### 2.3 Architecture du banc de simulation (phase 2) — mise à jour

```
┌────────────────────────────────────────────────────────────────┐
│ SERVEUR (lourd)                                                │
│                                                                │
│  ForeFire (service GPL isolé, HTTP/processus)                  │
│    ├── « feu vérité » caché au système (scénario)              │
│    └── moteur de prédiction de NOTRE jumeau numérique          │
│  Assimilation (filtre d'ensemble) ── Enjeux (PostGIS)          │
│  API temps réel (WebSocket/gRPC) ──► GCS-Lite (MapLibre)       │
│                                  └─► GCS-Cinéma (Unreal, ph.4) │
└───────────────┬────────────────────────────────────────────────┘
                │ MAVSDK-Python (mission) / MAVLink
┌───────────────┴───────────────────────────────┐
│ TERRAIN simulé (léger)                        │
│  PX4 SITL × N drones ── Gazebo (Gz, headless) │
│  Détecteur virtuel bruité (interroge le feu   │
│  vérité, renvoie détections imparfaites)      │
└───────────────────────────────────────────────┘
```

Le même ForeFire joue deux rôles distincts (feu « vérité » du scénario, et moteur de prédiction du jumeau) avec des paramètres volontairement différents — c'est ce qui rend le test d'assimilation honnête : le système doit converger vers une vérité qu'il ne connaît pas.

---

## 3. Prochaines actions découlant de ce livrable

1. **Valider les recommandations** (Camille) → je rédige les ADR-001 (ForeFire, avec stratégie GPL) à ADR-004 (Gazebo Gz) en ouverture de Phase 1.
2. **Contact scientifique Université de Corse / équipe ForeFire** à préparer (après le démonstrateur Landiras : arriver avec un résultat, pas une demande).
3. **Livrable 2 de Phase 0** : matrice capteurs (P-10) + comparatif communications (C-05).
4. **Guide d'installation du banc** (ForeFire Docker + PX4 SITL + Gazebo sur le PC de Camille) : peut démarrer immédiatement, ForeFire fournissant une démo Aullène (Corse) prête à l'emploi pour valider l'installation.

## Sources principales
- github.com/forefireAPI/forefire ; forefire.univ-corse.fr (FireCaster) ; pages Université de Corse (déploiement OpenDFCI/Entente Valabre, juin 2020 ; SATT Sud-Est)
- Filippi et al., ForeFire (RSFF'18 ; 2014) — méthode front-tracking DES
- Allaire, Filippi, Mallet (2020), ensembles de simulations, *Int. J. Wildland Fire*
- Pais et al. (2021), Cell2Fire, *Frontiers in Forests and Global Change* ; Kim, Pais, González (2025), *Scientific Reports* — optimisation contre contours réels ; dépôts fire2a (C2F-W, C2FK, C2FSB)
- docs.px4.io (Simulation — statut Gazebo/Gazebo Classic, variables SITL, rapport d'enquête simulation Dronecode déc. 2025) ; comparatifs PX4/ArduPilot 2025-2026 ; docs ArduPilot SITL

---

> **Note de rangement (2026-07-12)** : document reçu via le pack de contexte agent GSIE-Feu, classé ici sans modification de contenu. Statut de gouvernance : recommandations techniques, non des décisions actées — restent à valider par le Fondateur puis à tracer en `DEC-`/ADR le moment venu, conformément à `02_RFC/RFC-0004.md`.
