#!/bin/bash
# Test PX4 avec differentes methodes de startup
export HOME=/home/camil

pkill -9 -f gz 2>/dev/null || true
pkill -9 -f px4 2>/dev/null || true
sleep 3

PX4_DIR=~/gsie-ignis/PX4-Autopilot
BUILD_DIR="$PX4_DIR/build/px4_sitl_default"
ROOTFS_DIR="$BUILD_DIR/rootfs"

source "$ROOTFS_DIR/gz_env.sh"

# Gazebo
gz sim -s -r "$PX4_DIR/Tools/simulation/gz/worlds/default.sdf" > /tmp/gz_run.log 2>&1 &
for i in $(seq 1 30); do
    gz topic -l 2>/dev/null | grep -q "/world/default/stats" && break
    sleep 1
done
echo "Gazebo pret"

# Test 1: PX4 depuis rootfs avec -s chemin absolu
echo "=== Test 1: rootfs + -s absolu ==="
cd "$ROOTFS_DIR"
HEADLESS=1 PX4_SIM_MODEL=gz_x500 GZ_IP=127.0.0.1 \
    timeout 15 "$BUILD_DIR/bin/px4" -s "$ROOTFS_DIR/etc/init.d-posix/rcS" > /tmp/px4_t1.log 2>&1
echo "EXIT=$?"
head -10 /tmp/px4_t1.log

pkill -9 -f px4 2>/dev/null || true
sleep 2

# Test 2: PX4 depuis build_dir avec argument positionnel
echo "=== Test 2: build_dir + arg positionnel ==="
cd "$BUILD_DIR"
HEADLESS=1 PX4_SIM_MODEL=gz_x500 GZ_IP=127.0.0.1 \
    timeout 15 ./bin/px4 etc/init.d-posix/rcS 0 > /tmp/px4_t2.log 2>&1
echo "EXIT=$?"
head -10 /tmp/px4_t2.log

pkill -9 -f px4 2>/dev/null || true
pkill -9 -f gz 2>/dev/null || true
echo "Done"
