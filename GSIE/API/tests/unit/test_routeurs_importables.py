"""Test de fumée — importabilité de tous les routeurs de moteurs présents.

Les routeurs ne sont chargés que par les tests d'intégration, qui exigent
Docker (testcontainers + PostgreSQL/PostGIS). Sans ce test, un routeur dont
l'import casse — nom de constante inexistant, import manquant, syntaxe
erronée — survit à ruff, mypy --strict et à toute la suite unitaire : il est
mort à l'arrivée sans qu'aucune porte ne le voie.

Ce test importe explicitement le sous-module ``router`` de chaque paquet
moteur qui en possède un. Il ne valide aucune route, aucun contrat, aucune
réponse — uniquement que le module se charge. C'est la porte la plus basique
possible, et celle qui manquait.

La propriété vérifiée est « tout routeur présent s'importe », et non « tout
moteur a un routeur » : un moteur en cours de construction (Diagnostic avant
R4) n'a pas encore de routeur, et ce n'est pas un défaut. Le test saute
silencieusement les paquets sans ``router.py``.

Contexte : ``router.py`` du Reasoning Engine référençait
``status.HTTP_422_UNPROCESSABLE_CONTENT`` (introduit dans une version de
Starlette postérieure à celle qu'épingle FastAPI 0.115.6). Aucune porte
existante ne l'a vu ; le bug a été découvert au premier lancement des tests
d'intégration.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

import gsie_api.engines as engines
from gsie_api.app import create_app


def _paquets_moteurs_avec_routeur() -> list[str]:
    """Noms des paquets moteurs qui possèdent effectivement un ``router.py``."""
    noms: list[str] = []
    for module in pkgutil.iter_modules(engines.__path__):
        if not module.ispkg:
            continue
        if (Path(engines.__path__[0]) / module.name / "router.py").exists():
            noms.append(module.name)
    return noms


def test_tous_les_routeurs_sont_importables() -> None:
    """Un routeur présent non importable est un module mort que les portes ne voient pas.

    Les routeurs ne sont charges que par les tests d'integration, qui exigent
    Docker. Sans ce test, un nom de constante errone ou un import casse survit
    a ruff, mypy et a toute la suite unitaire.

    Un moteur sans ``router.py`` n'est pas un défaut : il est en cours de
    construction. Le test saute silencieusement les paquets sans routeur.
    """
    for nom in _paquets_moteurs_avec_routeur():
        importlib.import_module(f"gsie_api.engines.{nom}.router")


def test_tous_les_routeurs_presents_sont_montes_sur_l_application() -> None:
    """Un routeur importable mais non monté est inatteignable, donc inutile.

    Le test d'importabilité ci-dessus ne voit pas ce défaut : un routeur peut
    se charger parfaitement, passer ruff, mypy et toute la suite unitaire, et
    n'être exposé par aucune route parce que ``app.py`` ne l'inclut jamais.

    Cas réel (2026-07-22) : le Reasoning Engine avait un ``engine.py`` de 655
    lignes, un ``router.py`` de 240 lignes et ~1 500 lignes de tests verts —
    et n'était monté nulle part. Le travail était intégralement inatteignable
    depuis l'API sans qu'aucune porte ne le signale.

    La propriété vérifiée est « tout routeur présent est monté », pas « tout
    moteur a un routeur » : un moteur en cours de construction n'a pas encore
    de ``router.py``, et ce n'est pas un défaut.
    """
    prefixes_montes = {route.path for route in create_app().routes}

    for nom in _paquets_moteurs_avec_routeur():
        module = importlib.import_module(f"gsie_api.engines.{nom}.router")
        prefixe = module.router.prefix
        assert any(chemin.startswith(f"/api/v1{prefixe}") for chemin in prefixes_montes), (
            f"Le routeur du moteur '{nom}' (préfixe '{prefixe}') s'importe mais "
            f"n'est monté sur aucune route de l'application — ajouter "
            f"`app.include_router({nom}_router, prefix=_settings.api_v1_prefix)` "
            f"dans app.py."
        )
