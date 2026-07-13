# TECHNOLOGY_STACK — Stack technologique de GSIE

| Champ | Valeur |
|---|---|
| **Livrable** | 202 — Stack technologique (ADR) |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date de révision** | 2026-07-12 |
| **Lois fondatrices** | GSIE-CON-003, GSIE-CON-007, GSIE-CON-010 |
| **Constitutions liées** | Technique (T-1, T-2, T-8, T-10) |
| **RFC de référence** | RFC-0003 (GSIE-Net) |
| **Décision d'ouverture** | DEC-000004 |
| **Source du choix de stack** | Journal Ignis, session 1 (2026-07-12) |

---

## 1. Objet

Documenter et justifier la stack technologique de GSIE sous forme
d'Architecture Decision Records (ADR). Chaque choix de langage est
un ADR distinct, conforme au gabarit
`17_DOCUMENTATION/ADR_TEMPLATE.md`.

La Constitution Technique (T-10) impose que toute dépendance externe
soit **justifiée** et que les versions soient **épinglées** en
production. Ce document respecte cette règle : aucune dépendance
flottante (`latest`, `*`) n'est admise.

> **Note de gouvernance :** le choix de la stack a été acté dans le
> journal de bord Ignis (session 1, 2026-07-12) par le Fondateur.
> Ce document formalise ce choix sous forme d'ADR pour traçabilité
> (CON-005) et explicabilité (CON-004). Il ne contredit aucune
> décision antérieure.

---

## 2. Vue d'ensemble de la stack

```
┌─────────────────────────────────────────────────────────────┐
│  COUCHE PRÉSENTATION                                        │
│  TypeScript — React Native (mobile) · React (web)           │
│  → Interfaces utilisateur, aucun raisonnement métier        │
├─────────────────────────────────────────────────────────────┤
│  COUCHE APPLICATION (orchestration)                         │
│  Python 3.12 — FastAPI, workflows, bundles de mission       │
│  → Coordonne les moteurs, gère la synchronisation           │
├─────────────────────────────────────────────────────────────┤
│  COUCHE DOMAINE (cœur IP)                                   │
│  Rust (via pyo3) — Evidence, Knowledge, Reasoning,          │
│  Correlation, Diagnostic, Validation                        │
│  → Performance, sécurité mémoire, embarquabilité            │
├─────────────────────────────────────────────────────────────┤
│  COUCHE INFRASTRUCTURE                                      │
│  Python (accès données) · Rust (noyaux critiques)           │
│  Go (optionnel — API temps réel, GCS-Lite)                  │
│  → Stockage, réseau, intégration sources externes           │
├─────────────────────────────────────────────────────────────┤
│  COUCHE GSIE-NET (RFC-0003)                                 │
│  Python (logique de synchronisation)                        │
│  → Routage, découverte, priorités, déduplication            │
└─────────────────────────────────────────────────────────────┘
```

### Répartition synthétique

| Langage | Rôle | Couche | Justification courte |
|---|---|---|---|
| **Python** | Orchestration, accès données, GSIE-Net | Application + Infrastructure | Écosystème scientifique, lisibilité, rapidité de développement |
| **Rust** | Cœur IP (moteurs critiques), noyaux performants | Domaine | Sécurité mémoire, performance, embarquabilité future |
| **Go** | API temps réel (optionnel), GCS-Lite | Infrastructure (temps réel) | Concurrence native, faible latence, binaire statique |
| **TypeScript** | Interfaces (mobile, web, desktop) | Présentation | Typage statique, écosystème React, partage de code mobile/web |

---

## 3. ADR-0001 — Python pour l'orchestration et l'accès aux données

| Champ | Valeur |
|---|---|
| **ID** | ADR-0001 |
| **Statut** | Accepté |
| **Date** | 2026-07-12 |
| **Auteur** | Fondateur GSIE |
| **Décision liée** | DEC-000004, journal Ignis session 1 |

### Contexte

