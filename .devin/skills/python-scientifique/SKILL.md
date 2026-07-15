---
name: python-scientifique
description: Stack Python scientifique pour GSIE — numpy, scipy, pandas, geopandas, sklearn, mypy
triggers:
  - user
  - model
---

# Python Scientifique — Conventions GSIE

## Stack validée (Phase 4)

```toml
# pyproject.toml dependencies
python = ">=3.11"
numpy = ">=1.26"
scipy = ">=1.12"
pandas = ">=2.1"
geopandas = ">=0.14"
scikit-learn = ">=1.4"
pydantic = ">=2.5"
fastapi = ">=0.110"
asyncpg = ">=0.29"
pytest = ">=8.0"
mypy = ">=1.8"
ruff = ">=0.3"
```

## Règles de typage (mypy strict)

```python
# JAMAIS de paramètre non typé en signature publique
def compute_crown_coverage(
    tree_points: np.ndarray,
    resolution: float = 1.0
) -> tuple[float, np.ndarray]:  # ✓

def compute(data, res):  # ✗ — mypy rejettera
    ...

# Utiliser TypeAlias pour les types complexes
from typing import TypeAlias
ForestMatrix: TypeAlias = np.ndarray  # shape: (n_trees, n_features)
```

## Traitement géospatial

```python
import geopandas as gpd
from shapely.geometry import Point, Polygon

# Toujours spécifier le CRS
gdf = gpd.GeoDataFrame(
    data,
    geometry=gpd.points_from_xy(lon, lat),
    crs="EPSG:4326"
)

# Reprojection systématique avant calculs de distance
gdf_lambert = gdf.to_crs("EPSG:2154")  # Lambert 93 pour la France
area_ha = gdf_lambert.geometry.area / 10_000
```

## Algorithmes forestiers (moteurs GSIE)

Les algorithmes documentés sont dans `GSIE/ALGORITHMS/`. Toujours :
1. Lire la fiche algorithme avant d'implémenter
2. Citer la source scientifique dans un docstring
3. Tester avec des valeurs de référence issues de la littérature

```python
def compute_basal_area(diameter_cm: float) -> float:
    """Surface terrière en m² à partir du diamètre à 1.30m.
    
    Formule: g = π/4 × d²
    Source: ONF, Guide de cubages, 2019.
    
    Args:
        diameter_cm: Diamètre à hauteur de poitrine (cm)
    
    Returns:
        Surface terrière (m²)
    """
    return math.pi / 4 * (diameter_cm / 100) ** 2
```

## Performance

- Vectoriser avec numpy avant de boucler
- `@lru_cache` pour les calculs déterministes répétés
- Traitement batch avec pandas plutôt que row-by-row
- Profiler avec `cProfile` avant d'optimiser

## Qualité

- `ruff check` + `ruff format` avant commit
- `mypy --strict` sur tous les modules moteurs
- Coverage cible : 80% sur la logique métier
