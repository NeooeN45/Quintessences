# Centre de Commandement GSIE — Unreal Engine 5.8 : architecture, briques existantes, précédents scientifiques

| Champ | Valeur |
|---|---|
| **Livrable** | 211 — Centre de Commandement GSIE (Unreal Engine 5.8) |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date de révision** | 2026-07-13 (v2.2.0 — complément de recherche §9 : UE5.8, Cesium post-avril 2026, précédents multi-domaines, MCP, publications 2026) |
| **Lois fondatrices** | GSIE-CON-004, GSIE-CON-005, GSIE-CON-007 |
| **Constitutions liées** | Technique (T-2, T-8, T-10) |
| **Directives liées** | GSIE-DIR-0005 (jumeau numérique vivant), GSIE-DIR-0006 (moteur cognitif), GSIE-DIR-0009 (restructuration écosystème) |
| **RFC de référence** | RFC-0004 (Ignis, §8 garde-fous) |
| **Décision d'adoption** | DEC-000010 (adoption UE 5.8 + Cesium), DEC-000013 (restructuration GSIE) |
| **Documents connexes** | `GSIE_MASTER_ARCHITECTURE.md` (livrable 201), `ENGINE_DATA_SOCLE.md` (livrable 310), `GSIE_IGNIS_ARCHITECTURE.md` (livrable 208), `GSIE_IGNIS_DATA_PIPELINE.md` (livrable 209), `GSIE_IGNIS_DRONE_ARCHITECTURE.md` (livrable 210) |

> Version 2.0.0 — 2026-07-13
> Repositionne le livrable 211 : ce n'est plus seulement le GCS-Cinéma d'Ignis, c'est le **Centre de Commandement GSIE** — un poste de pilotage immersif où TOUTES les données de l'écosystème Quintessences convergent (GeoSylva, Artemis, Ignis, Hydro, Flora). Le contenu technique (Cesium, Niagara, WebSocket) est conservé et élargi à l'ensemble des apps.
> Principe directeur : « avec ce qui existe » — chaque recommandation ci-dessous s'appuie sur une capacité native du moteur, un plugin établi, ou une publication de recherche déjà validée. Rien n'est inventé de zéro.

---

## Résumé exécutif

| # | Brique | Recommandation | Statut |
|---|---|---|---|
| 1 | Moteur | Unreal Engine 5.8 (dernière version majeure UE5, sortie 17/06/2026) | ✅ décidé |
| 2 | Terrain géoréférencé | Cesium for Unreal (Cesium ion + 3D Tiles) | ✅ décidé |
| 3 | Ingestion de données temps réel | Module natif `WebSockets` + `Json` d'Unreal (C++), pas de plugin tiers nécessaire | ✅ décidé |
| 4 | Feu / fumée | Niagara, piloté par les données du jumeau numérique, à la manière de FIRETWIN (§3) | ✅ décidé |
| 5 | Photogrammétrie / Gaussian Splatting | Pipeline Cesium ion (support natif des Gaussian Splats via 3D Tiles, LOD hiérarchique, avril 2026) | ✅ validé |
| 6 | Simulation drone dans Unreal (recherche) | Cosys-AirSim (fork maintenu, voir correction §6) | 🔍 veille |
| 7 | IA embarquée dans l'éditeur | Plugin MCP expérimental UE 5.8 (connexion directe de Claude au projet) | 🔍 à surveiller |

---

## 0. Périmètre — du GCS-Cinéma d'Ignis au Centre de Commandement GSIE

### 0.1 Repositionnement (GSIE-DIR-0009, DEC-000013)

Ce document était initialement consacré au **GCS-Cinéma** d'Ignis — le
poste de commandement 3D dédié à la surveillance des incendies. Avec la
restructuration de l'écosystème Quintessences (GSIE-DIR-0009,
DEC-000013), Unreal Engine 5.8 est repositionné comme le **Centre de
Commandement GSIE** : un poste de pilotage immersif unique où
**TOUTES les données de l'écosystème convergent**.

