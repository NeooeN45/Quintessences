# Hub Unreal — Langages et technologies autour du Centre de Commandement GSIE

| Champ | Valeur |
|---|---|
| **Livrable** | Architecture des langages et technologies du Hub Unreal et de son environnement |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation (cadrage architectural) |
| **Dernière mise à jour** | 2026-08-07 |
| **Décisions liées** | DEC-000010 (UE 5.8 + Cesium), DEC-000019 (stack Python + Rust + Go + TypeScript), DEC-000053 (Server Meshing) |
| **RFC liées** | RFC-0004 (Ignis), RFC-0035 (Server Meshing), RFC-0037 (Environmental Digital Twin Platform) |
| **Documents connexes** | `GSIE/ARCHITECTURE/TECHNOLOGY_STACK.md`, `GSIE/RESEARCH/EMERGING_LANGUAGES_STUDY.md`, `GSIE/RESEARCH/VEILLE_BEAM_OTP_SERVER_MESHING_2026-08-07.md`, `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md`, `GSIE/ARCHITECTURE/SERVER_MESHING_TARGET.md` |

---

## 1. Résumé exécutif

Le **Hub Unreal** est la **couche de visualisation, d'interaction, de simulation 3D et de commandement** du jumeau numérique fédéré GSIE. Il ne doit jamais devenir le backend, le moteur scientifique ou la source de vérité du système.

Ce document classe les langages et technologies autour du Hub en quatre catégories :

| Catégorie | Langages | Signification |
|---|---|---|
| **A — Fondamentaux** | C++, Rust, Python, Go (différé), Kotlin, TypeScript, SQL/PostGIS | Décisions actives ou incontournables pour le système. |
| **B — Stratégiques** | Elixir, Gleam, Julia, WebAssembly | Intéressants pour des composants indépendants, sous conditions d'activation. |
| **C — Accélérateurs spécialisés** | Futhark, Taichi, Mojo | Réservés à des goulots d'étranglement mesurés (GPU, simulation). |
| **D — Recherche et validation** | P, Dafny, Pony, Unison, MoonBit, Zig | Veille, preuve de concept ou vérification formelle uniquement. |

**Principe fondamental :** un nouveau langage n'est accepté que s'il apporte une capacité difficilement réalisable avec les technologies existantes, ou s'il améliore fortement la sécurité, la performance, la distribution, la science ou la vérification. Sinon, il n'est pas adopté.

---

## 2. Rôle architectural du Hub Unreal

Le Hub Unreal est :

- la **représentation 3D interactive** de l'état GSIE ;
- un **client** des projections métier (GeoSylva, Ignis, Hydro, Flora, Artemis, QGISIA) ;
- un **environnement de simulation et de comparaison** de scénarios ;
- un **poste de commandement** où les actions physiques passent par `ActionRequest` et validation humaine.

Le Hub Unreal **n'est pas** :

- la source de vérité de l'état environnemental ;
- un moteur de calcul scientifique autoritatif ;
- un orchestrateur distribué global ;
- un système de persistance principal ;
- un monolithe contenant toutes les responsabilités de Quintessences.

```text
                        QUINTESSENCES
                              │
                              ▼
                       GSIE SERVER PLATFORM
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼
  GSIE Runtime Fabric                      GSIE Data Fabric
 Python/FastAPI/Rust                 PostgreSQL / PostGIS / Redis
          │
          ▼
   GSIE Native Core
        Rust
          │
          ├───────────────┬────────────────────┐
          │               │                    │
          ▼               ▼                    ▼
   Science Engine      AI Engine          Simulation Engine
     Python/Julia       Python/Rust         Python/C++/Rust
          │               │                    │
          └───────────────┴────────────────────┘
                          │
                          ▼
                  GSIE Unreal Gateway
                          │
                          ▼
                Unreal Engine 5.8 / C++
                          │
                          ▼
                    HUB QUINTESSENCES
```

