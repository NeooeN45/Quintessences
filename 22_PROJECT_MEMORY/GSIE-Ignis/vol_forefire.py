"""GSIE-Ignis — Vol drone + simulation ForeFire temps réel.

Pipeline complet :
1. ForeFire démarre en mode serveur HTTP (port 8000)
2. Gazebo + PX4 SITL démarrent (monde Corse, GPS aligné ForeFire)
3. Le drone décolle et survole la zone en pattern lawnmower
4. À intervalles réguliers, le drone interroge ForeFire via HTTP :
   - fait avancer la simulation de N secondes
   - récupère le front de feu en GeoJSON
   - calcule la distance drone ↔ front de feu
   - enregistre une capture (position + front + distance)
5. Atterrissage + sauvegarde JSON + visualisation matplotlib

Prérequis :
- PX4 SITL compilé dans ~/gsie-ignis/PX4-Autopilot
- ForeFire compilé dans ~/gsie-ignis/forefire
- data.nc + fuels.csv dans ~/gsie-ignis/data/forefire/
- corse.sdf dans ~/gsie-ignis/data/forefire/
"""
import asyncio
import http.client
import json
import math
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw, VelocityNedYaw

# === Paramètres mission ===
ALTITUDE = 40.0          # m — altitude surveillance
CLIMB_RATE = 5.0         # m/s
CRUISE_SPEED = 10.0      # m/s
GRID_SPACING = 50.0      # m — espacement entre lignes
GRID_LINES = 4           # nombre de lignes
LINE_LENGTH = 150.0      # m — longueur de chaque ligne
CAPTURE_INTERVAL = 3.0   # s — intervalle entre captures
FF_STEP_SECONDS = 30     # s — avancement ForeFire par capture

# Coordonnées Corse (alignées ForeFire data.nc)
HOME_LAT = 41.9520
HOME_LON = 8.7000

# ForeFire HTTP
FF_HOST = "localhost"
FF_PORT = 8000
FF_BASE_URL = f"http://{FF_HOST}:{FF_PORT}"

# Chemins
HOME = str(Path.home())
PX4_BUILD_DIR = f"{HOME}/gsie-ignis/PX4-Autopilot/build/px4_sitl_default"
PX4_GZ_ENV = f"{HOME}/gsie-ignis/PX4-Autopilot/build/px4_sitl_default/rootfs/gz_env.sh"
FOREFIRE_DIR = f"{HOME}/gsie-ignis/forefire"
FOREFIRE_DATA = f"{HOME}/gsie-ignis/data/forefire"
FOREFIRE_LIB = f"{FOREFIRE_DIR}/lib"
FF_SCRIPT = f"{FOREFIRE_DATA}/surveillance.ff"
CORSE_SDF = f"{FOREFIRE_DATA}/corse.sdf"
OUTPUT_DIR = f"{HOME}/gsie-ignis/outputs"
OUTPUT_JSON = "/mnt/a/GSIE/22_PROJECT_MEMORY/GSIE-Ignis/captures_forefire_temps_reel.json"
OUTPUT_PLOT = "/mnt/a/GSIE/22_PROJECT_MEMORY/GSIE-Ignis/trajet_forefire_temps_reel.png"


# === Helpers géométriques ===

def latlon_to_local_m(lat: float, lon: float) -> tuple:
    """Convertit lat/lon en mètres locaux (N, E) depuis le home."""
    cos_lat = math.cos(math.radians(HOME_LAT))
    north = (lat - HOME_LAT) * 111320.0
    east = (lon - HOME_LON) * 111320.0 * cos_lat
    return north, east


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance haversine en mètres."""
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# === Client ForeFire HTTP ===

def ff_send(command: str) -> str:
    """Envoie une commande à ForeFire via HTTP GET.

    Utilise http.client pour éviter les problèmes d'encodage URL de urllib.
    Les commandes ne doivent pas contenir d'espaces (utiliser geojson pour startFire).
    """
    import http.client
    conn = http.client.HTTPConnection(FF_HOST, FF_PORT, timeout=10)
    try:
        conn.request("GET", f"/ff:{command}")
        resp = conn.getresponse()
        data = resp.read().decode("utf-8")
        return data
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        conn.close()


def ff_step(seconds: int) -> str:
    """Fait avancer la simulation ForeFire de N secondes."""
    return ff_send(f"step[dt={seconds}]")


def ff_get_front(snapshot_name: str) -> str:
    """Demande à ForeFire d'écrire le front de feu dans un fichier GeoJSON."""
    return ff_send(f"print[{snapshot_name}]")