GSIE est un système scientifique dont la couche application doit
coordonner 14 moteurs, gérer des workflows complexes (bundles de
mission, synchronisation différée), et intégrer de nombreuses
sources de données externes (IGN, Météo-France, INRAE, GBIF). La
couche application n'est pas le cœur IP — elle est l'orchestrateur.

Contraintes :
- lisibilité prime sur la concision (T-3) ;
- l'écosystème scientifique Python est dominant (pandas, numpy,
  scipy, rasterio, geopandas) ;
- l'orchestration doit être modifiable rapidement sans recompilation ;
- la couche application ne contient pas de logique métier critique
  (T-4) — elle coordonne.

### Options envisagées

1. **Python** — langage dominant en science des données, écosystème
   géospatial mature (rasterio, geopandas, shapely), lisibilité
   élevée, interopérabilité native avec Rust via pyo3.
   *Avantages :* écosystème, rapidité de développement, lisibilité,
   communauté scientifique.
   *Inconvénients :* performance brute limitée (compensée par Rust
   pour le cœur IP), GIL (compensé par asyncio et multiprocessing).

2. **Go** — excellent pour les services concurrents, binaire
   statique, mais écosystème scientifique/geospatial immature.
   *Avantages :* concurrence native, performance, déploiement simple.
   *Inconvénients :* écosystème scientifique pauvre, verbosité,
   pas d'interopérabilité native avec Rust aussi mature que pyo3.

3. **Node.js/TypeScript** — bon pour l'asynchrone, mais écosystème
   scientifique inexistant, pas adapté au calcul scientifique.
   *Avantages :* un seul langage front/back.
   *Inconvénients :* inadapté au calcul scientifique, écosystème
   géospatial inexistant.

### Décision

**Python 3.12** pour la couche application (orchestration) et
l'accès aux données (couche infrastructure).

**Justification :** l'orchestration n'est pas le goulot de
performance — le cœur IP l'est, et il est en Rust (ADR-0002). Python
excelle là où Rust serait excessif : workflows, intégration de
sources hétérogènes, scripts de préparation des bundles. L'écosystème
géospatial Python (rasterio, geopandas) est un facteur décisif : les
données IGN, LiDAR et raster s'intègrent naturellement. L'interopérabilité
pyo3 permet d'appeler les moteurs Rust depuis Python sans friction.

### Conséquences

- **Positives :** développement rapide de l'orchestration,
  écosystème scientifique disponible, interopérabilité Rust native.
