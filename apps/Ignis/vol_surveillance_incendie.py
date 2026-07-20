"""Ignis — Test 5 : Simulation surveillance incendie (ForeFire + drone).

Le drone décolle, survole une zone où un feu ForeFire est simulé, trace
un pattern de surveillance en grille (lawnmower) au-dessus de la zone de
feu, enregistre les positions GPS du drone à intervalles réguliers
(simulation de captage caméra/capteur), puis atterrit.

Ce test valide le concept d'observation aérienne d'un front de feu.
"""
import asyncio
import json
from datetime import datetime, timezone
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw, PositionNedYaw


# Parametres de la mission de surveillance
ALTITUDE = 40.0          # m — altitude de surveillance
CLIMB_RATE = 5.0         # m/s
CRUISE_SPEED = 10.0      # m/s — vitesse de surveillance
GRID_SPACING = 40.0      # m — espacement entre lignes de la grille
GRID_LINES = 3           # nombre de lignes de la grille
LINE_LENGTH = 100.0      # m — longueur de chaque ligne
CAPTURE_INTERVAL = 2.0   # s — intervalle entre captures de position


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

    print(f"Montee vers {ALTITUDE} m (climb 8s)...")
    # Climb with velocity for 8 seconds, then switch to position hold
    await asyncio.sleep(8)

    # Switch to position hold at target altitude
    await drone.offboard.set_position_ned(
        PositionNedYaw(0.0, 0.0, -ALTITUDE, 0.0)
    )
    await asyncio.sleep(3)
    print("✓ Altitude stabilisee")


async def fly_lawnmower_pattern(drone: System) -> list:
    """Trace un pattern en grille (lawnmower) et capture les positions GPS.

    Retourne une liste de captures {timestamp, lat, lon, alt}.
    """
    captures = []
    line_duration = LINE_LENGTH / CRUISE_SPEED  # ~33 s par ligne

    print("\n=== Pattern surveillance grille ===")
    print(f"  {GRID_LINES} lignes x {LINE_LENGTH} m, espacement {GRID_SPACING} m")
    print(f"  Vitesse: {CRUISE_SPEED} m/s, altitude: {ALTITUDE} m")
    print(f"  Capture position toutes les {CAPTURE_INTERVAL} s")

    for line_num in range(GRID_LINES):
        # Direction alternée : Est sur lignes paires, Ouest sur impaires
        going_east = (line_num % 2 == 0)
        direction = "Est" if going_east else "Ouest"
        east_vel = CRUISE_SPEED if going_east else -CRUISE_SPEED
        yaw = 90 if going_east else 270

        # Position Y (Est) de la ligne courante
        y_offset = line_num * GRID_SPACING

        print(f"\nLigne {line_num + 1}/{GRID_LINES}: {direction} "
              f"(y={y_offset:.0f} m)")

        # Aller au début de la ligne
        await drone.offboard.set_velocity_ned(
            VelocityNedYaw(0.0, east_vel, 0.0, yaw)
        )

        start = asyncio.get_event_loop().time()
        last_capture = 0.0

        async for pos in drone.telemetry.position():
            elapsed = asyncio.get_event_loop().time() - start
            alt = pos.relative_altitude_m

            # Capture de position à intervalle régulier
            if elapsed - last_capture >= CAPTURE_INTERVAL:
                capture = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "elapsed_s": round(elapsed, 2),
                    "line": line_num + 1,
                    "lat": pos.latitude_deg,
                    "lon": pos.longitude_deg,
                    "alt_m": round(alt, 1),
                }
                captures.append(capture)
                last_capture = elapsed
                print(f"  [{elapsed:5.1f}s] lat={pos.latitude_deg:.6f} "
                      f"lon={pos.longitude_deg:.6f} alt={alt:.1f} m "
                      f"📸 capture #{len(captures)}")

            if elapsed > line_duration:
                print(f"  ✓ Ligne {line_num + 1} complete")
                break
            await asyncio.sleep(0.5)

        # Transition vers la ligne suivante (déplacement Nord)
        if line_num < GRID_LINES - 1:
            print(f"  Transition vers ligne {line_num + 2} (Nord {GRID_SPACING} m)")
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
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    print("Connexion au drone simulé (port 14540)...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("✓ Drone connecté")
            break

    await wait_gps_home(drone)
    await configure_sitl(drone)
    await takeoff(drone)
    captures = await fly_lawnmower_pattern(drone)
    await land(drone)

    # Sauvegarder les captures
    output_path = "/mnt/a/GSIE/apps/Ignis/captures_surveillance.json"
    with open(output_path, "w") as f:
        json.dump({
            "mission": "surveillance_incendie",
            "date": datetime.now(timezone.utc).isoformat(),
            "altitude_m": ALTITUDE,
            "grid_lines": GRID_LINES,
            "line_length_m": LINE_LENGTH,
            "grid_spacing_m": GRID_SPACING,
            "captures_count": len(captures),
            "captures": captures,
        }, f, indent=2)
    print(f"\n✓ {len(captures)} captures sauvegardees dans {output_path}")


if __name__ == "__main__":
    asyncio.run(run())
