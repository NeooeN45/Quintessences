#!/bin/bash
# GSIE-Ignis — Visualisation du premier feu
export HOME=/home/camil
source ~/GSIE-Ignis/.venv/bin/activate

pip install matplotlib numpy netcdf4 geojson 2>&1 | tail -3

cd ~/GSIE-Ignis/forefire/tests/runff
python ~/GSIE-Ignis/scripts/plot_front.py 2>&1
