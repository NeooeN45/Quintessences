"""Tests d'intégration — Correlation Engine (persistance PostgreSQL réelle).

Couvre : calcul pearson/spearman/kendall, classification de force
(Evans 1996), significativité, persistance (resource + CorrelationModel),
stats. Utilise la base PostgreSQL/PostGIS réelle (testcontainers, fixture
partagée dans tests/conftest.py).
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.correlation.engine import CorrelationEngine, CorrelationEngineError
from gsie_api.engines.correlation.schemas import (
    CorrelationComputeRequest,
    DomaineCorrelation,
    ParametreCorrelation,
    SourceMoteur,
    TypeRelation,
)
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.infrastructure.models.enums import CorrelationMethod, CorrelationStrength
from tests.conftest import requires_docker

pytestmark = requires_docker


def _make_source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="Rameau et al. (2008)",
        date_publication="2008",
        reference="Flore forestière française, tome 1, IDF",
    )


def _make_request(
    valeurs_a: list[float],
    valeurs_b: list[float],
    methode: CorrelationMethod = CorrelationMethod.pearson,
    seuil_significativite: float = 0.05,
) -> CorrelationComputeRequest:
    return CorrelationComputeRequest(
        requete_id=uuid4(),
        domaine=DomaineCorrelation.stationnel,
        variable_a=ParametreCorrelation(
            source_moteur=SourceMoteur.pedology, variable="pH", unite=None, valeurs=valeurs_a
        ),
        variable_b=ParametreCorrelation(
            source_moteur=SourceMoteur.botanical,
            variable="presence_chene_sessile",
            unite=None,
            valeurs=valeurs_b,
        ),
        methode=methode,
        seuil_significativite=seuil_significativite,
        source=_make_source(),
        evidence_level=EvidenceLevel.B,
        domaine_validite="France atlantique, sols acides",
    )


@pytest.fixture
def engine(db_session: AsyncSession) -> CorrelationEngine:
    return CorrelationEngine(db_session)


async def should_compute_strong_positive_correlation(engine: CorrelationEngine):
    """Deux variables parfaitement corrélées doivent donner un coefficient proche de 1."""
    request = _make_request([1.0, 2.0, 3.0, 4.0, 5.0], [2.0, 4.0, 6.0, 8.0, 10.0])
    result = await engine.compute(request)

    assert result.coefficient == pytest.approx(1.0, abs=1e-6)
    assert result.type_relation == TypeRelation.positive
    assert result.strength == CorrelationStrength.very_strong
    assert result.n_observations == 5
    assert result.evidence_level == EvidenceLevel.B
    assert result.refutation is None


async def should_omit_refutation_by_default(engine: CorrelationEngine):
    """Sans avec_refutation=true, le résultat ne contient pas de RefutationResult."""
    request = _make_request([1.0, 2.0, 3.0, 4.0, 5.0], [2.0, 4.0, 6.0, 8.0, 10.0])

    result = await engine.compute(request)

    assert result.refutation is None


async def should_flag_strong_linear_correlation_as_robust_to_permutation(
    engine: CorrelationEngine,
):
    """Une corrélation linéaire parfaite doit résister au test de permutation."""
    request = _make_request([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], [2, 4, 6, 8, 10, 12, 14, 16])
    request = request.model_copy(update={"avec_refutation": True, "n_permutations": 200})

    result = await engine.compute(request)

    assert result.refutation is not None
    assert result.refutation.n_permutations == 200
    assert result.refutation.robuste is True
    assert (
        result.refutation.interpretation
        == "association observée, robuste au test de permutation"
    )
    assert "cause" not in result.refutation.interpretation


async def should_flag_noise_correlation_as_not_robust_to_permutation():
    """Une corrélation issue du bruit ne doit pas résister au test de permutation."""
    import numpy as np

    from gsie_api.infrastructure.models import ResourceModel  # noqa: F401  (import guard only)

    rng = np.random.default_rng(seed=42)
    valeurs_a = list(rng.normal(size=30))
    valeurs_b = list(rng.normal(size=30))

    request = _make_request(valeurs_a, valeurs_b, methode=CorrelationMethod.pearson)
    request = request.model_copy(
        update={"avec_refutation": True, "n_permutations": 300, "seuil_significativite": 0.4}
    )

    class _FakeSession:
        def add(self, *_args: object, **_kwargs: object) -> None:
            pass

        async def flush(self) -> None:
            pass

    engine = CorrelationEngine(_FakeSession(), rng=np.random.default_rng(seed=7))  # type: ignore[arg-type]
    result = await engine.compute(request)

    assert result.refutation is not None
    # Coefficient de bruit — le test de permutation ne doit pas le déclarer robuste
    # à un seuil aussi permissif (0.4) que celui utilisé pour p_valeur elle-même.
    assert result.refutation.p_valeur_permutation > 0.05


async def should_compute_negative_correlation(engine: CorrelationEngine):
    """Deux variables inversement liées doivent donner un coefficient négatif."""
    request = _make_request([1.0, 2.0, 3.0, 4.0, 5.0], [10.0, 8.0, 6.0, 4.0, 2.0])
    result = await engine.compute(request)

    assert result.coefficient < 0
    assert result.type_relation == TypeRelation.negative


async def should_mark_non_significant_when_p_value_high(engine: CorrelationEngine):
    """Des données non corrélées doivent produire type_relation=non_significative."""
    request = _make_request([1.0, 5.0, 2.0, 4.0, 3.0], [3.0, 1.0, 5.0, 2.0, 4.0])
    result = await engine.compute(request)

    assert result.type_relation == TypeRelation.non_significative


async def should_support_spearman_method(engine: CorrelationEngine):
    """La méthode spearman doit être calculable et retournée telle quelle."""
    request = _make_request(
        [1.0, 2.0, 3.0, 4.0, 5.0], [1.5, 4.0, 3.5, 8.0, 9.5], methode=CorrelationMethod.spearman
    )
    result = await engine.compute(request)

    assert result.methode == CorrelationMethod.spearman
    assert -1.0 <= result.coefficient <= 1.0


async def should_support_kendall_method(engine: CorrelationEngine):
    """La méthode kendall doit être calculable."""
    request = _make_request(
        [1.0, 2.0, 3.0, 4.0, 5.0], [1.5, 4.0, 3.5, 8.0, 9.5], methode=CorrelationMethod.kendall
    )
    result = await engine.compute(request)

    assert result.methode == CorrelationMethod.kendall


async def should_reject_unsupported_method(engine: CorrelationEngine):
    """Une méthode non calculable (ex. expert, literature) doit être rejetée."""
    request = _make_request(
        [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], methode=CorrelationMethod.expert
    )
    with pytest.raises(CorrelationEngineError, match="non calculable"):
        await engine.compute(request)


def should_reject_mismatched_value_counts():
    """La validation Pydantic doit rejeter des séries de tailles différentes."""
    with pytest.raises(ValueError, match="même nombre de valeurs"):
        _make_request([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0])


async def should_persist_correlation_and_appear_in_stats(engine: CorrelationEngine):
    """Une corrélation calculée doit être comptée dans stats()."""
    assert (await engine.stats())["total_correlations"] == 0

    request = _make_request([1.0, 2.0, 3.0, 4.0, 5.0], [2.0, 4.0, 6.0, 8.0, 10.0])
    result = await engine.compute(request)

    stats = await engine.stats()
    assert stats["total_correlations"] == 1
    assert stats[f"methode_{result.methode.value}"] == 1


async def should_format_variable_label_with_unit(engine: CorrelationEngine):
    """Le label de variable doit inclure l'unité quand elle est fournie."""
    request = _make_request([1.0, 2.0, 3.0, 4.0, 5.0], [2.0, 4.0, 6.0, 8.0, 10.0])
    request.variable_a.unite = "unité pH"
    result = await engine.compute(request)

    assert result.variable_a == "pH (unité pH)"


def should_return_engine_version():
    """version() doit retourner une chaîne non vide."""
    assert len(CorrelationEngine.version()) > 0
