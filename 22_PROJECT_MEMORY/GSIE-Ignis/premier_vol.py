"""GSIE-Ignis — Premier vol drone simulé (PX4 SITL + MAVSDK).

Usage:
    1. Terminal 1: cd ~/GSIE-Ignis/PX4-Autopilot && HEADLESS=1 make px4_sitl gz_x500
    2. Terminal 2: source ~/GSIE-Ignis/.venv/bin/activate
                   python ~/GSIE-Ignis/scripts/premier_vol.py

Le script arme le drone, décolle à 30m, lit la télémétrie et atterrit.
"""
import asyncio
from mavsdk import System


async def run() -> None:
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    print("Connexion au drone simulé...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("✓ Drone connecté")
            break

    print("Armement + décollage...")
    await drone.action.arm()
    await drone.action.set_takeoff_altitude(30.0)
    await drone.action.takeoff()
    await asyncio.sleep(15)

    print("Position actuelle :")
    async for pos in drone.telemetry.position():
        print(
            f"  lat={pos.latitude_deg:.6f} "
            f"lon={pos.longitude_deg:.6f} "
            f"alt={pos.relative_altitude_m:.1f} m"
        )
        break

    print("Atterrissage...")
    await drone.action.land()
    await asyncio.sleep(10)
    print("✓ Vol terminé")


if __name__ == "__main__":
    asyncio.run(run())
