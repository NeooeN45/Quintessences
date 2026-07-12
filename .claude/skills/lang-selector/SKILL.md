---
name: lang-selector
description: >
  Choisit le meilleur langage de programmation pour une tâche donnée en
  tenant compte de l'écosystème du projet, de la performance, de la
  maintenabilité et de l'interopérabilité avec les autres langages déjà
  utilisés. Trigger : "quel langage", "langage pour", "choix technologique",
  "Rust vs Python", "Go vs", "stack technique", "dois-je utiliser",
  "réécrire en", "optimiser avec".
trigger: always_on
---

# Lang-Selector — Sélection de langage par tâche

## Principe

Aucun langage n'est bon pour tout. La bonne question n'est pas
« quel est le meilleur langage ? » mais « quel est le meilleur langage
**pour cette tâche**, dans **ce projet**, avec **ces contraintes ? ».

Cette skill aide à choisir en tenant compte de :
1. **La nature de la tâche** (calcul, IO, UI, orchestration, embarqué)
2. **Les langages déjà présents** dans le projet (interopérabilité)
3. **Le contexte de performance** (prototype vs production vs embarqué)
4. **La courbe d'apprentissage** de l'utilisateur
5. **La maturité de l'écosystème** pour le domaine

## Matrice de décision

### Par nature de tâche

| Tâche | Langage primaire | Alternative | À éviter |
|---|---|---|---|
| Prototypage / exploration | **Python** | Julia | Rust, C++ |
| Calcul scientifique / math | **Python** (numpy/scipy) | Julia, Rust (pyo3) | Go, JS |
| Calcul haute perf (hot path) | **Rust** (via pyo3) | C++ | Python pur |
| Filtrage / assimilation données | **Python** → **Rust** (pyo3) | Julia | Go |
| Orchestration de processus | **Python** (subprocess) | Go (goroutines) | Rust (trop verbeux) |
| API HTTP / WebSocket | **Python** (FastAPI) | Go (net/http), TS (Node) | C++, Rust (si simple) |
| API temps réel critique | **Go** (tokio-equivalent) | Rust (axum/tokio) | Python (GIL) |
| Frontend / UI web | **TypeScript** (React/Next) | — | Python, Rust |
| Cartographie / géospatial | **Python** (GeoPandas/shapely) | TS (MapLibre/deck.gl) | Rust (écosystème jeune) |
| SIG lourd / raster | **Python** (rasterio/GDAL) | C++ (GDAL natif) | Go |
| Drone / MAVLink / mission | **Python** (MAVSDK) | Rust (mavlink crate) | C++ (sauf PX4 custom) |
| Embarqué edge (Jetson) | **Rust** (no_std possible) | C++ (CUDA natif) | Python (GC jitter) |
| Inférence ML / NN | **Python** (PyTorch/ONNX) | Rust (candle/ort) | Go (écosystème faible) |
| Scripts système / CI | **Bash** (simple) | Python (complexe) | Rust (overkill) |
| CLI tools | **Rust** (clap, single binary) | Go (cobra) | Python (si perf critique) |
| Parsing / sérialisation | **Rust** (serde) | Python (pydantic) | Go (verbose) |
| Concurrence massive | **Go** (goroutines) | Rust (tokio) | Python (GIL) |
| Temps réel dur / safety-critical | **Rust** (pas de GC) | C++ (RT extensions) | Python, Go (GC) |
| Base de données / stockage | **Rust** (sled, rocksdb bindings) | Go (badger/bbolt) | Python (perf) |
| Documentation / notebooks | **Python** (Jupyter) | Julia (Pluto) | Tout le reste |

### Par contrainte de performance

| Contrainte | Langage recommandé |
|---|---|
| < 1ms latency | Rust, C++ |
| 1-10ms latency | Rust, Go, C++ |
| 10-100ms latency | Python, Go, Rust |
| Batch / asynchrone | Python, Go |
| Startup instant (< 10ms) | Go, Rust (binaire natif) |
| Startup lent acceptable | Python, Julia (JIT warmup) |

### Par contrainte d'interopérabilité

| Langage existant | Comment appeler |
|---|---|
| Python ← Rust | **pyo3/maturin** (extension native) |
| Python ← C++ | **pybind11** ou **ctypes** |
| Python ← Go | **cgo + shared lib** ou gRPC |
| Rust ← Python | **PyO3 reverse** ou subprocess |
| TypeScript ← Rust | **WASM** (wasm-bindgen) ou napi-rs |
| TypeScript ← Python | **HTTP API** (FastAPI) |
| Go ← Rust | **FFI (cgo)** ou gRPC |
| Go ← Python | **gRPC** ou subprocess |

## Règles de compatibilité (anti-silos)

1. **Un langage ne doit pas être ajouté au projet s'il ne peut pas
   communiquer avec les autres.** Vérifier l'interopérabilité avant.
2. **Préférer le langage déjà présent** si la différence de performance
   est < 2x. La fragmentation technologique coûte plus cher que le gain.
3. **Le pattern "Python shell + X core"** est privilégié pour les
   projets scientifiques : Python pour l'orchestration, langage système
   pour le hot path.
4. **Une interface propre (API/contrat) rend le langage interchangeable.**
   Si le module a une interface documentée, on peut changer d'avis plus
   tard sans tout casser.
5. **Maximum 3-4 langages par projet.** Au-delà, la maintenance devient
   un cauchemar. Chaque langage doit justifier sa présence par un gain
   que les autres ne peuvent pas fournir.

## Procédure de recommandation

Quand l'utilisateur demande "quel langage pour X" :

1. **Identifier la tâche** précise (pas juste "faire une API" mais
   "API WebSocket temps réel qui diffuse des positions de drone à 10Hz")
2. **Identifier les langages déjà présents** dans le projet
3. **Identifier les contraintes** (performance, embarqué, équipe,
   courbe d'apprentissage, écosystème)
4. **Consulter la matrice** ci-dessus
5. **Recommander un langage primaire + une alternative**
6. **Justifier le choix** en 3-5 lignes (pourquoi, pas quoi)
7. **Indiquer le pont d'interopérabilité** avec les langages existants
8. **Si pertinent, suggérer un ADR** (Architecture Decision Record)
   pour tracer la décision

## Anti-patterns

- Choisir un langage parce qu'il est "tendance" sans justification
- Ajouter Rust pour 100 lignes de code qui tourneraient en Python
- Ajouter Go pour un script qui tournerait en Bash
- Mélanger plus de 4 langages dans un projet sans architecture claire
- Réécrire un module qui fonctionne pour "le faire en X" sans gain
  mesurable
- Choisir un langage que personne dans l'équipe ne maîtrise pour un
  composant critique (risque de maintenance)

## Stack de référence GSIE-FEU (exemple d'application)

```
Python   → orchestration, prototypage, géospatial, MAVSDK, tests
Rust     → cœur assimilation (pyo3), futur embarqué drone
Go       → orchestrateur multi-simulations, API temps réel (optionnel)
TypeScript → GCS-Lite, interfaces utilisateur
C++      → contributions à ForeFire/PX4 (uniquement si nécessaire)
Bash     → scripts CI, setup banc
Julia    → veille recherche (assimilation avancée, émulateurs)
```

Cette stack respecte les règles :
- 4 langages principaux (Python, Rust, Go, TypeScript)
- 2 langages secondaires (C++, Bash) pour des tâches spécifiques
- 1 langage de veille (Julia)
- Interopérabilité vérifiée : pyo3 (Python↔Rust), HTTP/gRPC (Python↔Go),
  WASM/napi (Rust↔TS), FastAPI (Python→TS)
