#!/bin/bash
# GSIE-FEU — Premier vol drone : PX4 SITL + MAVSDK en un seul script
set -e
export HOME=/home/camil

# Nettoyer toute instance precedente
pkill -9 -f 'bin/px4' 2>/dev/null || true
pkill -9 -f 'gz sim' 2>/dev/null || true
sleep 2

# Lancer PX4 SITL en background
cd ~/gsie-feu/PX4-Autopilot
echo "=== Demarrage PX4 SITL (gz_x500, headless) ==="
HEADLESS=1 PX4_SYS_AUTOSTART=4001 ./build/px4_sitl_default/bin/px4 \
    -i etc/init.d-posix/airframes/4001_gz_x500 \
    > /tmp/px4_stdout.log 2>&1 &
PX4_PID=$!
echo "PX4 PID: $PX4_PID"

# Attendre que PX4 soit pret (MAVLink sur 14580)
echo "Attente demarrage PX4..."
for i in $(seq 1 30); do
    if ss -ulnp 2>/dev/null | grep -q "14580"; then
        echo "✓ PX4 pret (MAVLink actif)"
        break
    fi
    sleep 1
done

# Verifier que PX4 tourne toujours
if ! kill -0 $PX4_PID 2>/dev/null; then
    echo "✗ PX4 est mort"
    cat /tmp/px4_stdout.log | tail -20
    exit 1
fi

# Lancer le script MAVSDK
source ~/gsie-feu/.venv/bin/activate
echo "=== Lancement premier_vol.py ==="
timeout 90 python ~/gsie-feu/scripts/premier_vol.py 2>&1 || echo "Script MAVSDK termine (timeout ou erreur)"

# Arreter PX4 proprement
echo "=== Arret PX4 ==="
kill $PX4_PID 2>/dev/null || true
sleep 2
pkill -9 -f 'gz sim' 2>/dev/null || true
echo "=== Vol termine ==="
