# GeoSylva-Unreal — Architecture, pipeline de données et briques techniques

| Champ | Valeur |
|---|---|
| **Livrable** | 212 — GeoSylva-Unreal Architecture (pipeline LiDAR + PCG) |
| **Phase** | 2 — Architecture |
| **Statut** | Draft — **piste en attente volontaire** (ne pas construire avant MVP Ignis) |
| **Date de révision** | 2026-07-12 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-005, GSIE-CON-007, GSIE-CON-010 |
| **Constitutions liées** | Scientifique (S-1, S-2, S-7, S-8), Technique (T-8, T-10) |
| **Directives liées** | GSIE-DIR-0005 (jumeau numérique vivant — gradient de fidélité) |
| **Décision d'adoption** | DEC-000010 (adoption UE 5.8 + Cesium, base partagée) |
| **Documents connexes** | `GSIE_IGNIS_GCS_CINEMA_UNREAL.md` (livrable 211, base technique commune §9) |

> Version 1.0.0 — 2026-07-12
> Statut : recherche et architecture — **cette piste ne doit pas être construite avant qu'Ignis ait son MVP fonctionnel** (règle S-08/discipline validée dans la session précédente).
> Note de nommage : ce document ouvre une numérotation propre à GeoSylva (distincte de « GSIE-Feu_Phase0_LivrableN », qui appartient à Ignis). Les deux pistes partageront de l'infrastructure (§9) mais restent des spécialisations séparées dans Quintessences.
> Registre associé : `GSIE-Feu_registre_idees.md`, module 10 (GU-01 à GU-07).

---

## Résumé exécutif