def load_fire_front_geojson(filename: str) -> list:
    """Charge un fichier GeoJSON produit par ForeFire et extrait les points."""
    path = os.path.join(FOREFIRE_DATA, filename)
    if not os.path.exists(path):
        return []

    with open(path, "r") as f:
        data = json.load(f)

    points = []
    for feature in data.get("features", []):
        geom = feature.get("geometry", {})
        gtype = geom.get("type", "")
        coords = geom.get("coordinates", [])

        if gtype == "MultiPolygon":
            for polygon in coords:
                for ring in polygon:
                    for pt in ring:
                        lon, lat = pt[0], pt[1]
                        points.append((lat, lon))
        elif gtype == "Polygon":
            for ring in coords:
                for pt in ring:
                    lon, lat = pt[0], pt[1]
                    points.append((lat, lon))
        elif gtype == "LineString":
            for pt in coords:
                lon, lat = pt[0], pt[1]
                points.append((lat, lon))

    return points


def min_dist_to_fire(drone_lat: float, drone_lon: float, fire_points: list) -> float:
    """Distance minimale (m) entre le drone et le front de feu."""
    if not fire_points:
        return float("inf")
    return min(haversine_m(drone_lat, drone_lon, f_lat, f_lon) for f_lat, f_lon in fire_points)


# === ForeFire processus ===

def start_forefire() -> subprocess.Popen:
    """Lance ForeFire en mode serveur HTTP dédié (flag -l).

    Le flag -l démarre le serveur HTTP avec une boucle infinie qui maintient
    le processus en vie. Toutes les commandes (setup, step, print) sont ensuite
    envoyées via HTTP POST.
    """
    env = dict(os.environ,
        LD_LIBRARY_PATH=f"{FOREFIRE_LIB}:{os.environ.get('LD_LIBRARY_PATH', '')}",
        PWD=FOREFIRE_DATA,
    )
    proc = subprocess.Popen(
        [f"{FOREFIRE_DIR}/bin/forefire", "-l"],
        cwd=FOREFIRE_DATA,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    return proc


def setup_forefire() -> None:
    """Envoie les commandes de setup à ForeFire via HTTP."""
    cmds = [
        "setParameter[ForeFireDataDirectory=.]",
        "setParameter[fuelsTableFile=fuels.csv]",
        "setParameter[propagationModel=Rothermel]",
        "setParameter[dumpMode=geojson]",
        "setParameter[perimeterResolution=10]",
        "setParameter[spatialIncrement=3]",
        "setParameter[propagationSpeedAdjustmentFactor=0.6]",
        "setParameter[windReductionFactor=0.4]",
        "loadData[data.nc;2025-02-10T17:35:54Z]",
        'startFire[geojson="""{"type":"FeatureCollection","valid_at":"2025-02-10T17:35:54Z","features":[{"type":"Feature","properties":{"numberOfPolygons":1},"geometry":{"type":"MultiPolygon","coordinates":[[[[8.69992,41.95206,0],[8.69984,41.95194,0],[8.69976,41.95182,0],[8.70024,41.95182,0],[8.70000,41.95218,0],[8.69992,41.95206,0]]]]}}]}"""]',
        "trigger[wind;loc=(0.,0.,0.);vel=(10,5,0.)]",
    ]
    for cmd in cmds:
        resp = ff_send(cmd)
        if "ERROR" in resp:
            print(f"  ⚠ ForeFire: {cmd[:50]} → {resp[:80]}")


def stop_forefire(proc: subprocess.Popen) -> None:
    """Arrête ForeFire proprement."""
    try:
        proc.stdin.write("quit[]\n")
        proc.stdin.flush()
    except Exception:
        pass
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# === PX4 + Gazebo ===

def _source_gz_env() -> dict:
    """Source gz_env.sh et retourne l'environnement complet."""
    env = dict(os.environ)
    if os.path.exists(PX4_GZ_ENV):
        result = subprocess.run(
            ["bash", "-c", f"source {PX4_GZ_ENV} && env"],
            capture_output=True, text=True
        )
        for line in result.stdout.split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                env[k] = v
    return env


def start_gazebo() -> subprocess.Popen:
    """Lance Gazebo server-only avec le monde Corse via bash (source gz_env.sh)."""
    env = _source_gz_env()
    # Lancer via bash pour garantir que gz_env.sh est sourcé
    cmd = f"source {PX4_GZ_ENV} && gz sim -s -r {CORSE_SDF}"
    proc = subprocess.Popen(
        ["bash", "-c", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    return proc


def start_px4() -> subprocess.Popen:
    """Lance PX4 SITL avec le modèle x500 via bash (source gz_env.sh)."""
    env = _source_gz_env()
    env["PX4_SIM_MODEL"] = "gz_x500"
    env["PX4_GZ_WORLD"] = "corse"

    log_path = os.path.join(OUTPUT_DIR, "px4_forefire.log")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Lancer via bash pour garantir que gz_env.sh est sourcé
    cmd = f"source {PX4_GZ_ENV} && cd {PX4_BUILD_DIR} && ./bin/px4 etc/init.d-posix/rcS 0"
    proc = subprocess.Popen(
        ["bash", "-c", cmd],
        stdout=open(log_path, "w"),
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    return proc


def wait_mavlink(timeout_s: int = 60) -> bool:
    """Attend que PX4 publie MAVLink sur le port 14580."""
    for _ in range(timeout_s):
        result = subprocess.run(["ss", "-ulnp"], capture_output=True, text=True)
        if "14580" in result.stdout:
            return True
        time.sleep(1)
    return False


# === Mission drone ===

async def wait_gps_home(drone: System) -> None:
    print("  Attente GPS fix...")
    async for gps in drone.telemetry.gps_info():
        if gps.num_satellites >= 6:
            print(f"  ✓ GPS fix: {gps.num_satellites} satellites")
            break
        await asyncio.sleep(1)

    print("  Attente position home...")
    async for health in drone.telemetry.health():
        if health.is_home_position_ok and health.is_global_position_ok:
            print("  ✓ Position home OK")
            break
        await asyncio.sleep(1)


async def configure_drone(drone: System) -> None:
    print("  Configuration paramètres...")
    await drone.param.set_param_int("COM_RCL_EXCEPT", 7)
    await drone.param.set_param_int("NAV_DLL_ACT", 0)
    await drone.param.set_param_int("NAV_RCL_ACT", 0)
    await drone.param.set_param_float("MPC_THR_HOVER", 0.5)
    await drone.param.set_param_float("MPC_Z_VEL_MAX_UP", 10.0)
    await drone.param.set_param_float("MPC_XY_VEL_MAX", 12.0)
    await drone.param.set_param_float("MPC_XY_CRUISE", 10.0)
    await drone.param.set_param_float("MPC_TILTMAX_AIR", 45.0)
    print("  ✓ Paramètres configurés")
    await asyncio.sleep(3)


async def takeoff(drone: System) -> None:
    print(f"  Préparation setpoint offboard (climb {CLIMB_RATE} m/s)...")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -CLIMB_RATE, 0.0))

    print("  Armement...")
    await drone.action.arm()
    print("  ✓ Drone armé")

    print("  Activation mode offboard...")
    try:
        await drone.offboard.start()
        print("  ✓ Offboard actif")
    except OffboardError as e:
        print(f"  ✗ Erreur offboard: {e}")
        await drone.action.disarm()
        raise

    print(f"  Montée (climb {CLIMB_RATE} m/s pendant 8 s)...")
    await asyncio.sleep(8)
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -ALTITUDE, 0.0))
    await asyncio.sleep(3)
    print("  ✓ Altitude stabilisée")


