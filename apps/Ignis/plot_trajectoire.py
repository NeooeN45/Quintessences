"""Ignis — Visualisation des trajectoires de vol.

Génère un graphique matplotlib montrant la trajectoire GPS du drone
à partir des captures de surveillance. Utile pour valider visuellement
les patterns de vol.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Headless
import matplotlib.pyplot as plt
import numpy as np


def load_captures(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def plot_trajectory(data: dict, output_path: str) -> None:
    captures = data["captures"]

    # Extraire les coordonnées
    lats = [c["lat"] for c in captures]
    lons = [c["lon"] for c in captures]
    alts = [c["alt_m"] for c in captures]
    lines = [c["line"] for c in captures]
    times = [c["elapsed_s"] for c in captures]

    # Convertir en mètres relatifs (approximation)
    # 1 degré lat ≈ 111320 m, 1 degré lon ≈ 111320 * cos(lat) m
    lat0 = lats[0]
    lon0 = lons[0]
    cos_lat = np.cos(np.radians(lat0))
    x = [(lon - lon0) * 111320 * cos_lat for lon in lons]  # Est (m)
    y = [(lat - lat0) * 111320 for lat in lats]             # Nord (m)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"Ignis — {data['mission']}\n"
        f"{data['date'][:19]} | {data['captures_count']} captures | "
        f"{data['grid_lines']} lignes × {data['line_length_m']} m",
        fontsize=12,
    )

    # 1. Vue de dessus (plan XY)
    ax1 = axes[0, 0]
    colors = plt.cm.viridis(np.linspace(0, 1, max(lines) + 1))
    for line_num in sorted(set(lines)):
        idx = [i for i, l in enumerate(lines) if l == line_num]
        ax1.scatter(
            [x[i] for i in idx],
            [y[i] for i in idx],
            c=[colors[line_num]],
            s=80,
            label=f"Ligne {line_num}",
            zorder=3,
        )
    ax1.plot(x, y, "k--", alpha=0.3, zorder=1)
    ax1.set_xlabel("Est (m)")
    ax1.set_ylabel("Nord (m)")
    ax1.set_title("Trajectoire vue de dessus")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect("equal")

    # 2. Profil altimétrique
    ax2 = axes[0, 1]
    ax2.plot(times, alts, "b-o", markersize=4)
    ax2.axhline(y=data["altitude_m"], color="r", linestyle="--",
                label=f"Altitude cible: {data['altitude_m']} m")
    ax2.set_xlabel("Temps (s)")
    ax2.set_ylabel("Altitude relative (m)")
    ax2.set_title("Profil altimétrique")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Position Nord vs temps
    ax3 = axes[1, 0]
    ax3.plot(times, y, "g-o", markersize=4, label="Nord")
    ax3.plot(times, x, "b-s", markersize=4, label="Est")
    ax3.set_xlabel("Temps (s)")
    ax3.set_ylabel("Position relative (m)")
    ax3.set_title("Position N/E vs temps")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Tableau résumé
    ax4 = axes[1, 1]
    ax4.axis("off")
    table_data = [
        ["Captures", str(data["captures_count"])],
        ["Lignes", str(data["grid_lines"])],
        ["Longueur ligne", f"{data['line_length_m']} m"],
        ["Espacement", f"{data['grid_spacing_m']} m"],
        ["Altitude cible", f"{data['altitude_m']} m"],
        ["Altitude min", f"{min(alts):.1f} m"],
        ["Altitude max", f"{max(alts):.1f} m"],
        ["Altitude moy", f"{np.mean(alts):.1f} m"],
        ["Durée totale", f"{max(times):.1f} s"],
        ["Déplacement Nord", f"{max(y) - min(y):.1f} m"],
        ["Déplacement Est", f"{max(x) - min(x):.1f} m"],
    ]
    table = ax4.table(
        cellText=table_data,
        colLabels=["Paramètre", "Valeur"],
        cellLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    ax4.set_title("Résumé de la mission")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Trajectoire sauvegardee: {output_path}")


if __name__ == "__main__":
    input_path = sys.argv[1] if len(sys.argv) > 1 else \
        "/mnt/a/GSIE/apps/Ignis/captures_surveillance.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else \
        "/mnt/a/GSIE/apps/Ignis/trajectoire_surveillance.png"

    data = load_captures(input_path)
    plot_trajectory(data, output_path)