Ce schéma est une **vue conceptuelle** : les moteurs scientifiques peuvent rester en Python ou Rust ; l'ajout de Julia, Futhark ou Taichi n'est justifié que par des benchmarks mesurés.

---

## 3. Tableau synthétique des langages

| Langage | Rôle principal | Maturité | Performance | Sécurité | Concurrence | Distribution | Sci/GPU | Interop | Maintenabilité | Pertinence GSIE |
|---|---|---|---|---|---|---|---|---|---|---|
| **C++** | Hub Unreal, plugins, Niagara, Cesium | ✅ Très haute | ✅ Haute | ⚠️ Manualle | ⚠️ Complexe | ❌ Non native | ⚠️ Possible via libs | ✅ UE native | ⚠️ Exige expertise | ✅ Fondamentale |
| **Go** | Services temps réel, GCS-Lite, streaming (différé) | ✅ Mature | ✅ Haute | ✅ Mémoire safe | ✅ Goroutines | ⚠️ Via stdlib | ❌ | ✅ gRPC / REST | ✅ Mature | 🟡 Stratégique (différé) |
| **Rust** | Gateway, parsing, géospatial, services edge, cœur IP | ✅ Mature | ✅ Haute | ✅ Mémoire safe | ✅ async/tokio | ⚠️ Via crates | ⚠️ Possible | ✅ FFI / gRPC / pyo3 | ⚠️ Courbe d'apprentissage | ✅ Fondamentale |
| **Python** | API, orchestration, IA, moteurs scientifiques | ✅ Très haute | ⚠️ Limité par GIL | ⚠️ Runtime | ✅ async | ❌ | ⚠️ NumPy/CuPy | ✅ pyo3 / gRPC | ✅ Excellente | ✅ Fondamentale |
| **Kotlin** | GeoSylva Android, applications terrain | ✅ Mature | ✅ JVM/Native | ✅ JVM | ✅ Coroutines | ❌ | ❌ | ✅ API / SDK | ✅ Mature | ✅ Fondamentale |
| **Elixir** | Temps réel, connexions massives, messaging | ✅ Mature (BEAM) | ⚠️ Latence OK, pas HPC | ✅ Isolation panne | ✅ Green processes | ✅ OTP | ❌ | ⚠️ Via ports/NIF | ✅ Mature | 🟡 Stratégique |
| **Gleam** | BEAM + types statiques | ✅ 1.x | ⚠️ Similaire Elixir | ✅ Type-safe | ✅ BEAM | ✅ BEAM | ❌ | ⚠️ Via BEAM | ⚠️ Écosystème jeune | 🔴 Ignore (doublon) |
| **Julia** | Calcul scientifique, simulation, optimisation | ✅ Mature | ✅ Proche C/Fortran | ⚠️ Runtime | ⚠️ Possible | ⚠️ Possible | ✅ SciML, GPU | ⚠️ Via Julia API | ⚠️ Écosystème scientifique | 🟡 Stratégique |
| **Futhark** | Calcul data-parallel GPU (rasters, grilles) | ✅ Stable | ✅ GPU | ✅ Type-safe | ✅ GPU | ❌ | ✅ GPU massif | ⚠️ FFI / Python | ⚠️ Niche | 🔵 Accélérateur |
| **Taichi** | Simulation physique, particules, fluides | ✅ Mature | ✅ GPU | ⚠️ Runtime | ✅ GPU | ❌ | ✅ GPU | ⚠️ Python/C++ | ⚠️ Niche | 🔵 Accélérateur |
| **Mojo** | Kernels CPU/GPU, accélération IA | ⚠️ 1.0 fin 2026 | ✅ Prometteur | ⚠️ Non établi | ⚠️ Possible | ❌ | ✅ AI/ML | ⚠️ Python interop | ⚠️ Très jeune | 🔵 Accélérateur |
| **P** | Vérification formelle de protocoles distribués | ✅ MSR | N/A | N/A | N/A | ✅ Modèles | N/A | N/A | ⚠️ Spécialisé | 🟠 R&D |
| **Dafny** | Preuve d'invariants, logique critique | ✅ MSR | N/A | N/A | N/A | N/A | N/A | ⚠️ Génère C#/Java/Go/Python | ⚠️ Spécialisé | 🟠 R&D |
| **Pony** | Acteurs, concurrence sans data races | ⚠️ Niche | ✅ Haute | ✅ Capabilities | ✅ Acteurs | ⚠️ Possible | ❌ | ⚠️ FFI | ⚠️ Écosystème faible | 🔴 R&D/doublon |
| **Unison** | Calcul distribué content-addressed | ⚠️ Expérimental | ⚠️ Inconnu | ⚠️ Inconnu | ⚠️ Possible | ✅ Distribué | ❌ | ⚠️ Limité | ⚠️ Très jeune | 🔴 R&D |
| **MoonBit** | WebAssembly, plugins, edge | ⚠️ Jeune | ⚠️ Dépend Wasm | ✅ Type-safe | ⚠️ Wasm | ⚠️ Wasm | ❌ | ✅ Wasm | ⚠️ Écosystème naissant | 🟠 R&D |
| **Zig** | Systèmes, interop C, cross-compilation | ⚠️ 1.0 en 2027 | ✅ Haute | ⚠️ Manualle | ⚠️ Manuelle | ❌ | ❌ | ✅ C | ⚠️ Jeune | 🔴 R&D/doublon |
| **WebAssembly** | Sandboxing, plugins, extensions contrôlées | ✅ Standard | ⚠️ Overhead | ✅ Mémoire isolée | ⚠️ Pas natif | ❌ | ⚠️ Wasm-GPU naissant | ✅ Multi-langages | ✅ Standard | 🟡 Stratégique |