- **Négatives :** performance Python limitée pour les tâches CPU
  (mitigée par délégation à Rust) ; GIL (mitigé par asyncio pour
  l'I/O et multiprocessing pour le CPU).
- **Impact :** la couche application est Python ; les moteurs
  critiques exposent des bindings pyo3.

### Dépendances clés (épinglées)

> Les versions ci-dessous sont les versions **cibles** au moment de
> la rédaction. Elles seront épinglées dans les fichiers de lock
  (requirements.txt, pyproject.toml) lors de l'implémentation (Phase 4).
> Aucune version flottante en production (T-10).

| Dépendance | Version cible | Rôle | Justification |
|---|---|---|---|
| Python | 3.12.x | Runtime | Stabilité, correspond à l'environnement WSL2 validé (journal Ignis) |
| pyo3 | 0.22.x | Bridge Rust ↔ Python | Liaison native entre le cœur IP Rust et l'orchestration Python |
| FastAPI | 0.115.x | API REST | Documentation OpenAPI auto-générée, typage Pydantic, async natif |
| Pydantic | 2.x | Validation des données | Validation des contrats d'interface au runtime, cohérent avec FastAPI |
| SQLAlchemy | 2.x | ORM / accès base | Abstraction SQL, support SQLite (local) et PostgreSQL (serveur) |
| Alembic | 1.13.x | Migrations de schéma | Versioning du schéma de base (T-6) |
| asyncio | stdlib | Concurrence I/O | Évite le GIL pour les opérations réseau |
| structlog | 24.x | Journalisation structurée | Logs traçables et structurés (CON-005, T-7) |
| pytest | 8.x | Tests | Tests unitaires et d'intégration (T-5) |

> Les dépendances géospatiales (rasterio, geopandas, shapely) seront
> épinglées dans l'ADR dédié au GIS Engine (livrable 207).

---

## 4. ADR-0002 — Rust pour le cœur IP (moteurs critiques)

| Champ | Valeur |
|---|---|
| **ID** | ADR-0002 |
| **Statut** | Accepté |
| **Date** | 2026-07-12 |
| **Auteur** | Fondateur GSIE |
| **Décision liée** | DEC-000004, journal Ignis session 1 |

### Contexte

Le cœur intellectuel de GSIE (Evidence, Knowledge, Correlation,
Reasoning, Diagnostic, Validation) est la propriété IP du système.
Ces moteurs manipulent des structures de données complexes (graphes
de connaissances, matrices de corrélation, chaînes d'inférence) et
doivent garantir :

- **sécurité mémoire** — aucune corruption de donnée n'est
  acceptable pour un système scientifique (CON-002) ;
- **performance** — les corrélations et le raisonnement sur des
  grands graphes exigent une performance proche du C ;
- **embarquabilité future** — RFC-0003 prévoit des Edge Nodes et
  potentiellement des modules radio ; Rust compile vers des cibles
  embarquées (no_std, ARM) ;
- **explicabilité** — le typage fort et la sûreté du compilateur
  réduisent les bugs silencieux qui pourraient produire des
  résultats inexpliquables (CON-004).

Contraintes :
- le cœur IP doit être appelable depuis Python (orchestration) ;
- la réécriture du cœur dans 10 ans ne doit pas être nécessaire ;
- la sécurité mémoire est non négociable pour un système
  scientifique traçable.

### Options envisagées

1. **Rust** — sécurité mémoire garantie par le borrow checker,
   performance équivalente au C/C++, interopérabilité Python via
   pyo3, écosystème croissant, cibles embarquées (no_std).
   *Avantages :* sécurité mémoire sans GC, performance, pyo3 mature,
   embarquabilité, typage expressif.
   *Inconvénients :* courbe d'apprentissage, temps de compilation,
   écosystème scientifique plus jeune que Python.

2. **C++** — performance équivalente, écosystème scientifique mature
   (ForeFire, PX4 sont en C++), mais sécurité mémoire manuelle.
   *Avantages :* performance, écosystème, interopérabilité.
   *Inconvénients :* sécurité mémoire non garantie (UB, fuites,
   use-after-free), complexité du langage, dette technique
   structurelle.

3. **C** — performance maximale, mais aucune abstraction, sécurité
   mémoire manuelle, pas de système de types expressif.
   *Avantages :* simplicité, universalité.
   *Inconvénients :* pas d'abstractions, sécurité mémoire manuelle,
   inadapté à la complexité des moteurs.

4. **Zig** — langage moderne, sécurité mémoire améliorée vs C, mais
   écosystème immature et pas de binding Python mature.
   *Avantages :* modernité, simplicité.
   *Inconvénients :* écosystème immature, pas de pyo3 équivalent,
   risque de dépendance à un langage non stabilisé.

### Décision

**Rust** pour le cœur IP (moteurs critiques : Evidence, Knowledge,
Correlation, Reasoning, Diagnostic, Validation). Exposition via
**pyo3** pour appel depuis l'orchestration Python.

**Justification :** la sécurité mémoire garantie par le compilateur
est le facteur décisif. Un système scientifique dont la légitimité
repose sur la rigueur (CON-002) ne peut pas tolérer de
corruption mémoire silencieuse. Rust élimine toute une classe de
bugs (use-after-free, data races, buffer overflows) que C++ laisse
au programmeur. La performance est équivalente au C++. L'embarquabilité
future (Edge Nodes, modules radio — RFC-0003) est native (cibles
ARM, no_std). pyo3 fournit une interopérabilité Python mature et
testée.

Le C++ reste pertinent **uniquement** pour contribuer directement à
des projets existants en C++ (ForeFire, PX4 — branche Ignis) ;
il n'est pas le langage du cœur IP GSIE.

### Conséquences

- **Positives :** sécurité mémoire garantie, performance, cœur IP
  embarquable, interopérabilité Python via pyo3.
- **Négatives :** courbe d'apprentissage (le Fondateur apprend Rust
  — journal Ignis), temps de compilation, écosystème scientifique
  Rust plus jeune (compensé par Python pour l'accès aux données).
- **Impact :** les moteurs critiques sont des crates Rust exposés
  comme modules Python via pyo3. L'orchestration Python les appelle
  comme des fonctions natives.

### Dépendances clés (épinglées)

| Dépendance | Version cible | Rôle | Justification |
|---|---|---|---|
| Rust | 1.80.x | Toolchain | Édition 2021, stable |
| pyo3 | 0.22.x | Bindings Python | Liaison native Rust ↔ Python (cohérent avec ADR-0001) |
| serde | 1.0.x | Sérialisation/désérialisation | Sérialisation typée et sûre des messages inter-moteurs |
| tokio | 1.39.x | Runtime async | Concurrence pour les moteurs nécessitant de l'I/O asynchrone |
| thiserror | 1.0.x | Gestion d'erreurs | Erreurs typées et explicites (T-7) |
| tracing | 0.1.x | Instrumentation | Journalisation structurée côté Rust (CON-005) |
| rayon | 1.10.x | Parallélisme data | Parallélisation des calculs de corrélation et de raisonnement |

---

## 5. ADR-0003 — Go pour l'API temps réel (optionnel)

| Champ | Valeur |
|---|---|
| **ID** | ADR-0003 |
| **Statut** | Proposé (optionnel — activé si besoin temps réel) |
| **Date** | 2026-07-12 |
| **Auteur** | Fondateur GSIE |
| **Décision liée** | DEC-000004, journal Ignis session 1 |

### Contexte

Ignis (RFC-0004) introduit un besoin de **temps réel** : télémétrie
drone, streaming de données capteur, interface de contrôle (GCS-Lite).
L'orchestration Python (FastAPI) est adaptée au REST classique mais
moins optimale pour le streaming basse latence et la concurrence
massive (WebSockets, SSE, MAVLink).

Contraintes :
- le temps réel n'est pas un besoin du moteur GSIE principal
  (GeoSylva) — c'est un besoin de la spécialisation Ignis ;
- l'API temps réel doit coexister avec l'API REST Python ;
- le binaire doit être déployable sur des postes légers (GCS-Lite).

### Options envisagées

1. **Go** — concurrence native (goroutines), binaire statique
   (déploiement trivial), écosystème MAVSDK mature, faible latence.
   *Avantages :* concurrence, déploiement, MAVSDK, performance.
   *Inconvénients :* écosystème scientifique pauvre (mais ce n'est
   pas le rôle ici), langage supplémentaire dans la stack.

2. **Python (FastAPI + WebSockets)** — pas de langage
   supplémentaire, mais GIL et performance limitée pour le
   streaming massif.
   *Avantages :* unification de la stack.
   *Inconvénients :* GIL, performance streaming, latence.

3. **Rust (axum + tokio)** — performance maximale, pas de langage
   supplémentaire (Rust déjà dans la stack), mais courbe
   d'apprentissage pour le temps réel et écosystème MAVLink moins
   mature qu'en Go.
   *Avantages :* performance, pas de langage supplémentaire.
   *Inconvénients :* écosystème MAVLink moins mature, complexité.

### Décision

**Go** pour l'API temps réel, **uniquement si le besoin temps réel
est confirmé** (Ignis). Statut **Proposé** — non activé par
défaut pour GeoSylva.

**Justification :** Go excelle sur un créneau précis — la concurrence
massive à faible latence avec un déploiement trivial (binaire
statique). L'écosystème MAVSDK/MAVLink est plus mature en Go qu'en
Rust. Pour Ignis, la télémétrie drone et le GCS-Lite bénéficient
directement de ces propriétés. Pour GeoSylva (pas de temps réel),
FastAPI Python suffit et Go n'est pas nécessaire.

L'option Rust (axum) reste ouverte si l'écosystème MAVLink Rust
mûrit ; la décision sera réévaluée lors de l'architecture détaillée
de Ignis (livrable 210).

### Conséquences

- **Positives :** performance temps réel, déploiement simple,
  écosystème MAVLink.
- **Négatives :** langage supplémentaire (complexité de la stack),
  uniquement justifié par Ignis.
- **Impact :** Go est isolé dans la couche infrastructure (API
  temps réel). Il n'implémente aucun moteur — il transporte.

### Dépendances clés (épinglées)

| Dépendance | Version cible | Rôle | Justification |
|---|---|---|---|
| Go | 1.22.x | Runtime | Stabilité, generics disponibles |
| Fiber ou Chi | 2.x / 5.x | Router HTTP | Léger, performant, minimal |
| gorilla/websocket | 1.5.x | WebSockets | Streaming temps réel (télémétrie) |
| mavsdk-go | 1.x | SDK drone | Intégration PX4/MAVLink (Ignis) |

---

## 6. ADR-0004 — TypeScript pour les interfaces (présentation)

| Champ | Valeur |
|---|---|
| **ID** | ADR-0004 |
| **Statut** | Accepté |
| **Date** | 2026-07-12 |
| **Auteur** | Fondateur GSIE |
| **Décision liée** | DEC-000004, journal Ignis session 1 |

### Contexte

GSIE a trois interfaces principales : mobile (terrain, offline-first),
web (console de gestion), desktop (bureau d'études). Le partage de
code entre mobile et web est un facteur clé : les composants
d'interface (cartes, formulaires, visualisations) sont largement
communs.

Contraintes :
- offline-first (T-8) — l'interface mobile doit fonctionner hors-ligne ;
- typage statique — les contrats d'API doivent être vérifiés à la
  compilation (T-2) ;
- partage de code mobile/web — éviter la duplication (T-4) ;
- la couche présentation ne contient aucune logique métier.

### Options envisagées

1. **TypeScript + React Native (mobile) + React (web)** — typage
   statique, partage de code via React Native + React, écosystème
   mature, offline-first supporté (AsyncStorage, SQLite local).
   *Avantages :* typage, partage mobile/web, écosystème, communauté.
   *Inconvénients :* runtime JavaScript (performance limitée pour
   le calcul, mais la couche présentation ne calcule pas).

2. **Kotlin (Android natif) + TypeScript (web)** — performance
   native mobile, mais pas de partage de code mobile/web, deux
   langages, pas de support iOS sans Kotlin Multiplatform.
   *Avantages :* performance native Android.
   *Inconvénients :* pas de partage mobile/web, deux langages,
   complexité iOS.

3. **Flutter (Dart)** — un seul langage mobile/web/desktop, mais
   écosystème géospatial immature (cartes IGN, raster) et Dart est
   moins répandu.
   *Avantages :* un seul langage, un seul codebase.
   *Inconvénients :* écosystème géospatial immature, Dart peu
   répandu, intégration des cartes IGN complexe.

4. **Kotlin Multiplatform (KMP)** — partage de code métier entre
   mobile/web/desktop, mais support web immature et écosystème
   géospatial web limité.
   *Avantages :* partage de code, performance native.
   *Inconvénients :* support web immature, complexité.

### Décision

**TypeScript** pour la couche présentation : React Native (mobile) +
React (web). Partage de composants et de types via une bibliothèque
commune.

**Justification :** le facteur décisif est le **partage de code
mobile/web**. Les interfaces GeoSylva et Ignis partagent des
composants (cartes, arbres, diagnostics) — les dupliquer en Kotlin
+ TypeScript violerait T-4. React Native permet un partage
significatif tout en ciblant iOS et Android. Le typage TypeScript
vérifie les contrats d'API à la compilation (T-2). L'écosystème
géospatial web (MapLibre, deck.gl, Leaflet) est mature et
intégrable en React Native. L'offline-first est supporté nativement
(AsyncStorage, SQLite, WatermelonDB).

### Conséquences

- **Positives :** partage mobile/web, typage statique, écosystème
  géospatial mature, offline-first supporté.
- **Négatives :** runtime JavaScript (acceptable — la présentation
  ne calcule pas), dépendance à l'écosystème React Native.
- **Impact :** l'interface est TypeScript ; les contrats d'API sont
  générés depuis les schémas Python/Rust (OpenAPI → TypeScript).

### Dépendances clés (épinglées)

| Dépendance | Version cible | Rôle | Justification |
|---|---|---|---|
| TypeScript | 5.5.x | Langage | Typage statique, vérification des contrats |
| React Native | 0.75.x | Framework mobile | Cross-platform iOS/Android, partage avec React web |
| React | 18.x | Framework web | Écosystème mature, partage de composants |
| React Native Maps / MapLibre RN | 1.x / 6.x | Cartographie mobile | Affichage des données géospatiales (IGN, raster) |
| MapLibre GL JS | 4.x | Cartographie web | Rendu vectoriel, offline tiles |
| Zod | 3.x | Validation runtime | Validation des réponses API côté client |
| TanStack Query | 5.x | Cache/sync données | Gestion du cache offline, synchronisation |
| WatermelonDB | 1.x | Base locale mobile | SQLite offline-first, synchronisation différée |
| Expo | 51.x | Toolchain RN | Build, déploiement, OTA updates |

---

## 7. ADR-0005 — Julia gardé en veille pour la recherche

| Champ | Valeur |
|---|---|
| **ID** | ADR-0005 |
| **Statut** | Remplacé (non retenu pour la production, veille recherche) |
| **Date** | 2026-07-12 |
| **Auteur** | Fondateur GSIE |
| **Décision liée** | journal Ignis session 1 |

### Contexte

Julia est un langage scientifique performant (performance proche du
C, syntaxe proche de Python). Il aurait pu être candidat pour le
cœur IP ou les calculs scientifiques.

### Options envisagées

1. **Julia pour le cœur IP** — performance, syntaxe scientifique,
   mais écosystème immature pour la production, pas de binding
   Python aussi mature que pyo3, temps de démarrage (TTFP), pas
   d'embarquabilité.
2. **Julia en veille** — gardé pour la recherche (CIFRE/doctorat
   éventuel), non retenu pour la production.

### Décision

**Julia n'est pas retenu pour la production.** Il est gardé en veille
pour la recherche académique (CIFRE/doctorat éventuel).

**Justification :** Julia excelle en recherche mais son écosystème
production (déploiement, embarquabilité, bindings inter-langages,
stabilité des versions) n'est pas au niveau de Rust + Python pour
un système destiné à durer plusieurs décennies. Le risque de
dépendance à un écosystème non stabilisé est incompatible avec
l'objectif de longévité (CON-010).

### Conséquences

- **Positives :** stack production stable (Rust + Python), Julia
  disponible pour la recherche sans impact production.
- **Négatives :** pas de Julia en production (compensé par Rust pour
  la performance et Python pour la science).
- **Impact :** aucun — Julia reste hors du périmètre production.

---

## 8. ADR-0006 — C++ uniquement pour contribution à des projets existants

| Champ | Valeur |
|---|---|
| **ID** | ADR-0006 |
| **Statut** | Accepté (périmètre restreint) |
| **Date** | 2026-07-12 |
| **Auteur** | Fondateur GSIE |
| **Décision liée** | journal Ignis session 1 |

### Contexte

ForeFire (simulateur de feu) et PX4 (autopilote drone) sont en C++.
La branche Ignis (RFC-0004) doit interagir avec ces projets.

### Décision

**C++ uniquement si contribution directe à ForeFire ou PX4.** Le C++
n'est jamais le langage d'un moteur GSIE — il est le langage
d'interopérabilité avec des dépendances C++ existantes.

**Justification :** ForeFire et PX4 sont des projets matures en C++.
Les réécrire en Rust serait disproportionné. L'interopérabilité se
fait via des bindings (FFI) ou des processus séparés. Le cœur IP
GSIE reste en Rust.

### Conséquences

- **Positives :** pas de réécriture de ForeFire/PX4, interopérabilité
  via FFI.
- **Négatives :** C++ dans le périmètre (limité à l'interopérabilité).
- **Impact :** aucun moteur GSIE en C++ ; uniquement des adapters
  pour ForeFire/PX4 dans la branche Ignis.

---

## 8bis. ADR-0007 — Unreal Engine 5.8 + Cesium pour le jumeau numérique vivant

| Champ | Valeur |
|---|---|
| **ID** | ADR-0007 |
| **Statut** | Accepté |
| **Date** | 2026-07-12 |
| **Auteur** | Fondateur GSIE |
| **Décision liée** | DEC-000010 (adoption UE 5.8 + Cesium) |
| **Directives servies** | GSIE-DIR-0005 (jumeau numérique vivant), GSIE-DIR-0006 (moteur cognitif) |

### Contexte

GSIE-DIR-0005 fixe la vision du jumeau numérique vivant : terrain comme
interface unique, zoom progressif, moteur 3D interchangeable sans logique
métier. ADR-001 du livrable 208 pose le principe d'interchangeabilité.
Il faut maintenant choisir le moteur 3D concret.

### Options envisagées

1. **Unreal Engine 5.8** — moteur triple-A, Cesium for Unreal, Niagara,
   PCG production-ready, WebSockets natifs, Nanite/Lumen.
2. **Unity 6** — moteur solide, mais moins de précédents académiques en
   jumeau numérique incendie.
3. **Three.js / web** — léger, mais pas adapté à la qualité visuelle
   exigée (DIR-0005 « immersion comme outil de compréhension »).
4. **Godot 4** — open source, mais écosystème Cesium immature.

### Décision

**Unreal Engine 5.8 + Cesium for Unreal** comme moteur 3D du jumeau
numérique vivant.

### Justification

1. **GSIE-CON-002 (science)** : trois publications académiques récentes
   (FIRETWIN 2025, FIRE-VLM 2026, IVSR 2026) valident l'approche dans UE.
   Voir `06_RESEARCH/UNREAL_ENGINE_PRECEDENTS.md`.
2. **GSIE-CON-007 (modularité)** : UE 5.8 est un client de visualisation,
   jamais une dépendance de calcul. Le jumeau numérique tourne côté
   serveur (DIR-0006) ; UE reflète l'état, il ne le calcule pas.
3. **Cesium for Unreal** (racheté par Bentley Systems 2024) : plugin
   open source adossé à un acteur sérieux. Géoréférencement WGS84,
   ingestion LAS/LAZ/GeoTIFF, Gaussian Splats via 3D Tiles.
4. **WebSockets natifs** : aucun plugin tiers pour l'ingestion temps réel.
5. **PCG production-ready** (depuis UE 5.7) : génération procédural
   pilotée par landscape data layers — exactement le mécanisme pour
   GeoSylva (gradient de fidélité).
6. **Calendrier stable** : UE 5.8 = fin du cycle majeur UE5. UE6 stable
   en 2028. Pas de question à se poser avant 2028.

### Conséquences

- **Positives :** base technique validée par la recherche, écosystème
  mature, prototype WebSocket en cours.
- **Négatives :** UE est un moteur lourd (compilation, stockage) —
  compensé par la philosophie « lourd serveur / léger terrain » (C-06).
- **Impact :** ADR-001 du livrable 208 est réalisé. Les livrables 211
  (GCS-Cinéma Ignis) et 212 (GeoSylva-Unreal) documentent l'architecture
  détaillée. C++ entre dans le périmètre (limité au plugin UE, cohérent
  avec ADR-0006).

### Garde-fous

- RFC-0004 §8 (autonomie limitée à la navigation) — UE est un outil de
  visualisation, pas de commandement.
- GSIE-CON-001 (décideur humain) — le COS reste le décideur.
- GeoSylva-Unreal (livrable 212) en attente volontaire jusqu'à MVP Ignis.

---

## 9. Matrice de compatibilité inter-langages

```
                    Python          Rust            Go (opt.)      TypeScript     C++ (UE 5.8)
                    (orchest.)      (cœur IP)       (temps réel)   (présentation) (jumeau 3D)
  ┌──────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
  │ Python   │      —       │  pyo3 (natif)│  gRPC/REST   │  OpenAPI     │  WebSocket   │
  │ Rust     │   pyo3       │      —       │  FFI/gRPC    │  OpenAPI     │  WebSocket   │
  │ Go       │  gRPC/REST   │  FFI/gRPC    │      —       │  OpenAPI/WS  │  WebSocket   │
  │ TypeScr. │  OpenAPI     │  OpenAPI     │  OpenAPI/WS  │      —       │  N/A         │
  │ C++ (UE) │  WebSocket   │  WebSocket   │  WebSocket   │  N/A         │      —       │
  └──────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

**Lecture :**
- **Python ↔ Rust :** pyo3 (appel de fonction natif, zéro copie) ;
- **Python ↔ Go :** gRPC ou REST (processus séparé) ;
- **Go ↔ Rust :** FFI (CGo) ou gRPC (processus séparé) ;
- **TypeScript ↔ * :** OpenAPI (REST/WebSockets) — les contrats sont
  générés depuis les schémas serveur ;
- **C++ (UE 5.8) ↔ * :** WebSocket/JSON natif (module `WebSockets` +
  `Json` d'Unreal) — UE est un client de visualisation, jamais un
  calculateur (ADR-0007, DEC-000010).

---

## 10. Règles de gestion des dépendances

Conformément à T-10 (Constitution Technique) :

1. **Épinglage obligatoire** — toute dépendance a une version exacte
   dans le fichier de lock (requirements.txt, Cargo.lock, go.mod,
   package-lock.json). Pas de `latest`, `*`, `^` en production.
2. **Justification obligatoire** — toute dépendance doit répondre à
   la question : « que donne-t-elle que la stdlib ne donne pas ? »
3. **Vérification CVE** — les CVE sont vérifiées avant ajout et
   régulièrement (audit automatisé en CI).
4. **Minimalisme** — le nombre de dépendances est minimisé. Une
   dépendance qui ne sert qu'une fonction est préférée en
   implémentation interne si la fonction est triviale.
5. **Pas de dépendance flottante** — les mises à jour sont
   intentionnelles, testées et tracées.

---

## 11. Ce que ce document ne fait PAS

- Il n'implémente aucun code (Phase 2 — interdit, DEC-000004).
- Il ne liste pas toutes les dépendances transitive (à gérer par les
  fichiers de lock en Phase 4).
- Il ne choisit pas de base de données définitive (SQLite local +
  PostgreSQL serveur est l'hypothèse courante, à confirmer par ADR
  dédié).
- Il ne contredit aucun article constitutionnel.

---

## 12. Historique

| Date | Événement |
|---|---|
| 2026-07-12 | Création — 6 ADR (Python, Rust, Go, TypeScript, Julia, C++) |
| 2026-07-12 | Ajout ADR-0007 — Unreal Engine 5.8 + Cesium (DEC-000010), matrice étendue C++/UE |

---

## 13. Validation

Document en statut **Draft**. Passage en `Review` soumis à
validation du Fondateur. Les ADR individuels suivent le cycle de vie
défini dans `17_DOCUMENTATION/ADR_TEMPLATE.md`.