GSIE devient le **moteur central** (système nerveux) et le Centre de
Commandement en devient le **poste de pilotage visuel**. Les
applications ne sont plus des silos isolés : elles sont des couches
de données qui s'affichent et se croisent dans une même scène 3D
géoréférencée.

### 0.2 Les apps qui convergent dans le Centre de Commandement

| App | Rôle dans l'écosystème | Visualisation dans le Centre de Commandement |
|---|---|---|
| **GeoSylva** | Forêt | Peuplements, diagnostics sylvicoles, recommandations, carte interactive |
| **Ignis** | Incendies | Front de feu (Niagara), combustibles, météo temps réel, drones, propagation |
| **Artemis** | Faune | Habitats faune, observations, territories, corrélations flore-faune |
| **Hydro** | Eau | Réseau hydrographique, zones humides, régimes hydriques |
| **Flora** | Végétation | Cartographie végétale, phénologie, répartition floristique |

### 0.3 Principe de convergence

Le Centre de Commandement n'est pas une sixième application : c'est
la **couche de visualisation immersive** qui surplombe toutes les
apps. Chaque app expose ses données via l'API GSIE (livrable 207) ;
le Centre de Commandement consomme ces mêmes sorties validées et les
rend dans une scène 3D unifiée. L'opérateur peut activer/désactiver
les couches (forêt, feu, faune, eau, flore) et les croiser visuellement
dans un même environnement géoréférencé.

```
                    API GSIE (livrable 207)
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    Sorties GeoSylva  Sorties Ignis   Sorties Artemis
    Sorties Hydro     Sorties Flora
          │                │                │
          └────────────────┼────────────────┘
                           │
                    WebSocket / JSON
                           │
                           ▼
          ┌────────────────────────────────────┐
          │    CENTRE DE COMMANDEMENT GSIE      │
          │         (Unreal Engine 5.8)         │
          │                                     │
          │  Cesium for Unreal (globe 3D)       │
          │  ├── Couche forêt (GeoSylva)        │
          │  ├── Couche incendie (Ignis)        │
          │  ├── Couche faune (Artemis)         │
          │  ├── Couche eau (Hydro)             │
          │  └── Couche végétation (Flora)      │
          │  Niagara (effets feu/eau/fumée)     │
          └────────────────────────────────────┘
```

> **Note :** le contenu technique des sections 1 à 8 ci-dessous a été
> rédigé quand le document couvrait uniquement Ignis. Les briques
> (Cesium, WebSockets, Niagara) sont **génériques** et s'appliquent
> à toutes les apps. Les références à Ignis (G-05 à G-13, ForeFire,
> drones) restent valides comme **premier cas d'usage** du Centre de
> Commandement — le plus exigeant en temps réel — mais le périmètre
> est désormais l'ensemble de l'écosystème.

---

## 1. Où en est Unreal Engine mi-2026

Le calendrier est maintenant clair et stable pour les 18-24 prochains mois : <cite index="27-1">UE5.8, sorti en juin 2026, marque la fin du cycle majeur UE5 ; UE6 est officiellement annoncé mais son accès anticipé n'arrivera qu'à la fin 2027, et sa version stable qu'en 2028</cite>. Concrètement : **construis sur UE5.8**, sans te poser la question d'UE6 avant 2028 — les compétences et le code UE5 se transposeront de toute façon.

UE 5.8 apporte, en fonctionnalités jugées prêtes pour la production : MegaLights, Audio Insights, Live Link Hub, Movie Render Graph, et un outil expérimental de terrain sans limite de heightfield (« Mesh Terrain ») — pertinent pour couvrir un massif entier sans les contraintes habituelles de résolution.

## 2. Cesium for Unreal — le terrain, résolu

