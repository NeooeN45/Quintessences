"""Test connexion MAVSDK minimale."""
import asyncio
from mavsdk import System


async def run():
    drone = System(port=14540)
    print("Connexion udpin://0.0.0.0:14540...")
    await drone.connect(system_address="udpin://0.0.0.0:14540")

    print("Attente connexion...")
    try:
        async for state in drone.core.connection_state():
            print(f"  is_connected={state.is_connected}")
            if state.is_connected:
                print("✓ Connecte!")
                break
            await asyncio.sleep(1)
    except asyncio.TimeoutError:
        print("✗ Timeout connexion")

    # Lire un paramètre simple
    try:
        print("Lecture param COM_RCL_EXCEPT...")
        val = await drone.param.get_param_int("COM_RCL_EXCEPT")
        print(f"  COM_RCL_EXCEPT = {val}")
    except Exception as e:
        print(f"  Erreur: {e}")

    print("Done")


if __name__ == "__main__":
    asyncio.run(run())
