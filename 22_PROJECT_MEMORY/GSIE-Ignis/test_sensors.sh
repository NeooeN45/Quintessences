#!/bin/bash
# Test complet : Gazebo + PX4 avec capteurs
export HOME=/home/camil

pkill -9 -f gz 2>/dev/null || true
pkill -9 -f px4 2>/dev/null || true
pkill -9 -f mavsdk 2>/dev/null || true
sleep 3

PX4_DIR=~/gsie-ignis/PX4-Autopilot
BUILD_DIR="$PX4_DIR/build/px4_sitl_default"
ROOTFS_DIR="$BUILD_DIR/rootfs"

# Sourcer l'environnement Gazebo
source "$ROOTFS_DIR/gz_env.sh"

echo "=== 1. Demarrage Gazebo ==="
gz sim -s -r "$PX4_DIR/Tools/simulation/gz/worlds/default.sdf" > /tmp/gz_run.log 2>&1 &
GZ_PID=$!
echo "GZ_PID=$GZ_PID"

for i in $(seq 1 30); do
    gz topic -l 2>/dev/null | grep -q "/world/default/stats" && break
    sleep 1
done
echo "Gazebo pret"

echo "=== 2. Topics Gazebo (avant PX4) ==="
gz topic -l 2>/dev/null | head -20

echo "=== 3. Demarrage PX4 ==="
cd "$ROOTFS_DIR"
HEADLESS=1 PX4_SIM_MODEL=gz_x500 GZ_IP=127.0.0.1 \
    "$BUILD_DIR/bin/px4" -s etc/init.d-posix/rcS > /tmp/px4_run.log 2>&1 &
PX4_PID=$!
echo "PX4_PID=$PX4_PID"

for i in $(seq 1 30); do
    ss -ulnp 2>/dev/null | grep -q "14580" && break
    if ! kill -0 $PX4_PID 2>/dev/null; then
        echo "PX4 est mort!"
        break
    fi
    sleep 1
done

echo "=== 4. PX4 log ==="
head -30 /tmp/px4_run.log

echo "=== 5. Topics Gazebo (apres PX4) ==="
gz topic -l 2>/dev/null | grep -i "imu\|air\|mag\|nav\|sensor" | head -10

echo "=== 6. Topics Gazebo (x500) ==="
gz topic -l 2>/dev/null | grep "x500" | head -10

echo "=== 7. Arret ==="
kill $PX4_PID 2>/dev/null || true
sleep 2
pkill -9 -f px4 2>/dev/null || true
pkill -9 -f gz 2>/dev/null || true
echo "Done"
