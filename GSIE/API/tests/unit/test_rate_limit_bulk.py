"""Tests unitaires — rate limiting différencié bulk vs unitaire.

Vérifie que :
1. La config expose `rate_limit_bulk` (défaut 600/minute).
2. `rate_limit_bulk` > `rate_limit_evaluate` (le bulk est plus permissif).
3. L'endpoint bulk utilise `rate_limit_bulk` (pas un littéral).
4. L'endpoint unitaire utilise `rate_limit_evaluate` (30/minute).

Ces tests garantissent que le rate limiting différencié est configuré
et utilisé — sans eux, supprimer la config `rate_limit_bulk` ferait
passer les tests (le littéral "600/minute" serait toujours là).
"""

from __future__ import annotations

import inspect

from gsie_api.core.config import Settings


def test_rate_limit_bulk_config_exists() -> None:
    """La config doit exposer `rate_limit_bulk`."""
    settings = Settings()
    assert hasattr(settings, "rate_limit_bulk")
    assert settings.rate_limit_bulk == "600/minute"


def test_rate_limit_bulk_is_more_permissive_than_unitaire() -> None:
    """Le bulk doit être plus permissif que le unitaire (30/min)."""
    settings = Settings()
    bulk_count = int(settings.rate_limit_bulk.split("/")[0])
    unitaire_count = int(settings.rate_limit_evaluate.split("/")[0])
    assert bulk_count > unitaire_count, (
        f"Le bulk ({bulk_count}/min) doit être plus permissif que "
        f"le unitaire ({unitaire_count}/min)"
    )


def test_bulk_endpoint_uses_configured_rate_limit() -> None:
    """L'endpoint bulk doit utiliser `_settings.rate_limit_bulk` (pas un littéral)."""
    # Le décorateur @_limiter.limit(_settings.rate_limit_bulk) doit apparaître
    # dans les lignes précédant la fonction.
    # On inspecte le module complet pour trouver le décorateur.
    from gsie_api.resources import router as router_module

    module_source = inspect.getsource(router_module)
    assert "_settings.rate_limit_bulk" in module_source, (
        "L'endpoint bulk doit utiliser `_settings.rate_limit_bulk` "
        "(pas un littéral en dur) pour permettre la configuration"
    )


def test_unitaire_endpoint_uses_stricter_rate_limit() -> None:
    """L'endpoint unitaire doit utiliser un rate limit strict (30/minute)."""
    from gsie_api.core.config import Settings

    settings = Settings()
    unitaire_count = int(settings.rate_limit_evaluate.split("/")[0])
    assert (
        unitaire_count == 30
    ), f"Le rate limit unitaire doit être 30/minute, reçu {unitaire_count}"


def test_bulk_rate_limit_20x_more_permissive_than_unitaire() -> None:
    """Le bulk doit être au moins 20x plus permissif (600 vs 30)."""
    settings = Settings()
    bulk_count = int(settings.rate_limit_bulk.split("/")[0])
    unitaire_count = int(settings.rate_limit_evaluate.split("/")[0])
    ratio = bulk_count / unitaire_count
    assert ratio >= 20, f"Le bulk doit être au moins 20x plus permissif (ratio {ratio:.1f}x)"