---

## 4. Langages fondamentaux (catégorie A)

### 4.1 C++ — cœur natif du Hub Unreal

**Responsabilités :**

- intégration profonde Unreal Engine 5.8 ;
- Actors, Components, Subsystems, World Partition, Mass Entity si pertinent ;
- réseau Unreal, réplication, streaming ;
- chargement des données et interfaces de service ;
- plugins Unreal et extensions de moteur ;
- visualisation massive de données (Cesium, Niagara, LiDAR).

**Ce que C++ ne doit PAS absorber :**

- moteur IA complet ;
- infrastructure cloud / Server Meshing ;
- logique métier globale ;
- calcul scientifique expérimental ;
- stockage principal ;
- orchestration distribuée globale.

**Justification :** C++ est imposé par Unreal Engine. Son rôle est strictement limité au moteur 3D et à ses performances critiques. Toute logique métier qui n'est pas liée au rendu ou à l'interaction doit être externalisée.

### 4.2 Blueprints — couche de présentation

**Responsabilités :**

- UI, widgets, interactions opérateur ;
- prototypage rapide et scénarios de formation ;
- animation, événements visuels, logique de présentation ;
- configuration de comportements et outils opérateurs.

**Ce que les Blueprints ne doivent PAS devenir :**

- backend du système ;
- moteur de calcul scientifique ;
- persistance principale ;
- moteur du Server Meshing ;
- logique métier difficile à maintenir.

**Règle simple :**

```text
C++     = infrastructure et logique critique du moteur 3D
Blueprint = orchestration visuelle et expérience utilisateur
```

### 4.3 Rust — Native Core et passerelle haute performance

**Responsabilités autour du Hub :**

- parsing et transformation de données géospatiales ;
- protocoles, compression, sérialisation (MessagePack, FlatBuffers) ;
- streaming, services edge, bibliothèques natives ;
- passerelles réseau, traitement massif, sécurité mémoire ;
- GSIE Unreal Gateway (option privilégiée) ;
- cœur IP (Evidence, Knowledge, Reasoning, etc.).

**Modes d'intégration avec Unreal :**

```text
Unreal C++         Unreal              Unreal
   │                  │                   │
   ├── FFI ───────► Rust Library          │
   │                                    gRPC / QUIC
   │                  │                   │
   ▼                  ▼                   ▼
 Rust Library     Rust Service       Rust Gateway
```