Cesium for Unreal est un plugin open source (racheté par Bentley Systems en 2024, donc adossé à un acteur infrastructure sérieux, pas un projet fragile) qui gère exactement notre problème le plus dur : <cite index="42-1">il combine un globe WGS84 haute précision avec les standards ouverts 3D Tiles pour streamer du contenu 3D réel — photogrammétrie, terrain, imagerie, bâtiments — directement dans Unreal Engine</cite>.

Ce qu'il résout pour nous, concrètement :
- **Géoréférencement précis** : le composant `CesiumGeoreference` gère la courbure terrestre et la gravité radiale — un problème qu'on aurait dû résoudre nous-mêmes sinon.
- **Ingestion de nos propres données** : Cesium ion traite LAS/LAZ (notre LiDAR HD IGN), GeoTIFF, glTF et l'imagerie drone pour les convertir en 3D Tiles streamables — un pipeline tout fait pour nos couches SIG françaises.
- **Découverte majeure pour G-05/M-19** : <cite index="48-1">Cesium ion supporte nativement les Gaussian Splats via 3D Tiles avec streaming par niveau de détail</cite>. Autrement dit, une reconstruction 3D Gaussian Splatting faite depuis une vidéo drone (M-19) peut passer par le **même pipeline** que le terrain et l'imagerie — pas besoin d'un système de rendu séparé. Ça simplifie beaucoup l'architecture qu'on avait esquissée. **✅ Validé en avril 2026** : le blog Cesium (27/04/2026) confirme le support production-ready des Gaussian Splats dans Cesium for Unreal avec LOD hiérarchique, standardisation glTF (`KHR_gaussian_splatting` + compression SPZ -90 %), pipeline bout-en-bout dans Cesium ion (upload photos → reconstruction automatique géoréférencée, via web ou API REST). Voir `GSIE/RESEARCH/UNREAL_ENGINE_PRECEDENTS.md` — fiche « Cesium 3D Gaussian Splats ». Les Gaussian Splats excellent sur végétation, lignes électriques et surfaces réflectives — exactement les éléments que la photogrammétrie classique gère mal en forêt.
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

