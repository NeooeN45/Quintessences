#!/bin/bash
# GSIE-FEU — Lancement démo Aullène (Corse) ForeFire
export HOME=/home/camil
export PATH=$PATH:~/gsie-feu/forefire/build/bin
export LD_LIBRARY_PATH=~/gsie-feu/forefire/lib:$LD_LIBRARY_PATH

echo "=== ForeFire version ==="
forefire --version 2>&1 || echo "no --version flag"

echo "=== Recherche exemples ==="
cd ~/gsie-feu/forefire
find . -iname '*aullene*' 2>&1 | head -20
echo "=== Liste examples ==="
ls examples/ 2>&1 || echo "no examples dir"
ls tests/ 2>&1 | head -20