**Quand FFI, quand service séparé ?**

- **FFI** : bibliothèque purement locale, appel fréquent, faible latence, pas d'état partagé complexe (ex. parser binaire, compression).
- **Service séparé** : état réseau, concurrence, reprise sur panne, sécurité, déploiement indépendant (ex. Gateway, edge runtime).
- **WebSocket/gRPC** : flux temps réel entre Unreal et le backend GSIE.

### 4.4 Python — IA, orchestration et moteurs scientifiques

**Responsabilités :**

- API GSIE (FastAPI), orchestration des moteurs ;
- Machine Learning, Deep Learning, PyTorch, JAX, transformers ;
- pipelines de données, prototypage scientifique ;
- intégration des sources externes (IGN, Météo-France, GBIF) ;
- moteurs Python (GIS, Climate, Botanical, Pedology, Forest Dynamics, Simulation).

**Relation avec le Hub :** le Hub consomme les résultats Python via l'API GSIE. Les modèles IA peuvent être servis à distance, exportés en ONNX ou exécutés via TensorRT/NVIDIA NIM. Le Hub ne les exécute pas localement.

### 4.5 Kotlin — applications terrain

**Responsabilités :**

- GeoSylva Android, éventuellement d'autres applications GSIE ;
- communication avec GSIE API via REST/WebSocket ;
- mode offline-first et synchronisation.

**Règle :** GeoSylva ne se connecte jamais directement au processus Unreal. Le jumeau GSIE est l'intermédiaire.

### 4.6 SQL / PostGIS — persistance géospatiale

**Responsabilités :**

- source de vérité canonique pour l'état environnemental ;
- bitemporalité, historique, provenance (métamodèle v6.2) ;
- requêtes géospatiales, tuiles, rasters indexes.

---

## 5. Langages stratégiques (catégorie B)

### 5.0 Go — services temps réel différés

**Rôle potentiel :** API temps réel, GCS-Lite, streaming de télémétrie, binaires statiques déployables sur des nœuds edge.

**Condition d'activation :** FastAPI/WebSocket atteint ses limites mesurées (> 100 ms de latence ou < 10 000 messages/s selon DEC-000019, Vague 6). Go est alors un candidat naturel avant d'envisager Elixir.

**Justification :** concurrence native, binaire statique, écosystème réseau mature. L'écosystème scientifique/geospatial reste limité : Go ne remplace pas Python pour les moteurs, seulement pour la couche temps réel.

### 5.1 Elixir / Erlang / Gleam — GSIE Runtime Fabric

**Rôle potentiel :** gestion de milliers d'événements, télémétrie, sessions, messaging, supervision, acteurs, Server Meshing.

**Analyse par langage :**

| Langage | Verdict existant | Justification |
|---|---|---|
| **Erlang** | 🟡 Surveiller (OTP bas niveau) | BEAM éprouvé, mais écosystème web/scientifique limité. |
| **Elixir** | 🟡 Surveiller | Phoenix, LiveView, OTP, plus accessible qu'Erlang pour les équipes. |
| **Gleam** | 🔴 Ignorer | Même cas d'usage qu'Elixir sur BEAM, mais écosystème plus jeune (DEC-000019, EMERGING_LANGUAGES_STUDY). |

**Condition d'activation d'Elixir :** Go ou Python ne suffit plus pour le nombre de connexions simultanées (ex. milliers de drones/capteurs) et la latence moyenne dépasse les seuils fixés.

### 5.2 Julia — moteur scientifique

**Rôle potentiel :** propagation incendie, hydrologie, météorologie, écologie, optimisation, assimilation de données, modèles climatiques.

**Condition d'activation :** Python devient un goulot mesurable sur les moteurs Forest Dynamics, ForeFire ou Simulation. Le benchmark cible est explicité dans EMERGING_LANGUAGES_STUDY : Python < 10 fps sur simulation.

