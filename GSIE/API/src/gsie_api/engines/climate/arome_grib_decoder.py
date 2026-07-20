"""Décodage réel de fichiers GRIB2 AROME (température 2 m) via cfgrib/eccodes.

Vérifié manuellement le 2026-07-18 : un GRIB2 réel (zone Bordeaux,
0.01°, 60 Ko) se décode en un `xarray.Dataset` avec une variable `t2m`
(Kelvin) sur une grille lat/lon réelle. `cfgrib` exige un chemin de
fichier (pas de bytes en mémoire) — écriture dans un fichier temporaire,
nettoyé après lecture, y compris le fichier d'index `.idx` qu'eccodes
crée à côté (nom réel observé : `<chemin>.<hash>.idx`).
"""

from __future__ import annotations

import contextlib
import glob
import os
import tempfile

import cfgrib


class AromeGribDecodeError(Exception):
    """Erreur de décodage d'un GRIB2 AROME (fichier corrompu, variable absente)."""


def extract_nearest_temperature_celsius(
    grib_bytes: bytes, latitude: float, longitude: float
) -> float:
    """Décode un GRIB2 réel et retourne la température au point de grille le plus proche.

    Raises:
        AromeGribDecodeError: si le fichier n'est pas un GRIB2
            exploitable ou ne contient pas la variable attendue —
            jamais une température approximée (ADR-007).
    """
    with tempfile.NamedTemporaryFile(suffix=".grib2", delete=False) as tmp_file:
        tmp_file.write(grib_bytes)
        tmp_path = tmp_file.name

    try:
        try:
            datasets = cfgrib.open_datasets(tmp_path)
        except Exception as exc:  # cfgrib lève des exceptions eccodes non typées finement
            raise AromeGribDecodeError(f"GRIB2 AROME illisible : {exc}") from exc

        if not datasets or "t2m" not in datasets[0]:
            raise AromeGribDecodeError(
                "GRIB2 AROME décodé mais variable t2m absente — réponse inattendue"
            )

        point = datasets[0].sel(latitude=latitude, longitude=longitude, method="nearest")
        kelvin = float(point["t2m"].values)
        return kelvin - 273.15
    finally:
        # cfgrib/eccodes peut garder un descripteur ouvert sur Windows
        # après un échec de parsing (fichier invalide) — la suppression
        # ne doit jamais masquer l'erreur de décodage déjà levée ci-dessus.
        for path in [tmp_path, *glob.glob(tmp_path + "*.idx")]:
            with contextlib.suppress(OSError):
                os.remove(path)
