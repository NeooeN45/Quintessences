"""Tests unitaires — Correlation Engine compute_matrix (matrice N×N).

Couvre :
- compute_matrix() avec numpy.corrcoef vectorisé (Pearson)
- compute_matrix() avec scipy pairwise (Spearman/Kendall)
- Extraction des paires significatives (filtrage par seuil_force + seuil_significativite)
- Tri par |coefficient| décroissant
- Gardes : variable constante, méthode non supportée, moins de 2 variables
- Validation matrice symétrique, diagonale None

Aucune DB réelle — la session est un MagicMock (compute_matrix ne persiste pas).
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import numpy as np
import pytest
from pydantic import ValidationError

from gsie_api.engines.correlation.engine import CorrelationEngine, CorrelationEngineError
from gsie_api.engines.correlation.schemas import (
    CorrelationMatrixRequest,
    DomaineCorrelation,
    ParametreCorrelation,
    SourceMoteur,
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


def _make_variable(
    name: str,
    valeurs: list[float],
    source_moteur: SourceMoteur = SourceMoteur.pedology,
    unite: str | None = None,
) -> ParametreCorrelation:
    return ParametreCorrelation(
        source_moteur=source_moteur,
        variable=name,
        unite=unite,
        valeurs=valeurs,
    )


def _make_matrix_request(
    variables: list[ParametreCorrelation],
    methode: CorrelationMethod = CorrelationMethod.pearson,
    seuil_significativite: float = 0.05,
    seuil_force: CorrelationStrength = CorrelationStrength.moderate,
) -> CorrelationMatrixRequest:
    return CorrelationMatrixRequest(
        requete_id=uuid4(),
        domaine=DomaineCorrelation.stationnel,
        variables=variables,
        methode=methode,
        seuil_significativite=seuil_significativite,
        source=_make_source(),
        evidence_level=EvidenceLevel.B,
        seuil_force=seuil_force,
    )


def _make_mock_session() -> MagicMock:
    return MagicMock()


class TestComputeMatrixPearson:
    """compute_matrix() avec Pearson vectorisé (numpy.corrcoef)."""

    async def should_compute_3x3_matrix_with_perfect_correlations(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        # 3 variables : a et b parfaitement corrélées positivement,
        # c parfaitement corrélées négativement avec a
        request = _make_matrix_request(
            [
                _make_variable("pH", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
                _make_variable("calcium", [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0]),
                _make_variable("acidite", [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]),
            ]
        )

        result = await engine.compute_matrix(request)

        assert result.n_variables == 3
        assert result.n_observations == 8
        assert result.n_paires_total == 3  # 3*2/2
        assert len(result.matrice) == 3
        assert len(result.matrice[0]) == 3
        # Diagonale = None
        assert result.matrice[0][0] is None
        assert result.matrice[1][1] is None
        assert result.matrice[2][2] is None
        # a-b : corrélation parfaite positive
        assert result.matrice[0][1] == pytest.approx(1.0, abs=1e-6)
        assert result.matrice[1][0] == pytest.approx(1.0, abs=1e-6)
        # a-c : corrélation parfaite négative
        assert result.matrice[0][2] == pytest.approx(-1.0, abs=1e-6)
        assert result.matrice[2][0] == pytest.approx(-1.0, abs=1e-6)
        # Symétrie
        assert result.matrice[1][2] == pytest.approx(result.matrice[2][1], abs=1e-6)

    async def should_extract_significant_pairs_sorted_by_abs_coefficient(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        rng = np.random.default_rng(seed=42)
        base = rng.standard_normal(50)
        # Var1 et Var2 : forte corrélation
        var2 = base * 0.9 + rng.standard_normal(50) * 0.1
        # Var3 et Var4 : corrélation modérée
        var4 = base * 0.5 + rng.standard_normal(50) * 0.5
        # Var5 : bruit pur (pas de corrélation)
        var5 = rng.standard_normal(50)

        request = _make_matrix_request(
            [
                _make_variable("var1", base.tolist()),
                _make_variable("var2", var2.tolist()),
                _make_variable("var3", base.tolist()),
                _make_variable("var4", var4.tolist()),
                _make_variable("var5", var5.tolist()),
            ],
            seuil_force=CorrelationStrength.weak,
        )

        result = await engine.compute_matrix(request)

        # Au moins 2 paires significatives (var1-var2, var1-var3, var3-var2)
        assert len(result.paires_significatives) >= 2
        # Tri par |coefficient| décroissant
        coeffs = [abs(p.coefficient) for p in result.paires_significatives]
        assert coeffs == sorted(coeffs, reverse=True)
        # Toutes les paires significatives ont |r| >= seuil weak (0.20)
        for pair in result.paires_significatives:
            assert abs(pair.coefficient) >= 0.20
            assert pair.p_valeur < 0.05

    async def should_filter_by_strength_threshold(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        rng = np.random.default_rng(seed=42)
        base = rng.standard_normal(50)
        # Corrélation faible (~0.3) avec beaucoup de bruit
        var2 = base * 0.3 + rng.standard_normal(50) * 0.9

        request = _make_matrix_request(
            [
                _make_variable("var1", base.tolist()),
                _make_variable("var2", var2.tolist()),
            ],
            seuil_force=CorrelationStrength.strong,  # |r| >= 0.60
        )

        result = await engine.compute_matrix(request)

        # Corrélation faible < 0.60 (strong) -> pas de paire significative
        assert len(result.paires_significatives) == 0
        # Mais la matrice est quand même calculée
        assert result.matrice[0][1] is not None

    async def should_include_variable_labels_with_units(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = _make_matrix_request(
            [
                _make_variable("pH", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], unite="unitless"),
                _make_variable("altitude", [100.0, 200.0, 300.0, 400.0, 500.0, 600.0], unite="m"),
            ]
        )

        result = await engine.compute_matrix(request)

        assert result.variables == ["pH (unitless)", "altitude (m)"]


class TestComputeMatrixSpearmanKendall:
    """compute_matrix() avec Spearman/Kendall (scipy pairwise)."""

    async def should_compute_spearman_matrix(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = _make_matrix_request(
            [
                _make_variable("rank1", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
                _make_variable("rank2", [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0]),
                _make_variable("rank3", [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]),
            ],
            methode=CorrelationMethod.spearman,
        )

        result = await engine.compute_matrix(request)

        assert result.methode == CorrelationMethod.spearman
        assert result.matrice[0][1] == pytest.approx(1.0, abs=1e-6)
        assert result.matrice[0][2] == pytest.approx(-1.0, abs=1e-6)

    async def should_compute_kendall_matrix(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = _make_matrix_request(
            [
                _make_variable("k1", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
                _make_variable("k2", [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0]),
            ],
            methode=CorrelationMethod.kendall,
        )

        result = await engine.compute_matrix(request)

        assert result.methode == CorrelationMethod.kendall
        assert result.matrice[0][1] == pytest.approx(1.0, abs=1e-6)


class TestComputeMatrixGuards:
    """Gardes d'erreur pour compute_matrix()."""

    async def should_raise_when_method_not_calculable(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = _make_matrix_request(
            [
                _make_variable("v1", [1.0, 2.0, 3.0, 4.0, 5.0]),
                _make_variable("v2", [2.0, 4.0, 6.0, 8.0, 10.0]),
            ],
            methode=CorrelationMethod.expert,
        )

        with pytest.raises(CorrelationEngineError, match="non calculable"):
            await engine.compute_matrix(request)

    async def should_raise_when_variable_is_constant(self) -> None:
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = _make_matrix_request(
            [
                _make_variable("const", [5.0, 5.0, 5.0, 5.0, 5.0]),
                _make_variable("var", [1.0, 2.0, 3.0, 4.0, 5.0]),
            ]
        )

        with pytest.raises(CorrelationEngineError, match="constante"):
            await engine.compute_matrix(request)


class TestComputeMatrixValidation:
    """Validation des schémas CorrelationMatrixRequest."""

    def should_reject_less_than_2_variables(self) -> None:
        with pytest.raises(ValidationError, match="at least 2"):
            CorrelationMatrixRequest(
                requete_id=uuid4(),
                domaine=DomaineCorrelation.stationnel,
                variables=[_make_variable("solo", [1.0, 2.0, 3.0])],
                source=_make_source(),
                evidence_level=EvidenceLevel.B,
            )

    def should_reject_mismatched_observation_counts(self) -> None:
        with pytest.raises(ValueError, match="appariées"):
            CorrelationMatrixRequest(
                requete_id=uuid4(),
                domaine=DomaineCorrelation.stationnel,
                variables=[
                    _make_variable("v1", [1.0, 2.0, 3.0]),
                    _make_variable("v2", [1.0, 2.0, 3.0, 4.0]),
                ],
                source=_make_source(),
                evidence_level=EvidenceLevel.B,
            )

    def should_reject_more_than_200_variables(self) -> None:
        variables = [_make_variable(f"v{i}", [1.0, 2.0, 3.0]) for i in range(201)]
        with pytest.raises(ValueError, match="200"):
            CorrelationMatrixRequest(
                requete_id=uuid4(),
                domaine=DomaineCorrelation.stationnel,
                variables=variables,
                source=_make_source(),
                evidence_level=EvidenceLevel.B,
            )


class TestStrengthThreshold:
    """_strength_threshold_value — mapping force → |r| minimum."""

    @pytest.mark.parametrize(
        "strength, expected",
        [
            (CorrelationStrength.very_strong, 0.80),
            (CorrelationStrength.strong, 0.60),
            (CorrelationStrength.moderate, 0.40),
            (CorrelationStrength.weak, 0.20),
            (CorrelationStrength.negligible, 0.0),
        ],
    )
    def should_return_threshold_for_strength(
        self, strength: CorrelationStrength, expected: float
    ) -> None:
        assert CorrelationEngine._strength_threshold_value(strength) == pytest.approx(expected)

    def should_return_zero_when_strength_unknown(self) -> None:
        """Fallback défensif — force inconnue retourne 0.0 (ligne 396)."""
        # CorrelationStrength est un enum StrEnum ; on injecte une valeur
        # inexistante via mock pour tester le fallback.
        fake = type("FakeStrength", (), {"__eq__": lambda self, other: False})()
        assert CorrelationEngine._strength_threshold_value(fake) == 0.0  # type: ignore[arg-type]


class TestComputeMatrixNanFilter:
    """Filtrage des paires NaN dans compute_matrix (ligne 293)."""

    async def should_skip_pairs_with_nan_coefficient(self) -> None:
        """Une paire avec coefficient NaN est skippée (pas dans significatives)."""
        session = _make_mock_session()
        engine = CorrelationEngine(session)
        request = _make_matrix_request(
            [
                _make_variable("v1", [1.0, 2.0, 3.0, 4.0, 5.0]),
                _make_variable("v2", [2.0, 4.0, 6.0, 8.0, 10.0]),
            ]
        )

        # Mock _pearson_matrix_vectorized pour injecter un NaN
        original = engine._pearson_matrix_vectorized

        def _mock_pearson(data: np.ndarray, n_obs: int) -> tuple[np.ndarray, np.ndarray]:
            corr, pval = original(data, n_obs)
            # Injecte NaN sur la paire (0,1)
            corr[0, 1] = np.nan
            corr[1, 0] = np.nan
            return corr, pval

        with patch.object(engine, "_pearson_matrix_vectorized", side_effect=_mock_pearson):
            result = await engine.compute_matrix(request)

        # La matrice contient NaN (arrondi)
        assert result.matrice[0][1] != result.matrice[0][1]  # NaN != NaN
        # Aucune paire significative (NaN skippé)
        assert len(result.paires_significatives) == 0
