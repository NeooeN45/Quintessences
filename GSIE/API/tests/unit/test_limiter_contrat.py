"""Contrat du limiter partagé — deux invariants que le code seul ne garantit pas.

1. Aucun router n'instancie son propre `Limiter`. Un limiter local ignore
   `rate_limit_enabled` et garde son stockage en mémoire : en production le
   quota anti-flood serait multiplié par le nombre de workers Gunicorn, et le
   drapeau de désactivation resterait sans effet.
2. Tout endpoint décoré par `@_limiter.limit(...)` déclare `response: Response`.
   Le limiter partagé a `headers_enabled=True` : sans ce paramètre, slowapi
   lève une exception et **chaque appel** à l'endpoint devient un 500.
"""

from __future__ import annotations

import inspect
import pkgutil
from importlib import import_module
from typing import TYPE_CHECKING

from fastapi import Response
from slowapi import Limiter

import gsie_api
from gsie_api.app import create_app
from gsie_api.core.limiter import limiter as limiter_partage

if TYPE_CHECKING:
    from types import ModuleType


def _tous_les_modules() -> list[ModuleType]:
    modules: list[ModuleType] = []
    for info in pkgutil.walk_packages(gsie_api.__path__, prefix="gsie_api."):
        try:
            modules.append(import_module(info.name))
        except Exception:  # noqa: BLE001 — un module optionnel absent n'est pas le sujet
            continue
    return modules


def test_aucun_router_n_instancie_son_propre_limiter() -> None:
    locaux: list[str] = []
    for module in _tous_les_modules():
        for nom, valeur in vars(module).items():
            if isinstance(valeur, Limiter) and valeur is not limiter_partage:
                locaux.append(f"{module.__name__}.{nom}")

    assert locaux == [], (
        "Limiter(s) local(aux) détecté(s) : importer "
        "`from gsie_api.core.limiter import limiter` à la place — "
        f"{sorted(locaux)}"
    )


def test_tout_endpoint_limite_declare_response() -> None:
    """`headers_enabled=True` impose `response: Response` sur l'endpoint décoré."""
    app = create_app()
    limites = set(limiter_partage._route_limits)

    manquants: list[str] = []
    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        cle = f"{endpoint.__module__}.{endpoint.__qualname__}"
        if cle not in limites and endpoint.__name__ not in limites:
            continue
        parametres = inspect.signature(endpoint).parameters
        parametre = parametres.get("response")
        annotations = inspect.get_annotations(endpoint, eval_str=True)
        if parametre is None or annotations.get("response") is not Response:
            manquants.append(cle)

    assert manquants == [], (
        "Endpoint(s) limité(s) sans `response: Response` — chaque appel "
        f"renverrait 500 : {sorted(manquants)}"
    )
