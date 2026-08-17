# Registre des opportunités — Hub Unreal Engine

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-REG-HUB |
| **Statut** | Draft |
| **Version** | 1.0.0 |
| **Dernier reclassement** | 2026-08-16 |
| **Cible** | Centre de Commandement GSIE (Unreal Engine 5.8), GCS-Cinéma Ignis, GeoSylva-Unreal |
| **Contraintes de la cible** | Matériel exigeant · rendu temps réel · géoréférencement strict · poste de pilotage, jamais source de vérité |
| **Registres frères** | GSIE Serveur · GSIE PC · Applications mobiles · Applications clientes |

---

## 1. Comment lire ce registre

Identifiants `OPP-xxx` stables et uniques dans tous les registres. Classement sur
le seul **intérêt** pour cette cible, de 1 à 5. Le **verrou** décrit ce qui bloque
et ce qu'il faudrait pour le lever — ce n'est pas une pénalité de rang.

**Statuts** : INTÉGRER · BENCHMARKER · SURVEILLER · ÉCARTER.

---

## 2. Ce que la cible Hub impose, quel que soit l'intérêt

1. **Le Hub affiche, il ne décide pas et il ne détient rien.** La vérité reste
   dans GSIE. Tout ce qui apparaît à l'écran est une projection reconstruisible.
   Un état qui n'existerait que dans la scène Unreal est un bug de conception.
2. **Une simulation est un scénario, jamais une alerte réglementaire.** Cette
   règle vaut pour les prévisions météo comme pour la propagation de feu. Le
   passage du scénario à la décision opérationnelle passe par un humain.
3. **Le matériel est une contrainte réelle, pas un détail d'optimisation.** Les
   auteurs de FIRETWIN reconnaissent eux-mêmes le coût matériel de l'approche —
   une honnêteté qui vaut aussi pour notre calendrier.
4. **Aucune dépendance de runtime sur un connecteur non garanti.** Voir OPP-122.

---

## 3. Classement au 2026-08-16

| Rang | ID | Opportunité | Intérêt | Verrou actuel | Pour le lever | Statut |
|---:|---|---|:-:|---|---|---|
| 1 | OPP-082 | **Génération de données d'entraînement synthétiques** — capteurs RGB, profondeur, thermique et satellite simulés dans la scène | 5 | Chaîne à monter ; réalisme à valider contre des images réelles | Reproduire le pipeline FIRETWIN sur une parcelle, puis mesurer l'écart au réel | BENCHMARKER |
| 2 | OPP-070 | **Cesium for Unreal** — terrain géoréférencé | 5 | Aucun — brique considérée comme résolue | Intégration directe | INTÉGRER |
| 3 | OPP-071 | **3D Gaussian Splats à LOD hiérarchique** (3D Tiles, Cesium ion) | 5 | Pipeline non testé sur nos propres vidéos drone | Test bout-en-bout sur une parcelle forestière | INTÉGRER |
| 3bis | OPP-145 | **WildFireGS** — simulation de feu physique directement dans une scène Gaussian Splatting forestière | 5 | Publication du 11 août 2026, aucune implémentation locale | Auditer le dépôt ; c'est la fusion native de OPP-071 et OPP-072, à ne pas construire séparément | SURVEILLER |
| 4 | OPP-072 | **Niagara** — feu et fumée avec traînée, vent, gravité, collisions | 5 | Aucun — méthode éprouvée, validée par FIRETWIN | Intégration selon l'approche G-06 du registre Ignis | INTÉGRER |
| 5 | OPP-081 | **PCG — génération procédurale de forêt** depuis couches de données du terrain | 5 | Couches pédologiques GeoSylva à câbler sur les *landscape data layers* | Transposer le mécanisme FIRETWIN, combustible → pédologie | BENCHMARKER |
| 6 | OPP-073 | **3D Tiles 2.0 + glTF `KHR_gaussian_splatting`** — pipeline unique | 4 | Ratification Khronos Q2 2026 ; 3D Tiles 2.0 en standard communautaire proposé | Suivre la ratification ; le pipeline fonctionne déjà | INTÉGRER |
| 7 | OPP-075 | **Bibliothèque de scénarios précalculés** comparée au direct (IVSR) | 4 | Aucune bibliothèque constituée | Précalculer un petit corpus de scénarios sur un territoire pilote | BENCHMARKER |
| 8 | OPP-077 | **OpenUSD comme format d'échange** vers le Hub | 4 | Aucun, *à condition* de ne pas dépendre du connecteur Omniverse (OPP-122) | Usage strictement en format de fichier | INTÉGRER |
| 9 | OPP-074 | **Cosys-AirSim** — drone simulé dans la scène Unreal | 3 | Hors chemin critique du MVP (PX4 SITL + Gazebo pour la physique de vol) | Audit si un besoin de drone simulé *dans* la scène du GCS émerge | SURVEILLER |
| 10 | OPP-078 | **Plugin MCP pour l'éditeur Unreal** | 3 | Maturité à qualifier | Test sur une tâche d'édition réelle avant tout usage dans le flux de travail | SURVEILLER |
| 11 | OPP-027 | **World models génératifs** — Cosmos, MiniMax H3 | 3 | Besoin non établi ; le domaine bouge trop vite pour s'engager | Attendre qu'un besoin de scénarios rares soit formulé. *Renvoi croisé : registre GSIE Serveur.* | SURVEILLER |
| 12 | OPP-083 | **FIRE-VLM** — drone traquant un front de feu par renforcement | 2 | Autonomie de navigation — garde-fous RFC-0004 §8 applicables | Piste de recherche, potentiellement CIFRE. Pas pour le MVP | SURVEILLER |

