# GEO-001 — Spécification fonctionnelle GeoSylva

| Champ | Valeur |
|---|---|
| **Document** | GEO-001 |
| **Dossier** | 05_SPECIFICATIONS/GEOSYLVA/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-001 (décideur humain), GSIE-CON-002 (science avant tout), GSIE-CON-003 (connaissance avant code), GSIE-CON-005 (traçabilité), GSIE-CON-007 (modularité), GSIE-CON-010 (versionnement) |
| **Constitutions liées** | Scientifique (S-1 référentiels officiels, S-6 domaines de connaissance, S-7 reproductibilité, S-8 discipline), Technique (T-2 interchangeabilité, T-8 fonctionnement hors-ligne, T-10 résilience) |
| **Directives liées** | GSIE-DIR-0005 (jumeau numérique vivant — gradient de fidélité), GSIE-DIR-0006 (raisonnement multi-échelle), GSIE-DIR-0008 (Encyclopédie de l'Écosystème), GSIE-DIR-0009 (restructuration écosystème) |
| **Décisions liées** | DEC-000010 (UE 5.8 + Cesium), DEC-000011 (ouverture Phase 3), DEC-000013 (restructuration GSIE) |
| **Architecture de référence** | `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` (livrable 212), `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211) |
| **Ontologie de référence** | `GSIE/KNOWLEDGE/FOREST_ONTOLOGY.md` (livrable 303) |
| **Catalogue de données** | `GSIE/DATASETS/DATASET_CATALOG.md` (livrable 305 — DS-001 à DS-026) |
| **Documents connexes** | `HUB_001_SPECIFICATION.md`, `HUB_002_INTERFACE_CONTRACT.md`, `HUB_AND_APPS_PLAN.md`, `apps/GeoSylva/README.md`, `apps/GeoSylva/MASTER_PLAN.md`, `02_RFC/RFC-0003.md` (GSIE-Net, offline) |

> Cette spécification décrit **ce que GeoSylva doit faire**, pas comment
> (rôle de l'architecture, livrable 212). Aucun code métier n'est produit
> ici (CON-003, Phase 3). GeoSylva est une application cliente de GSIE :
> elle consomme les moteurs et expose ses sorties au Hub via le contrat
> d'interface HUB-002.

---

## 1. Objet et périmètre

### 1.1 Définition

**GeoSylva** est l'application forestière de l'écosystème Quintessences.
Spécialisation du moteur GSIE sur le domaine forestier, elle couvre
deux surfaces complémentaires :

1. **App mobile terrain** (Android, existante — `apps/GeoSylva/`) —
   inventaire forestier, dendrométrie, martelage, cartographie,
   entièrement hors-ligne. Conçue par des forestiers, pour des
   forestiers.
2. **Visualisation Hub** (Centre de Commandement, Unreal Engine 5.8) —
   représentation 3D géoréférencée de la forêt : peuplements, arbres
   individuels, végétation procédurale, diagnostics, biomasse.

GeoSylva est une **cliente de GSIE** : elle ingère les datasets
référencés (DS-xxx), sollicite les moteurs GSIE (Diagnostic,
Recommendation, Forest Dynamics, GIS) et publie ses sorties via l'API
GSIE (livrable 207) au format défini par le contrat d'interface Hub ↔
Apps (HUB-002).

### 1.2 Principe fondamental

> **La connaissance avant le code (CON-003) ; le forestier décide
> (CON-001).**

GeoSylva ne calcule pas la science elle-même — elle délègue les
calculs métier aux moteurs GSIE et **reflète** les résultats validés.
L'IA assiste le forestier en produisant des diagnostics et
recommandations explicables, mais la décision opérationnelle
(martelage, coupe, itinéraire sylvicole) appartient toujours au
forestier. Toute recommandation est contournable et tracée.

Cette séparation est cohérente avec le principe directeur du Hub
(HUB-001 §1.2) : le Hub reflète l'état du jumeau numérique, il ne le
calcule jamais. GeoSylva suit la même logique — l'IA écrit dans la
couche de données GSIE, le Hub et l'app mobile reflètent l'état
(livrable 212 §8).

### 1.3 Périmètre inclus

- **Inventaire forestier** — segmentation d'arbres individuels depuis
  LiDAR HD, dendrométrie (hauteur, DBH, surface terrière, densité),
  saisie terrain mobile
- **Diagnostic sylvicole** — évaluation de l'état du peuplement,
  identification des besoins (éclaircie, régénération, sanitaire)
- **Recommandations de gestion** — itinéraires sylvicoles proposés par
  le moteur Recommendation, validés par le forestier
- **Visualisation 3D forêt (Hub)** — peuplements, arbres individuels,
  végétation procédurale PCG, Gaussian Splats pour parcelles de
  référence
- **App mobile terrain (offline-first)** — inventaire, martelage,
  clinomètre, GPS, cartographie embarquée, exports SIG
- **Estimation biomasse / carbone** — biomasse locale (LiDAR HD),
  biomasse spatiale (GEDI, ESA Biomass CCI), suivi inter-annuel

### 1.4 Périmètre exclu

- **Calcul métier** (segmentation, diagnostic, recommandation,
  modèles de croissance) → moteurs GSIE (Forest Dynamics, Diagnostic,
  Recommendation, Simulation)
- **Stockage persistant des données** → API GSIE / base de
  connaissances (`GSIE/KNOWLEDGE/`)
- **Décision opérationnelle finale** (martelage, coupe) → forestier
  (CON-001)
- **Rendu 3D temps réel** → Hub / Centre de Commandement (livrable
  211)
- **Modélisation pédologique ou climatique** → Pedology Engine,
  Climate Engine (GeoSylva consomme leurs sorties)

---

## 2. Acteurs et rôles

| Acteur | Rôle dans GeoSylva | Niveau d'interaction |
|---|---|---|
| **Forestier / sylviculteur** | Réalise l'inventaire terrain, consulte les diagnostics, valide ou rejette les recommandations, décide du martelage | Saisie + lecture + validation (CON-001) |
| **Gestionnaire ONF** | Supervise les peuplements à l'échelle du massif, consulte les cartes dendrométriques, planifie les interventions | Lecture + annotation |
| **Chercheur (INRAE, IGN)** | Explore les dynamiques de peuplement, exporte les données pour publication, calibre les modèles de croissance | Lecture + export |
| **Propriétaire privé** | Consulte l'état de sa parcelle, les recommandations simplifiées | Lecture seule |
| **App mobile GeoSylva (Android)** | Saisie terrain offline, GPS, clinomètre, cartographie embarquée, synchronisation différée | Producteur de données terrain |
| **API GSIE** | Fournit les données calculées (diagnostics, recommandations, biomasse) et reçoit les saisies terrain | Producteur + consommateur |
| **Hub (Centre de Commandement)** | Consomme les couches `geosylva.*` publiées par GeoSylva via l'API GSIE | Consommateur passif (HUB-002 §1) |

---

## 3. Exigences fonctionnelles

### 3.1 Inventaire et segmentation (GEO-F-01 à GEO-F-04)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-F-01 | GeoSylva doit ingérer les produits LiDAR HD IGN (MNT 50 cm, MNS, MNH) comme socle terrain et canopée pour les zones d'étude | P0 | DS-002, livrable 212 §2 |
| GEO-F-02 | GeoSylva doit segmenter les arbres individuels depuis le MNH LiDAR HD, en utilisant PyCrown comme premier outil et SegmentAnyTreeV2 comme évolution de montée en gamme (zero-shot, cross-domain) | P0 | Livrable 212 §3.2 |
| GEO-F-03 | GeoSylva doit calculer les attributs dendrométriques extractibles par arbre : hauteur, diamètre de houppier, position (x, y), proxy DBH (avec incertitude liée à la densité du nuage), surface terrière et densité agrégées au niveau peuplement | P0 | Livrable 212 §3.1, ontologie DOM-DEN (livrable 303 §5) |
| GEO-F-04 | GeoSylva doit identifier les essences par fusion des données BD Forêt v2 (DS-001, inférence par contexte et peuplement) et, si un capteur hyperspectral drone est disponible, classification par Crown-BERT (83-91 % OA). Les attributs non extractibles du LiDAR seul (essence, âge, état sanitaire) doivent être signalés comme incertains et nécessiter une vérification terrain | P1 | DS-001, livrable 212 §3.1-§3.2, Crown-BERT (doi:10.6084/m9.figshare.32296654) |

> **Honnêteté scientifique (livrable 212 §3.1) :** le DBH, l'essence,
> l'âge et l'état sanitaire précis ne sont **pas** extractibles du LiDAR
> seul. GeoSylva doit distinguer visuellement et dans les métadonnées
> les attributs démontrés (hauteur, houppier) des attributs inférés
> (DBH, essence) et des attributs nécessitant vérification terrain
> (âge, sanitaire). Cette distinction est conforme au framework de
> preuve (livrable 306, CON-002).

### 3.2 Peuplements et cartographie (GEO-F-05 à GEO-F-07)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-F-05 | GeoSylva doit cartographier les peuplements forestiers depuis BD Forêt v2 (polygones, surface minimum 500 m², nomenclature essences IGN) | P0 | DS-001, ontologie DOM-SYL (livrable 303 §10) |
| GEO-F-06 | GeoSylva doit caractériser chaque peuplement par son type (futaie régulière, futaie irrégulière, taillis, mélange), sa structure (stade : semis, gaulis, perchis, futaie jeune, futaie adulte) et sa composition (essence dominante + accompagnement) | P0 | Ontologie DOM-DYN §12, DOM-SYL §10 (livrable 303) |
| GEO-F-07 | GeoSylva doit produire des cartes dendrométriques à l'échelle du peuplement (surface terrière G, DBH moyen et dominant, hauteur dominante, densité de tiges, structure) selon le modèle ONF validé à 700 m²/pixel | P1 | Livrable 212 §3.3 (précédent ONF), DS-002, DS-003 |

> **Précédent opérationnel (livrable 212 §3.3) :** l'ONF a validé en
> production le croisement LiDAR HD + données dendrométriques terrain
> pour produire des cartes à 700 m²/pixel (surface terrière, diamètre,
> hauteur dominante, densité, structure). Citation Fabrice Coq (ONF) :
> *« La télédétection, et notamment le LiDAR HD, a le même impact pour
> les forestiers que l'arrivée d'internet »*. Ce précédent confirme la
> faisabilité du pipeline GeoSylva en France — pas théorique.

### 3.3 Biomasse et carbone (GEO-F-08 à GEO-F-10)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-F-08 | GeoSylva doit estimer la biomasse aérienne locale (AGB) à haute résolution depuis le LiDAR HD IGN (DS-002), calibrée sur les placettes IFN (DS-003), avec incertitude par arbre et par peuplement | P1 | DS-002, DS-003, livrable 212 §3.1, ontologie DOM-DEN |
| GEO-F-09 | GeoSylva doit estimer la biomasse spatiale sur les zones non couvertes par le LiDAR HD IGN en utilisant GEDI L4A/L4B (footprint 25 m, grille 1 km) et ESA Biomass CCI v7 (100 m × 100 m), avec incertitude fournie par cellule | P2 | DS-025 (GEDI L4A v3, L4B v2.1), DS-026 (ESA Biomass CCI v7.0) |
| GEO-F-10 | GeoSylva doit suivre les changements inter-annuels et décennaux de biomasse en utilisant les cartes annuelles ESA Biomass CCI v7 (2015-2024) et les cartes de changement décennal (2020-2010), complétées par les alertes déforestation RADD (Sentinel-1) | P2 | DS-026 (v7.0, publiée 2026-05-21) |

> **Complémentarité des sources (DS-002 / DS-025 / DS-026) :** le LiDAR
> HD IGN fournit la biomasse à haute résolution nationale là où il est
> publié (84 % de la France en juillet 2026, couverture complète fin
> 2026). GEDI comble les zones non encore publiées et permet les
> comparaisons internationales. ESA Biomass CCI fournit la série
> temporelle longue pour le suivi des changements. GeoSylva doit
> indiquer clairement la source utilisée pour chaque estimation
> (CON-005).

### 3.4 Diagnostic et recommandations (GEO-F-11 à GEO-F-13)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-F-11 | GeoSylva doit produire un diagnostic sylvicole par peuplement (état sanitaire, structure, densité vs densité optimale, besoins d'intervention) en sollicitant le moteur Diagnostic, qui croise les données dendrométriques, l'ontologie forestière et l'étation écologique | P0 | Moteur Diagnostic, ontologie DOM-SYL/DOM-DYN (livrable 303), DS-001, DS-002, DS-003 |
| GEO-F-12 | GeoSylva doit proposer des recommandations de gestion (éclaircie, régénération, coupe sanitaire, itinéraire sylvicole) en sollicitant le moteur Recommendation, avec justification explicitable pour chaque recommandation (facteurs déterminants, référentiels ONF/CRPF/IDF) | P0 | Moteur Recommendation, ontologie DOM-SYL (livrable 303 §10), référentiels ONF/CRPF/IDF |
| GEO-F-13 | GeoSylva doit soumettre chaque recommandation à la validation du forestier (CON-001) : le forestier peut valider, modifier ou rejeter. Toute décision (y compris le rejet) est tracée et versionnée (CON-010). L'IA ne décide jamais à la place du forestier | P0 | GSIE-CON-001, RFC-0004 §8 (garde-fous), ontologie DOM-SYL |

> **Garde-fou constitutionnel (CON-001) :** les recommandations sont
> explicables et contournables. Le forestier reste le décideur. Aucune
> action critique (martelage, coupe) n'est exécutée sans validation
> humaine explicite. Cette exigence est commune au Hub (HUB-F-24) et à
> GeoSylva.

### 3.5 Visualisation Hub (GEO-F-14 à GEO-F-17)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-F-14 | GeoSylva doit exposer ses sorties au Hub via les couches `geosylva.*` définies dans le contrat d'interface HUB-002 (peuplements, arbres, essences, diagnostics, recommandations, biomasse, pcg_vegetation), au format 3D Tiles / GeoJSON / GeoTIFF selon le canal | P0 | HUB-002 §2 (registre des couches) |
| GEO-F-15 | GeoSylva doit piloter la génération de végétation procédurale dans le Hub via le framework PCG d'Unreal Engine (production-ready 5.7+), en injectant des rasters scientifiques (pente, exposition, sol, essences dominantes) comme landscape data layers, avec un nœud de requête landscape par essence et un positionnement physique post-placement | P1 | Livrable 212 §4 (PCG + landscape data layers), DS-001, DS-002 |
| GEO-F-16 | GeoSylva doit appliquer le gradient de fidélité à trois niveaux dans la même scène 3D : (1) contexte (relief, occupation du sol — BD ALTI, BD Forêt, orthophoto) ; (2) procédural scientifique (végétation plausible pilotée par PCG — massifs environnants) ; (3) haute fidélité (arbres individuels réels depuis LiDAR HD + inventaire terrain — parcelle étudiée) | P1 | Livrable 212 §1 (gradient de fidélité), GSIE-DIR-0005 |
| GEO-F-17 | GeoSylva doit exposer des Gaussian Splats géoréférencés pour les arbres remarquables et les parcelles de référence (reconstruction drone), streamés via le pipeline Cesium ion (3D Tiles, LOD hiérarchique) | P2 | Livrable 211 §2 (Gaussian Splats validés avril 2026), livrable 212 §1 |

> **Gradient de fidélité (livrable 212 §1) :** ce principe acté donne un
> chemin de croissance naturel — une parcelle inventoriée aujourd'hui
> passe du niveau « procédural » au niveau « haute fidélité »
> simplement en important ses données réelles, sans reconstruire la
> scène. C'est l'architecture qu'utilisent les jumeaux numériques à
> grande échelle (simulateurs de vol, moteurs de rendu de villes).

### 3.6 App mobile terrain (GEO-F-18 à GEO-F-21)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-F-18 | GeoSylva (app Android) doit fonctionner offline-first sur le terrain : 100 % des fonctionnalités de saisie, calcul, cartographie et export disponibles sans connexion réseau, avec tuiles cartographiques téléchargeables | P0 | RFC-0003 (GSIE-Net), T-8/T-10, apps/GeoSylva existant |
| GEO-F-19 | GeoSylva doit permettre la saisie d'inventaire terrain par essence et classe de diamètre (95+ essences pré-configurées), avec comptage par boutons +/−, GPS automatique, clinomètre numérique intégré, et calcul temps réel de la surface terrière (G/ha) | P0 | apps/GeoSylva (v2.4.0 existant), ontologie DOM-DEN |
| GEO-F-20 | GeoSylva doit synchroniser les données terrain vers l'API GSIE en mode différé (synchronisation différée) quand la connexion est disponible, avec résolution des conflits et traçabilité des versions (CON-010) | P0 | RFC-0003 (GSIE-Net), T-10, CON-010 |
| GEO-F-21 | GeoSylva doit fournir un GPS de précision (moyennage multi-lectures, rejet d'outliers) et une cartographie embarquée (12 couches, tuiles offline, import Shapefile, filtre de fiabilité GPS) | P1 | apps/GeoSylva existant, DS-001 (BD Forêt), DS-002 (terrain) |

> **App existante (apps/GeoSylva) :** l'application Android v2.4.0
> existe déjà et couvre l'inventaire terrain, le martelage, l'IBP CNPF,
> le clinomètre, le GPS, la cartographie offline et les exports SIG.
> La spécification GEO-001 couvre à la fois cette app mobile ET la
> visualisation Hub. L'intégration GSIE (synchronisation vers l'API,
> exposition des couches au Hub) est l'extension Phase 4.

### 3.7 État réel vs simulé (GEO-F-22 à GEO-F-23)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-F-22 | GeoSylva doit séparer strictement l'état réel (mesures terrain, LiDAR — source de vérité, versionné, historisé, jamais écrasé) de l'état simulé (scénario sylvicole : éclaircie, coupe, croissance projetée — copie de départ + modifications hypothétiques, jamais réinjecté automatiquement dans l'état réel) | P0 | CON-010, livrable 212 §6 |
| GEO-F-23 | GeoSylva doit respecter la convention du contrat HUB-002 pour la distinction état réel / état simulé : préfixe `simulated.` dans le `layer_id` pour les scénarios (ex. `simulated.geosylva.peuplements`), avec teinte bleutée / hachurée dans le Hub | P0 | HUB-002 §7 (convention état réel vs simulé) |

> **Patron architectural générique (livrable 212 §6) :** cette
> séparation est le même patron que G-18 (front de feu calculé vs
> observé dans Ignis) — distinguer ce qu'on sait mesuré de ce qu'on a
> inféré/simulé, ne jamais laisser le second écraser silencieusement le
> premier. C'est un principe GSIE générique qui traverse les deux
> spécialisations.

---

## 4. Exigences non fonctionnelles

| ID | Exigence | Cible | Source |
|---|---|---|---|
| GEO-NF-01 | App mobile — plateforme | Android 8.0+ (minSdk 26), Kotlin, Jetpack Compose | apps/GeoSylva existant |
| GEO-NF-02 | App mobile — offline | 100 % hors-ligne, tuiles cartographiques téléchargeables, aucune dépendance réseau pour la saisie | RFC-0003, T-8/T-10 |
| GEO-NF-03 | App mobile — synchronisation | Sync différée avec résolution de conflits, traçabilité des versions (CON-010), pas de perte de données en cas de crash | RFC-0003, T-10 |
| GEO-NF-04 | App mobile — sécurité | Chiffrement base de données (SQLCipher), FLAG_SECURE, conformité RGPD documentée, pas de données sensibles en clair | apps/GeoSylva (SQLCipher actif), 19_LEGAL/ |
| GEO-NF-05 | App mobile — GPS | Précision ≤ 3 m (excellent) à ≤ 12 m (modéré), moyennage multi-lectures avec rejet d'outliers (MAD-based) | apps/GeoSylva existant |
| GEO-NF-06 | App mobile — performance | Saisie fluide (< 200 ms de réponse UI), pas de blocage sur calculs dendrométriques, sauvegarde automatique WorkManager | apps/GeoSylva existant |
| GEO-NF-07 | Visualisation Hub — socle | Unreal Engine 5.8 + Cesium for Unreal (DEC-000010), couches `geosylva.*` au format HUB-002 | DEC-000010, HUB-002 |
| GEO-NF-08 | Visualisation Hub — PCG | Framework PCG (production-ready UE 5.7+), landscape data layers pour l'injection des rasters scientifiques | Livrable 212 §4 |
| GEO-NF-09 | Interopérabilité | API GSIE (livrable 207) via WebSocket/JSON (temps réel) et HTTP REST (3D Tiles, GeoJSON, GeoTIFF) | HUB-002 §3, livrable 211 §3 |
| GEO-NF-10 | Systèmes de coordonnées | Lambert 93 (EPSG:2154) en interne (France métropole), WGS84 (EPSG:4326) aux interfaces, WGS84 géocentrique (EPSG:4978) pour 3D Tiles | DEC-000010, HUB-002 §3 |
| GEO-NF-11 | Traçabilité | Chaque couche expose `source_datasets` (DS-xxx), `evidence_level` (A-F), `version` (ISO 8601) — CON-005, CON-010 | HUB-002 §5, livrable 306 |
| GEO-NF-12 | Modularité | GeoSylva est une app remplaçable et désactivable sans casser le Hub (CON-007) ; logique spécifique GeoSylva séparée d'Ignis en module/plugin | CON-007, livrable 212 §9 |

---

## 5. Cas d'usage prioritaires

### 5.1 CU-01 — Diagnostic sylvicole d'une parcelle

**Acteur :** Forestier / sylviculteur
**Scénario :**
1. Le forestier navigue vers une parcelle dans le Hub (recherche par
   commune ou coordonnées Lambert 93).
2. La couche GeoSylva est active : peuplements (BD Forêt, DS-001),
   arbres individuels (segmentation LiDAR HD, DS-002), essences,
   diagnostics.
3. Le forestier active la génération procédurale (PCG) — la végétation
   3D apparaît, pilotée par les couches scientifiques (essence, pente,
   exposition, sol). La parcelle étudiée s'affiche en haute fidélité
   (arbres réels), les massifs environnants en procédural.
4. Le forestier clique sur un arbre → métadonnées (essence, hauteur,
   houppier, DBH estimé avec incertitude, biomasse, source, niveau de
   preuve).
5. Le forestier consulte le diagnostic sylvicole du peuplement (moteur
   Diagnostic) : structure, densité, état sanitaire, besoins
   d'intervention.
6. Le forestier consulte les recommandations (moteur Recommendation) :
   éclaircie à X % de surface terrière, régénération, itinéraire
   sylvicole.
7. Le forestier valide, modifie ou rejette chaque recommandation
   (CON-001). Sa décision est tracée et versionnée (CON-010).

### 5.2 CU-02 — Inventaire terrain offline

**Acteur :** Forestier / sylviculteur (sur le terrain, sans réseau)
**Scénario :**
1. Le forestier télécharge les tuiles cartographiques de sa zone de
   travail avant de partir sur le terrain (offline-first).
2. Sur place, sans réseau, le forestier crée un inventaire : saisie par
   essence et classe de diamètre (boutons +/−), GPS automatique par
   tige, clinomètre numérique pour la hauteur.
3. La surface terrière (G/ha) et la densité (N/ha) sont calculées en
   temps réel pendant la saisie.
4. Le forestier visualise les tiges sur la carte (clustering, code
   couleur par essence, cercles de précision GPS).
5. Le forestier exporte les données (Shapefile, GeoJSON, CSV) pour SIG
   de bureau — disponible immédiatement, hors-ligne.
6. De retour au bureau (ou quand le réseau est disponible), les
   données terrain se synchronisent vers l'API GSIE (sync différée).
   Les conflits éventuels sont résolus et les versions tracées
   (CON-010).
7. Les données terrain alimentent l'état réel du jumeau numérique
   (GEO-F-22) et deviennent la source de vérité versionnée pour cette
   parcelle.

### 5.3 CU-03 — Estimation biomasse et suivi carbone

**Acteur :** Chercheur / gestionnaire ONF
**Scénario :**
1. Le chercheur sélectionne un massif forestier dans le Hub.
2. La couche `geosylva.biomasse` est activée (GeoTIFF, REST, annuel).
3. Sur la zone couverte par le LiDAR HD IGN (DS-002), la biomasse
   s'affiche à haute résolution (calibrée sur placettes IFN, DS-003),
   avec incertitude par pixel.
4. Sur les zones non couvertes, la biomasse est complétée par GEDI
   L4B (DS-025, grille 1 km) et ESA Biomass CCI v7 (DS-026, 100 m).
   La source de chaque pixel est indiquée dans les métadonnées
   (CON-005).
5. Le chercheur active le suivi des changements inter-annuels :
   comparaison ESA Biomass CCI 2015 vs 2024, avec alertes RADD
   (Sentinel-1) pour les pertes récentes.
6. Le chercheur exporte les données (GeoTIFF, JSON) pour publication
   scientifique.

---

## 6. Couches GeoSylva exposées au Hub

> Source : HUB-002 §2 (registre des couches). Détail des fiches couches
> dans `HUB_003_LAYER_SHEETS.md` (à créer).

| `layer_id` | `display_name` | Canal | Format | Fréquence | Mode de rendu Hub |
|---|---|---|---|---|---|
| `geosylva.peuplements` | Peuplements forestiers | REST | 3D Tiles | Statique | Mesh + matériau |
| `geosylva.arbres` | Arbres individuels | REST | GeoJSON | Statique | PCG + instanced meshes |
| `geosylva.essences` | Essences dominantes | REST | 3D Tiles | Statique | Mesh + couleur |
| `geosylva.diagnostics` | Diagnostics sylvicoles | REST | GeoJSON | Quotidien | Mesh + matériau |
| `geosylva.recommandations` | Recommandations | REST | GeoJSON | Quotidien | Mesh + matériau |
| `geosylva.biomasse` | Biomasse (GEDI/ESA) | REST | GeoTIFF | Annuel | Texture sur terrain (draped) |
| `geosylva.pcg_vegetation` | Végétation procédurale | REST | Metadata | Statique | PCG (landscape data layers) |
| `simulated.geosylva.peuplements` | Peuplements (scénario sylvicole) | REST | 3D Tiles | À la demande | Mesh + matériau (teinte bleutée) |

> **Convention état réel vs simulé (HUB-002 §7) :** les couches
> d'état réel utilisent le préfixe `geosylva.` (couleurs naturelles) ;
> les couches d'état simulé utilisent le préfixe `simulated.geosylva.`
> (teinte bleutée / hachurée). Un scénario sylvicole (éclaircie,
> croissance projetée) publie ses couches avec le préfixe `simulated.`
> et ne modifie jamais l'état réel versionné (CON-010, GEO-F-22).

---

## 7. Matrice de traçabilité (exigence → source)

| Exigence | Architecture (livrable) | Dataset | Moteur GSIE | Ontologie (livrable 303) | Contrat Hub |
|---|---|---|---|---|---|
| GEO-F-01 Ingestion LiDAR HD | 212 §2 | DS-002 | GIS Engine | DOM-DEN | — |
| GEO-F-02 Segmentation arbres | 212 §3.2 | DS-002 | Forest Dynamics | DOM-DEN (EC-ARB) | `geosylva.arbres` |
| GEO-F-03 Dendrométrie | 212 §3.1 | DS-002, DS-003 | Forest Dynamics | DOM-DEN §5 | `geosylva.arbres` |
| GEO-F-04 Identification essences | 212 §3.1-§3.2 | DS-001 | Botanical Engine | DOM-BOT §6 | `geosylva.essences` |
| GEO-F-05 Cartographie peuplements | 212 §1 | DS-001 | GIS Engine | DOM-SYL §10 | `geosylva.peuplements` |
| GEO-F-06 Types et structure | — | DS-001 | Forest Dynamics | DOM-DYN §12, DOM-SYL §10 | `geosylva.peuplements` |
| GEO-F-07 Cartes dendrométriques | 212 §3.3 (ONF) | DS-002, DS-003 | Forest Dynamics | DOM-DEN §5 | `geosylva.peuplements` |
| GEO-F-08 Biomasse locale | 212 §3.1 | DS-002, DS-003 | Forest Dynamics | DOM-DEN | `geosylva.biomasse` |
| GEO-F-09 Biomasse spatiale | — | DS-025, DS-026 | Forest Dynamics, Correlation | DOM-DEN | `geosylva.biomasse` |
| GEO-F-10 Suivi changements | — | DS-026 | Forest Dynamics, Correlation | DOM-DYN §12 | `geosylva.biomasse` |
| GEO-F-11 Diagnostic sylvicole | — | DS-001, DS-002, DS-003 | Diagnostic Engine | DOM-SYL, DOM-DYN | `geosylva.diagnostics` |
| GEO-F-12 Recommandations | — | DS-001, DS-003 | Recommendation Engine | DOM-SYL §10 | `geosylva.recommandations` |
| GEO-F-13 Validation forestier | — | — | Validation Engine | — | — |
| GEO-F-14 Couches geosylva.* | 211 §0.3 | — | — | — | HUB-002 §2 |
| GEO-F-15 Végétation procédurale PCG | 212 §4 | DS-001, DS-002 | Forest Dynamics | DOM-BOT, DOM-ECO | `geosylva.pcg_vegetation` |
| GEO-F-16 Gradient de fidélité | 212 §1 | DS-001, DS-002, DS-004 | — | — | — |
| GEO-F-17 Gaussian Splats | 211 §2 (validé 04/2026) | — | — | — | `gaussian_splat` |
| GEO-F-18 Offline-first | RFC-0003 | — | — | — | — |
| GEO-F-19 Saisie inventaire terrain | apps/GeoSylva | DS-001 | — | DOM-DEN §5 | — |
| GEO-F-20 Synchronisation différée | RFC-0003 | — | — | — | — |
| GEO-F-21 GPS + cartographie | apps/GeoSylva | DS-001, DS-002 | GIS Engine | — | — |
| GEO-F-22 État réel vs simulé | 212 §6 | — | Simulation Engine | — | HUB-002 §7 |
| GEO-F-23 Convention simulated. | 212 §6 | — | — | — | HUB-002 §7 |

---

## 8. Critères d'acceptation

La spécification GEO-001 est considérée **complète** quand :

- [x] Toutes les exigences fonctionnelles (GEO-F-01 à GEO-F-23) sont
  tracées vers une source (architecture, dataset, moteur, ontologie,
  contrat Hub).
- [x] Toutes les exigences non fonctionnelles (GEO-NF-01 à GEO-NF-12)
  sont quantifiées (plateforme, offline, sync, sécurité, GPS,
  performance, interopérabilité, coordonnées, traçabilité, modularité).
- [x] Les cas d'usage prioritaires couvrent le diagnostic sylvicole
  (Hub), l'inventaire terrain offline (mobile) et l'estimation biomasse
  (recherche).
- [x] Les garde-fous constitutionnels sont respectés (CON-001 décideur
  humain, CON-002 science, CON-003 pas de code, CON-005 traçabilité,
  CON-007 modularité, CON-010 versionnement).
- [x] Les datasets sont cités par leur identifiant (DS-001, DS-002,
  DS-003, DS-025, DS-026).
- [x] Le gradient de fidélité (livrable 212 §1) est spécifié.
- [x] Les précédents opérationnels (ONF 700 m²/pixel, SDIS 63,
  Arbonaut SaniLidar — livrable 212 §3.3) sont cités.
- [x] La couverture double (app mobile + visualisation Hub) est
  explicitée.
- [x] Les couches `geosylva.*` exposées au Hub sont listées (HUB-002).
- [x] La convention état réel vs simulé (préfixe `simulated.`) est
  spécifiée (HUB-002 §7).
- [ ] La spécification non fonctionnelle détaillée (GEO-002) est
  produite — **à créer**.
- [ ] La matrice de traçabilité détaillée (GEO-003) est produite — **à
  créer**.

---

## 9. Glossaire

| Terme | Définition |
|---|---|
| **GeoSylva** | Application forestière de l'écosystème Quintessences (app mobile Android + visualisation Hub) |
| **DBH / DHP** | Diamètre à Hauteur de Poitrine (1,30 m) — mesure dendrométrique fondamentale (ontologie DOM-DEN) |
| **Surface terrière (G)** | Somme des sections transversales des arbres à 1,30 m, exprimée en m²/ha (ontologie DOM-DEN) |
| **MNH** | Modèle Numérique de Hauteur (canopée) = MNS − MNT, directement exploitable pour la segmentation d'arbres (DS-002) |
| **Peuplement** | Unité homogène d'arbres sur une parcelle (échelle EC-PEU, ontologie livrable 303 §13) |
| **Gradient de fidélité** | Principe de représentation 3D à 3 niveaux : contexte → procédural → haute fidélité (livrable 212 §1) |
| **PCG** | Procedural Content Generation — système d'Unreal Engine pour la génération procédurale pilotée par des règles |
| **Landscape data layers** | Couches de poids peintes sur le terrain Unreal, lues par les nœuds PCG pour piloter la végétation |
| **Gaussian Splat** | Représentation 3D par splats gaussiens (reconstruction drone), streamé via Cesium ion en 3D Tiles |
| **État réel** | Données versionnées, source de vérité (mesures terrain, LiDAR) — jamais écrasé (CON-010) |
| **État simulé** | Résultat d'un scénario hypothétique (éclaircie, croissance projetée) — préfixe `simulated.` (HUB-002 §7) |
| **Offline-first** | Architecture où toutes les fonctionnalités sont disponibles sans réseau, la sync est différée (RFC-0003) |
| **AGB** | Aboveground Biomass — biomasse aérienne (Mg/ha), estimée par LiDAR, GEDI ou ESA Biomass CCI |
| **IBP** | Indice de Biodiversité Potentielle — scoring CNPF (10 critères, max 50 points) |
| **Crown-BERT** | Modèle transformer pour la classification d'essences par fusion LiDAR + hyperspectral (83-91 % OA) |
| **SegmentAnyTreeV2** | Foundation model (Point Transformer v3) pour la segmentation d'arbres zero-shot, cross-domain (F1 85 %) |
| **PyCrown** | Outil de segmentation d'arbres par maxima locaux sur MNH (Dalponte & Coomes 2016) — point de départ recommandé |

---

> Statut : *Draft — spécification fonctionnelle Phase 3 (préparation
> Phase 4). À valider par le Fondateur. Aucun code métier produit
> (CON-003).*
