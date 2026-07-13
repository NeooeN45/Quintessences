#!/bin/bash
export HOME=/home/camil
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
sleep 2

cd ~/gsie-feu/PX4-Autopilot
echo "=== Starting PX4 + Gazebo ==="
HEADLESS=1 make px4_sitl gz_x500 > /tmp/px4_stdout.log 2>&1 &
MAKE_PID=$!

# Wait for MAVLink
echo "Waiting for PX4..."
for i in $(seq 1 60); do
    if ss -ulnp 2>/dev/null | grep -q "14580"; then
        echo "PX4 ready"
        break
    fi
    sleep 1
done
sleep 10

# Run MAVSDK script in background
source ~/gsie-feu/.venv/bin/activate
cp /mnt/a/GSIE/22_PROJECT_MEMORY/Ignis/premier_vol.py ~/gsie-feu/scripts/premier_vol.py
python ~/gsie-feu/scripts/premier_vol.py > /tmp/mavsdk_stdout.log 2>&1 &
MAVSDK_PID=$!

# Wait for drone to arm and enter offboard
sleep 20

# Check motor speeds
echo "=== MOTOR SPEEDS (5 samples) ==="
timeout 5 gz topic -e -t /x500_0/command/motor_speed -n 5 2>&1 || echo "No data on /x500_0/command/motor_speed"

echo "=== MOTOR SPEEDS (model prefix, 5 samples) ==="
timeout 5 gz topic -e -t /model/x500_0/command/motor_speed -n 5 2>&1 || echo "No data on /model/x500_0/command/motor_speed"

# Wait for MAVSDK to finish
wait $MAVSDK_PID 2>/dev/null

echo "=== MAVSDK LOG ==="
cat /tmp/mavsdk_stdout.log

# Cleanup
kill $MAKE_PID 2>/dev/null || true
sleep 2
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
echo "=== Done ==="