---

## 4. Fiches

### OPP-082 · La scène Unreal comme usine à données annotées
**C'est le rang 1, et pour une raison qui dépasse ce registre.**

Trois autres registres sont bloqués par le même verrou : le pack essences
embarqué (mobile), la perception drone (applications clientes), le fine-tuning
DeepForest (PC). Dans les trois cas il manque un corpus annoté, et le constituer
à la main coûte cher.

Or FIRETWIN ne fait pas que *consommer* les prédictions d'un modèle : il
**génère en retour des données d'entraînement synthétiques**, en simulant des
capteurs RGB, profondeur, thermique et satellite dans la scène. L'annotation est
gratuite, puisque la scène connaît la vérité terrain par construction.

C'est exactement l'idée D-05 du registre Ignis, validée indépendamment par une
publication financée NASA/NSF.

**La réserve qui compte :** un modèle entraîné sur du synthétique ne se comporte
pas forcément bien sur du réel. L'écart doit être mesuré, pas supposé — c'est
précisément ce que le banc à construire devra établir. Le synthétique complète un
corpus réel ; il ne le remplace pas.

### OPP-071 · Gaussian Splats — la brique qui est passée de « à tester » à « validé »
Le billet Cesium d'avril 2026 change le statut de la brique 5 du livrable 211.
Ce qui est acquis : support dans Cesium for Unreal avec streaming par niveau de
détail via 3D Tiles ; pipeline bout-en-bout dans Cesium ion (photos sources →
mesh, nuage de points **ou** splats géoréférencés) ; standardisation glTF avec
compression SPZ de Niantic annoncée à **-90 % par rapport au PLY**, harmoniques
sphériques comprises.

**Pourquoi ça compte particulièrement en forêt :** les Gaussian Splats excellent
sur la végétation, les lignes électriques et les surfaces réfléchissantes —
précisément ce que la photogrammétrie classique rend mal. Et une reconstruction
issue d'une vidéo drone emprunte le **même pipeline** que le terrain et
l'imagerie : pas de système de rendu séparé à maintenir.

### OPP-081 · PCG — la forêt générée depuis nos propres couches
FIRETWIN utilise les *landscape data layers* et des nœuds de requête pour générer
la forêt procéduralement, avec des données de combustible CAWFE en entrée. Le
mécanisme est le même que celui prévu pour GeoSylva-Unreal ; seule la donnée
d'entrée change — nos couches pédologiques à la place du combustible.

### OPP-075 · La bibliothèque de scénarios précalculés
L'apport d'IVSR n'est pas technique mais stratégique : comparer en continu les
conditions observées à une bibliothèque de simulations précalculées permet de
calibrer des tactiques **sans attendre** le neural operator complet. C'est une
piste d'accélération de l'émulateur J-02, pas un contournement.

---

## 4bis. Enrichissement — recherche web du 2026-08-16

**WildFireGS (arXiv, 11 août 2026) — la fusion qui n'était pas encore documentée.**
Publiée cinq jours après la première version de ce registre, cette approche fait
tourner un **modèle de combustion physique par particules** (ignition, transfert
de chaleur, propagation de flamme) **directement dans une reconstruction Gaussian
Splatting forestière à grande échelle**. C'est exactement la combinaison de
OPP-071 (Splats) et OPP-072 (Niagara) que ce registre visait déjà — sauf qu'elle
existe désormais comme approche unifiée, pas comme deux briques à assembler.
**Positionnement :** SURVEILLER activement, pas encore BENCHMARKER — la
publication a moins d'une semaine, aucune implémentation de référence stabilisée
n'est encore auditée. À réévaluer sous 1-2 mois.

**Précédent supplémentaire confirmé — reconstruction du King Fire.** Un jumeau
numérique géo-synchronisé dans Unreal Engine, combinant Google Maps et Niagara, a
reconstruit l'étendue de 39 500+ hectares du King Fire 2014 (Eldorado National
Forest, Californie). Ce précédent renforce la lecture stratégique du §7 : le
domaine est actif et publié, pas isolé.

**Correction mineure sur FIRETWIN.** Les sources vérifiées le 16 août confirment
un environnement **Unreal Engine 5.3** (terrain USGS haute résolution, fuel maps
LANDFIRE, produits de ligne de feu CAWFE) — pas 5.8 comme la version antérieure
de ce registre l'implique par extension. Sans conséquence sur la validité de
l'approche pour notre cible UE 5.8, mais à corriger dans toute citation précise.

