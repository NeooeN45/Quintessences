#!/bin/bash
# GSIE-Ignis — Lanceur : ForeFire + PX4 SITL + Gazebo + vol drone
# Usage : ./run_forefire.sh
set -euo pipefail

echo "============================================================"
echo "GSIE-IGNIS — Vol drone + ForeFire temps réel"
echo "============================================================"

# Nettoyer les processus précédents
pkill -9 -f "bin/px4" 2>/dev/null || true
pkill -9 -f "gz sim" 2>/dev/null || true
pkill -f "forefire" 2>/dev/null || true
sleep 2

# Variables
export LD_LIBRARY_PATH="$HOME/gsie-ignis/forefire/lib:${LD_LIBRARY_PATH:-}"
export PYTHONUNBUFFERED=1

# Lancer le script Python
cd /mnt/a/GSIE/22_PROJECT_MEMORY/GSIE-Ignis
timeout 300 python3 -u vol_forefire.py
EXIT_CODE=$?

# Nettoyage final
pkill -9 -f "bin/px4" 2>/dev/null || true
pkill -9 -f "gz sim" 2>/dev/null || true
pkill -f "forefire" 2>/dev/null || true

echo ""
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Mission terminée avec succès"
else
    echo "✗ Mission terminée avec code $EXIT_CODE"
fi
echo "============================================================"
exit $EXIT_CODE