**Flux type :**

```text
Julia Simulation
       │
       ▼
GSIE Science API
       │
       ▼
GSIE State Fabric
       │
       ▼
Unreal Hub
       │
       ▼
Visualisation 3D
```

### 5.3 WebAssembly — sandboxing et plugins

**Rôle potentiel :** plugins téléchargeables, règles utilisateur, traitement edge, extensions partenaires.

**Runtime à imposer :**

- permissions ;
- mémoire, CPU, durée maximale ;
- APIs accessibles ;
- accès réseau ;
- accès données.

**Architecture :**

```text
Plugin GSIE
    │
    ▼
WebAssembly Component
    │
    ├── Rust
    ├── MoonBit
    └── C/C++
```

WebAssembly est structurant pour la sécurité des extensions, pas comme langage principal.

---

## 6. Accélérateurs spécialisés (catégorie C)

### 6.1 Futhark — calcul GPU data-parallel

**Rôle potentiel :** tableaux massifs, rasters, NDVI, modèles sur grille, cartes de risque, Monte-Carlo.

**Exemple GSIE :**

```text
MNT + Vent + Humidité + Combustible + Pente
                  │
                  ▼
               Futhark
                  │
                  ▼
                 GPU
                  │
                  ▼
       Raster dynamique de risque
                  │
                  ▼
                IGNIS
                  │
                  ▼
             Unreal Engine
```

**Condition d'activation :** un calcul raster régulier devient un goulot d'étranglement mesurable ; le prototype Python/NumPy est insuffisant.

### 6.2 Taichi — simulation physique

**Rôle potentiel :** fumée, particules, fluides, champs vectoriels, voxelisation, structures spatiales, calculs LiDAR.

**Exemple pour Ignis :**

```text
Fire Model
   │
   ├── température
   ├── vent
   ├── fumée
   ├── particules
   └── combustible
           │
           ▼
         Taichi
           │
           ▼
           GPU
           │
           ▼
       Unreal Hub
```

**Frontière impérative :** un bel effet Niagara n'est pas un modèle scientifique. Taichi peut produire une simulation physique validée ; Niagara reste un rendu visuel piloté par le jumeau.

### 6.3 Mojo — accélération IA et GPU

**Rôle potentiel :** kernels CPU/GPU, SIMD, optimisation de pipelines Python, IA.

**Verdict :** expérimental/stratégique. La maturité et l'écosystème ne justifient pas une dépendance critique en 2026.

**Architecture :**

```text
Python Prototype
      │
      ▼
Mojo Optimized Kernel
      │
      ▼
CPU / GPU
```

---

## 7. Recherche et validation (catégorie D)

### 7.1 P — vérification de protocoles distribués

**Rôle :** vérification par machines à états du protocole de transfert d'autorité du Server Meshing.

**Propriétés à garantir :**

```text
Propriété : il ne doit jamais exister
Owner = Cell_A AND Owner = Cell_B

Propriété : autant que possible éviter
Owner = NONE
```

**Condition d'activation :** le Server Meshing est spécifié et comporte un transfert d'autorité entre nœuds distribués. P permet de rechercher des contre-exemples avant implémentation.

### 7.2 Dafny — vérification formelle d'invariants

**Rôle :** preuve de propriétés (pré/post-conditions, invariants) sur les algorithmes critiques.

**Condition d'activation :** des bugs logiques récurrents apparaissent dans un moteur critique (Reasoning, Validation, Server Meshing) malgré Rust. Le code Dafny peut être compilé vers C#, Java, Go ou Python.

### 7.3 Pony — modèle acteur expérimental

**Rôle :** acteurs, concurrence sans data races, services temps réel.

**Verdict :** doublon probable avec BEAM (Elixir) et Rust. Aucun avantage suffisant pour justifier un langage supplémentaire.

### 7.4 Unison — calcul distribué expérimental

**Rôle :** content-addressed code, déploiement, fonctions distribuées, code mobile, reproductibilité.

