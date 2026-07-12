# Journal de bord — GSIE-FEU

## 2026-07-12 — Session 1 : démarrage du banc

### Fait
- Phase 1 GSIE clôturée (DEC-000004, entrée en Phase 2)
- WSL2 Ubuntu 24.04 vérifié : Python 3.12.3, 8 threads, 15 Go RAM, 948 Go dispo
- `.wslconfig` créé (20GB RAM, 6 CPU, 8GB swap)
- Socle logiciel installé : cmake 3.28.3, GCC 13.3, NetCDF 4.9.2, Make 4.3
- Structure `~/gsie-feu/` créée (forefire/, PX4-Autopilot/, data/, scripts/,
  assimilation/, gcs-lite/, notes/)
- Venv Python 3.12 créé + pip 26.1.2
- ForeFire cloné et **compilé avec succès** (-j4, ~2 min)
- Premier feu simulé : `forefire -i tests/runff/run.ff` → GeoJSON produit
- `propagation.png` généré (première image du projet GSIE-FEU)
- Scripts `plot_front.py` et `premier_vol.py` déployés
- `.bashrc` configuré (PATH forefire + activation venv)
- PX4-Autopilot cloné (--recursive), setup ubuntu.sh en cours
- Skill `lang-selector` créée (sélection de langage par tâche)

### Décidé
- Stack langages : Python (orchestration) + Rust (cœur IP, pyo3) + Go
  (optionnel, API temps réel) + TypeScript (GCS-Lite)
- Rust est le prochain langage à apprendre pour Camille (priorité
  stratégique : cœur assimilation + futur embarqué)
- Julia gardé en veille pour la recherche (CIFRE/doctorat éventuel)
- C++ uniquement si contribution directe à ForeFire/PX4

### Prochain pas
- Finir setup PX4 + Gazebo (ubuntu.sh en cours)
- Premier vol drone : `HEADLESS=1 make px4_sitl gz_x500`
- Script `premier_vol.py` (MAVSDK) : armement → décollage → télémétrie →
  atterrissage
- git init sur ~/gsie-feu/ (scripts/, assimilation/, gcs-lite/, notes/)