async def fly_and_capture(drone: System) -> list:
    """Pattern lawnmower + capture temps réel du front de feu ForeFire."""
    captures = []
    line_duration = LINE_LENGTH / CRUISE_SPEED
    ff_time = 0  # temps simulé ForeFire écoulé

    print(f"\n  === Pattern surveillance grille ===")
    print(f"  {GRID_LINES} lignes x {LINE_LENGTH} m, espacement {GRID_SPACING} m")
    print(f"  Vitesse: {CRUISE_SPEED} m/s, altitude: {ALTITUDE} m")
    print(f"  ForeFire: +{FF_STEP_SECONDS}s par capture")

    for line_num in range(GRID_LINES):
        going_east = (line_num % 2 == 0)
        direction = "Est" if going_east else "Ouest"
        east_vel = CRUISE_SPEED if going_east else -CRUISE_SPEED
        yaw = 90 if going_east else 270
        y_offset = line_num * GRID_SPACING

        print(f"\n  Ligne {line_num + 1}/{GRID_LINES}: {direction} (y={y_offset:.0f} m)")

        await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, east_vel, 0.0, yaw))

        start = asyncio.get_event_loop().time()
        last_capture = 0.0

        async for pos in drone.telemetry.position_velocity_ned():
            elapsed = asyncio.get_event_loop().time() - start

            if elapsed - last_capture >= CAPTURE_INTERVAL:
                # 1. Avancer ForeFire
                ff_time += FF_STEP_SECONDS
                ff_step(FF_STEP_SECONDS)

                # 2. Récupérer le front de feu
                snapshot_name = f"front_{len(captures):03d}.geojson"
                ff_get_front(snapshot_name)
                fire_points = load_fire_front_geojson(snapshot_name)

                # 3. Position drone (NED local → lat/lon)
                north = pos.position.north_m
                east = pos.position.east_m
                cos_lat = math.cos(math.radians(HOME_LAT))
                drone_lat = HOME_LAT + north / 111320.0
                drone_lon = HOME_LON + east / (111320.0 * cos_lat)

                # 4. Distance au front de feu
                dist = min_dist_to_fire(drone_lat, drone_lon, fire_points)

                capture = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "elapsed_s": round(elapsed, 2),
                    "ff_time_s": ff_time,
                    "line": line_num + 1,
                    "ned_n": round(north, 2),
                    "ned_e": round(east, 2),
                    "lat": round(drone_lat, 6),
                    "lon": round(drone_lon, 6),
                    "alt_m": round(-pos.position.down_m, 1),
                    "dist_to_fire_m": round(dist, 1) if dist != float("inf") else None,
                    "fire_points_count": len(fire_points),
                    "fire_front": [{"lat": p[0], "lon": p[1]} for p in fire_points[:50]],
                }
                captures.append(capture)
                last_capture = elapsed

                dist_str = f"dist_feu={dist:.0f}m" if dist != float("inf") else "dist_feu=N/A"
                print(f"    [{elapsed:5.1f}s] N={north:6.1f} E={east:6.1f} "
                      f"alt={-pos.position.down_m:.1f}m "
                      f"📸 #{len(captures)} ff_t={ff_time}s "
                      f"pts_feu={len(fire_points)} {dist_str}")

            if elapsed > line_duration:
                print(f"  ✓ Ligne {line_num + 1} complète")
                break
            await asyncio.sleep(0.5)

        # Transition vers la ligne suivante
        if line_num < GRID_LINES - 1:
            print(f"  Transition (Nord {GRID_SPACING} m)")
            await drone.offboard.set_velocity_ned(VelocityNedYaw(CRUISE_SPEED, 0.0, 0.0, 0.0))
            await asyncio.sleep(GRID_SPACING / CRUISE_SPEED)

    # Stabiliser
    print("\n  Stabilisation...")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    return captures


