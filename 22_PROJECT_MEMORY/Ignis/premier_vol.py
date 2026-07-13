"""Ignis — Premier vol drone simulé (PX4 SITL + MAVSDK).

Utilise un setpoint de velocite (climb rate 5 m/s) en offboard pour forcer
la montee, puis transition vers position hold a 30m.
"""
import asyncio
from mavsdk import System
from mavsdk.offboard import (
    OffboardError,
    VelocityNedYaw,
    PositionNedYaw,
)


async def run() -> None:
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    print("Connexion au drone simulé (port 14540)...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("✓ Drone connecté")
            break

    # Attendre GPS
    print("Attente GPS fix...")
    async for gps in drone.telemetry.gps_info():
        if gps.num_satellites >= 6:
            print(f"✓ GPS fix: {gps.num_satellites} satellites")
            break
        await asyncio.sleep(1)

    # Attendre position home
    print("Attente position home...")
    async for health in drone.telemetry.health():
        if health.is_home_position_ok and health.is_global_position_ok:
            print("✓ Position home OK")
            break
        await asyncio.sleep(1)

    # Params SITL
    print("Configuration parametres SITL...")
    await drone.param.set_param_int("COM_RCL_EXCEPT", 7)
    await drone.param.set_param_int("NAV_DLL_ACT", 0)
    await drone.param.set_param_int("NAV_RCL_ACT", 0)
    # Reduire hover thrust pour forcer plus de poussee au decollage
    await drone.param.set_param_float("MPC_THR_HOVER", 0.5)
    # Augmenter la vitesse de montee max
    await drone.param.set_param_float("MPC_Z_VEL_MAX_UP", 10.0)
    # Desactiver la limitation de poussee au sol
    await drone.param.set_param_float("MPC_THR_MIN", 0.2)
    print("✓ Params SITL configures")
    await asyncio.sleep(3)

    # Preparer offboard avec setpoint de velocite initiale
    # NED frame: Z negatif = montee
    print("Preparation setpoint offboard (velocite montee 5 m/s)...")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -5.0, 0.0))

    # Armer
    print("Armement...")
    await drone.action.arm()
    print("✓ Drone arme")

    # Activer offboard
    print("Activation mode offboard...")
    try:
        await drone.offboard.start()
        print("✓ Offboard actif")
    except OffboardError as e:
        print(f"✗ Erreur offboard: {e}")
        await drone.action.disarm()
        return

    # Phase 1: monter avec velocite pendant 10s
    print("Phase 1: Montee a 5 m/s pendant 10s...")
    start = asyncio.get_event_loop().time()
    async for pos in drone.telemetry.position():
        elapsed = asyncio.get_event_loop().time() - start
        print(f"  [{elapsed:5.1f}s] alt={pos.relative_altitude_m:.1f} m")
        if elapsed > 10:
            break
        await asyncio.sleep(2)

    # Phase 2: maintenir position a altitude actuelle
    alt_reached = 0.0
    async for pos in drone.telemetry.position():
        alt_reached = pos.relative_altitude_m
        break

    print(f"Phase 2: Maintien position a {alt_reached:.1f}m pendant 15s...")
    # Convertir alt en NED Z (negatif)
    target_z = -max(alt_reached, 5.0)
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, target_z, 0.0))

    start = asyncio.get_event_loop().time()
    async for pos in drone.telemetry.position():
        elapsed = asyncio.get_event_loop().time() - start
        print(f"  [{elapsed:5.1f}s] alt={pos.relative_altitude_m:.1f} m")
        if elapsed > 15:
            break
        await asyncio.sleep(2)

    # Atterrissage
    print("Arret offboard + atterrissage...")
    await drone.offboard.stop()
    await drone.action.land()
    await asyncio.sleep(15)
    print("✓ Vol termine")


if __name__ == "__main__":
    asyncio.run(run())
