"""GSIE-Ignis — Test 4 : Vol Return-to-Home (RTH) avec tuning PX4.

Le drone décolle en offboard (velocity climb), se déplace à 100 m au Nord
en offboard (position NED setpoint), active le mode RTL de PX4,
retourne au point de décollage et atterrit automatiquement.

Utilise position_velocity_ned() pour le monitoring (local NED frame,
mise à jour pleine vitesse) au lieu du GPS lat/lon (lag important).
"""
import asyncio
import math
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw, PositionNedYaw
from mavsdk.action import ActionError


async def log_flight_mode(drone: System, duration: float) -> None:
    start = asyncio.get_event_loop().time()
    async for mode in drone.telemetry.flight_mode():
        if asyncio.get_event_loop().time() - start > duration:
            break
        print(f"  [mode] {mode}")
        await asyncio.sleep(5)


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


async def try_set_param_int(drone: System, name: str, value: int) -> None:
    try:
        await drone.param.set_param_int(name, value)
    except Exception:
        print(f"  (skip {name})")


async def try_set_param_float(drone: System, name: str, value: float) -> None:
    try:
        await drone.param.set_param_float(name, value)
    except Exception:
        print(f"  (skip {name})")


async def configure_sitl(drone: System) -> None:
    print("Configuration parametres...")
    await try_set_param_int(drone, "COM_RCL_EXCEPT", 7)
    await try_set_param_int(drone, "NAV_DLL_ACT", 0)
    await try_set_param_int(drone, "NAV_RCL_ACT", 0)
    await try_set_param_float(drone, "MPC_THR_HOVER", 0.5)
    await try_set_param_float(drone, "MPC_Z_VEL_MAX_UP", 10.0)
    await try_set_param_float(drone, "MPC_XY_VEL_MAX", 15.0)
    await try_set_param_float(drone, "MPC_XY_CRUISE", 10.0)
    await try_set_param_float(drone, "MPC_TILTMAX_AIR", 45.0)
    await try_set_param_float(drone, "RTL_RETURN_ALT", 20.0)
    await try_set_param_float(drone, "MPC_Z_VEL_MAX_DN", 5.0)
    await try_set_param_float(drone, "MPC_LAND_SPEED", 2.5)
    await try_set_param_float(drone, "MPC_LAND_ALT1", 10.0)
    await try_set_param_float(drone, "MPC_LAND_ALT2", 5.0)
    await try_set_param_int(drone, "COM_DISARM_LAND", 5)
    print("✓ Params configures")
    await asyncio.sleep(3)


async def get_ned_pos(drone: System) -> tuple:
    """Retourne (north, east, down, vn, ve, vd) depuis position_velocity_ned."""
    async for pv in drone.telemetry.position_velocity_ned():
        return (pv.position.north_m, pv.position.east_m, pv.position.down_m,
                pv.velocity.north_m_s, pv.velocity.east_m_s, pv.velocity.down_m_s)