async def land(drone: System) -> None:
    print("\n  Arrêt offboard + atterrissage...")
    await drone.offboard.stop()
    await drone.action.land()
    await asyncio.sleep(15)
    print("  ✓ Vol terminé")


# === Visualisation ===

def plot_results(captures: list) -> None:
    """Génère un graphique matplotlib : trajectoire drone + fronts de feu."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Polygon
        from matplotlib.collections import PatchCollection
    except ImportError:
        print("  ⚠ matplotlib non disponible — pas de visualisation")
        return

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    # Trajectoire drone
    drone_n = [c["ned_n"] for c in captures]
    drone_e = [c["ned_e"] for c in captures]
    colors_drone = range(len(captures))

    ax.plot(drone_e, drone_n, "b-", linewidth=1.5, alpha=0.5, label="Trajectoire drone")
    scatter = ax.scatter(drone_e, drone_n, c=colors_drone, cmap="cool", s=30, zorder=5)
    plt.colorbar(scatter, ax=ax, label="Capture #")

    # Fronts de feu (quelques snapshots)
    snapshots_to_show = [0, len(captures) // 3, len(captures) * 2 // 3, len(captures) - 1]
    snapshots_to_show = [i for i in snapshots_to_show if 0 <= i < len(captures)]

    fire_cmap = plt.cm.Reds
    for idx, snap_idx in enumerate(snapshots_to_show):
        c = captures[snap_idx]
        fire_pts = c.get("fire_front", [])
        if not fire_pts:
            continue

        fire_n = []
        fire_e = []
        for fp in fire_pts:
            n, e = latlon_to_local_m(fp["lat"], fp["lon"])
            fire_n.append(n)
            fire_e.append(e)

        alpha = 0.3 + 0.5 * (idx + 1) / len(snapshots_to_show)
        color = fire_cmap(0.4 + 0.5 * idx / max(1, len(snapshots_to_show) - 1))
        ax.plot(fire_e, fire_n, "o-", color=color, markersize=3,
                alpha=alpha, label=f"Front feu t={c['ff_time_s']}s")

    # Marquer le home
    ax.plot(0, 0, "k^", markersize=15, label="Home (décollage)", zorder=10)

    # Annotations distance au feu
    for c in captures:
        if c["dist_to_fire_m"] is not None and c["dist_to_fire_m"] < 100:
            ax.annotate(f"{c['dist_to_fire_m']:.0f}m",
                        (c["ned_e"], c["ned_n"]),
                        fontsize=7, color="red",
                        xytext=(5, 5), textcoords="offset points")

    ax.set_xlabel("Est (m)", fontsize=12)
    ax.set_ylabel("Nord (m)", fontsize=12)
    ax.set_title("GSIE-Ignis — Surveillance feu ForeFire (temps réel)", fontsize=14)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT, dpi=150)
    print(f"  ✓ Visualisation : {OUTPUT_PLOT}")


# === Orchestration ===

async def run() -> None:
    print("=" * 70)
    print("GSIE-IGNIS — VOL DRONE + SIMULATION FOREFIRE TEMPS RÉEL")
    print("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # === Phase 1 : ForeFire ===
    print("\n--- Phase 1 : Démarrage ForeFire (serveur HTTP) ---")
    ff_proc = start_forefire()
    print(f"  ForeFire PID={ff_proc.pid}")

    # Attendre que le serveur HTTP réponde
    print("  Attente serveur ForeFire...")
    ff_ready = False
    for _ in range(15):
        resp = ff_send("step[dt=1]")
        if "ERROR" not in resp:
            ff_ready = True
            break
        time.sleep(1)

    if not ff_ready:
        print("  ✗ ForeFire n'a pas démarré — abandon")
        stop_forefire(ff_proc)
        return
    print("  ✓ ForeFire serveur HTTP prêt (port 8000)")

    # Setup : charger terrain, carburants, allumer le feu, vent
    print("  Configuration ForeFire (terrain, feu, vent)...")
    setup_forefire()
    print("  ✓ ForeFire configuré")

    # === Phase 2 : Gazebo + PX4 ===
    print("\n--- Phase 2 : Démarrage Gazebo + PX4 ---")
    subprocess.run(["pkill", "-9", "-f", "bin/px4"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "gz sim"], capture_output=True)
    time.sleep(2)

    gz_proc = start_gazebo()
    print(f"  Gazebo PID={gz_proc.pid}")
    time.sleep(5)

    px4_proc = start_px4()
    print(f"  PX4 PID={px4_proc.pid}")

    print("  Attente MAVLink (port 14580)...")
    if not wait_mavlink(60):
        print("  ✗ PX4 n'a pas démarré à temps")
        stop_forefire(ff_proc)
        px4_proc.terminate()
        gz_proc.terminate()
        return
    print("  ✓ PX4 prêt (MAVLink actif)")

    # Stabilisation capteurs
    print("  Stabilisation capteurs (10s)...")
    time.sleep(10)

    # === Phase 3 : Mission drone ===
    print("\n--- Phase 3 : Mission de surveillance ---")
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    print("  Connexion au drone...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("  ✓ Drone connecté")
            break

    await wait_gps_home(drone)
    await configure_drone(drone)
    await takeoff(drone)
    captures = await fly_and_capture(drone)
    await land(drone)

    # === Phase 4 : Sauvegarde + analyse ===
    print("\n--- Phase 4 : Sauvegarde et analyse ---")
    output_data = {
        "mission": "forefire_temps_reel",
        "date": datetime.now(timezone.utc).isoformat(),
        "home_lat": HOME_LAT,
        "home_lon": HOME_LON,
        "altitude_m": ALTITUDE,
        "grid_lines": GRID_LINES,
        "line_length_m": LINE_LENGTH,
        "grid_spacing_m": GRID_SPACING,
        "ff_step_seconds": FF_STEP_SECONDS,
        "captures_count": len(captures),
        "captures": captures,
    }
    with open(OUTPUT_JSON, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"  ✓ {len(captures)} captures → {OUTPUT_JSON}")

    # Statistiques
    dists = [c["dist_to_fire_m"] for c in captures if c["dist_to_fire_m"] is not None]
    if dists:
        print(f"\n  Statistiques distance au feu :")
        print(f"    Min : {min(dists):.1f} m")
        print(f"    Max : {max(dists):.1f} m")
        print(f"    Moy : {sum(dists) / len(dists):.1f} m")

    # Visualisation
    plot_results(captures)

    # === Nettoyage ===
    print("\n--- Nettoyage ---")
    stop_forefire(ff_proc)
    px4_proc.terminate()
    gz_proc.terminate()
    time.sleep(3)
    subprocess.run(["pkill", "-9", "-f", "bin/px4"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "gz sim"], capture_output=True)
    print("  ✓ Simulation terminée")


if __name__ == "__main__":
    asyncio.run(run())
