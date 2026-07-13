#!/bin/bash
# Ignis — Structure projet + git init
# Crée la structure de dossiers, fichiers de config, et commit initial
export HOME=/home/camil
PROJECT=~/gsie-ignis

cd "$PROJECT" || exit 1

# 1. Créer les dossiers manquants
mkdir -p scripts data/raw data/processed data/forefire outputs logs

# 2. .gitignore enrichi
cat > .gitignore << 'GITIGNORE'
# Depots clones (pas notre code)
forefire/
PX4-Autopilot/

# Venv
.venv/

# Donnees lourdes
data/**/*.nc
data/**/*.tif
data/**/*.asc
data/**/*.bin

# Sorties de simulation
outputs/*.geojson
outputs/*.kml
outputs/*.png
outputs/*.json
logs/*.ulg
logs/*.log

# Python
__pycache__/
*.pyc
*.egg-info/
.pytest_cache/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
GITIGNORE

# 3. README du projet
cat > README.md << 'README'
# Ignis — Banc de simulation drone + feu

Banc de simulation pour la spécialisation incendie de GSIE (Quintessences).

## Architecture

```
gsie-ignis/
├── forefire/          # ForeFire (clone, simulation de feu)
├── PX4-Autopilot/     # PX4 SITL (clone, autopilote drone)
├── scripts/           # Scripts Python (MAVSDK, vol, surveillance)
├── data/              # Données (raw, processed, forefire)
├── outputs/           # Sorties de simulation (GeoJSON, PNG, captures)
├── logs/              # Logs de vol (ULog, console)
├── assimilation/      # Assimilation de données (futur)
├── gcs-lite/          # GCS légère (futur)
├── notes/             # Notes de recherche
├── .venv/             # Environnement virtuel Python
└── Makefile           # Tâches courantes
```

## Prérequis

- WSL2 Ubuntu 24.04
- Python 3.12 + venv
- PX4 SITL v1.18+ (compilé)
- Gazebo Harmonic 8.x
- ForeFire (compilé)

## Tâches courantes

```bash
make vol              # Premier vol (test 1)
make vol-waypoint     # Vol waypoint (test 2)
make vol-pattern      # Pattern carré (test 3)
make vol-rth          # Return-to-Home (test 4)
make vol-surveillance # Surveillance incendie (test 5)
make forefire-demo    # Démo ForeFire
make plot             # Visualisation trajectoires
```

## Scripts de vol

| Script | Description |
|--------|-------------|
| `premier_vol.py` | Décollage + stabilisation + atterrissage |
| `vol_waypoint.py` | Navigation 5 waypoints GPS |
| `vol_pattern_carre.py` | Pattern carré 200m × 200m |
| `vol_rth.py` | Return-to-Home |
| `vol_surveillance_incendie.py` | Pattern lawnmower + captures GPS |
| `run_test.sh` | Lanceur générique |

## Contexte

Projet GSIE (General System Intelligence Engine) — Quintessences.
Banc hors dépôt principal (voir `a:/GSIE/22_PROJECT_MEMORY/Ignis/`).
README

# 4. requirements.txt
cat > requirements.txt << 'REQS'
mavsdk>=2.3.0
matplotlib>=3.8
numpy>=1.26
pyulog>=0.12
REQS

# 5. Makefile
cat > Makefile << 'MAKEFILE'
.PHONY: vol vol-waypoint vol-pattern vol-rth vol-surveillance forefire-demo plot clean

PY := source .venv/bin/activate
RUN := bash scripts/run_test.sh

vol:
	$(RUN) premier_vol.py

vol-waypoint:
	$(RUN) vol_waypoint.py

vol-pattern:
	$(RUN) vol_pattern_carre.py

vol-rth:
	$(RUN) vol_rth.py

vol-surveillance:
	$(RUN) vol_surveillance_incendie.py

forefire-demo:
	cd forefire && ./bin/forefire -i tests/runff/run.ff

plot:
	$(PY) && python scripts/plot_trajectoire.py

clean:
	rm -f outputs/*.png outputs/*.json logs/*.log
MAKEFILE

# 6. Copier les scripts depuis le dépôt GSIE
cp /mnt/a/GSIE/22_PROJECT_MEMORY/Ignis/*.py scripts/ 2>/dev/null || true
cp /mnt/a/GSIE/22_PROJECT_MEMORY/Ignis/*.sh scripts/ 2>/dev/null || true
cp /mnt/a/GSIE/22_PROJECT_MEMORY/Ignis/run_test.sh scripts/ 2>/dev/null || true

echo "✓ Structure créée"
ls -la