**Verdict :** R&D uniquement. Pas de cas GSIE immédiat.

### 7.5 MoonBit — laboratoire WebAssembly

**Rôle :** plugins WebAssembly, petits modules, extensions GSIE.

**Verdict :** à surveiller, mais ne pas en faire une dépendance fondamentale tant que la maturité n'est pas établie.

### 7.6 Zig — bas niveau et interopérabilité

**Rôle :** intégration C, bibliothèques natives, embedded, cross-compilation.

**Verdict :** non retenu. Rust couvre déjà ces cas avec sécurité mémoire. Zig n'apporte pas d'avantage suffisant pour compenser un langage supplémentaire.

---

## 8. Classification finale

### 8.1 Catégorie A — Fondamentaux

- **C++** : Hub Unreal, plugins, rendu.
- **Rust** : Gateway, cœur IP, services edge, parsing, géospatial.
- **Python** : API, orchestration, moteurs scientifiques, IA.
- **Go** : services temps réel si FastAPI/WebSocket atteint ses limites (différé).
- **Kotlin** : GeoSylva Android.
- **TypeScript** : interfaces web et administration, en dehors du Hub Unreal.
- **PostGIS/SQL** : source de vérité.

### 8.2 Catégorie B — Stratégiques

- **Elixir** : temps réel distribué si Go/Python ne scale pas.
- **Julia** : moteurs scientifiques si Python devient goulot.
- **WebAssembly** : plugins et extensions sécurisés.

### 8.3 Catégorie C — Accélérateurs

- **Futhark** : GPU data-parallel sur rasters.
- **Taichi** : simulation physique sur GPU.
- **Mojo** : kernels IA/GPU (expérimental).

### 8.4 Catégorie D — Recherche et validation

- **P, Dafny** : vérification formelle.
- **Pony, Unison, MoonBit, Zig** : veille, non adoptés.

---

## 9. Frontières entre les composants

```text
Unreal          → représentation 3D et interaction
BEAM (Elixir)   → orchestration temps réel si activé
Rust            → infrastructure native, gateway, cœur IP
Python          → API, IA, orchestration
Julia           → science si benchmark justifie
Futhark/Taichi  → accélération GPU si benchmark justifie
PostGIS         → géospatial persistant
P/Dafny         → validation formelle
```

Aucune responsabilité ne doit migrer d'une couche vers une autre sans justification technique mesurable.

---

## 10. Communication entre les langages

### 10.1 Mécanismes comparés

| Mécanisme | Latence | Débit | Usage GSIE |
|---|---|---|---|
| **gRPC** | Faible | Élevé | Services internes, moteurs ↔ API. |
| **Protocol Buffers** | — | — | Sérialisation structurée, stable. |
| **FlatBuffers** | Très faible | Très élevé | Flux temps réel, accès zéro-copy. |
| **Cap'n Proto** | Très faible | Très élevé | Inter-process, services temps réel. |
| **WebSocket** | Faible | Moyen | Hub Unreal ↔ GSIE Gateway. |
| **QUIC** | Faible | Élevé | Futur streaming multi-flux. |
| **REST/JSON** | Moyen | Faible | API publique, intégrations. |
| **MessagePack** | Faible | Moyen | Alternative légère à JSON. |
| **NATS** | Faible | Élevé | Pub/sub temps réel, télémétrie. |
| **MQTT** | Faible | Faible | IoT, capteurs, Meshtastic/LoRa. |
| **Kafka/Redpanda** | Moyen | Très élevé | Journal d'événements, analytics. |
| **FFI** | Très faible | Haut | Rust ↔ C++ dans le même processus. |
| **Shared memory** | Très faible | Très haut | Même machine, gros volumes. |
| **WebAssembly Component** | Faible | Moyen | Plugins sandboxés. |

### 10.2 Choix recommandés

