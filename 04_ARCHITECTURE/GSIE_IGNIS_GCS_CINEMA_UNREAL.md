# GCS-Cinéma : Unreal Engine — architecture, briques existantes, précédents scientifiques

| Champ | Valeur |
|---|---|
| **Livrable** | 211 — GCS-Cinéma Unreal Engine (GSIE-Ignis) |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date de révision** | 2026-07-12 |
| **Lois fondatrices** | GSIE-CON-004, GSIE-CON-005, GSIE-CON-007 |
| **Constitutions liées** | Technique (T-2, T-8, T-10) |
| **Directives liées** | GSIE-DIR-0005 (jumeau numérique vivant), GSIE-DIR-0006 (moteur cognitif) |
| **RFC de référence** | RFC-0004 (GSIE-Ignis, §8 garde-fous) |
| **Décision d'adoption** | DEC-000010 (adoption UE 5.8 + Cesium) |
| **Documents connexes** | `GSIE_IGNIS_ARCHITECTURE.md` (livrable 208), `GSIE_IGNIS_DATA_PIPELINE.md` (livrable 209), `GSIE_IGNIS_DRONE_ARCHITECTURE.md` (livrable 210) |

> Version 1.0.0 — 2026-07-12
> Complète le Livrable 1 (moteurs de propagation & pile de simulation). Ce document couvre le poste de commandement 3D (G-05 à G-13 du registre).
> Principe directeur : « avec ce qui existe » — chaque recommandation ci-dessous s'appuie sur une capacité native du moteur, un plugin établi, ou une publication de recherche déjà validée. Rien n'est inventé de zéro.

---

## Résumé exécutif

| # | Brique | Recommandation | Statut |
|---|---|---|---|
| 1 | Moteur | Unreal Engine 5.8 (dernière version majeure UE5, sortie 17/06/2026) | ✅ décidé |
| 2 | Terrain géoréférencé | Cesium for Unreal (Cesium ion + 3D Tiles) | ✅ décidé |
| 3 | Ingestion de données temps réel | Module natif `WebSockets` + `Json` d'Unreal (C++), pas de plugin tiers nécessaire | ✅ décidé |
| 4 | Feu / fumée | Niagara, piloté par les données du jumeau numérique, à la manière de FIRETWIN (§3) | ✅ décidé |
| 5 | Photogrammétrie / Gaussian Splatting | Pipeline Cesium ion (support natif des Gaussian Splats via 3D Tiles) | 🔍 à tester |
| 6 | Simulation drone dans Unreal (recherche) | Cosys-AirSim (fork maintenu, voir correction §6) | 🔍 veille |
| 7 | IA embarquée dans l'éditeur | Plugin MCP expérimental UE 5.8 (connexion directe de Claude au projet) | 🔍 à surveiller |

---

## 1. Où en est Unreal Engine mi-2026

Le calendrier est maintenant clair et stable pour les 18-24 prochains mois : <cite index="27-1">UE5.8, sorti en juin 2026, marque la fin du cycle majeur UE5 ; UE6 est officiellement annoncé mais son accès anticipé n'arrivera qu'à la fin 2027, et sa version stable qu'en 2028</cite>. Concrètement : **construis sur UE5.8**, sans te poser la question d'UE6 avant 2028 — les compétences et le code UE5 se transposeront de toute façon.

UE 5.8 apporte, en fonctionnalités jugées prêtes pour la production : MegaLights, Audio Insights, Live Link Hub, Movie Render Graph, et un outil expérimental de terrain sans limite de heightfield (« Mesh Terrain ») — pertinent pour couvrir un massif entier sans les contraintes habituelles de résolution.

## 2. Cesium for Unreal — le terrain, résolu

Cesium for Unreal est un plugin open source (racheté par Bentley Systems en 2024, donc adossé à un acteur infrastructure sérieux, pas un projet fragile) qui gère exactement notre problème le plus dur : <cite index="42-1">il combine un globe WGS84 haute précision avec les standards ouverts 3D Tiles pour streamer du contenu 3D réel — photogrammétrie, terrain, imagerie, bâtiments — directement dans Unreal Engine</cite>.

Ce qu'il résout pour nous, concrètement :
- **Géoréférencement précis** : le composant `CesiumGeoreference` gère la courbure terrestre et la gravité radiale — un problème qu'on aurait dû résoudre nous-mêmes sinon.
- **Ingestion de nos propres données** : Cesium ion traite LAS/LAZ (notre LiDAR HD IGN), GeoTIFF, glTF et l'imagerie drone pour les convertir en 3D Tiles streamables — un pipeline tout fait pour nos couches SIG françaises.
- **Découverte majeure pour G-05/M-19** : <cite index="48-1">Cesium ion supporte nativement les Gaussian Splats via 3D Tiles avec streaming par niveau de détail</cite>. Autrement dit, une reconstruction 3D Gaussian Splatting faite depuis une vidéo drone (M-19) peut passer par le **même pipeline** que le terrain et l'imagerie — pas besoin d'un système de rendu séparé. Ça simplifie beaucoup l'architecture qu'on avait esquissée.
- **Vue globale gratuite** : intégration des 3D Tiles photoréalistes de Google Maps comme contexte large avant de zoomer sur nos données haute résolution propres.