Il existe déjà plusieurs publications qui construisent quasiment notre Centre de Commandement GSIE (cas d'usage incendie). À connaître absolument, y compris pour la crédibilité scientifique et les dossiers de financement :

**FIRETWIN** (2025, financé NASA + NSF) — un jumeau numérique cyber-physique qui <cite index="63-1">intègre un modèle couplé atmosphère-feu (CAWFE) dans Unreal Engine 5, avec des émetteurs de feu Niagara modélisant traînée aérodynamique, vent, gravité et collisions</cite>. Le système <cite index="63-1">simule aussi des capteurs RGB, profondeur, satellite et thermique, et complète la 3D par des cartes 2D de masse de combustible et d'intensité du feu</cite>. Point remarquable : <cite index="63-1">le système consomme les prédictions d'un modèle IA de prévision ET génère des données d'entraînement synthétiques en retour</cite> — exactement notre idée D-05, validée indépendamment par une équipe financée NASA. Limite reconnue par les auteurs eux-mêmes : exigeant en matériel, encore en phase de validation opérationnelle — une honnêteté qui nous rassure sur notre propre calendrier réaliste.

**FIRE-VLM** (2026) — encore plus proche de notre ambition long terme : un drone simulé apprend à traquer un front de feu par renforcement (PPO), guidé par un modèle vision-langage type CLIP, dans un jumeau numérique Unreal Engine 5.3 <cite index="68-1">construit sur un terrain USGS haute résolution avec cartes de combustible LANDFIRE et produits de front de feu dérivés de CAWFE</cite>. C'est le pendant américain de notre M-20 (raisonnement) et V-06 (orchestrateur) combinés — une piste de recherche à garder pour plus tard (potentiellement CIFRE), pas pour le MVP.

**IVSR** (février 2026) — une « salle de situation virtuelle » avec agents IA autonomes, qui <cite index="65-1">ingère en continu imagerie multi-capteurs, données météo et modèles 3D de forêt pour créer une réplique virtuelle vivante de l'environnement du feu, et calibre les tactiques d'intervention en comparant les conditions émergentes à une bibliothèque de simulations de désastres précalculées</cite>. Cette idée de « bibliothèque de scénarios précalculés » comparée en continu au direct est une piste intéressante pour accélérer notre émulateur (J-02) sans attendre le neural operator complet.

Existe aussi une revue de synthèse complète sur les jumeaux numériques appliqués aux feux de forêt (*Journal of Forestry Research*, Springer) — à citer dans tout dossier académique ou de financement pour montrer que le domaine est reconnu, pas une lubie isolée.

**Lecture stratégique** : ces publications confirment que notre approche est scientifiquement défendable et récente (aucune n'a plus d'un an), mais aussi qu'on n'est plus seuls sur ce terrain précis — l'équipe FIRETWIN (financement NASA/NSF) mérite d'être identifiée nommément (auteurs, laboratoire) comme piste de veille, voire de contact académique à moyen terme, sur le modèle de ce qu'on fait avec l'Université de Corse pour ForeFire.

## 6. Correction au Livrable 1 — AirSim mérite d'être nuancé

Le Livrable 1 disait « AirSim archivé par Microsoft, ne pas construire dessus ». À nuancer : FIRETWIN et FIRE-VLM utilisent tous les deux **Cosys-AirSim**, un fork activement maintenu par la communauté (Université de Delft notamment), pour la simulation de capteurs (RGB/profondeur/thermique) et la connexion drone-Unreal. Ça reste hors du chemin critique du MVP (notre choix PX4 SITL + Gazebo pour la physique de vol tient toujours), mais si un jour on veut du drone simulé *dans* la même scène Unreal que le Centre de Commandement (plutôt que deux systèmes séparés), Cosys-AirSim est la piste à auditer en premier — pas Colosseum.

## 7. Architecture recommandée — la synthèse

```
Centre de Commandement GSIE (Unreal Engine 5.8)
├── Cesium for Unreal
│   ├── Terrain géoréférencé (LiDAR HD IGN → Cesium ion → 3D Tiles)
│   ├── Imagerie/orthophoto en overlay
│   └── Gaussian Splats (reconstructions drone) — même pipeline 3D Tiles
├── Module natif WebSockets + Json (C++)
│   └── Connexion à l'API GSIE temps réel (livrable 207)
│       ├── Ignis    → positions drones, front de feu, vecteur, vent
│       ├── GeoSylva → diagnostics, recommandations, peuplements
│       ├── Artemis  → habitats faune, observations
│       ├── Hydro    → réseau hydrographique, zones humides
│       └── Flora    → cartographie végétale, phénologie
├── Niagara (effets visuels)
│   ├── Feu/fumée (Ignis) — émetteurs pilotés par les données (façon FIRETWIN)
│   ├── Eau/cours d'eau (Hydro) — fluides et particules
│   └── [extensible] — nouveaux effets par app
├── Acteurs unités (camions, drones, capteurs) — cliquables, fiche info
├── Couches activables/désactivables (forêt, feu, faune, eau, flore)
└── [réserve] Live Link — si le WebSocket brut manque de fluidité
```

Ce qui ne change rien à notre philosophie « lourd serveur / léger terrain » (C-06) : le Centre de Commandement est un **client de visualisation**, jamais une dépendance de calcul — il peut planter ou être fermé sans affecter les moteurs GSIE qui tournent côté serveur.

## 8. Prochaines actions

1. Installer UE5.8 + Cesium for Unreal, géoréférencer une première scène sur une zone connue (Landiras, pour rester cohérent avec le jalon Ignis en cours).
2. Prototype minimal : un cube qui bouge dans Unreal, piloté par un message WebSocket envoyé depuis un script Python — valide toute la chaîne de bout en bout avant d'investir dans le visuel.
3. Identifier les auteurs de FIRETWIN (affiliation, labo) — piste de veille académique, à ajouter au radar recherche.
4. Une fois le prototype validé : brancher Niagara sur les mêmes données pour le premier feu visualisé en 3D (couche Ignis).
5. Étendre le prototype aux autres apps : afficher une couche forêt (GeoSylva), un cours d'eau (Hydro), une observation faune (Artemis) et une cartographie végétale (Flora) dans la même scène — valider le principe de convergence multi-apps.
6. Définir le système de couches activables/désactivables (forêt, feu, faune, eau, flore) dans l'interface du Centre de Commandement.

## 9. Compléments de recherche (mise à jour)

> Recherche complémentaire (2026-07-13), portant spécifiquement sur ce qui n'est pas déjà couvert par les sections 1 à 8 : détail des fonctionnalités UE5.8 pertinentes pour un centre de commandement multi-domaines, mises à jour Cesium postérieures à avril 2026, précédents de convergence multi-domaines (hors incendie), maturité actuelle du plugin MCP, et nouvelles publications académiques 2026 sur les jumeaux numériques environnementaux au-delà du feu.

### 9.1 UE5.8 — fonctionnalités de production complémentaires pour un centre de commandement multi-domaines

Le §1 cite déjà MegaLights, Live Link Hub, Movie Render Graph et l'outil expérimental de terrain comme fonctionnalités « prêtes pour la production » de UE5.8. Le détail de chacune, une fois creusé, est directement pertinent pour le Centre de Commandement :

- **Mesh Terrain** (expérimental) — alternative au terrain heightfield 2,5D classique, reposant sur un maillage 3D complet : il peut représenter falaises, surplombs, tunnels et îles flottantes, avec une résolution géométrique variable selon les zones, et s'intègre à PCG, Nanite, World Partition et One File Per Actor sans perdre l'édition non destructive. Intérêt pour GSIE : couvrir un massif forestier accidenté (ravins, corniches, gorges) sans les limites de résolution d'un heightfield classique — pertinent pour les terrains GeoSylva/Ignis en zone de relief marqué.
- **MegaLights** (passé Production-Ready en 5.8) — grand nombre de lumières dynamiques à ombres portées, bruit réduit, meilleures performances, et surtout support de la diffusion sous-surface (*subsurface scattering*), de la translucidité, des canaux d'éclairage et des ombres de nuages. La translucidité et la diffusion sous-surface sont directement utiles pour l'éclairage réaliste d'une canopée forestière en extérieur (feuillage traversé par la lumière, ombres changeantes) — un cas d'usage plus proche de GeoSylva/Flora que du rendu intérieur pour lequel MegaLights a d'abord été pensé.
- **Movie Render Graph** (Production-Ready) — fenêtre de rendu repensée exposant les réglages sous forme de graphe, isolation de l'éclairage par plan, support nDisplay. Utilisable pour générer automatiquement des rendus ou cinématiques standardisés (rapport de diagnostic sylvicole, bilan de campagne de surveillance incendie) directement depuis l'état du jumeau numérique, sans reconfiguration manuelle à chaque export.
- **Live Link Hub** (Production-Ready) — interface centrale de supervision de flux vidéo/données multiples, synchronisation Live Link, pilotage d'enregistreurs compatibles sur IP. À évaluer comme voie d'ingestion complémentaire pour des flux caméra/capteur (drones, stations fixes), en plus du couple WebSocket/JSON déjà retenu (§3) — pas un remplacement, un complément pour les flux vidéo/temps réel spécifiquement.

### 9.2 Cesium for Unreal / Cesium ion — mises à jour postérieures à avril 2026

Le blog Cesium confirme, dans ses parutions mensuelles jusqu'à juillet 2026 :

- **Cesium for Unreal 2.28.0** (juillet 2026) — prise en charge officielle d'Unreal Engine 5.8, mise à jour du moteur natif `cesium-native` (0.61.0 → 0.62.0), correction d'un bug de rendu des Gaussian Splats en session « Standalone Game ». Point de vigilance pour la planification : c'est la **dernière version à supporter UE 5.5** — les versions suivantes de Cesium for Unreal exigeront UE 5.6 minimum, ce qui ne pose aucun risque pour notre choix UE5.8.
- **Nouveaux formats côté Cesium ion (SaaS)** — conversion de fichiers **NetCDF vers 3D Tiles via le « voxel tiler »**, pertinente pour des données climatiques/hydrologiques volumétriques (moteur Climate, app Hydro), et conversion de **GeoJSON vers 3D Tiles via le « vector tiler »**, pertinente pour nos couches vectorielles (parcelles GeoSylva, habitats Artemis, réseau hydrographique Hydro) sans étape de conversion manuelle. Import d'iModels depuis Bentley Infrastructure Cloud également ajouté.
- **Rapprochement SaaS / Self-Hosted** — Cesium annonce que les capacités de modélisation de la réalité de Cesium ion SaaS (dont la création de Gaussian Splats avec LOD) deviennent progressivement disponibles pour les déploiements **Self-Hosted**. Pertinent si GSIE devait un jour héberger son propre pipeline Cesium ion plutôt que dépendre du SaaS public, pour des raisons de maîtrise des données environnementales.

### 9.3 Précédents de convergence multi-domaines (au-delà du feu)

Trois précédents, non issus du domaine environnemental mais directement transposables, éclairent l'architecture de « couches activables/désactivables » du Centre de Commandement :

- **NVIDIA Omniverse / OpenUSD** — le modèle de composition en couches non destructives d'OpenUSD (Open Universal Scene Description) est le précédent industriel le plus direct : plusieurs couches de données hétérogènes (CAO, champs de simulation, flux de capteurs IoT, annotations IA) coexistent dans une même scène et peuvent être activées, désactivées ou mises à jour indépendamment, sans dupliquer les données sous-jacentes. Le domaine d'application reste industriel (jumeaux numériques d'usines, d'événements), pas environnemental — mais le principe de composition par couches est directement transposable à notre modèle « forêt / feu / faune / eau / flore ».
- **ArcGIS Urban (Esri)** — plateforme de jumeau numérique urbain agrégeant plusieurs couches géospatiales (occupation du sol, bâti, démographie, BIM) pour la planification territoriale ; la mise à jour de mars 2026 ajoute un fond de carte photoréaliste 3D (Google 3D Photorealistic basemap, bêta) et des flux de densification paramétrés. Précédent de plateforme multi-couches SIG/3D à visée professionnelle.
- **Cesium ion Enterprise / Self-Hosted** — voir §9.2 : le rapprochement des capacités SaaS et Self-Hosted répond au même besoin de déploiement multi-tenant/multi-organisation qu'un centre de commandement partagé pourrait rencontrer à terme.

Un précédent académique 2026 rejoint directement cette réflexion : Ene, Badea, Badea & Grădinaru, *« Development of Urban Digital Twins Using GIS and Game Engine Systems »* (*Land*, 2026), comparent explicitement une approche SIG « professionnelle » (analyse, suivi) et une approche moteur de jeu (immersion, participation) pour le jumeau numérique urbain — la même dualité que GSIE pose entre QGISIA (SIG) et le Centre de Commandement (Unreal).

**Précédent institutionnel français** — l'IGN propose désormais un service « **Jumeau numérique** » explicitement décrit comme un outil de « simulation et anticipation territoriale » dans son catalogue d'offres (`ign.fr/offre`), aux côtés de LiDAR HD, BD TOPO, données forestières et Panoramax. C'est un précédent institutionnel direct et français — à surveiller de près, y compris pour d'éventuelles synergies de données (LiDAR HD, BD TOPO, données forestières IGN, cf. §8 du `GIS_ENGINE`) plutôt que pour son architecture technique interne, non documentée publiquement à ce stade.

### 9.4 Maturité du plugin MCP pour l'éditeur Unreal (mise à jour)

Le plugin mentionné en veille dans la version précédente de ce document a maintenant un nom et une documentation officielle : **Unreal MCP**, livré avec UE5.8 (annoncé au State of Unreal 2026) et documenté sur dev.epicgames.com. Il embarque un serveur MCP dans le processus de l'éditeur, permettant à un client MCP (Claude, Cursor, MCP Inspector) de piloter l'éditeur via une connexion HTTP locale : manipulation d'acteurs, création d'instances de matériaux, configuration de l'éclairage, inspection de widgets Slate, exécution de tests d'automatisation.

Le statut reste explicitement **expérimental** : la documentation officielle d'Epic précise que « de nombreuses fonctionnalités sont incomplètes ou manquantes, les API et formats de données sont susceptibles de changer à tout moment ». Limites documentées : transport restreint à HTTP/Server-Sent Events (ni stdio, ni WebSocket), liaison à `localhost` uniquement sans couche d'authentification, redémarrage complet de l'éditeur nécessaire pour toute nouvelle fonction ajoutée via Live Coding.

Une comparaison publiée par StraySpark Studio (juillet 2026 — source spécialisée non académique, à traiter comme un avis technique et non comme une donnée officielle Epic) situe le plugin officiel derrière les serveurs MCP tiers existants sur cinq dimensions : couverture d'outils, efficacité de contexte, exécution transactionnelle par lot, profondeur d'inspection, et sécurité (authentification, contrôle de portée). Epic présente néanmoins ce plugin comme une brique fondatrice pour Unreal Engine 6 (fin 2027) — ce qui confirme l'intérêt de le garder en veille active plutôt que de l'adopter en production dès mi-2026, conformément à la posture déjà retenue dans ce document.

### 9.5 Nouvelles publications académiques 2026 — au-delà du feu

Deux domaines complètent utilement FIRETWIN/FIRE-VLM/IVSR (tous trois centrés incendie) :

- **Hydrologie** — Kang, W. & Jang, E., *« A Digital Twin of River Experiment Infrastructure Based on a 3D Game Engine and Validation of Water Flow with a Real-Scale Experiment »*, *Applied Sciences*, 2025, vol. 15, n° 23, article 12507 (DOI: 10.3390/app152312507) : jumeau numérique d'une installation d'essais hydrauliques construit dans **Unreal Engine 5**, utilisant le plugin de simulation de fluides *Fluid Flux* (équations de Saint-Venant en eaux peu profondes, champs de hauteur 2D), validé par comparaison directe à une expérience physique à échelle réelle. C'est actuellement le précédent le plus direct identifiable pour l'app **Hydro** — un cas « moteur de jeu + hydraulique » validé expérimentalement, sur le même principe que ce que FIRETWIN apporte au feu.
- **Convergence SIG / moteur de jeu (urbain, transposable)** — Ene, A., Badea, A.-C., Badea, G. & Grădinaru, A., *« Development of Urban Digital Twins Using GIS and Game Engine Systems »*, *Land*, 2026, vol. 15, n° 2, article 254 (DOI: 10.3390/land15020254). Centré sur le jumeau numérique urbain, pas forestier, mais c'est la publication 2026 la plus récente identifiée qui documente explicitement la complémentarité SIG professionnel / moteur de jeu immersif.
- **Faune** — aucune publication 2026 combinant explicitement moteur de jeu et jumeau numérique de la faune n'a pu être identifiée avec certitude lors de cette recherche ; à ne pas présenter comme un précédent établi. Le travail le plus proche reste Islam, S. et al., *« FAIR digital twins for biodiversity: enabling data, model, and workflow integration »*, *npj Biodiversity*, 2026 (DOI: 10.1038/s44185-025-00116-3), issu du projet européen **BioDT** (2022-2025) : il documente des prototypes de jumeaux numériques pour la dynamique forestière (couplage du modèle LANDIS-II à un modèle de communauté d'espèces), les prairies (GRASSMIND) et le suivi ornithologique en temps réel par science citoyenne — **mais il s'agit d'un cadre d'intégration de données/modèles/workflows (principes FAIR, format RO-Crate), pas d'une implémentation en moteur de jeu 3D**. À citer comme précédent de gouvernance scientifique des données pour Artemis/GeoSylva, pas comme précédent d'architecture Unreal.

