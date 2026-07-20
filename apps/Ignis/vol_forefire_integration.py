"""Ignis — Intégration ForeFire + drone : surveillance de feu.

Ce script orchestre une simulation complète de surveillance d'incendie :

1. Lance une simulation ForeFire en arrière-plan (feu près du point de
   décollage du drone)
2. Démarre PX4 SITL + Gazebo
3. Le drone décolle et survole la zone de feu en pattern lawnmower
4. Capture les positions GPS du drone à intervalles réguliers
5. Charge le GeoJSON du front de feu produit par ForeFire
6. Calcule la distance entre le drone et le front de feu à chaque capture
7. Génère une visualisation combinée (trajectoire drone + front de feu)

Prérequis :
- PX4 SITL compilé dans ~/gsie-ignis/PX4-Autopilot
- ForeFire compilé dans ~/gsie-ignis/forefire
- Fichier surveillance_incendie.ff dans ~/gsie-ignis/data/forefire/
- data.nc et fuels.csv dans ~/gsie-ignis/data/forefire/
"""
import asyncio
import json
import math
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw, PositionNedYaw


# === Paramètres de la mission ===
ALTITUDE = 40.0          # m — altitude de surveillance
CLIMB_RATE = 5.0         # m/s
CRUISE_SPEED = 10.0      # m/s
GRID_SPACING = 50.0      # m — espacement entre lignes
GRID_LINES = 4           # nombre de lignes
LINE_LENGTH = 150.0      # m — longueur de chaque ligne
CAPTURE_INTERVAL = 2.0   # s — intervalle entre captures

# Coordonnées du point de décollage (PX4 SITL Zurich)
HOME_LAT = 47.397971
HOME_LON = 8.546164

# Chemins
HOME = str(Path.home())
PX4_DIR = f"{HOME}/gsie-ignis/PX4-Autopilot"
FOREFIRE_DIR = f"{HOME}/gsie-ignis/forefire"
FOREFIRE_DATA = f"{HOME}/gsie-ignis/data/forefire"
OUTPUT_DIR = f"{HOME}/gsie-ignis/outputs"
FF_SCRIPT = "/mnt/a/GSIE/apps/Ignis/surveillance_incendie.ff"


def latlon_to_ned(lat: float, lon: float, ref_lat: float, ref_lon: float):
    """Convertit lat/lon en coordonnées NED (Nord, Est) relatives."""
    cos_lat = math.cos(math.radians(ref_lat))
    north = (lat - ref_lat) * 111320.0
    east = (lon - ref_lon) * 111320.0 * cos_lat
    return north, east


