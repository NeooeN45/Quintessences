#!/bin/bash
# Ignis — Premier feu ForeFire
export HOME=/home/camil
export PATH=$PATH:~/Ignis/forefire/bin
export LD_LIBRARY_PATH=~/Ignis/forefire/lib:$LD_LIBRARY_PATH

echo "=== ForeFire version ==="
forefire --version 2>&1 || forefire -h 2>&1 | head -5

echo "=== Lancement test run.ff ==="
cd ~/Ignis/forefire/tests/runff
forefire -i run.ff 2>&1 | head -40

echo "=== Sorties produites ==="
ls -la *.geojson *.json *.kml *.nc 2>/dev/null | head -20
