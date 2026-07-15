"""Module de seeding — alimentation de la base de connaissances.

Responsabilité : insérer les données de référence (taxonomie botanique,
écosystèmes, connaissances) dans PostgreSQL.

Utilisation :
    python -m gsie_api.seeds.run_seeds  # tous les seeds
    python -m gsie_api.seeds.run_seeds --botanical  # seulement botanique
    python -m gsie_api.seeds.run_seeds --ecosystem  # seulement écosystèmes

Les seeds sont idempotents : ils utilisent INSERT ... ON CONFLICT DO NOTHING.
Aucune donnée n'est écrasée si elle existe déjà.
"""

from __future__ import annotations
