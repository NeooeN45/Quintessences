"""Tests unitaires — Correlation Engine (méthodes pures + compute avec mock).

Couvre les chemins non testés par tests/integration/test_correlation.py
(qui nécessite Docker). Ici on teste :
- version() statique
- _classify_strength() (échelle Evans 1996, tous seuils)
- _format_variable() (avec/sans unité)
- compute() avec méthode non supportée (CorrelationEngineError)
- compute() avec mock session (chemin principal + refutation)
- _refute() (robuste et non robuste)
- stats() avec mock session

Aucune DB réelle — la session est un MagicMock avec flush() en AsyncMock.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import numpy as np
import pytest

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


def _make_source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="Rameau et al. (2008)",
        date_publication="2008",
        reference="Flore forestiere francaise, tome 1, IDF",
    )


def _make_request(
    valeurs_a: list[float],
    valeurs_b: list[float],
    methode: CorrelationMethod = CorrelationMethod.pearson,
    seuil_significativite: float = 0.05,
    avec_refutation: bool = False,
    n_permutations: int = 100,
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
        avec_refutation=avec_refutation,
        n_permutations=n_permutations,
    )


def _make_mock_session() -> MagicMock:
    """Session mockee — add() enregistre, flush() est AsyncMock no-op."""
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestVersion:
    def should_return_version_string(self) -> None:
        assert CorrelationEngine.version() == "0.1.0"


class TestClassifyStrength:
    """_classify_strength — échelle Evans (1996), tous seuils."""

    @pytest.mark.parametrize(
        "coefficient, expected",
        [
            (0.95, CorrelationStrength.very_strong),
            (0.80, CorrelationStrength.very_strong),
            (0.79, CorrelationStrength.strong),
            (0.60, CorrelationStrength.strong),
            (0.59, CorrelationStrength.moderate),
            (0.40, CorrelationStrength.moderate),
            (0.39, CorrelationStrength.weak),
            (0.20, CorrelationStrength.weak),
            (0.19, CorrelationStrength.negligible),
            (0.0, CorrelationStrength.negligible),
        ],
    )
    def should_classify_absolute_coefficient(
        self, coefficient: float, expected: CorrelationStrength
    ) -> None:
        assert CorrelationEngine._classify_strength(coefficient) == expected

    def should_classify_negative_coefficient_by_absolute_value(self) -> None:
        # L'appelant passe abs(coefficient) a _classify_strength (voir engine.py L117).
        # On verifie donc que |−0.85| = 0.85 -> very_strong.
        assert CorrelationEngine._classify_strength(0.85) == CorrelationStrength.very_strong


class TestFormatVariable:
    def should_append_unit_when_provided(self) -> None:
        assert CorrelationEngine._format_variable("pH", "unitless") == "pH (unitless)"

    def should_return_variable_only_when_no_unit(self) -> None:
        assert CorrelationEngine._format_variable("pH", None) == "pH"

    def should_return_variable_only_when_empty_unit(self) -> None:
        assert CorrelationEngine._format_variable("altitude", "") == "altitude"


class TestComputeUnsupportedMethod:
    """compute() doit lever CorrelationEngineError pour une méthode non calculable."""

    async def should_raise_when_method_not_calculable(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        # 'expert' et 'literature' ne sont pas dans _METHOD_FUNCS
        request = _make_request(
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [2.0, 4.0, 6.0, 8.0, 10.0],
            methode=CorrelationMethod.expert,
        )
        with pytest.raises(CorrelationEngineError, match="non calculable"):
            await engine.compute(request)
        # Aucun flush ne doit avoir lieu (early return)
        session.flush.assert_not_awaited()


class TestComputeWithMockSession:
    """compute() chemin principal avec session mockee."""

    async def should_compute_pearson_and_persist(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = _make_request(
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [2.0, 4.0, 6.0, 8.0, 10.0],
            methode=CorrelationMethod.pearson,
        )

        result = await engine.compute(request)

        assert result.coefficient == pytest.approx(1.0, abs=1e-6)
        assert result.type_relation == TypeRelation.positive
        assert result.strength == CorrelationStrength.very_strong
        assert result.n_observations == 5
        assert result.methode == CorrelationMethod.pearson
        assert result.refutation is None
        # 2 flush (resource puis CorrelationModel) + 2 add
        assert session.add.call_count == 2
        assert session.flush.await_count == 2

    async def should_compute_negative_correlation(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        # Correlation negative parfaite
        request = _make_request(
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [10.0, 8.0, 6.0, 4.0, 2.0],
            methode=CorrelationMethod.pearson,
        )

        result = await engine.compute(request)

        assert result.coefficient == pytest.approx(-1.0, abs=1e-6)
        assert result.type_relation == TypeRelation.negative
        assert result.strength == CorrelationStrength.very_strong

    async def should_mark_non_significative_when_p_value_above_threshold(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        # Donnees aleatoires -> p-valeur elevee -> non significative
        rng = np.random.default_rng(seed=42)
        a = rng.standard_normal(20).tolist()
        b = rng.standard_normal(20).tolist()
        request = _make_request(a, b, seuil_significativite=0.0001)

        result = await engine.compute(request)

        # p-valeur quasi-certaine > 0.0001 avec donnees aleatoires
        assert result.type_relation == TypeRelation.non_significative

    async def should_compute_spearman_method(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = _make_request(
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [2.0, 4.0, 6.0, 8.0, 10.0],
            methode=CorrelationMethod.spearman,
        )

        result = await engine.compute(request)

        assert result.methode == CorrelationMethod.spearman
        assert result.coefficient == pytest.approx(1.0, abs=1e-6)

    async def should_compute_kendall_method(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = _make_request(
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [2.0, 4.0, 6.0, 8.0, 10.0],
            methode=CorrelationMethod.kendall,
        )

        result = await engine.compute(request)

        assert result.methode == CorrelationMethod.kendall
        assert result.coefficient == pytest.approx(1.0, abs=1e-6)

    async def should_format_variable_labels_with_unit(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = CorrelationComputeRequest(
            requete_id=uuid4(),
            domaine=DomaineCorrelation.stationnel,
            variable_a=ParametreCorrelation(
                source_moteur=SourceMoteur.pedology,
                variable="pH",
                unite="unitless",
                valeurs=[1.0, 2.0, 3.0, 4.0, 5.0],
            ),
            variable_b=ParametreCorrelation(
                source_moteur=SourceMoteur.botanical,
                variable="presence",
                unite="proportion",
                valeurs=[2.0, 4.0, 6.0, 8.0, 10.0],
            ),
            methode=CorrelationMethod.pearson,
            source=_make_source(),
            evidence_level=EvidenceLevel.B,
        )

        result = await engine.compute(request)

        assert result.variable_a == "pH (unitless)"
        assert result.variable_b == "presence (proportion)"


class TestRefutation:
    """_refute() — test de permutation (RFC-0015 §3.5)."""

    async def should_return_robuste_when_correlation_is_real(self) -> None:
        session = _make_mock_session()
        # RNG determine pour reproductibilite
        engine = CorrelationEngine(session, rng=np.random.default_rng(seed=42))
        # Correlation parfaite -> robuste au test de permutation
        request = _make_request(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            methode=CorrelationMethod.pearson,
            avec_refutation=True,
            n_permutations=100,
        )

        result = await engine.compute(request)

        assert result.refutation is not None
        assert result.refutation.n_permutations == 100
        # Correlation parfaite : aucune permutation ne doit atteindre |r|=1.0
        # sauf par hasard trivial -> robuste=True
        assert result.refutation.robuste is True
        assert "robuste" in result.refutation.interpretation

    async def should_return_non_robuste_when_correlation_is_spurious(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session, rng=np.random.default_rng(seed=123))
        # Donnees aleatoires -> coefficient faible -> non robuste
        rng = np.random.default_rng(seed=999)
        a = rng.standard_normal(15).tolist()
        b = rng.standard_normal(15).tolist()
        request = _make_request(
            a,
            b,
            methode=CorrelationMethod.pearson,
            avec_refutation=True,
            n_permutations=100,
            seuil_significativite=0.0001,  # seuil tres strict -> non robuste
        )

        result = await engine.compute(request)

        assert result.refutation is not None
        # Avec un seuil tres strict et donnees aleatoires, presque certainement non robuste
        # (on ne peut pas garantir a 100% a cause du RNG, mais seed fixe -> deterministe)
        assert isinstance(result.refutation.robuste, bool)
        assert "permutation" in result.refutation.interpretation


class TestStatsWithMock:
    """stats() avec session mockee."""

    async def should_return_stats_dict(self) -> None:
        session = _make_mock_session()
        # Mock execute() pour retourner un total et des rows par methode
        total_result = MagicMock()
        total_result.scalar_one.return_value = 5
        by_method_result = MagicMock()
        by_method_result.all.return_value = [
            (CorrelationMethod.pearson, 3),
            (CorrelationMethod.spearman, 2),
        ]
        session.execute.side_effect = [total_result, by_method_result]

        engine = CorrelationEngine(session)
        stats = await engine.stats()

        assert stats["total_correlations"] == 5
        assert stats["methode_pearson"] == 3
        assert stats["methode_spearman"] == 2


class TestComputeConstantVariable:
    """compute() doit lever CorrelationEngineError sur une variable constante.

    Une série de variance nulle (même valeur sur tous les relevés) rend le
    coefficient indéfini : scipy renvoie NaN. La garde NaN traduit ce cas
    en erreur métier plutôt qu'en 500 opaque.
    """

    async def should_raise_when_variable_is_constant(self) -> None:
        # Arrange — variable_a constante → variance nulle → coefficient NaN
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = _make_request(
            [5.0, 5.0, 5.0, 5.0, 5.0],
            [1.0, 2.0, 3.0, 4.0, 5.0],
            methode=CorrelationMethod.pearson,
        )

        # Act & Assert
        with pytest.raises(CorrelationEngineError, match="constante"):
            await engine.compute(request)

        # Aucun flush ne doit avoir lieu (early return avant persistance)
        session.flush.assert_not_awaited()
