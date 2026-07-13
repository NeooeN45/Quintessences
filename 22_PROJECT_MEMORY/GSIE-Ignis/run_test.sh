#!/bin/bash
# GSIE-Ignis — Lanceur générique de test de vol
# Usage: bash run_test.sh <script_python>
export HOME=/home/camil

SCRIPT_NAME="${1:-premier_vol.py}"
SCRIPT_PATH="/mnt/a/GSIE/22_PROJECT_MEMORY/GSIE-Ignis/${SCRIPT_NAME}"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "✗ Script introuvable: $SCRIPT_PATH"
    echo "Usage: bash run_test.sh <script_python>"
    ls /mnt/a/GSIE/22_PROJECT_MEMORY/GSIE-Ignis/vol_*.py 2>/dev/null | xargs -n1 basename
    exit 1
fi

# Nettoyer
pkill -9 -f 'mavsdk' 2>/dev/null || true
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
sleep 3

PX4_DIR=~/gsie-ignis/PX4-Autopilot
BUILD_DIR="$PX4_DIR/build/px4_sitl_default"
ROOTFS_DIR="$BUILD_DIR/rootfs"

# Sourcer l'environnement Gazebo (plugins capteurs, models, server.config)
source "$ROOTFS_DIR/gz_env.sh"

# 1. Gazebo (avec server.config pour les plugins de capteurs)
echo "=== Demarrage Gazebo (headless) ==="
gz sim -s -r "$PX4_DIR/Tools/simulation/gz/worlds/default.sdf" > /tmp/gz_stdout.log 2>&1 &
GZ_PID=$!
echo "Gazebo PID: $GZ_PID"

echo "Attente Gazebo..."
for i in $(seq 1 30); do
    if gz topic -l 2>/dev/null | grep -q "/world/default/stats"; then
        echo "✓ Gazebo pret"
        break
    fi
    sleep 1
done

# 2. PX4 (depuis build_dir avec argument positionnel — méthode qui fonctionne)
echo "=== Demarrage PX4 SITL ==="
cd "$BUILD_DIR"
HEADLESS=1 PX4_SIM_MODEL=gz_x500 GZ_IP=127.0.0.1 \
    ./bin/px4 etc/init.d-posix/rcS 0 > /tmp/px4_stdout.log 2>&1 &
PX4_PID=$!
echo "PX4 PID: $PX4_PID"

echo "Attente demarrage PX4..."
for i in $(seq 1 60); do
    if ss -ulnp 2>/dev/null | grep -q "14580"; then
        echo "✓ PX4 pret (MAVLink actif)"
        break
    fi
    if ! kill -0 $PX4_PID 2>/dev/null; then
        echo "✗ PX4 est mort"
        tail -30 /tmp/px4_stdout.log
        pkill -9 -f 'gz sim' 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

echo "Stabilisation capteurs (15s)..."
sleep 15

if ! kill -0 $PX4_PID 2>/dev/null; then
    echo "✗ PX4 est mort"
    tail -20 /tmp/px4_stdout.log
    pkill -9 -f 'gz sim' 2>/dev/null || true
    exit 1
fi
echo "✓ PX4 operationnel"

# 3. Script MAVSDK
cp "$SCRIPT_PATH" ~/gsie-ignis/scripts/"$SCRIPT_NAME"
echo "=== Lancement ${SCRIPT_NAME} ==="
PYTHONUNBUFFERED=1 timeout 300 ~/gsie-ignis/.venv/bin/python3 -u ~/gsie-ignis/scripts/"$SCRIPT_NAME" 2>&1
RESULT=$?
echo "=== Script MAVSDK termine (exit=$RESULT) ==="

# 4. Arret
echo "=== Arret ==="
kill $PX4_PID 2>/dev/null || true
sleep 2
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
pkill -9 -f 'mavsdk' 2>/dev/null || true
echo "=== Test termine ==="