def ned_to_latlon(north: float, east: float, ref_lat: float, ref_lon: float):
    """Convertit NED en lat/lon."""
    cos_lat = math.cos(math.radians(ref_lat))
    lat = ref_lat + north / 111320.0
    lon = ref_lon + east / (111320.0 * cos_lat)
    return lat, lon


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance haversine en mètres entre deux points GPS."""
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def start_forefire() -> subprocess.Popen:
    """Lance ForeFire en arrière-plan avec le scénario de surveillance."""
    os.makedirs(FOREFIRE_DATA, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Copier data.nc et fuels.csv depuis les tests ForeFire
    test_data = f"{FOREFIRE_DIR}/tests/runff"
    for f in ["data.nc", "fuels.csv"]:
        src = f"{test_data}/{f}"
        dst = f"{FOREFIRE_DATA}/{f}"
        if not os.path.exists(dst) and os.path.exists(src):
            subprocess.run(["cp", src, dst], check=True)

    # Copier le script ForeFire
    dst_ff = f"{FOREFIRE_DATA}/surveillance_incendie.ff"
    subprocess.run(["cp", FF_SCRIPT, dst_ff], check=True)

    # Lancer ForeFire
    print(f"  Lancement ForeFire: {dst_ff}")
    proc = subprocess.Popen(
        [f"{FOREFIRE_DIR}/build/bin/forefire", "-i", dst_ff],
        cwd=FOREFIRE_DATA,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc


def load_fire_front() -> list:
    """Charge le GeoJSON du front de feu produit par ForeFire."""
    geojson_path = f"{FOREFIRE_DATA}/surveillance_fire_front.geojson"
    if not os.path.exists(geojson_path):
        print(f"  ⚠ Pas de fichier front de feu: {geojson_path}")
        return []

    with open(geojson_path, "r") as f:
        data = json.load(f)

    # Extraire les coordonnées du front de feu
    fire_points = []
    for feature in data.get("features", []):
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [])
        if geom.get("type") == "MultiPolygon":
            for polygon in coords:
                for ring in polygon:
                    for point in ring:
                        lon, lat, _ = point[0], point[1], point[2] if len(point) > 2 else 0
                        fire_points.append({"lat": lat, "lon": lon})
        elif geom.get("type") == "Polygon":
            for ring in coords:
                for point in ring:
                    lon, lat = point[0], point[1]
                    fire_points.append({"lat": lat, "lon": lon})
        elif geom.get("type") == "LineString":
            for point in coords:
                lon, lat = point[0], point[1]
                fire_points.append({"lat": lat, "lon": lon})

    return fire_points


async def wait_gps_home(drone: System) -> None:
    print("Attente GPS fix...")
    async for gps in drone.telemetry.gps_info():
        if gps.num_satellites >= 6:
            print(f"✓ GPS fix: {gps.num_satellites} satellites")
            break
        await asyncio.sleep(1)

    print("Attente position home...")
    async for health in drone.telemetry.health():
        if health.is_home_position_ok and health.is_global_position_ok:
            print("✓ Position home OK")
            break
        await asyncio.sleep(1)


async def configure_sitl(drone: System) -> None:
    print("Configuration parametres SITL...")
    await drone.param.set_param_int("COM_RCL_EXCEPT", 7)
    await drone.param.set_param_int("NAV_DLL_ACT", 0)
    await drone.param.set_param_int("NAV_RCL_ACT", 0)
    await drone.param.set_param_float("MPC_THR_HOVER", 0.5)
    await drone.param.set_param_float("MPC_Z_VEL_MAX_UP", 10.0)
    await drone.param.set_param_float("MPC_XY_VEL_MAX", 12.0)
    print("✓ Params SITL configures")
    await asyncio.sleep(3)


async def takeoff(drone: System) -> None:
    print(f"Preparation setpoint offboard (climb {CLIMB_RATE} m/s)...")
    await drone.offboard.set_velocity_ned(
        VelocityNedYaw(0.0, 0.0, -CLIMB_RATE, 0.0)
    )

    print("Armement...")
    await drone.action.arm()
    print("✓ Drone arme")

    print("Activation mode offboard...")
    try:
        await drone.offboard.start()
        print("✓ Offboard actif")
    except OffboardError as e:
        print(f"✗ Erreur offboard: {e}")
        await drone.action.disarm()
        raise

    # Climb 8 s puis position hold
    print(f"Montee (climb {CLIMB_RATE} m/s pendant 8 s)...")
    await asyncio.sleep(8)
    await drone.offboard.set_position_ned(
        PositionNedYaw(0.0, 0.0, -ALTITUDE, 0.0)
    )
    await asyncio.sleep(3)
    print("✓ Altitude stabilisee")


async def fly_surveillance_pattern(drone: System, fire_points: list) -> list:
    """Pattern lawnmower avec capture de positions et calcul distance au feu."""
    captures = []
    line_duration = LINE_LENGTH / CRUISE_SPEED

    print("\n=== Pattern surveillance grille ===")
    print(f"  {GRID_LINES} lignes x {LINE_LENGTH} m, espacement {GRID_SPACING} m")
    print(f"  Vitesse: {CRUISE_SPEED} m/s, altitude: {ALTITUDE} m")
    if fire_points:
        print(f"  Front de feu: {len(fire_points)} points charges")

    for line_num in range(GRID_LINES):
        going_east = (line_num % 2 == 0)
        direction = "Est" if going_east else "Ouest"
        east_vel = CRUISE_SPEED if going_east else -CRUISE_SPEED
        yaw = 90 if going_east else 270
        y_offset = line_num * GRID_SPACING

        print(f"\nLigne {line_num + 1}/{GRID_LINES}: {direction} (y={y_offset:.0f} m)")

        await drone.offboard.set_velocity_ned(
            VelocityNedYaw(0.0, east_vel, 0.0, yaw)
        )

        start = asyncio.get_event_loop().time()
        last_capture = 0.0

        async for pos in drone.telemetry.position():
            elapsed = asyncio.get_event_loop().time() - start
            alt = pos.relative_altitude_m

            if elapsed - last_capture >= CAPTURE_INTERVAL:
                # Calculer la distance minimale au front de feu
                min_dist = float("inf")
                if fire_points:
                    for fp in fire_points:
                        d = haversine_m(
                            pos.latitude_deg, pos.longitude_deg,
                            fp["lat"], fp["lon"]
                        )
                        if d < min_dist:
                            min_dist = d

                capture = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "elapsed_s": round(elapsed, 2),
                    "line": line_num + 1,
                    "lat": pos.latitude_deg,
                    "lon": pos.longitude_deg,
                    "alt_m": round(alt, 1),
                    "dist_to_fire_m": round(min_dist, 1) if min_dist != float("inf") else None,
                }
                captures.append(capture)
                last_capture = elapsed

                dist_str = f"dist_feu={min_dist:.0f}m" if min_dist != float("inf") else "dist_feu=N/A"
                print(f"  [{elapsed:5.1f}s] lat={pos.latitude_deg:.6f} "
                      f"lon={pos.longitude_deg:.6f} alt={alt:.1f}m "
                      f"📸 #{len(captures)} {dist_str}")

            if elapsed > line_duration:
                print(f"  ✓ Ligne {line_num + 1} complete")
                break
            await asyncio.sleep(0.5)

        # Transition vers la ligne suivante
        if line_num < GRID_LINES - 1:
            print(f"  Transition (Nord {GRID_SPACING} m)")
            await drone.offboard.set_velocity_ned(
                VelocityNedYaw(CRUISE_SPEED, 0.0, 0.0, 0.0)
            )
            await asyncio.sleep(GRID_SPACING / CRUISE_SPEED)

    # Stabiliser
    print("\nStabilisation...")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    return captures


async def land(drone: System) -> None:
    print("\nArret offboard + atterrissage...")
    await drone.offboard.stop()
    await drone.action.land()
    await asyncio.sleep(15)
    print("✓ Vol termine")


async def run() -> None:
    # === Phase 1 : Lancer ForeFire ===
    print("=" * 60)
    print("PHASE 1 : Simulation ForeFire (feu de foret)")
    print("=" * 60)
    ff_proc = start_forefire()
    print("✓ ForeFire lance en arriere-plan (PID={})".format(ff_proc.pid))

    # Attendre que ForeFire produise le GeoJSON
    geojson_path = f"{FOREFIRE_DATA}/surveillance_fire_front.geojson"
    print(f"Attente du front de feu ({geojson_path})...")
    for i in range(30):
        if os.path.exists(geojson_path):
            print("✓ Front de feu disponible")
            break
        await asyncio.sleep(1)
    else:
        print("⚠ ForeFire n'a pas produit de GeoJSON a temps (continue sans)")

    # Charger le front de feu
    fire_points = load_fire_front()
    print(f"✓ {len(fire_points)} points du front de feu charges")

    # === Phase 2 : Démarrer PX4 + Gazebo ===
    print("\n" + "=" * 60)
    print("PHASE 2 : Demarrage PX4 SITL + Gazebo")
    print("=" * 60)

    # Nettoyer instances précédentes
    subprocess.run(["pkill", "-9", "-f", "bin/px4"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "gz sim"], capture_output=True)
    await asyncio.sleep(2)

    # Lancer PX4
    env = dict(os.environ, HEADLESS="1")
    px4_proc = subprocess.Popen(
        ["make", "px4_sitl", "gz_x500"],
        cwd=PX4_DIR,
        stdout=open(f"{HOME}/gsie-ignis/logs/px4_surveillance.log", "w"),
        stderr=subprocess.STDOUT,
        env=env,
    )
    print(f"✓ PX4 lance (PID={px4_proc.pid})")

    # Attendre MAVLink
    print("Attente MAVLink (port 14580)...")
    for i in range(60):
        result = subprocess.run(
            ["ss", "-ulnp"], capture_output=True, text=True
        )
        if "14580" in result.stdout:
            print("✓ PX4 pret (MAVLink actif)")
            break
        await asyncio.sleep(1)
    else:
        print("✗ PX4 n'a pas demarre a temps")
        ff_proc.terminate()
        return

    # Stabilisation capteurs
    print("Stabilisation capteurs (10s)...")
    await asyncio.sleep(10)

    # === Phase 3 : Mission drone ===
    print("\n" + "=" * 60)
    print("PHASE 3 : Mission de surveillance drone")
    print("=" * 60)

    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    print("Connexion au drone...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("✓ Drone connecté")
            break

    await wait_gps_home(drone)
    await configure_sitl(drone)
    await takeoff(drone)
    captures = await fly_surveillance_pattern(drone, fire_points)
    await land(drone)

    # === Phase 4 : Sauvegarder et analyser ===
    print("\n" + "=" * 60)
    print("PHASE 4 : Sauvegarde et analyse")
    print("=" * 60)

    output_path = "/mnt/a/GSIE/apps/Ignis/captures_forefire_integration.json"
    output_data = {
        "mission": "forefire_drone_integration",
        "date": datetime.now(timezone.utc).isoformat(),
        "altitude_m": ALTITUDE,
        "grid_lines": GRID_LINES,
        "line_length_m": LINE_LENGTH,
        "grid_spacing_m": GRID_SPACING,
        "fire_points_count": len(fire_points),
        "captures_count": len(captures),
        "fire_front": fire_points[:100],  # Limiter pour la taille
        "captures": captures,
    }
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"✓ {len(captures)} captures sauvegardees dans {output_path}")

    # Statistiques de distance au feu
    dists = [c["dist_to_fire_m"] for c in captures if c["dist_to_fire_m"] is not None]
    if dists:
        print("\nStatistiques distance au feu:")
        print(f"  Min: {min(dists):.1f} m")
        print(f"  Max: {max(dists):.1f} m")
        print(f"  Moy: {sum(dists) / len(dists):.1f} m")

    # === Nettoyage ===
    print("\nNettoyage...")
    px4_proc.terminate()
    ff_proc.terminate()
    await asyncio.sleep(3)
    subprocess.run(["pkill", "-9", "-f", "bin/px4"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "gz sim"], capture_output=True)
    print("✓ Simulation terminee")


if __name__ == "__main__":
    asyncio.run(run())
