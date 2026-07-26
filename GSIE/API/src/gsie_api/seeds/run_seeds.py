"""Point d'entrée historique des seeds v6.1, volontairement désactivé.

Les jeux de données source restent archivés dans ce paquet pour leur futur
portage vers les resources v6.2. Aucun chemin d'écriture vers les douze tables
legacy supprimées n'est conservé.
"""

from __future__ import annotations

import argparse
import asyncio


async def run_seeds(botanical: bool = True, ecosystem: bool = True) -> None:
    """Refuse l'ancien seed plutôt que d'écrire dans un schéma retiré."""
    del botanical, ecosystem
    raise RuntimeError(
        "seed v6.1 retiré par DEC-000023 : migrer ces données vers les resources "
        "v6.2 avant toute initialisation"
    )


def main() -> None:
    """Expose un refus explicite aux anciens appels CLI."""
    parser = argparse.ArgumentParser(description="Seed v6.1 retiré de la base GSIE")
    parser.add_argument("--botanical-only", action="store_true")
    parser.add_argument("--ecosystem-only", action="store_true")
    args = parser.parse_args()

    botanical = not args.ecosystem_only
    ecosystem = not args.botanical_only
    asyncio.run(run_seeds(botanical=botanical, ecosystem=ecosystem))


if __name__ == "__main__":
    main()
