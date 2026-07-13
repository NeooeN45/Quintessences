"""GSIE-Ignis — Visualisation 3D des trajectoires + fronts de feu ForeFire.

Génère un graphique 3D matplotlib montrant :
1. La trajectoire du drone en 3D (x, y, altitude)
2. Le front de feu ForeFire projeté au sol
3. Les distances drone-feu calculées
4. Une vue de dessus avec heatmap de distance

Usage :
  python plot_3d.py [captures.json] [output.png]
"""
import json
import sys
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D


def load_data(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def latlon_to_xy(lat: float, lon: float, ref_lat: float, ref_lon: float):
    """Convertit lat/lon en mètres relatifs (Nord, Est)."""
    cos_lat = math.cos(math.radians(ref_lat))
    north = (lat - ref_lat) * 111320.0
    east = (lon - ref_lon) * 111320.0 * cos_lat
    return north, east


def plot_3d_trajectory(data: dict, output_path: str) -> None:
    captures = data["captures"]
    fire_points = data.get("fire_front", [])

    # Référence : premier point de capture
    if captures:
        ref_lat = captures[0]["lat"]
        ref_lon = captures[0]["lon"]
    else:
        ref_lat = 47.397971
        ref_lon = 8.546164

    # Convertir captures en mètres
    drone_x = []  # Est (m)
    drone_y = []  # Nord (m)
    drone_z = []  # Altitude (m)
    dists = []
    times = []

    for c in captures:
        north, east = latlon_to_xy(c["lat"], c["lon"], ref_lat, ref_lon)
        drone_x.append(east)
        drone_y.append(north)
        drone_z.append(c["alt_m"])
        dists.append(c.get("dist_to_fire_m") or 0)
        times.append(c["elapsed_s"])

    # Convertir front de feu en mètres
    fire_x = []
    fire_y = []
    for fp in fire_points:
        north, east = latlon_to_xy(fp["lat"], fp["lon"], ref_lat, ref_lon)
        fire_x.append(east)
        fire_y.append(north)

    fig = plt.figure(figsize=(18, 14))
    fig.suptitle(
        f"GSIE-Ignis — {data['mission']}\n"
        f"{data['date'][:19]} | {data['captures_count']} captures | "
        f"{data.get('fire_points_count', 0)} points feu",
        fontsize=14, fontweight="bold",
    )

    # === 1. Vue 3D : trajectoire drone + front de feu ===
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")

    # Trajectoire drone
    if drone_x:
        ax1.plot(drone_x, drone_y, drone_z, "b-o", markersize=4,
                 label="Trajectoire drone", zorder=5)
        # Points colorés par distance au feu
        scatter = ax1.scatter(drone_x, drone_y, drone_z, c=dists,
                              cmap="RdYrGn_r", s=50, zorder=6,
                              label="Captures (couleur = distance au feu)")

    # Front de feu au sol (z=0)
    if fire_x:
        ax1.plot(fire_x, fire_y, 0, "r-", linewidth=2, label="Front de feu")
        ax1.scatter(fire_x, fire_y, 0, c="red", s=20, zorder=4)

    ax1.set_xlabel("Est (m)")
    ax1.set_ylabel("Nord (m)")
    ax1.set_zlabel("Altitude (m)")
    ax1.set_title("Vue 3D — Trajectoire drone + front de feu")
    ax1.legend(loc="upper left", fontsize=8)

    # === 2. Vue de dessus : trajectoire + feu + heatmap distance ===
    ax2 = fig.add_subplot(2, 2, 2)

    if fire_x:
        ax2.fill(fire_x, fire_y, color="red", alpha=0.3, label="Zone de feu")
        ax2.plot(fire_x, fire_y, "r-", linewidth=2)

    if drone_x:
        scatter2 = ax2.scatter(drone_x, drone_y, c=dists,
                               cmap="RdYrGn_r", s=60, edgecolors="black",
                               linewidth=0.5, zorder=5)
        ax2.plot(drone_x, drone_y, "k--", alpha=0.3)
        cbar = plt.colorbar(scatter2, ax=ax2, label="Distance au feu (m)")

    ax2.set_xlabel("Est (m)")
    ax2.set_ylabel("Nord (m)")
    ax2.set_title("Vue de dessus — Distance drone ↔ feu")
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect("equal")
    ax2.legend(loc="upper left", fontsize=8)

    # === 3. Distance au feu vs temps ===
    ax3 = fig.add_subplot(2, 2, 3)
    if times and dists:
        ax3.plot(times, dists, "b-o", markersize=4)
        ax3.axhline(y=50, color="orange", linestyle="--", alpha=0.5,
                    label="Zone de sécurité (50 m)")
        ax3.axhline(y=100, color="red", linestyle="--", alpha=0.5,
                    label="Zone critique (100 m)")
        ax3.fill_between(times, 0, 50, color="red", alpha=0.1)
        ax3.fill_between(times, 50, 100, color="orange", alpha=0.1)
        ax3.set_xlabel("Temps (s)")
        ax3.set_ylabel("Distance au feu (m)")
        ax3.set_title("Distance drone ↔ feu vs temps")
        ax3.legend()
        ax3.grid(True, alpha=0.3)

    # === 4. Profil altimétrique ===
    ax4 = fig.add_subplot(2, 2, 4)
    if times and drone_z:
        ax4.plot(times, drone_z, "g-o", markersize=4)
        ax4.axhline(y=data.get("altitude_m", 40), color="r", linestyle="--",
                    label=f"Altitude cible: {data.get('altitude_m', 40)} m")
        ax4.set_xlabel("Temps (s)")
        ax4.set_ylabel("Altitude (m)")
        ax4.set_title("Profil altimétrique")
        ax4.legend()
        ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Visualisation 3D sauvegardee: {output_path}")


if __name__ == "__main__":
    input_path = sys.argv[1] if len(sys.argv) > 1 else \
        "/mnt/a/GSIE/22_PROJECT_MEMORY/GSIE-Ignis/captures_forefire_integration.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else \
        "/mnt/a/GSIE/22_PROJECT_MEMORY/GSIE-Ignis/visualisation_3d.png"

    data = load_data(input_path)
    plot_3d_trajectory(data, output_path)
