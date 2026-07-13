#!/bin/bash
export HOME=/home/camil
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
sleep 2

cd ~/gsie-feu/PX4-Autopilot
echo "=== Starting PX4 + Gazebo ==="
HEADLESS=1 make px4_sitl gz_x500 > /tmp/px4_stdout.log 2>&1 &
MAKE_PID=$!

echo "Waiting for PX4..."
for i in $(seq 1 60); do
    if ss -ulnp 2>/dev/null | grep -q "14580"; then
        echo "PX4 ready"
        break
    fi
    sleep 1
done
sleep 10

echo "=== Topics ==="
gz topic -l 2>&1 | grep motor

echo "=== Publishing to /model/x500_0/command/motor_speed ==="
gz topic -t /model/x500_0/command/motor_speed -m gz.msgs.Actuators -p 'velocity: 800 velocity: 800 velocity: 800 velocity: 800' -d 5 2>&1 &
PUB_PID=$!

sleep 3
echo "=== Drone pose after 3s ==="
timeout 3 gz topic -e -t /world/default/dynamic_pose/info -n 1 2>&1 | grep -A5 'position'

sleep 3
echo "=== Drone pose after 6s ==="
timeout 3 gz topic -e -t /world/default/dynamic_pose/info -n 1 2>&1 | grep -A5 'position'

wait $PUB_PID 2>/dev/null

echo "=== Cleanup ==="
kill $MAKE_PID 2>/dev/null || true
sleep 2
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
echo "=== Done ==="
