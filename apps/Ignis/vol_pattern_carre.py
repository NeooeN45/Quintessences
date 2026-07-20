"""Ignis — Test 3 : Vol pattern carré (surveillance zone).

Le drone décolle, trace un carré de 200 m de côté à 50 m d'altitude en
utilisant des setpoints de vélocité pour un vol plus fluide, puis atterrit.
Simule un pattern de surveillance aérienne pour détecter des départs de feu.
"""
import asyncio
from mavsdk import System
from mavsdk.offboard import (
    OffboardError,
    VelocityNedYaw,
)


# Pattern carré : 4 côtés de 200 m à 50 m d'altitude
# Vitesse de croisière : 8 m/s
SIDE_LENGTH = 200.0  # m
CRUISE_SPEED = 8.0   # m/s
ALTITUDE = 50.0      # m
CLIMB_RATE = 5.0     # m/s


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
    await drone.param.set_param_float("MPC_XY_VEL_MAX", 15.0)
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

    print(f"Montee vers {ALTITUDE} m...")
    start = asyncio.get_event_loop().time()
    async for pos in drone.telemetry.position():
        elapsed = asyncio.get_event_loop().time() - start
        alt = pos.relative_altitude_m
        print(f"  [{elapsed:5.1f}s] alt={alt:.1f} m")
        if alt >= ALTITUDE - 2.0:
            print(f"✓ Altitude atteinte ({alt:.1f} m)")
            break
        if elapsed > 25:
            print(f"⚠ Timeout, alt={alt:.1f} m (continue)")
            break
        await asyncio.sleep(2)


async def fly_square_pattern(drone: System) -> None:
    """Trace un carré en utilisant des setpoints de vélocité NED."""
    # 4 côtés : Nord, Est, Sud, Ouest
    sides = [
        ("Nord", VelocityNedYaw(CRUISE_SPEED, 0.0, 0.0, 0.0)),
        ("Est", VelocityNedYaw(0.0, CRUISE_SPEED, 0.0, 90.0)),
        ("Sud", VelocityNedYaw(-CRUISE_SPEED, 0.0, 0.0, 180.0)),
        ("Ouest", VelocityNedYaw(0.0, -CRUISE_SPEED, 0.0, 270.0)),
    ]

    side_duration = SIDE_LENGTH / CRUISE_SPEED  # 25 s par côté

    for side_name, vel_cmd in sides:
        print(f"\nCote: {side_name} ({SIDE_LENGTH} m a {CRUISE_SPEED} m/s)")
        await drone.offboard.set_velocity_ned(vel_cmd)

        start = asyncio.get_event_loop().time()
        async for pos in drone.telemetry.position():
            elapsed = asyncio.get_event_loop().time() - start
            alt = pos.relative_altitude_m
            print(f"  [{elapsed:5.1f}s] alt={alt:.1f} m")
            if elapsed > side_duration:
                print(f"  ✓ Cote {side_name} complete")
                break
            await asyncio.sleep(5)

    # Stabiliser au centre
    print("\nStabilisation au centre...")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)


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
    await fly_square_pattern(drone)
    await land(drone)


if __name__ == "__main__":
    asyncio.run(run())
