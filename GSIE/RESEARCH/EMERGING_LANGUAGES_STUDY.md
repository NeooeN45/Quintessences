# Fiche recherche — Langages émergents : étude pour GSIE

| Champ | Valeur |
|---|---|
| **Document** | RESEARCH/EMERGING_LANGUAGES_STUDY |
| **Dossier** | GSIE/RESEARCH/ |
| **Phase** | 4 — Implémentation |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Méthode** | Subagent de recherche (sources web 2025-2026) |
| **Question** | Un 4e langage (au-delà de Python+Rust+Go+TypeScript) serait-il révolutionnaire pour GSIE ? |
| **Décision liée** | DEC-000019 (validation stack actuelle) |

---

## 1. Verdict

**La stack actuelle (Python+Rust+Go+TypeScript) est optimale pour GSIE.**
Aucun langage révolutionnaire ne justifie un changement architectural
en 2026. Trois langages méritent d'être **surveillés** pour des niches
spécifiques.

---

## 2. Tableau de synthèse — 10 langages analysés

| Langage | Maturité 2026 | Pertinence GSIE | Avantage révolutionnaire | Verdict |
|---|---|---|---|---|
| **Julia** | ✅ Mature ($65M Series B) | ✅ Calcul scientifique | SciML unique pour simulation | 🟡 Surveiller |
| **Mojo** | ❌ Immature (1.0 fin 2026) | ❌ Focus AI/ML exclusif | Performance Python-like | 🔴 Ignorer |
| **Zig** | ⚠️ Dev 0.14 (1.0 en 2027) | ⚠️ Systems | Simplicité vs Rust | 🔴 Ignorer |
| **Kotlin** | ✅ Mature (KMP) | ⚠️ Mobile+Backend | KMP unification | 🟡 Surveiller |
| **Elixir** | ✅ Très mature (BEAM) | ✅ Temps réel | Concurrency BEAM supérieure | 🟡 Surveiller |
| **Carbon** | ❌ Expérimental (0.1 fin 2026) | ⚠️ C++ successor | Interop C++ bidirectionnel | 🔴 Ignorer |
| **Nim** | ✅ Stable (2.0) | ⚠️ Rust alternative | Simplicité (pas de borrow checker) | 🔴 Ignorer |
| **Swift** | ✅ Mature (Vapor 4) | ❌ Pas d'iOS | Server-side | 🔴 Ignorer |
| **OCaml** | ✅ Très mature (Jane Street) | ✅ Raisonnement | Type system Hindley-Milner | 🟡 Surveiller |
| **Gleam** | ✅ Production-ready (1.17) | ⚠️ Temps réel | Type-safe sur BEAM | 🟡 Surveiller |

---

## 3. Langages à surveiller (3 candidats)

### 3.1 Julia — calcul scientifique intensif

| Critère | Détail |
|---|---|
| **Maturité** | JuliaHub $65M Series B (avril 2026). JuliaEO26 atelier international 2026 |
| **Écosystème géospatial** | JuliaGeo, LibPQ pour PostGIS, livre "Geospatial Data Science with Julia" |
| **Performance** | 10-100x Python sur benchmarks numériques, proche C++/Fortran |
| **Unique** | SciML (DifferentialEquations.jl, ModelingToolkit) — écosystème le plus avancé pour simulation scientifique |
| **Cas GSIE** | Remplacer Python pour calculs intensifs si goulot d'étranglement |
| **Condition activation** | Benchmarks montrent Python limitant sur simulations Forest Dynamics / ForeFire |

### 3.2 Elixir — temps réel distribué