| Canal | Protocole | Justification |
|---|---|---|
| **Unreal ↔ GSIE Gateway** | WebSocket + MessagePack (puis gRPC/QUIC) | Latence faible, JSON déjà utilisé, migration possible. |
| **Unreal ↔ Rust** | FFI (local) ou gRPC (service) | Selon la nature du composant. |
| **GSIE Server ↔ Julia** | gRPC + Protocol Buffers | Appels de moteur scientifique. |
| **GSIE Server ↔ Python** | Python natif (même processus) ou gRPC | Moteurs dans FastAPI ou services séparés. |
| **Drones ↔ GSIE** | MAVLink / MQTT / UDP | Protocoles du domaine UAV. |
| **GeoSylva ↔ GSIE** | HTTPS REST + WebSocket | Offline-first, synchronisation. |
| **Services ↔ Services** | gRPC / NATS | Communication interne faible latence. |
| **Télémétrie temps réel** | NATS / MQTT | Faible latence, pub/sub. |
| **Gros rasters / LiDAR / 3D** | HTTP + tuiles / fichiers objets | Streaming spatial, cache. |

---

## 11. GSIE Unreal Gateway

Le **GSIE Unreal Gateway** isole Unreal du reste de l'infrastructure.

**Responsabilités :**

- authentification et connexion ;
- subscriptions et événements ;
- streaming et delta updates ;
- réplication sélective et QoS ;
- sérialisation, cache, reconnect ;
- compression, monitoring ;
- conversion données serveur → Unreal.

**Implémentation recommandée :** principalement **Rust** (performance, sécurité mémoire, concurrence) avec une interface C++ dans Unreal via gRPC/WebSocket. L'implémentation Elixir est une alternative si le nombre de connexions simultanées justifie BEAM.

---

## 12. Intégration au Server Meshing

Le Server Meshing (RFC-0035, `SERVER_MESHING_TARGET.md`) organise le territoire en cellules avec transfert d'autorité.

**Hiérarchie :**

```text
France
 │
 ├── Région
 │    │
 │    ├── Département
 │    │      │
 │    │      ├── Massif
 │    │      │     │
 │    │      │     └── Cellule
```

**Langages par niveau :**

| Niveau | Langage | Responsabilité |
|---|---|---|
| **Orchestrateur de mesh** | Python (prototypage) / Rust ou Elixir (production) | Découpage, allocation, supervision. |
| **Serveur de zone** | Rust / Python | Autorité spatiale, logique métier, persistence via `IPersistenceLayer`. |
| **Serveur spécialisé** | Python / Rust / Julia | Moteurs scientifiques (Simulation, Learning, Drones). |
| **Graphe d'autorité** | PostGIS | Source de vérité du propriétaire de chaque entité. |
| **Client de rendu** | C++ (Unreal) | Visualisation, interaction. |

**Protocole de transfert d'autorité :** à modéliser en **P** avant implémentation, puis à vérifier avec des tests de mutation et des scénarios de partition réseau.

---

## 13. Principe essentiel : GSIE State ≠ Unreal World

Le monde Unreal est une **projection interactive** de l'état GSIE. L'état réel et persistant existe indépendamment du moteur Unreal.

```text
Unreal crash
     │
     ▼
GSIE continue

Unreal redémarre
     │
     ▼
State Fabric
     │
     ▼
Reconstruction du monde
```

Cette exigence est fondamentale : aucune donnée métier ne doit être perdue si Unreal plante.

---

## 14. Exemples de flux de données

### 14.1 Détection incendie par drone

```text
Drone IGNIS
     │
 télémétrie
     ▼
Runtime Fabric
     │
     ├── localisation
     ├── température
     └── image thermique
            │
            ▼
        AI Engine
            │
 détection point chaud
            ▼
       State Fabric
            │
     nouvel événement
            ▼
      Unreal Gateway
            │
            ▼
       Hub Unreal
            │
            ▼
   🔥 apparition événement incendie
```

### 14.2 Prévision de propagation

```text
Aeris / Météo-France
   │
prévision vent
   │
   ▼
Julia / Futhark
   │
propagation
   ▼
GSIE State
   │
   ▼
Unreal
   │
   ▼
front de feu prévisionnel 3D
```

