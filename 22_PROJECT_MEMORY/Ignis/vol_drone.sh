#!/bin/bash
# Ignis — Premier vol drone : PX4 SITL + Gazebo + MAVSDK
export HOME=/home/camil

# Nettoyer toute instance precedente
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
sleep 2

PX4_DIR=~/gsie-feu/PX4-Autopilot

# 1. Demarrer PX4 + Gazebo via make (headless)
echo "=== Demarrage PX4 SITL + Gazebo (headless) ==="
cd "$PX4_DIR"
HEADLESS=1 make px4_sitl gz_x500 > /tmp/px4_stdout.log 2>&1 &
MAKE_PID=$!
echo "Make PID: $MAKE_PID"

# Attendre que PX4 soit pret (MAVLink sur 14580)
echo "Attente demarrage PX4..."
for i in $(seq 1 60); do
    if ss -ulnp 2>/dev/null | grep -q "14580"; then
        echo "✓ PX4 pret (MAVLink actif)"
        break
    fi
    if ! kill -0 $MAKE_PID 2>/dev/null; then
        echo "✗ Make/PX4 est mort"
        tail -30 /tmp/px4_stdout.log
        exit 1
    fi
    sleep 1
done

# Laisser les capteurs se stabiliser
echo "Stabilisation capteurs (10s)..."
sleep 10

# Verifier que PX4 tourne
if ! kill -0 $MAKE_PID 2>/dev/null; then
    echo "✗ PX4 est mort"
    tail -20 /tmp/px4_stdout.log
    exit 1
fi
echo "✓ PX4 operationnel"

# 2. Lancer le script MAVSDK
cp /mnt/a/GSIE/22_PROJECT_MEMORY/Ignis/premier_vol.py ~/gsie-feu/scripts/premier_vol.py
source ~/gsie-feu/.venv/bin/activate
echo "=== Lancement premier_vol.py ==="
timeout 120 python ~/gsie-feu/scripts/premier_vol.py 2>&1
echo "=== Script MAVSDK termine ==="

# 3. Arret propre
echo "=== Arret ==="
kill $MAKE_PID 2>/dev/null || true
sleep 2
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
echo "=== Vol termine ==="