> **Lecture pour Artemis** : l'absence de précédent confirmé « moteur de jeu + faune » renforce l'intérêt de documenter notre propre approche, le cas échéant, comme contribution potentiellement originale plutôt que comme simple application d'un précédent existant — à revérifier par une revue de littérature ciblée avant tout dossier de publication ou de financement.

### Sources complémentaires

- Epic Games — *Unreal Engine 5.8 Release Notes*, dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes ; *State of Unreal 2026: Top news from the show* (unrealengine.com/news).
- Epic Games — *Unreal MCP in Unreal Editor*, https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor
- StraySpark Studio — *« Epic's Official MCP Plugin Is Here (UE 5.8): What It Does and Where Third-Party Servers Still Win »*, https://www.strayspark.studio/blog/epic-official-mcp-plugin-ue5-8-vs-third-party
- Cesium — *Cesium Releases in July 2026*, https://cesium.com/blog/2026/07/01/cesium-releases-in-july-2026/ ; CesiumGS/cesium-unreal, GitHub (page « Releases »)
- NVIDIA — documentation Omniverse / OpenUSD, docs.omniverse.nvidia.com
- Esri — *What's New in ArcGIS Urban (March 2026)*, esri.com/arcgis-blog/products/urban/announcements/whats-new-in-arcgis-urban-march-2026
- Ene, A., Badea, A.-C., Badea, G., Grădinaru, A. (2026). *Development of Urban Digital Twins Using GIS and Game Engine Systems*. Land, 15(2), 254. https://www.mdpi.com/2073-445X/15/2/254
- Kang, W., Jang, E. (2025). *A Digital Twin of River Experiment Infrastructure Based on a 3D Game Engine and Validation of Water Flow with a Real-Scale Experiment*. Applied Sciences, 15(23), 12507. https://www.mdpi.com/2076-3417/15/23/12507
- Islam, S., Koivula, H., Andrew, C. et al. (2026). *FAIR digital twins for biodiversity: enabling data, model, and workflow integration*. npj Biodiversity. DOI: 10.1038/s44185-025-00116-3 (projet BioDT, 2022-2025)
- IGN — *Catalogue des offres* (service « Jumeau numérique », LiDAR HD, BD TOPO, données forestières, Panoramax). https://www.ign.fr/offre

## Sources principales
State of Unreal 2026 / Epic Games (annonces UE6, UE5.8, plugin MCP) ; documentation Epic Developer Community (WebSockets, Live Link, Remote Control API) ; CesiumGS/cesium-unreal (GitHub) et cesium.com (capacités, Gaussian Splats, rachat Bentley) ; FIRETWIN — *Digital Twin Advancing Multi-Modal Sensing, Interactive Analytics for Wildfire Response* (2025, financement NASA/NSF, arXiv:2510.18879) ; FIRE-VLM — *Vision-Language-Driven Reinforcement Learning Framework for UAV Wildfire Tracking* (2026, arXiv:2601.03449) ; *Digital Twin and Agentic AI for Wild Fire Disaster Management* — IVSR (2026, arXiv:2602.08949) ; *Review and perspectives of digital twin systems for wildland fire management*, Journal of Forestry Research (Springer).