| # | Brique | Recommandation | Confiance |
|---|---|---|---|
| 1 | Principe directeur | Gradient de fidélité : haute fidélité (LiDAR, arbres individuels) sur zones/parcelles données ; procédural scientifique partout ailleurs | Haute — déjà validé par Camille |
| 2 | Terrain | BD ALTI (contexte large) + **LiDAR HD IGN** (précision, zones ciblées) | Haute — couverture nationale quasi achevée (voir §2) |
| 3 | Segmentation d'arbres individuels | **PyCrown** (Python natif) comme premier outil ; `lidR` (R) comme référence méthodologique ; ForAINet/TreeLearn (deep learning) si précision maximale requise plus tard | Haute pour PyCrown, moyenne pour le choix definitif long terme |
| 4 | Génération procédurale scientifique | **PCG framework** (production-ready depuis UE 5.7) piloté par des **couches de données de landscape** (soil/pente/altitude/essence peintes comme layers) | Haute — mécanisme confirmé et déjà utilisé dans un précédent académique direct (FIRETWIN) |
| 5 | Assets végétaux | Procedural Vegetation Editor (PVE, natif UE 5.7+) pour démarrer, gratuit ; SpeedTree ou Natsura en complément si espèces françaises spécifiques non couvertes | Moyenne — PVE encore jeune, à valider en pratique |
| 6 | Synchronisation jumeau numérique | Séparation stricte **état réel (source de vérité, versionné)** / **état simulé (scénario, jamais fusionné automatiquement)** | Haute — cohérent avec CON-010 de la Constitution Quintessences |
| 7 | VR | Reporté (« à terme » dans la vision initiale). Contrainte réelle à anticiper : Nanite/Lumen non supportés en VR autonome (casque seul), support partiel en PCVR | Haute sur la contrainte, basse priorité d'exécution |
| 8 | Intégration IA | L'IA écrit dans la couche de données GSIE ; Unreal **reflète** l'état (jamais l'inverse) | Haute — corrige l'incohérence relevée dans la vision initiale |
| 9 | Architecture Ignis ↔ GeoSylva-Unreal | Base commune (Cesium, ingestion WebSocket/JSON, conventions de données) partagée en plugin ; logique spécifique (Niagara feu vs PCG végétation) séparée par module | Moyenne — à trancher en RFC |

---

## 1. Principe directeur : le gradient de fidélité

Rappel de ce qui a été acté : **haute fidélité sur de petites zones/parcelles données**, pas sur des territoires entiers. Concrètement, trois niveaux de représentation coexistent dans la même scène :

| Niveau | Contenu | Source | Usage |
|---|---|---|---|
| **Contexte** | Relief général, occupation du sol grossière | BD ALTI, BD Forêt, orthophoto | Navigation, mise en situation, zones non prioritaires |
| **Procédural scientifique** | Végétation plausible, non individuellement mesurée | PCG piloté par pente/exposition/sol/essences dominantes (BD Forêt) | Massifs environnants, zones jamais inventoriées |
| **Haute fidélité** | Arbres individuels réels, attributs mesurés | LiDAR HD + inventaire terrain GeoSylva | La parcelle qu'on étudie vraiment, démonstrateurs, formation |

C'est exactement l'architecture que la plupart des vrais jumeaux numériques à grande échelle utilisent (simulateurs de vol, moteurs de rendu de villes) — et elle a un avantage supplémentaire chez toi : elle donne un chemin de croissance naturel. Une parcelle inventoriée aujourd'hui passe du niveau « procédural » au niveau « haute fidélité » simplement en important ses données réelles, sans rien reconstruire.

---

## 2. Terrain : BD ALTI + LiDAR HD — l'état réel de la donnée

Le programme national LiDAR HD de l'IGN vise la **couverture complète de la France métropolitaine (hors Guyane) d'ici fin 2026**, à une densité moyenne de 10 points/m². Point important pour ta planification : selon le dernier point d'avancement disponible, **93 % de la surface finale est déjà survolée et 84 % des nuages de points sont déjà publiés en open data**. Concrètement : pour n'importe quelle zone de test que tu choisiras (Landiras compris), la donnée LiDAR HD est très probablement déjà disponible ou le sera sous peu — ce n'est plus un pari sur l'avenir, c'est une ressource quasi prête.

Produits utiles, tous dérivés du même nuage de points classé (11 catégories : sol, végétation basse/moyenne/haute, bâtiment, eau...) :
- **MNT LiDAR HD** : modèle numérique de terrain, 50 cm de résolution, GeoTIFF, dalles 1×1 km.
- **MNS** (implicite, dérivé du nuage classé) et **MNH LiDAR HD** : ce dernier est directement la différence MNS−MNT — **c'est exactement la hauteur de canopée dont tu as besoin pour la génération procédurale et la détection d'arbres**.
- Diffusion : geoservices.ign.fr/lidarhd et cartes.gouv.fr, licence ouverte (réutilisation commerciale autorisée).
- ⚠️ Restriction à connaître : les ZICAD (zones interdites à la captation aérienne, sites sensibles) renvoient des données vides (nodata) — à prévoir dans la gestion d'erreurs du pipeline d'import.

BD ALTI reste utile comme fallback pour les zones pas encore publiées, et pour le contexte large où la précision LiDAR serait inutilement coûteuse à charger.

---

## 3. Pipeline LiDAR → arbres individuels

### 3.1 Ce que la segmentation individuelle sait faire aujourd'hui (état de l'art)

La segmentation d'arbres individuels depuis LiDAR aéroporté est un domaine de recherche mature, pas expérimental : les meilleures approches deep learning récentes atteignent des F-scores supérieurs à 85 % sur des jeux de données publics multi-pays (notamment le benchmark **FOR-Instance**, acquis par drone dans 5 pays).

**Attributs fiables directement extractibles** : hauteur, diamètre de houppier, volume de couronne, position (x, y), et — avec plus d'incertitude — un proxy du DBH (diamètre à hauteur de poitrine) selon la densité du nuage.

**⚠️ Attributs NON extractibles directement du LiDAR seul** : essence, âge, état sanitaire précis. Ces trois nécessitent soit du multispectral/hyperspectral en complément, soit une inférence statistique (contexte, BD Forêt), soit une vérification terrain. Ne pas promettre plus que ce que la donnée permet — c'est exactement la distinction démontré/prometteur/incertain que tu exiges.

### 3.2 Outils, du plus simple au plus poussé

| Outil | Langage | Nature | Quand l'utiliser |
|---|---|---|---|
| **PyCrown** | **Python** | Segmentation raster (sur Modèle de Hauteur de Canopée) par maxima locaux, optimisé Cython/Numba | Point de départ recommandé — colle à ton stack Python, rapide, méthode publiée (Dalponte & Coomes 2016) |
| `lidR` | R | Référence académique du domaine, très complet (CHM, segmentation nuage de points, métriques) | Référence méthodologique à consulter même si tu n'écris pas en R — beaucoup de papiers s'y comparent |
| ForAINet / TreeLearn | Python (deep learning) | Segmentation par réseaux de neurones sur nuage de points brut, meilleure précision sur canopées complexes/superposées | Si la précision de PyCrown ne suffit pas sur tes peuplements denses |
| TLS2trees | Python | Équivalent pour LiDAR terrestre (scan au sol, pas aéroporté) | Seulement si tu fais un jour du scan terrestre complémentaire — pas pertinent pour du LiDAR HD IGN (aéroporté) |
| Lidar360 / Lidarvisor | Commercial, clé en main | Pipeline complet nuage → rapport d'inventaire (PDF/CSV) | Option « acheter plutôt que construire » si le temps de développement presse |

**Recommandation concrète** : PyCrown sur un MNH LiDAR HD pour la première parcelle de test — c'est le chemin le plus court entre « j'ai un fichier LAZ » et « j'ai une liste d'arbres avec position et hauteur », et ça reste dans ton stack.

---

## 4. Génération procédurale pilotée par la science — le mécanisme exact

C'est la question technique centrale de toute la vision, et la réponse est maintenant précise, pas conceptuelle.

### 4.1 Le framework PCG

Le PCG (Procedural Content Generation) d'Unreal est passé d'expérimental (5.2) à bêta (5.4) à **production-ready en 5.7**, avec un doublement de performance. C'est un système de graphes (comme Niagara ou l'éditeur de matériaux) : pas de position à saisir à la main, des **règles**.