---

## 15. Architecture finale recommandée

```text
                        QUINTESSENCES
                              │
                    GSIE SERVER PLATFORM
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
     Runtime Fabric      Data Fabric       Compute Fabric
  Python/FastAPI/        PostgreSQL/       Python/Rust
  Rust/Elixir*           PostGIS/Redis     Julia/Futhark/Taichi*
           │                                     │
           │                           ┌─────────┼─────────┐
           │                           │         │         │
           │                          Julia     Futhark   Taichi
           │                           │         │         │
           │                           └─────────┼─────────┘
           │                                     │
           └─────────────────┬───────────────────┘
                             ▼
                      Rust Native Core
                             │
                             ▼
                   GSIE Unreal Gateway
                             │
                             ▼
                     UNREAL ENGINE 5.8
                             │
                   C++ + Blueprints
                             │
                             ▼
                       HUB GSIE 3D

Parallèlement :

VALIDATION
├── P
└── Dafny

PLUGIN / SANDBOX
└── WebAssembly
    ├── Rust
    └── MoonBit (veille)

RESEARCH LAB
├── Pony
├── Unison
├── Mojo
└── Zig
```

*Composants marqués d'une étoile : activés uniquement si les conditions d'activation sont remplies.

---

## 16. Stratégie de migration progressive

| Phase | Objectif | Langages concernés |
|---|---|---|
| **P0** | Tranche verticale Ignis, Unreal + Cesium + WebSocket | C++, Blueprints, Python, Rust |
| **P1** | Gateway Rust, fédération des projections | Rust, Python, C++ |
| **P2** | Simulation multi-domaines, tests de performance | Python, Rust, Julia* |
| **P3** | Gros volumes, rasters, simulation GPU | Futhark*, Taichi* |
| **P4** | Temps réel massif, Server Meshing | Elixir*, Rust, P |
| **P5** | Plugins partenaires, extensions | WebAssembly, Rust |

---

## 17. Risques de complexité

| Risque | Mitigation |
|---|---|
| Polyglossie incontrôlée | Stack de base limitée à C++/Rust/Python/Kotlin + PostGIS. Les autres langages passent par un POC validé. |
| FFI C++ ↔ Rust fragile | Tests de mutation, interfaces étroites, CI multi-plateforme. |
| Langages expérimentaux en production | Mojo, Pony, Unison, MoonBit interdits en production sans décision Fondateur. |
| Effets visuels confondus avec modèles scientifiques | Séparation `state_kind` (réel, simulé, proposé) et traçabilité de la source. |
| Hub monolithique | World Partition, Data Layers, plugins Unreal ; logique métier hors d'Unreal. |
| Latence Gateway sous-estimée | Benchmark p95/p99, backpressure, indicateur de fraîcheur. |

---

## 18. Recommandations définitives

1. **Conserver la stack fondamentale** : C++ (Unreal), Rust (cœur/gateway), Python (API/orchestration/science), Kotlin (Android), PostGIS (vérité).
2. **Ne pas adopter Gleam, Pony, Unison, Zig, MoonBit, Mojo en production** sans nouvelle preuve de valeur.
3. **Surveiller Julia, Elixir, WebAssembly** avec des critères d'activation mesurables.
4. **Réserver Futhark, Taichi, Mojo** à des goulots d'étranglement GPU identifiés par benchmark.
5. **Utiliser P et Dafny** pour valider le protocole de transfert d'autorité du Server Meshing.
6. **Toujours externaliser la logique métier du Hub** : Unreal est une projection, jamais la source de vérité.
7. **Toute action dans le Hub passe par `ActionRequest` + validation humaine**, conformément à RFC-0037.

---

## 19. Statut

Ce document est un **Draft** de cadrage architectural. Il ne modifie pas les décisions validées (DEC-000010, DEC-000019, DEC-000053) et n'autorise aucune adoption de nouvelle technologie sans un benchmark, un POC et une décision traçée.
