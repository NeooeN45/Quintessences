# Précédents scientifiques — Jumeaux numériques incendie dans Unreal Engine

| Champ | Valeur |
|---|---|
| **Document** | UNREAL_ENGINE_PRECEDENTS |
| **Dossier** | GSIE/RESEARCH/ |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date** | 2026-07-12 |
| **Décision liée** | DEC-000010 (adoption UE 5.8) |
| **Documents connexes** | `GSIE/ARCHITECTURE/GSIE_IGNIS_GCS_CINEMA_UNREAL.md` (livrable 211), `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` (livrable 212) |

---

## Objet

Recenser les publications académiques récentes qui valident l'approche
« jumeau numérique incendie dans Unreal Engine ». Ces précédents sont
essentiels pour la crédibilité scientifique (CON-002) et les dossiers de
financement. Aucune de ces publications n'a plus d'un an au moment de
cette recension.

---

## FIRETWIN (2025) — jumeau numérique cyber-physique

| Champ | Valeur |
|---|---|
| **Titre** | *Digital Twin Advancing Multi-Modal Sensing, Interactive Analytics for Wildfire Response* |
| **Année** | 2025 |
| **Financement** | NASA + NSF |
| **ArXiv** | arXiv:2510.18879 |
| **Moteur** | Unreal Engine 5 |

### Ce qu'il valide pour Ignis

- Intègre un **modèle couplé atmosphère-feu (CAWFE)** dans Unreal Engine 5.
- Émetteurs de feu **Niagara** modélisant traînée aérodynamique, vent,
  gravité et collisions — exactement l'approche G-06 du registre Ignis.
- Simule des **capteurs RGB, profondeur, satellite et thermique**.
- Complète la 3D par des **cartes 2D** de masse de combustible et
  d'intensité du feu.
- Consomme les prédictions d'un **modèle IA de prévision** ET génère des
  **données d'entraînement synthétiques** en retour — exactement l'idée
  D-05 du registre Ignis, validée indépendamment.

### Ce qu'il valide pour GeoSylva-Unreal

- Utilise le **même mécanisme PCG** (landscape data layers + nœuds de
  requête) pour la génération procédurale de forêt, avec des données de
  combustible CAWFE à la place des couches pédologiques GeoSylva.

### Limites reconnues par les auteurs

Exigeant en matériel, encore en phase de validation opérationnelle —
une honnêteté qui rassure sur notre propre calendrier réaliste.

### Action

Identifier les auteurs (affiliation, laboratoire) comme piste de veille
académique, sur le modèle de ce qu'on fait avec l'Université de Corse
pour ForeFire.

---

## FIRE-VLM (2026) — drone autonome par renforcement

| Champ | Valeur |
|---|---|
| **Titre** | *Vision-Language-Driven Reinforcement Learning Framework for UAV Wildfire Tracking* |
| **Année** | 2026 |
| **ArXiv** | arXiv:2601.03449 |
| **Moteur** | Unreal Engine 5.3 |

### Ce qu'il valide pour Ignis

- Un **drone simulé** apprend à traquer un front de feu par **renforcement
  (PPO)**, guidé par un **modèle vision-langage type CLIP**.
- Jumeau numérique construit sur un **terrain USGS haute résolution** avec
  **cartes de combustible LANDFIRE** et produits de front de feu dérivés
  de CAWFE.
- C'est le pendant américain de M-20 (raisonnement) et V-06 (orchestrateur)
  combinés du registre Ignis.

### Positionnement GSIE

Piste de recherche à garder pour plus tard (potentiellement CIFRE), pas
pour le MVP. Les garde-fous RFC-0004 §8 (supervision humaine) restent
applicables — l'autonomie de navigation est encadrée.

---

## IVSR (février 2026) — salle de situation virtuelle

| Champ | Valeur |
|---|---|
| **Titre** | *Digital Twin and Agentic AI for Wild Fire Disaster Management* (IVSR) |
| **Année** | 2026 |
| **ArXiv** | arXiv:2602.08949 |

### Ce qu'il valide pour Ignis

- Une **« salle de situation virtuelle »** avec agents IA autonomes.
- Ingère en continu **imagerie multi-capteurs, données météo et modèles
  3D de forêt** pour créer une réplique virtuelle vivante de
  l'environnement du feu.
- **Calibre les tactiques d'intervention** en comparant les conditions
  émergentes à une **bibliothèque de simulations de désastres
  précalculées**.

### Piste pour GSIE

L'idée de « bibliothèque de scénarios précalculés » comparée en continu
au direct est une piste intéressante pour accélérer l'émulateur (J-02)
sans attendre le neural operator complet.

---

## Revue de synthèse — Journal of Forestry Research (Springer)

| Champ | Valeur |
|---|---|
| **Titre** | *Review and perspectives of digital twin systems for wildland fire management* |
| **Éditeur** | Journal of Forestry Research (Springer) |

### Usage

À citer dans tout dossier académique ou de financement pour montrer que
le domaine des jumeaux numériques appliqués aux feux de forêt est
reconnu, pas une lubie isolée.

---

## Cosys-AirSim — simulation drone dans Unreal

Le Livrable 1 (moteurs de propagation) disait « AirSim archivé par
Microsoft, ne pas construire dessus ». À nuancer : FIRETWIN et FIRE-VLM
utilisent tous les deux **Cosys-AirSim**, un fork activement maintenu par
la communauté (Université de Delft notamment), pour la simulation de
capteurs (RGB/profondeur/thermique) et la connexion drone-Unreal.

Hors du chemin critique du MVP (PX4 SITL + Gazebo pour la physique de
vol), mais si un jour on veut du drone simulé *dans* la même scène Unreal
que le GCS-Cinéma, Cosys-AirSim est la piste à auditer en premier.

---

## Lecture stratégique

Ces publications confirment que l'approche Ignis est
**scientifiquement défendable et récente** (aucune n'a plus d'un an),
mais aussi qu'on n'est plus seuls sur ce terrain précis. L'équipe
FIRETWIN (financement NASA/NSF) mérite d'être identifiée nommément comme
piste de veille, voire de contact académique à moyen terme.

---

> Statut : *Draft — Phase 2 (Architecture). Recensement scientifique pour
> traçabilité (CON-005) et crédibilité (CON-002).*
