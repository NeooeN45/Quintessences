"""GSIE-Ignis — Test controle manuel direct (PX4 SITL + MAVSDK).

Teste si les sorties actuateurs fonctionnent en envoyant des commandes
manuelles directes (stick) au lieu de position setpoints.
"""
import asyncio
from mavsdk import System


async def run() -> None:
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    print("Connexion...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("✓ Connecte")
            break

    # Attendre GPS + home
    print("Attente GPS...")
    async for gps in drone.telemetry.gps_info():
        if gps.num_satellites >= 6:
            print(f"✓ GPS: {gps.num_satellites} sats")
            break
        await asyncio.sleep(1)

    print("Attente home...")
    async for health in drone.telemetry.health():
        if health.is_home_position_ok and health.is_global_position_ok:
            print("✓ Home OK")
            break
        await asyncio.sleep(1)

    # Params
    print("Params SITL...")
    await drone.param.set_param_int("COM_RCL_EXCEPT", 7)
    await drone.param.set_param_int("NAV_DLL_ACT", 0)
    await drone.param.set_param_int("NAV_RCL_ACT", 0)
    await asyncio.sleep(3)

    # Armer
    print("Armement...")
    await drone.action.arm()
    print("✓ Arme")

    # Envoyer du thrust manuel direct (z = 0.8 = 80% throttle)
    print("Envoi commande manuelle (throttle 80%)...")
    for i in range(50):
        # manual_control: x=roll, y=pitch, z=throttle (0-1), r=yaw
        await drone.manual_control.set_manual_control_input(
            x=0.0, y=0.0, z=0.8, r=0.0
        )
        await asyncio.sleep(0.1)

    # Lire altitude
    print("Altitude apres 5s de throttle:")
    async for pos in drone.telemetry.position():
        print(f"  alt={pos.relative_altitude_m:.1f} m")
        break

    # Atterrir
    print("Atterrissage...")
    await drone.action.land()
    await asyncio.sleep(10)
    print("✓ Test termine")


if __name__ == "__main__":
    asyncio.run(run())
