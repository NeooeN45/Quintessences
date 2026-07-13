#!/bin/bash
export HOME=/home/camil
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
sleep 2

# Start ONLY Gazebo (no PX4)
export GZ_SIM_RESOURCE_PATH=~/.simulation-gazebo/models
export GZ_SIM_SERVER_CONFIG_PATH=~/.simulation-gazebo/server.config
echo "=== Starting Gazebo only ==="
gz sim -s -r ~/.simulation-gazebo/worlds/default.sdf > /tmp/gz_only.log 2>&1 &
GZ_PID=$!
sleep 5

# Spawn x500 model
echo "=== Spawning x500 model ==="
gz sim -c 'create -f model://x500 -x 0 -y 0 -z 0.24' 2>&1 || echo "create failed"
sleep 3

echo "=== Topics ==="
gz topic -l 2>&1 | grep motor

echo "=== Publishing motor speeds ==="
# Try publishing with multiline format
gz topic -t /model/x500_0/command/motor_speed -m gz.msgs.Actuators \
    -p 'velocity: 900
velocity: 900
velocity: 900
velocity: 900' \
    -d 10 2>&1 &
PUB_PID=$!

sleep 5
echo "=== Drone pose after 5s ==="
timeout 3 gz topic -e -t /world/default/dynamic_pose/info -n 1 2>&1 | head -15

echo "=== Echo motor topic ==="
timeout 3 gz topic -e -t /model/x500_0/command/motor_speed -n 1 2>&1

wait $PUB_PID 2>/dev/null
kill $GZ_PID 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
echo "=== Done ==="
