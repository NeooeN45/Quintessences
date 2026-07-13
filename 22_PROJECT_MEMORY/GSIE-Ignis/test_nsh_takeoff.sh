#!/bin/bash
export HOME=/home/camil
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
sleep 2

cd ~/gsie-feu/PX4-Autopilot
echo "=== Starting PX4 + Gazebo ==="
HEADLESS=1 make px4_sitl gz_x500 > /tmp/px4_nsh.log 2>&1 &
MAKE_PID=$!

echo "Waiting for PX4..."
for i in $(seq 1 60); do
    if ss -ulnp 2>/dev/null | grep -q "14580"; then
        echo "PX4 ready"
        break
    fi
    sleep 1
done
sleep 15

# Send commands directly to PX4 nsh console via stdin
echo "=== Sending commander takeoff ==="
echo "commander takeoff" > /proc/$(pgrep -f 'bin/px4')/fd/0 2>/dev/null || echo "Could not write to PX4 stdin"

sleep 30

echo "=== Drone pose ==="
timeout 3 gz topic -e -t /world/default/dynamic_pose/info -n 1 2>&1 | head -10

echo "=== Motor speeds ==="
timeout 3 gz topic -e -t /x500_0/command/motor_speed -n 1 2>&1

echo "=== PX4 log (last 30 lines, filtered) ==="
grep -v '\[2K' /tmp/px4_nsh.log | grep -v '^pxh>' | tail -30

kill $MAKE_PID 2>/dev/null || true
sleep 2
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
echo "=== Done ==="