---

## 5. Renvois croisés — ce qui alimente le Hub sans y résider

| ID | Opportunité | Foyer | Ce qu'elle apporte au Hub |
|---|---|---|---|
| OPP-079 | **SegmentAnyTreeV2** — segmentation d'arbres agnostique capteur, F1 85 %, zero-shot cross-domain | GSIE PC | Peuple la scène en arbres individuels segmentés. Montée en gamme au-delà de PyCrown quand les peuplements denses le justifient |
| OPP-080 | **Crown-BERT** — essence par fusion LiDAR + hyperspectral, 83-91 % OA, 0,9 M paramètres | GSIE PC | Comble la limite du LiDAR seul : l'essence n'en est pas extractible. Nécessite un capteur hyperspectral drone |
| OPP-084 | **CesiumJS** — globe 3D web | GSIE PC | Pendant web du terrain Cesium for Unreal, même pipeline 3D Tiles |
| OPP-003 | **3DFin + lidR** | GSIE PC | Produit les métriques d'arbres que la scène représente |

**Chaîne complète, à travers trois registres :** acquisition LiDAR/drone →
segmentation (PyCrown, puis SegmentAnyTreeV2) → classification d'essence
(Crown-BERT) → génération procédurale dans Unreal (PCG) → simulation de capteurs
(OPP-082) → nouvelles données annotées. La boucle se referme.

---

## 6. Écartées — motifs durs uniquement

| ID | Opportunité | Motif |
|---|---|---|
| OPP-122 | **Connecteur Omniverse comme dépendance du runtime** | Documenté pour Unreal Engine 5.3, non garanti en runtime packagé. **OpenUSD est retenu séparément** comme format d'échange (OPP-077) : c'est le format qui vaut, pas le connecteur. |
| OPP-123 | **AirSim (Microsoft)** | Archivé par l'éditeur. Remplacé par Cosys-AirSim (OPP-074), fork activement maintenu — correction assumée au Livrable 1. |
| OPP-124 | **Autonomie de navigation drone non supervisée** | Garde-fous RFC-0004 §8. Cohérent avec la position tenue sur les VLA de navigation dans le registre Applications clientes. |
| OPP-125 | **Le Hub comme source de vérité** | Contredit la règle §2.1. Définitif. |

---

## 7. Précédents scientifiques — ce qui rend l'approche défendable

Quatre publications, aucune de plus d'un an au moment de leur recension, valident
que le jumeau numérique incendie dans Unreal n'est pas une lubie isolée :

| Publication | Année | Ce qu'elle valide |
|---|---|---|
| **FIRETWIN** (NASA + NSF, arXiv:2510.18879) | 2025 | Modèle couplé atmosphère-feu dans UE5, émetteurs Niagara, simulation de capteurs, génération de données synthétiques, PCG |
| **FIRE-VLM** (arXiv:2601.03449) | 2026 | Drone RL guidé par modèle vision-langage, terrain USGS + combustible LANDFIRE |
| **IVSR** (arXiv:2602.08949) | 2026 | Salle de situation virtuelle, agents autonomes, bibliothèque de scénarios précalculés |
| **Revue** — *Journal of Forestry Research* (Springer) | 2026 | Le domaine est reconnu académiquement |

**Lecture stratégique inchangée :** l'approche est scientifiquement défendable et
récente — mais nous ne sommes plus seuls sur ce terrain. L'équipe FIRETWIN mérite
d'être identifiée nommément comme piste de veille, voire de contact académique,
sur le modèle de la relation avec l'Université de Corse pour ForeFire.

---

## 8. Sources absorbées

| Document d'origine | Apport |
|---|---|
| `UNREAL_ENGINE_PRECEDENTS` | FIRETWIN, FIRE-VLM, IVSR, Cosys-AirSim, Gaussian Splats, SegmentAnyTreeV2, Crown-BERT |
| `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL` | Périmètre du Centre de Commandement, briques existantes, maturité du plugin MCP, architecture recommandée |
| `VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20` | Réserve sur le connecteur Omniverse, OpenUSD comme format d'échange |
| `VEILLE_NVIDIA_DEV_BLOG_2026-08-08` | World models Cosmos, Isaac/Warp |

---

## 9. Journal des reclassements

| Date | Mouvement | Motif |
|---|---|---|
| 2026-08-16 | Création — 12 opportunités actives, 4 écartées, 4 renvois croisés | Consolidation par cible d'exécution |
| 2026-08-16 | OPP-082 (données synthétiques) placée au rang 1 | Elle lève le verrou qui bloque trois autres registres |
| 2026-08-16 | OPP-077 (OpenUSD) séparée de OPP-122 (connecteur Omniverse) | Le format est retenu, le connecteur écarté — même logique que patron OTP / Elixir |

---

## 10. Historique

| Version | Date | Auteur | Modification |
|---|---|---|---|
| 1.0.0 | 2026-08-16 | Claude | Création — registre par cible d'exécution |
