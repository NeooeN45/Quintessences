#!/bin/bash
# GSIE-FEU — Visualisation du premier feu
export HOME=/home/camil
source ~/gsie-feu/.venv/bin/activate

pip install matplotlib numpy netcdf4 geojson 2>&1 | tail -3

cd ~/gsie-feu/forefire/tests/runff
python ~/gsie-feu/scripts/plot_front.py 2>&1
