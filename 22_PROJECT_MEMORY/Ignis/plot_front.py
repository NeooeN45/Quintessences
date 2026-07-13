"""Ignis — Visualisation des contours de front ForeFire.

Usage:
    cd ~/Ignis/forefire/examples/aullene
    python ~/Ignis/scripts/plot_front.py

Lit les fichiers GeoJSON/JSON de contours produits par ForeFire et
génère une image propagation.png avec les contours successifs.
"""
import json
import glob
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def _xy(coords):
    """Extract (x, y) from coords that may be 2D or 3D (x, y, z)."""
    pts = [(c[0], c[1]) for c in coords]
    return zip(*pts)


fig, ax = plt.subplots(figsize=(10, 8))

files = sorted(glob.glob("*.geojson") + glob.glob("output*.json"))
if not files:
    print("Aucun fichier de contour trouve. Verifie la sortie ForeFire.")
    raise SystemExit(1)

cmap = plt.cm.hot_r
n = len(files)
for i, f in enumerate(files):
    with open(f) as fh:
        data = json.load(fh)
    features = data.get("features", [data])
    for feat in features:
        geom = feat.get("geometry", feat)
        gtype = geom.get("type", "")
        color = cmap(i / max(n - 1, 1))
        if gtype == "Polygon":
            for ring in geom["coordinates"]:
                xs, ys = _xy(ring)
                ax.plot(xs, ys, color=color, lw=1.2)
        elif gtype == "LineString":
            xs, ys = _xy(geom["coordinates"])
            ax.plot(xs, ys, color=color, lw=1.2)
        elif gtype == "MultiPolygon":
            for poly in geom["coordinates"]:
                for ring in poly:
                    xs, ys = _xy(ring)
                    ax.plot(xs, ys, color=color, lw=1.2)
        elif gtype == "MultiLineString":
            for line in geom["coordinates"]:
                xs, ys = _xy(line)
                ax.plot(xs, ys, color=color, lw=1.2)

ax.set_title("Propagation du front — contours successifs")
ax.set_aspect("equal")
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
out = Path("propagation.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"→ {out.resolve()} ({len(files)} contours)")
