#!/usr/bin/env python3
"""Génère la visualisation matplotlib depuis le JSON de captures."""
import json
import sys

def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 else "/mnt/a/GSIE/22_PROJECT_MEMORY/GSIE-Ignis/captures_forefire_temps_reel.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "/mnt/a/GSIE/22_PROJECT_MEMORY/GSIE-Ignis/trajet_forefire_temps_reel.png"

    with open(json_path) as f:
        data = json.load(f)

    captures = data["captures"]
    home_lat = data["home_lat"]
    home_lon = data["home_lon"]

    import math
    def latlon_to_local_m(lat, lon):
        cos_lat = math.cos(math.radians(home_lat))
        north = (lat - home_lat) * 111320.0
        east = (lon - home_lon) * 111320.0 * cos_lat
        return north, east

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # Trajectoire drone
    drone_n = [c["ned_n"] for c in captures]
    drone_e = [c["ned_e"] for c in captures]
    colors_drone = range(len(captures))

    ax.plot(drone_e, drone_n, "b-", linewidth=1.5, alpha=0.5, label="Trajectoire drone")
    scatter = ax.scatter(drone_e, drone_n, c=colors_drone, cmap="cool", s=40, zorder=5)
    plt.colorbar(scatter, ax=ax, label="Capture #")

    # Fronts de feu (4 snapshots)
    n_captures = len(captures)
    snapshots_to_show = [0, n_captures // 3, n_captures * 2 // 3, n_captures - 1]
    snapshots_to_show = list(set([i for i in snapshots_to_show if 0 <= i < n_captures]))
    snapshots_to_show.sort()

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
                alpha=alpha, label=f"Front feu t={c['ff_time_s']}s ({len(fire_pts)} pts)")

    # Marquer le home
    ax.plot(0, 0, "k^", markersize=15, label="Home (décollage)", zorder=10)

    # Annotations distance au feu
    for c in captures:
        dist = c.get("dist_to_fire_m")
        if dist is not None and dist < 100:
            ax.annotate(f"{dist:.0f}m",
                        (c["ned_e"], c["ned_n"]),
                        fontsize=7, color="red",
                        xytext=(5, 5), textcoords="offset points")

    ax.set_xlabel("Est (m)", fontsize=12)
    ax.set_ylabel("Nord (m)", fontsize=12)
    ax.set_title(f"GSIE-Ignis — Surveillance feu ForeFire (temps réel)\n"
                 f"{n_captures} captures, feu: {captures[0]['ff_time_s']}s → {captures[-1]['ff_time_s']}s",
                 fontsize=14)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"✓ Visualisation : {output_path}")

if __name__ == "__main__":
    main()