Compatibilité : le plugin suit officiellement les trois dernières versions d'Unreal Engine — la compatibilité UE5.8 est donc couverte par leur politique de support, à vérifier au moment de l'installation (version exacte disponible sur le dépôt GitHub CesiumGS/cesium-unreal ou via Fab, l'ex-Marketplace Unreal).

## 3. Ingestion de données temps réel — plus simple que prévu

C'est le point technique le plus important de ce document. Pas besoin de plugin exotique : <cite index="52-1">Unreal Engine expose nativement des modules WebSocket, HTTP et JSON</cite>, utilisés en interne par Epic pour sa propre Remote Control API. Deux façons de les exploiter :

- **En C++ natif** (recommandé pour toi vu ton niveau) : les classes `FWebSocketsModule` / `IWebSocket` du module `WebSockets`, combinées au module `Json`, permettent de se connecter directement à notre API temps réel (G-11, WebSocket/JSON) sans aucune dépendance externe. C'est la voie la plus propre et la plus pérenne.
- **En Blueprint pur** (pour itérer vite sans C++) : des wrappers exposent ces modules natifs aux Blueprints — plusieurs existent sur Fab et en open source (par exemple des plugins communautaires comme *ue-websockets-helper* ou *BlueprintWebSocket*), à évaluer au moment de l'implémentation selon leur maintenance à jour pour 5.8.

Pour les données d'animation (positions de drones lissées, caméras) plutôt que du texte JSON brut, Unreal a aussi **Live Link**, son système natif de streaming temps réel — plus lourd à mettre en place (architecture Source/Subject) mais avec interpolation de frames intégrée. À garder en réserve si le WebSocket brut donne un rendu saccadé sur les positions de drones ; pas nécessaire pour un premier prototype.

## 4. Feu et fumée dans Niagara — méthode éprouvée

Niagara (le système de particules/fluides d'Unreal) est confirmé comme le bon outil par un précédent académique direct (voir §5) : fumée et flammes pilotées par des **émetteurs physiques** — traînée aérodynamique, vent, gravité, vélocité, accélération, collisions — alimentés en paramètres par notre jumeau numérique (position du front via ForeFire, intensité via la thermique radiométrique, direction via le vent mesuré). C'est exactement l'approche G-06 qu'on avait posée ; elle est maintenant validée par un usage réel en recherche, pas seulement par notre intuition.

## 5. Précédents scientifiques directs — la vraie découverte de cette session

Il existe déjà plusieurs publications qui construisent quasiment notre GCS-Cinéma. À connaître absolument, y compris pour la crédibilité scientifique et les dossiers de financement :

**FIRETWIN** (2025, financé NASA + NSF) — un jumeau numérique cyber-physique qui <cite index="63-1">intègre un modèle couplé atmosphère-feu (CAWFE) dans Unreal Engine 5, avec des émetteurs de feu Niagara modélisant traînée aérodynamique, vent, gravité et collisions</cite>. Le système <cite index="63-1">simule aussi des capteurs RGB, profondeur, satellite et thermique, et complète la 3D par des cartes 2D de masse de combustible et d'intensité du feu</cite>. Point remarquable : <cite index="63-1">le système consomme les prédictions d'un modèle IA de prévision ET génère des données d'entraînement synthétiques en retour</cite> — exactement notre idée D-05, validée indépendamment par une équipe financée NASA. Limite reconnue par les auteurs eux-mêmes : exigeant en matériel, encore en phase de validation opérationnelle — une honnêteté qui nous rassure sur notre propre calendrier réaliste.

**FIRE-VLM** (2026) — encore plus proche de notre ambition long terme : un drone simulé apprend à traquer un front de feu par renforcement (PPO), guidé par un modèle vision-langage type CLIP, dans un jumeau numérique Unreal Engine 5.3 <cite index="68-1">construit sur un terrain USGS haute résolution avec cartes de combustible LANDFIRE et produits de front de feu dérivés de CAWFE</cite>. C'est le pendant américain de notre M-20 (raisonnement) et V-06 (orchestrateur) combinés — une piste de recherche à garder pour plus tard (potentiellement CIFRE), pas pour le MVP.

**IVSR** (février 2026) — une « salle de situation virtuelle » avec agents IA autonomes, qui <cite index="65-1">ingère en continu imagerie multi-capteurs, données météo et modèles 3D de forêt pour créer une réplique virtuelle vivante de l'environnement du feu, et calibre les tactiques d'intervention en comparant les conditions émergentes à une bibliothèque de simulations de désastres précalculées</cite>. Cette idée de « bibliothèque de scénarios précalculés » comparée en continu au direct est une piste intéressante pour accélérer notre émulateur (J-02) sans attendre le neural operator complet.

Existe aussi une revue de synthèse complète sur les jumeaux numériques appliqués aux feux de forêt (*Journal of Forestry Research*, Springer) — à citer dans tout dossier académique ou de financement pour montrer que le domaine est reconnu, pas une lubie isolée.

**Lecture stratégique** : ces publications confirment que notre approche est scientifiquement défendable et récente (aucune n'a plus d'un an), mais aussi qu'on n'est plus seuls sur ce terrain précis — l'équipe FIRETWIN (financement NASA/NSF) mérite d'être identifiée nommément (auteurs, laboratoire) comme piste de veille, voire de contact académique à moyen terme, sur le modèle de ce qu'on fait avec l'Université de Corse pour ForeFire.

## 6. Correction au Livrable 1 — AirSim mérite d'être nuancé

Le Livrable 1 disait « AirSim archivé par Microsoft, ne pas construire dessus ». À nuancer : FIRETWIN et FIRE-VLM utilisent tous les deux **Cosys-AirSim**, un fork activement maintenu par la communauté (Université de Delft notamment), pour la simulation de capteurs (RGB/profondeur/thermique) et la connexion drone-Unreal. Ça reste hors du chemin critique du MVP (notre choix PX4 SITL + Gazebo pour la physique de vol tient toujours), mais si un jour on veut du drone simulé *dans* la même scène Unreal que le GCS-Cinéma (plutôt que deux systèmes séparés), Cosys-AirSim est la piste à auditer en premier — pas Colosseum.

## 7. Architecture recommandée — la synthèse

```
GCS-Cinéma (Unreal Engine 5.8)
├── Cesium for Unreal
│   ├── Terrain géoréférencé (LiDAR HD IGN → Cesium ion → 3D Tiles)
│   ├── Imagerie/orthophoto en overlay
│   └── Gaussian Splats (reconstructions drone) — même pipeline 3D Tiles
├── Module natif WebSockets + Json (C++)
│   └── Connexion à l'API temps réel du jumeau numérique (G-11)
│       → positions drones, front de feu, vecteur, incertitude, vent
├── Niagara (feu/fumée)
│   └── Émetteurs pilotés par les données reçues (façon FIRETWIN)
├── Acteurs unités (camions, drones) — cliquables, fiche info (G-08)
└── [réserve] Live Link — si le WebSocket brut manque de fluidité
```

Ce qui ne change rien à notre philosophie « lourd serveur / léger terrain » (C-06) : le GCS-Cinéma est un **client de visualisation**, jamais une dépendance de calcul — il peut planter ou être fermé sans affecter le jumeau numérique qui tourne côté serveur.

## 8. Prochaines actions

1. Installer UE5.8 + Cesium for Unreal, géoréférencer une première scène sur une zone connue (Landiras, pour rester cohérent avec le jalon en cours).
2. Prototype minimal : un cube qui bouge dans Unreal, piloté par un message WebSocket envoyé depuis un script Python — valide toute la chaîne de bout en bout avant d'investir dans le visuel.
3. Identifier les auteurs de FIRETWIN (affiliation, labo) — piste de veille académique, à ajouter au radar recherche.
4. Une fois le prototype validé : brancher Niagara sur les mêmes données pour le premier feu visualisé en 3D.

## Sources principales
State of Unreal 2026 / Epic Games (annonces UE6, UE5.8, plugin MCP) ; documentation Epic Developer Community (WebSockets, Live Link, Remote Control API) ; CesiumGS/cesium-unreal (GitHub) et cesium.com (capacités, Gaussian Splats, rachat Bentley) ; FIRETWIN — *Digital Twin Advancing Multi-Modal Sensing, Interactive Analytics for Wildfire Response* (2025, financement NASA/NSF, arXiv:2510.18879) ; FIRE-VLM — *Vision-Language-Driven Reinforcement Learning Framework for UAV Wildfire Tracking* (2026, arXiv:2601.03449) ; *Digital Twin and Agentic AI for Wild Fire Disaster Management* — IVSR (2026, arXiv:2602.08949) ; *Review and perspectives of digital twin systems for wildland fire management*, Journal of Forestry Research (Springer).