### 4.2 Comment injecter tes règles scientifiques concrètement

Le mécanisme s'appelle les **landscape data layers** (couches de données peintes sur le terrain, comme des calques de poids) et les **nœuds de requête landscape** qui les lisent. Concrètement, pour ton exemple « chênaie sur sol acide en exposition nord donne tel sous-bois » :

1. Tu dérives des rasters depuis tes vraies sources (déjà identifiées dans le registre Ignis, réutilisables ici) : pédologie (BDGSF/RRP), pente et exposition (calculées depuis le MNT), essences dominantes (BD Forêt).
2. Ces rasters sont importés comme **couches de poids** du terrain Unreal (le workflow standard : peindre/importer une texture de poids par couche, exactement comme peindre une texture d'herbe vs de roche).
3. Le graphe PCG utilise des nœuds « Landscape Sample » pour lire ces couches, des filtres de pente/altitude, puis une branche par essence :
```
Landscape Sample → Filtre pente/altitude/couche sol → Branche par essence
├── Chêne (densité, espacement, échelle) — actif si couche "sol acide" + pente <15°
├── Pin (densité, espacement, échelle) — actif si couche "sol sableux"
└── ... autres essences, sous-bois, fougères en branches parallèles
```
4. Un module de **positionnement physique** (post-placement) évite le classique « arbre qui flotte » en calant automatiquement chaque instance sur la pente réelle.

Ce n'est pas une extrapolation de ma part : **FIRETWIN utilise exactement ce mécanisme**, avec des données de combustible CAWFE à la place de tes couches pédologiques, et des variantes d'arbres (Pin grand/moyen/petit) par cellule de grille. Le même papier qui valide Ignis valide ce pipeline pour GeoSylva.

### 4.3 Une nuance honnête sur les feuillages ultra-réalistes (Nanite Foliage)

Le rendu de feuillage nouvelle génération d'Unreal (« Nanite Foliage », voxelisation, animation par vent sur maillage squelette, jusqu'à 20-40 millions de triangles par arbre sans coût de performance grâce à l'instanciation) est très impressionnant — mais **encore marqué expérimental en 5.7**, avec une production-readiness annoncée pour mi-2026. Vu la date d'aujourd'hui, il est possible qu'il vienne de basculer en stable ou soit sur le point de le faire — **à vérifier à l'installation**, pas à supposer.

---

## 5. Sources d'assets végétaux (les modèles 3D d'arbres eux-mêmes)

Trois options, pas mutuellement exclusives :

| Option | Nature | Limite actuelle |
|---|---|---|
| **Procedural Vegetation Editor (PVE)** | Natif UE 5.7+, gratuit, simule la croissance botanique (gravité, ramification, signaux hormonaux) pour générer des arbres Nanite-ready | Encore jeune : ne crée pas de nouvelles espèces from scratch, sert surtout à varier des espèces existantes (« Megaplants » presets actuels) |
| **SpeedTree** | Outil de référence historique du secteur, toujours activement supporté et importable dans le pipeline Nanite Foliage (via USD, hiérarchie squelette + métadonnées vent préservées) | Licence séparée à vérifier ; nécessaire si tu veux des espèces françaises précises non couvertes par PVE |
| **Natsura** | Outil tiers (moteur de croissance basé Houdini), « recettes d'espèces » définies indépendamment du moteur (Grow/Split/Mapping/Effectors/Decorations), exportables vers Nanite Foliage + PCG | Solution la plus proche philosophiquement de « règles scientifiques génériques », mais dépendance à un outil tiers payant |

**Recommandation** : démarrer avec PVE (natif, gratuit, suffisant pour un premier démonstrateur avec 3-4 essences françaises courantes), garder SpeedTree/Natsura en réserve si le besoin d'espèces spécifiques (ex. chêne pédonculé vs chêne vert, distinction importante pour toi) dépasse ce que PVE couvre nativement.

---

## 6. Synchronisation du jumeau numérique — l'architecture qui répond à ta contrainte

Ta règle : une donnée terrain modifiée doit se refléter automatiquement dans le jumeau ; une simulation ne doit jamais altérer les données réelles. C'est un problème d'architecture de données classique en digital twin, avec une solution éprouvée : **séparer strictement l'état réel de l'état simulé**.

```
État réel (source de vérité)              État simulé (scénario)
─────────────────────────────             ───────────────────────
Mesures terrain, LiDAR                    Copie de départ de l'état réel
Versionné, historisé (jamais écrasé)      + modifications hypothétiques
     │                                    (éclaircie, coupe, croissance
     │ lecture seule                      projetée, sécheresse...)
     ▼                                    Jamais réinjecté automatiquement
Unreal affiche l'état réel                dans l'état réel
                                                │
                                                ▼
                                    Unreal affiche le scénario,
                                    visuellement distingué du réel
```

Point notable : **c'est exactement le même patron architectural que G-18** (le front de feu calculé vs observé, ajouté dans le registre Ignis la session précédente) — distinguer *ce qu'on sait mesuré* de *ce qu'on a inféré/simulé*, ne jamais laisser le second écraser silencieusement le premier. Ce n'est pas une coïncidence : c'est un principe GSIE générique qui traverse les deux spécialisations, et une bonne raison de le documenter une seule fois au niveau du moteur GSIE plutôt que deux fois.

Bonus de gouvernance : cette architecture respecte directement **CON-010** de ta Constitution (« toute connaissance doit pouvoir évoluer sans perdre son historique ») — l'état réel versionné n'est jamais perdu, même quand un scénario s'en écarte radicalement.

---

## 7. VR — un point de vigilance technique honnête, pas un blocage

Tu situes toi-même la VR « à terme » — donc pas de priorité d'exécution ici, mais une contrainte réelle à connaître pour ne pas la découvrir tard :

- **Nanite et Lumen ne sont pas supportés en VR autonome** (casque seul, ex. Quest en mode standalone) — limitation matérielle (puce mobile), toujours vraie début 2026 selon les guides d'optimisation les plus récents.
- **En PCVR** (rendu PC, streamé vers le casque via câble/Air Link), Lumen fonctionne avec certains réglages (Forward Shading désactivé) ; Nanite reste plus incertain en pratique, même si des tests communautaires l'ont fait tourner avec réglages fins.
- Conséquence pratique : la scène « formation/exercice DFCI en VR » aura probablement besoin d'un **profil de rendu simplifié dédié** (géométrie classique avec LOD manuels, pas de Nanite Foliage), distinct du profil desktop haute fidélité. Ce n'est pas un obstacle, juste un budget de rendu à prévoir séparément le moment venu.

---

## 8. Intégration IA — la clarification de l'architecture

Reprise de la correction posée dans notre échange précédent : « pas de logique métier dans Unreal » et « IA reliée aux objets 3D » ne se contredisent que si on les lit littéralement. La version cohérente :

```
Capteurs/données → Moteurs GSIE (Diagnostic, Correlation, Forest Dynamics...)
                    calculent état sanitaire, risque, croissance prédite
                         │
                         │ écrit dans la couche de données GSIE
                         ▼
              Unreal LIT cet état et choisit mesh/matériau/animation
              en conséquence (arbre malade → texture altérée, etc.)
```

L'IA ne touche jamais un objet 3D directement — elle alimente la donnée, Unreal la reflète. C'est ce qui garde GSIE comme cœur du système, exactement ta propre exigence de départ.

---

## 9. Architecture d'ensemble : Ignis et GeoSylva-Unreal, partagés ou séparés ?

Question à trancher, avec une recommandation :

**Partager** (en plugin/module C++ commun) : la connexion Cesium au terrain géoréférencé, le module d'ingestion WebSocket/JSON natif (déjà construit pour Ignis, §7 de l'AGENTS.md), les conventions de données (Lambert 93 interne, WGS84 aux interfaces), la structure de synchronisation réel/simulé (§6 de ce document).

