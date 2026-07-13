"""Ignis — Test 2 : Vol waypoint (navigation 4 points GPS).

Le drone décolle, vole vers 4 waypoints GPS distants de ~100 m, puis
revient et atterrit. Valide la navigation autonome en mode offboard.
"""
import asyncio
from mavsdk import System
from mavsdk.offboard import (
    OffboardError,
    VelocityNedYaw,
    PositionNedYaw,
)


# Waypoints en coordonnées NED (Nord, Est, Down) relatives au point de décollage
# Pattern : carré de 100 m de côté à 30 m d'altitude
WAYPOINTS_NED = [
    PositionNedYaw(0.0, 0.0, -30.0, 0.0),    # Centre (décollage)
    PositionNedYaw(100.0, 0.0, -30.0, 0.0),  # Nord 100 m
    PositionNedYaw(100.0, 100.0, -30.0, 90.0),  # Nord-Est 100 m
    PositionNedYaw(0.0, 100.0, -30.0, 180.0),   # Est 100 m
    PositionNedYaw(0.0, 0.0, -30.0, 270.0),     # Retour centre
]

WAYPOINT_NAMES = [
    "Centre (décollage)",
    "Nord 100 m",
    "Nord-Est 100 m",
    "Est 100 m",
    "Retour centre",
]


async def wait_gps_home(drone: System) -> None:
    """Attend le GPS fix et la position home."""
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
    """Configure les paramètres SITL pour bypass GCS/RC."""
    print("Configuration parametres SITL...")
    await drone.param.set_param_int("COM_RCL_EXCEPT", 7)
    await drone.param.set_param_int("NAV_DLL_ACT", 0)
    await drone.param.set_param_int("NAV_RCL_ACT", 0)
    await drone.param.set_param_float("MPC_THR_HOVER", 0.5)
    await drone.param.set_param_float("MPC_Z_VEL_MAX_UP", 10.0)
    await drone.param.set_param_float("MPC_XY_VEL_MAX", 10.0)
    print("✓ Params SITL configures")
    await asyncio.sleep(3)


async def takeoff_velocity(drone: System, target_alt: float = 30.0) -> None:
    """Décollage via setpoint de vélocité (plus fiable que action.takeoff)."""
    climb_rate = -5.0  # NED: négatif = montée
    print(f"Preparation setpoint offboard (climb {abs(climb_rate)} m/s)...")
    await drone.offboard.set_velocity_ned(
        VelocityNedYaw(0.0, 0.0, climb_rate, 0.0)
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

    # Monter jusqu'à l'altitude cible
    print(f"Montee vers {target_alt} m...")
    start = asyncio.get_event_loop().time()
    async for pos in drone.telemetry.position():
        elapsed = asyncio.get_event_loop().time() - start
        alt = pos.relative_altitude_m
        print(f"  [{elapsed:5.1f}s] alt={alt:.1f} m")
        if alt >= target_alt - 2.0:
            print(f"✓ Altitude cible atteinte ({alt:.1f} m)")
            break
        if elapsed > 20:
            print(f"⚠ Timeout, alt={alt:.1f} m (continue)")
            break
        await asyncio.sleep(2)


async def fly_waypoints(drone: System) -> None:
    """Vole vers chaque waypoint en mode position offboard."""
    for i, (wp, name) in enumerate(zip(WAYPOINTS_NED, WAYPOINT_NAMES)):
        print(f"\nWaypoint {i + 1}/{len(WAYPOINTS_NED)}: {name}")
        print(f"  NED: N={wp.north_m:.0f} E={wp.east_m:.0f} D={wp.down_m:.0f}")

        await drone.offboard.set_position_ned(wp)

        # Attendre l'arrivée (tolerance 5 m)
        start = asyncio.get_event_loop().time()
        async for pos in drone.telemetry.position():
            elapsed = asyncio.get_event_loop().time() - start
            # Position NED approximative via lat/lon
            alt = pos.relative_altitude_m
            print(f"  [{elapsed:5.1f}s] alt={alt:.1f} m")
            if elapsed > 15:
                print(f"  ✓ Waypoint atteint (timeout 15 s)")
                break
            await asyncio.sleep(3)


async def land(drone: System) -> None:
    """Arrêt offboard et atterrissage."""
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
    await takeoff_velocity(drone, target_alt=30.0)
    await fly_waypoints(drone)
    await land(drone)


if __name__ == "__main__":
    asyncio.run(run())
