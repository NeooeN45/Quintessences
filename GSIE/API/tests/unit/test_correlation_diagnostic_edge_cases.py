"""Tests edge cases — moteurs correlation et diagnostic, lignes défensives non couvertes.

Cible les lignes identifiées par coverage :
- correlation/engine.py:277 — fallback _classify_strength (NaN)
- diagnostic/engine.py:180 — erreur "aucun élément produit" (code défensif)
- correlation/schemas.py:127 — validateur edge case

Valeurs métier (ADR-009) :
- Échelle Evans (1996) pour |r| en biostatistique.
- pH 4,5–6,0 — source : Rameau et al., 2018.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from gsie_api.engines.correlation.engine import CorrelationEngine
from gsie_api.engines.correlation.schemas import CorrelationStrength
from gsie_api.engines.diagnostic.engine import (
    DiagnosticEngine,
    DiagnosticEngineError,
)
from gsie_api.engines.diagnostic.schemas import (
    DiagnosticRequest,
    EtatGlobal,
    EtatGlobalDeclare,
)
from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    SourceReference,
    SourceType,
)
from gsie_api.engines.reasoning.schemas import (
    Conclusion,
    EtapeInference,
    MethodeConfiance,
)


# --- Correlation : fallback _classify_strength (ligne 277) ------------------


class TestClassifyStrengthFallback:
    """Vérifie le fallback défensif de _classify_strength.

    La liste _STRENGTH_THRESHOLDS contient (0.0, negligible), donc tout
    abs_coefficient >= 0.0 retourne negligible. Le seul cas où la ligne 277
    est atteinte est un NaN (not a number), car NaN >= 0.0 est False.
    """

    def test_nan_retourne_negligible_par_fallback(self) -> None:
        """Un coefficient NaN tombe dans le fallback défensif (ligne 277)."""
        result = CorrelationEngine._classify_strength(float("nan"))
        assert result == CorrelationStrength.negligible

    def test_negatif_inf_retourne_negligible_par_fallback(self) -> None:
        """-inf tombe aussi dans le fallback (aucun seuil >= 0 n'est satisfait)."""
        result = CorrelationEngine._classify_strength(float("-inf"))
        assert result == CorrelationStrength.negligible


# --- Diagnostic : erreur "aucun élément produit" (ligne 180) -----------------


_REQUETE_ID = UUID("44444444-4444-4444-8444-444444444444")
_STATION_ID = UUID("55555555-5555-4555-8555-555555555555")
_DATE_DIAGNOSTIC = datetime(2026, 7, 27, 12, 0, 0, tzinfo=UTC)


def _source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Rameau et al.",
        reference="doi:10.0000/test",
    )


def _etape() -> EtapeInference:
    return EtapeInference(
        ordre=1,
        regle_appliquee="R_TEST",
        source_regle=_source(),
        premisses=["pH <= 6.0"],
        conclusion_locale="Conclusion test",
        evidence_level=EvidenceLevel.B,
    )


def _conclusion() -> Conclusion:
    return Conclusion(
        conclusion_id=UUID("66666666-6666-4666-8666-666666666666"),
        enonce="Conclusion test.",
        niveau_confiance=0.8,
        methode_confiance=MethodeConfiance.fournie_par_regle,
        evidence_level_plancher=EvidenceLevel.B,
        chaine_inference=[_etape()],
        sources_utilisees=[_source()],
    )


def _etat_global() -> EtatGlobalDeclare:
    return EtatGlobalDeclare(
        etat=EtatGlobal.vigueur_reduite,
        justification="Vigueur reduite constatee",
        source=_source(),
        evidence_level=EvidenceLevel.B,
    )


class TestDiagnosticAucunElement:
    """Vérifie l'erreur défensive quand aucun élément n'est produit (ligne 180).

    DiagnosticRequest exige min_length=1 sur conclusions et qualifications,
    donc ce cas ne peut survenir que par construction directe (model_construct)
    qui bypass la validation Pydantic — simulant un bug interne ou un appel
    direct au moteur.
    """

    async def test_requete_avec_qualifications_vides_leve_erreur(self) -> None:
        """Un DiagnosticRequest avec qualifications=[] lève DiagnosticEngineError.

        On utilise model_construct pour bypasser la validation Pydantic
        (min_length=1) et tester le code défensif du moteur.
        """
        # Construire une requête avec conclusions mais qualifications vides
        # model_construct bypass la validation — on teste la défense du moteur
        requete = DiagnosticRequest.model_construct(
            requete_id=_REQUETE_ID,
            station_id=_STATION_ID,
            conclusions=[_conclusion()],
            qualifications=[],  # vide — bypass validation
            etat_global=_etat_global(),
            contradictions=[],
            contexte=None,
            type_diagnostic=None,
            peuplement_id=None,
        )

        engine = DiagnosticEngine(session=AsyncMock())
        with pytest.raises(DiagnosticEngineError, match="aucun élément produit"):
            await engine.diagnostiquer(requete, date_diagnostic=_DATE_DIAGNOSTIC)