**Séparer** (logique propre à chaque spécialisation) : Niagara feu/fumée (Ignis) vs PCG végétation (GeoSylva) ; le mode d'usage (Ignis = supervision opérationnelle temps réel, GeoSylva = planification/formation, rythme différent).

Recommandation : **un seul projet Unreal avec une architecture en plugins internes**, plutôt que deux projets séparés — ça évite de dupliquer Cesium/WebSocket deux fois, et ça respecte CON-007 (modularité) en gardant chaque spécialisation dans son propre module. À formaliser en RFC quand le moment viendra (pas maintenant, cf. discipline S-08).

---

## 10. Prochaines actions

1. **Ne pas commencer à construire** — cette piste reste en attente jusqu'à ce qu'Ignis ait son MVP (boucle d'assimilation fonctionnelle).
2. Quand le moment viendra : télécharger une dalle MNH LiDAR HD sur une parcelle test connue, faire tourner PyCrown dessus — premier test concret du pipeline §3, réalisable en une session, indépendant du reste.
3. En parallèle (pas de dépendance) : tester un premier graphe PCG simple (scatter de rochers ou d'arbres génériques sur un terrain quelconque) pour se familiariser avec le mécanisme avant d'y brancher de vraies données.
4. Formaliser en RFC : le renommage Ignis (déjà dû), et le choix d'architecture projet unique vs séparé (§9) quand GeoSylva-Unreal sera activement priorisé.

## Sources principales
Programme LiDAR HD IGN (ign.fr, cartes.gouv.fr, avancement officiel 2025-2026) ; PyCrown (Dalponte & Coomes 2016, GitHub manaakiwhenua) ; benchmark FOR-Instance ; ForAINet, TreeLearn (littérature deep learning segmentation LiDAR 2024-2026) ; documentation Epic Developer Community sur PCG et Nanite Foliage ; StraySpark — *UE 5.7: PCG Is Production-Ready* (2026) ; FIRETWIN (arXiv:2510.18879, section génération procédurale de forêt) ; Natsura (natsura.com) ; guides d'optimisation VR Unreal Engine 2026 (Nanite/Lumen sur XR mobile vs PCVR).
