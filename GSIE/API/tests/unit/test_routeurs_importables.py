"""Test de fumée — importabilité de tous les routeurs de moteurs.

Les routeurs ne sont chargés que par les tests d'intégration, qui exigent
Docker (testcontainers + PostgreSQL/PostGIS). Sans ce test, un routeur dont
l'import casse — nom de constante inexistant, import manquant, syntaxe
erronée — survit à ruff, mypy --strict et à toute la suite unitaire : il est
mort à l'arrivée sans qu'aucune porte ne le voie.

Ce test importe explicitement le sous-module ``router`` de chaque paquet
moteur. Il ne valide aucune route, aucun contrat, aucune réponse — uniquement
que le module se charge. C'est la porte la plus basique possible, et celle
qui manquait.

Contexte : ``router.py`` du Reasoning Engine référençait
``status.HTTP_422_UNPROCESSABLE_CONTENT`` (introduit dans une version de
Starlette postérieure à celle qu'épingle FastAPI 0.115.6). Aucune porte
existante ne l'a vu ; le bug a été découvert au premier lancement des tests
d'intégration.
"""

from __future__ import annotations

import importlib
import pkgutil

import gsie_api.engines as engines


def test_tous_les_routeurs_sont_importables() -> None:
    """Un routeur non importable est un module mort que les portes ne voient pas.

    Les routeurs ne sont charges que par les tests d'integration, qui exigent
    Docker. Sans ce test, un nom de constante errone ou un import casse survit
    a ruff, mypy et a toute la suite unitaire.
    """
    for module in pkgutil.iter_modules(engines.__path__):
        if not module.ispkg:
            continue
        importlib.import_module(f"gsie_api.engines.{module.name}.router")
