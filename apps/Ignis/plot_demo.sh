#!/bin/bash
# Ignis — Visualisation du premier feu
export HOME=/home/camil
source ~/Ignis/.venv/bin/activate

pip install matplotlib numpy netcdf4 geojson 2>&1 | tail -3

cd ~/Ignis/forefire/tests/runff
python ~/Ignis/scripts/plot_front.py 2>&1