| Critère | Détail |
|---|---|
| **Maturité** | BEAM VM éprouvée (WhatsApp, Ericsson). Phoenix Channels mature |
| **Concurrency** | Millions de green threads, fault tolerance native (supervision trees) |
| **Unique** | Phoenix LiveView (UI temps réel sans JS complexe), preuves drones (ex_drone, beamuav) |
| **Cas GSIE** | Remplacer Go pour temps réel Ignis si concurrency massive requise |
| **Condition activation** | Go ne scale pas pour milliers de connexions drones simultanées |
| **Limite** | Écosystème géospatial limité (pas d'équivalent PostGIS mature) |

### 3.3 OCaml — raisonnement et logique

| Critère | Détail |
|---|---|
| **Maturité** | Utilisé en finance (Jane Street, trading haute fréquence). OxCaml open-source |
| **Type system** | Hindley-Milner inféré, "correct by construction" pour logique complexe |
| **Performance** | Proche C++, GC low-pause (OxCaml pour hot paths sans pauses) |
| **Unique** | Garanties logiques supérieures via type system — prévient classes d'erreurs |
| **Cas GSIE** | Moteurs Reasoning et Validation si bugs logiques coûteux en production |
| **Condition activation** | Bugs logiques récurrents dans Reasoning/Validation malgré Rust |
| **Limite** | Écosystème géospatial limité, courbe d'apprentissage fonctionnelle |

---

## 4. Langages à ignorer (7)

| Langage | Raison principale |
|---|---|
| **Mojo** | Pas production-ready (1.0 fin 2026), écosystème quasi inexistant, focus AI/ML exclusif, license propriétaire incertaine |
| **Zig** | Pas 1.0 (estimé 2027), écosystème ~5000 packages vs 170K Rust/Go, memory safety non garantie |
| **Carbon** | Expérimental (0.1 MVP fin 2026 au plus tôt), Google a historiquement abandonné des projets, Rust déjà mature |
| **Nim** | Écosystème plus petit que Rust, Nim 3.0 en cours, moins de memory safety que Rust, Rust déjà adopté |
| **Swift** | Pas d'iOS dans GSIE (React Native), écosystème géospatial limité, ne résout pas problèmes critiques |
| **Gleam** | Écosystème plus jeune qu'Elixir pour même use case (BEAM), Elixir plus mature |
| **Kotlin** | Intéressant pour KMP mais ne résout pas problèmes critiques (Rust reste nécessaire pour cœur IP) |

---

## 5. Pourquoi la stack actuelle est optimale

| Besoin GSIE | Langage actuel | Alternative étudiée | Verdict |
|---|---|---|---|
| Orchestration + API + géospatial | Python 3.12 (FastAPI) | Julia, Mojo, Kotlin | Python reste meilleur (écosystème, maturité API) |
| Cœur IP (sécurité mémoire + perf) | Rust (pyo3) | Zig, Nim, Carbon, OCaml | Rust reste meilleur (safety garantie, pyo3 mature) |
| Temps réel (drones, streaming) | Go (différé) / FastAPI WebSocket | Elixir, Gleam | Go suffisant pour démarrer, Elixir si scale massive |
| Interfaces clientes | TypeScript (React) | Kotlin (KMP), Swift | TypeScript reste meilleur (écosystème React, partage web/mobile) |
| Simulation scientifique | ForeFire (C++) + Python | Julia (SciML) | Julia à surveiller si Python devient goulot |

---

## 6. Plan de surveillance

| Langage | Quand réévaluer | Critère | Action si activé |
|---|---|---|---|
| **Julia** | Semaine 17 (après Forest Dynamics) | Python < 10 fps sur simulation | POC Julia pour Forest Dynamics |
| **Elixir** | Semaine 25 (benchmark Go) | Go < 10k msg/s ou > 100ms latence | POC Phoenix Channels pour Ignis |
| **OCaml** | Semaine 21 (après Reasoning) | Bugs logiques récurrents | POC OCaml pour Reasoning Engine |

---

## 7. Conclusion

> **Aucun langage révolutionnaire manqué.** La stack Python+Rust+Go+TypeScript
> couvre tous les besoins de GSIE de manière optimale en 2026. Les 3 langages
> à surveiller (Julia, Elixir, OCaml) correspondent à des niches spécifiques
> qui pourraient devenir pertinentes si la stack actuelle atteint ses limites
> sur des cas précis (calcul scientifique, concurrency massive, logique
> critique). La complexité d'ajouter un langage supplémentaire (formation,
> tooling, CI/CD, maintenance) n'est pas justifiée par les avantages
> marginaux des langages analysés.

---

## 8. Sources 2025-2026

- Julia : JuliaHub Series B ($65M, avril 2026), JuliaGeo, JuliaEO26, "Geospatial Data Science with Julia" (2023)
- Mojo : Modular roadmap 2026, benchmarks 78-119x Python
- Zig : Zig 0.14 (mars 2025), Bun/TigerBeetle/Ghostty en production
- Kotlin : KMP mature 2026, Ktor backend
- Elixir : BEAM VM, Phoenix Channels, ex_drone, beamuav/groundstation
- Carbon : GitHub 33.7k stars, roadmap 0.1 fin 2026
- Nim : Nim 2.0 (2023), Nimony v0.2 (nov 2025)
- Swift : Vapor 4, Swift 5.9+
- OCaml : Jane Street, OxCaml, "Quantitative Finance with OCaml" (2026)
- Gleam : Gleam 1.17 (juin 2026), Hex ecosystem, rapports fintech 2026

---

> Statut : *Draft — étude langages émergents pour GSIE. Confirme que la
> stack actuelle (DEC-000019) est optimale. 3 langages à surveiller
> (Julia, Elixir, OCaml) pour niches spécifiques. Aucun code métier
> produit (CON-003).*
