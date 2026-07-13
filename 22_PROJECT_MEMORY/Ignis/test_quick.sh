#!/bin/bash
export HOME=/home/camil
pkill -9 -f 'mavsdk' 2>/dev/null || true
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
sleep 3

PX4_DIR=~/gsie-ignis/PX4-Autopilot
BUILD_DIR="$PX4_DIR/build/px4_sitl_default"

# Gazebo
export GZ_SIM_RESOURCE_PATH="$PX4_DIR/Tools/simulation/gz/models:~/.simulation-gazebo/models"
gz sim -s -r "$PX4_DIR/Tools/simulation/gz/worlds/default.sdf" > /tmp/gz.log 2>&1 &
for i in $(seq 1 30); do
    gz topic -l 2>/dev/null | grep -q "/world/default/stats" && break
    sleep 1
done
echo "✓ Gazebo pret"

# PX4
cd "$BUILD_DIR"
HEADLESS=1 PX4_SIM_MODEL=gz_x500 GZ_IP=127.0.0.1 \
    ./bin/px4 etc/init.d-posix/rcS 0 2>&1 | grep -v '\[2K' | grep -v '^pxh>' > /tmp/px4.log &
PX4_PID=$!
for i in $(seq 1 60); do
    ss -ulnp 2>/dev/null | grep -q "14580" && break
    sleep 1
done
echo "✓ PX4 pret"
sleep 10

# Test connexion
echo "=== Test connexion MAVSDK ==="
timeout 30 ~/gsie-ignis/.venv/bin/python3 /mnt/a/GSIE/22_PROJECT_MEMORY/Ignis/test_connect.py 2>&1

echo "=== Nettoyage ==="
kill $PX4_PID 2>/dev/null || true
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
pkill -9 -f 'mavsdk' 2>/dev/null || true
echo "=== Done ==="