async def takeoff_and_move(drone: System) -> float:
    """Décollage + déplacement 100m Nord en offboard (position NED)."""
    print("Preparation offboard (climb 5 m/s)...")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -5.0, 0.0))

    print("Armement...")
    await drone.action.arm()
    print("✓ Drone arme")

    print("Activation offboard...")
    try:
        await drone.offboard.start()
        print("✓ Offboard actif")
    except OffboardError as e:
        print(f"✗ Erreur offboard: {e}")
        await drone.action.disarm()
        raise

    # Montée
    print("Phase 1: Montee (climb 8 s)...")
    await asyncio.sleep(8)
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    # Lire position NED actuelle
    n, e, d, vn, ve, vd = await get_ned_pos(drone)
    alt = -d
    print(f"  Position NED: N={n:.1f}, E={e:.1f}, D={d:.1f} (alt={alt:.1f}m)")

    # Phase 2: déplacement 100m Nord via position NED
    target_n = n + 100.0  # 100m au Nord depuis position actuelle
    target_d = d           # maintenir altitude

    print(f"\nPhase 2: Deplacement NED (N={target_n:.1f}m, E={e:.1f}m, D={target_d:.1f}m)...")
    await drone.offboard.set_position_ned(PositionNedYaw(target_n, e, target_d, 0.0))

    start = asyncio.get_event_loop().time()
    async for pv in drone.telemetry.position_velocity_ned():
        elapsed = asyncio.get_event_loop().time() - start
        dist = math.sqrt(pv.position.north_m**2 + pv.position.east_m**2)
        speed = math.sqrt(pv.velocity.north_m_s**2 + pv.velocity.east_m_s**2)
        print(f"  [{elapsed:5.1f}s] N={pv.position.north_m:.1f}m, E={pv.position.east_m:.1f}m, "
              f"alt={-pv.position.down_m:.1f}m, dist={dist:.1f}m, speed={speed:.2f}m/s")

        if pv.position.north_m > target_n - 10:
            print(f"✓ Position atteinte: N={pv.position.north_m:.1f}m")
            break
        if elapsed > 60:
            print(f"⚠ Timeout: N={pv.position.north_m:.1f}m, speed={speed:.2f}m/s")
            break
        await asyncio.sleep(2)

    # Stabiliser
    print("Stabilisation...")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    return alt


async def activate_rth(drone: System) -> None:
    print("\n=== Activation RTL ===")

    await drone.offboard.stop()
    await asyncio.sleep(1)

    try:
        await drone.action.return_to_launch()
        print("✓ RTL active")
    except ActionError as e:
        print(f"✗ Erreur RTL: {e}")
        return

    mode_task = asyncio.create_task(log_flight_mode(drone, 240))

    print("Surveillance (240 s max):")
    start = asyncio.get_event_loop().time()
    landed = False
    last_log = 0
    returning = True

    async for pv in drone.telemetry.position_velocity_ned():
        elapsed = asyncio.get_event_loop().time() - start
        dist = math.sqrt(pv.position.north_m**2 + pv.position.east_m**2)
        alt = -pv.position.down_m
        speed = math.sqrt(pv.velocity.north_m_s**2 + pv.velocity.east_m_s**2)

        if elapsed - last_log >= 5 or alt < 1:
            phase = "retour" if alt > 20 else "descente" if alt > 5 else "atterrissage" if alt > 0.5 else "sol"
            print(f"  [{elapsed:5.1f}s] N={pv.position.north_m:.1f}m, alt={alt:.1f}m, "
                  f"dist={dist:.1f}m, speed={speed:.2f}m/s ({phase})")
            last_log = elapsed

        # Si le drone est proche du home (< 15m) et n'est pas en train d'atterrir,
        # forcer l'atterrissage
        if dist < 15 and alt > 5 and returning:
            print(f"  Proche du home (dist={dist:.1f}m) — atterrissage force")
            await drone.action.land()
            returning = False

        if alt < 0.3 and elapsed > 10:
            print(f"✓ Drone atterri (alt={alt:.2f}m)")
            landed = True
            break

        if elapsed > 240:
            print(f"⚠ Timeout (N={pv.position.north_m:.1f}m, alt={alt:.1f}m, dist={dist:.1f}m)")
            break

        await asyncio.sleep(0.5)

    mode_task.cancel()

    if not landed:
        print("Atterrissage manuel...")
        await drone.action.land()
        await asyncio.sleep(20)

    async for armed in drone.telemetry.armed():
        if not armed:
            print("✓ Drone desarme")
            break
        await asyncio.sleep(1)

    print("✓ Test RTH termine")


async def run() -> None:
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    print("Connexion (port 14540)...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("✓ Connecte")
            break

    await wait_gps_home(drone)
    await configure_sitl(drone)
    await takeoff_and_move(drone)
    await activate_rth(drone)


if __name__ == "__main__":
    asyncio.run(run())
