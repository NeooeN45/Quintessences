"""Tests d'invariants des schémas Recommendation (tranche R1).

Chaque test vérifie qu'une garantie du `RECOMMENDATION_ENGINE.md` §6 est
**inconstructible** lorsqu'elle est violée. Un invariant qu'on peut
contourner en construisant l'objet autrement n'est pas un invariant : c'est
un commentaire (`CODE_QUALITY_STANDARD` §3.2).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from gsie_api.engines.evidence.schemas import SourceReference
from gsie_api.engines.recommendation.schemas import (
    DecisionForestier,
    ForestierDecision,
    JustificationRecommandation,
    ObjectifForestier,
    Recommendation,
    RecommendationRequest,
    RecommendationSet,
    TypeAction,
)

_DIAGNOSTIC = UUID("11111111-1111-4111-8111-111111111111")


def _source() -> SourceReference:
    return SourceReference(
        type_source="peer_reviewed",
        auteur="Rameau et al. (2008)",
        reference="Flore forestière française, tome 1, IDF",
    )


def _justification(diagnostic_ref: UUID = _DIAGNOSTIC) -> JustificationRecommandation:
    return JustificationRecommandation(
        diagnostic_ref=diagnostic_ref,
        sources=[_source()],
        facteurs_limitants=["Diagnostic limité aux données pédologiques disponibles"],
    )


def _recommandation(
    *,
    recommandation_id: UUID | None = None,
    alternatives: list[Recommendation] | None = None,
    diagnostic_ref: UUID = _DIAGNOSTIC,
) -> Recommendation:
    return Recommendation(
        recommandation_id=recommandation_id or uuid4(),
        type_action=TypeAction.PLANTATION,
        description="Reconstituer le peuplement avec une essence adaptée à la station.",
        justification=_justification(diagnostic_ref),
        alternatives=alternatives or [],
        niveau_confiance=0.7,
    )


def _ensemble(recommandations: list[Recommendation]) -> RecommendationSet:
    return RecommendationSet(
        ensemble_id=uuid4(),
        requete_origine=uuid4(),
        diagnostic_source=_DIAGNOSTIC,
        recommandations=recommandations,
        date_generation=datetime.now(UTC),
    )


class TestContournabilite:
    """GSIE-CON-001 — le forestier peut toujours refuser."""

    def test_contournable_est_toujours_vrai(self) -> None:
        assert _recommandation().contournable is True

    def test_contournable_ne_peut_pas_etre_renverse(self) -> None:
        """Le champ est calculé : tenter de le fixer à `false` doit échouer.

        C'est la garantie la plus importante du moteur. Si un appelant
        pouvait construire une recommandation `contournable=false`, GSIE
        cesserait d'être un outil d'aide pour devenir un donneur d'ordre.
        """
        with pytest.raises(ValidationError):
            Recommendation(
                recommandation_id=uuid4(),
                type_action=TypeAction.COUPE_RASE,
                description="Coupe rase immédiate.",
                justification=_justification(),
                niveau_confiance=1.0,
                contournable=False,  # type: ignore[call-arg]
            )

    def test_contournable_est_serialise_dans_la_sortie(self) -> None:
        """Le contrat §5 exige que le champ figure dans la sortie."""
        assert _recommandation().model_dump()["contournable"] is True


class TestJustificationObligatoire:
    """GSIE-CON-002 / CON-004 — rien n'est recommandé sans fondement."""

    def test_recommandation_sans_justification_est_refusee(self) -> None:
        with pytest.raises(ValidationError):
            Recommendation(
                recommandation_id=uuid4(),
                type_action=TypeAction.ECLAIRCIE,
                description="Éclaircie.",
                niveau_confiance=0.5,
            )  # type: ignore[call-arg]

    def test_justification_sans_source_est_refusee(self) -> None:
        with pytest.raises(ValidationError):
            JustificationRecommandation(
                diagnostic_ref=_DIAGNOSTIC,
                sources=[],
                facteurs_limitants=["Une limite"],
            )

    def test_justification_sans_facteur_limitant_est_refusee(self) -> None:
        """Une recommandation sans limite affichée se lit comme une certitude."""
        with pytest.raises(ValidationError):
            JustificationRecommandation(
                diagnostic_ref=_DIAGNOSTIC,
                sources=[_source()],
                facteurs_limitants=[],
            )


class TestTracabiliteDuDiagnostic:
    """GSIE-CON-005 — une recommandation remonte à son diagnostic réel."""

    def test_justification_visant_un_autre_diagnostic_est_refusee(self) -> None:
        etranger = _recommandation(diagnostic_ref=uuid4())

        with pytest.raises(ValidationError, match="diagnostic"):
            _ensemble([etranger])

    def test_alternative_visant_un_autre_diagnostic_est_refusee(self) -> None:
        """Le contrôle porte aussi sur les alternatives, pas seulement la tête."""
        principale = _recommandation(alternatives=[_recommandation(diagnostic_ref=uuid4())])

        with pytest.raises(ValidationError, match="diagnostic"):
            _ensemble([principale])


class TestAlternatives:
    """§6 — plusieurs voies, présentables et auditables."""

    def test_alternative_ne_porte_pas_ses_propres_alternatives(self) -> None:
        imbriquee = _recommandation(alternatives=[_recommandation()])

        with pytest.raises(ValidationError, match="alternative"):
            _recommandation(alternatives=[imbriquee])

    def test_recommandation_ne_peut_pas_etre_sa_propre_alternative(self) -> None:
        identifiant = uuid4()

        with pytest.raises(ValidationError, match="propre alternative"):
            _recommandation(
                recommandation_id=identifiant,
                alternatives=[_recommandation(recommandation_id=identifiant)],
            )

    def test_deux_alternatives_ne_partagent_pas_d_identifiant(self) -> None:
        identifiant = uuid4()

        with pytest.raises(ValidationError, match="même identifiant"):
            _recommandation(
                alternatives=[
                    _recommandation(recommandation_id=identifiant),
                    _recommandation(recommandation_id=identifiant),
                ]
            )


class TestEnsemble:
    """§5 — l'absence d'action se dit, elle ne se déduit pas d'un vide."""

    def test_ensemble_vide_est_refuse(self) -> None:
        with pytest.raises(ValidationError):
            _ensemble([])

    def test_attente_surveillance_est_une_recommandation_valide(self) -> None:
        """Ne rien faire et observer est un conseil honnête, pas une absence."""
        attente = Recommendation(
            recommandation_id=uuid4(),
            type_action=TypeAction.ATTENTE_SURVEILLANCE,
            description="Observer l'évolution avant toute intervention.",
            justification=_justification(),
            niveau_confiance=0.4,
        )

        assert _ensemble([attente]).recommandations[0].type_action is (
            TypeAction.ATTENTE_SURVEILLANCE
        )

    def test_deux_recommandations_ne_partagent_pas_d_identifiant(self) -> None:
        identifiant = uuid4()

        with pytest.raises(ValidationError, match="même identifiant"):
            _ensemble(
                [
                    _recommandation(recommandation_id=identifiant),
                    _recommandation(recommandation_id=identifiant),
                ]
            )


class TestNiveauConfiance:
    """§6 — le niveau de confiance est affiché, donc borné."""

    @pytest.mark.parametrize("valeur", [-0.01, 1.01])
    def test_confiance_hors_bornes_est_refusee(self, valeur: float) -> None:
        with pytest.raises(ValidationError):
            Recommendation(
                recommandation_id=uuid4(),
                type_action=TypeAction.PLANTATION,
                description="Plantation.",
                justification=_justification(),
                niveau_confiance=valeur,
            )


class TestForestierDecision:
    """GSIE-CON-001 / CON-005 — l'écart du forestier est tracé, jamais exigé."""

    def test_refus_sans_justification_est_accepte(self) -> None:
        """Exiger une explication reviendrait à faire justifier le décideur."""
        decision = ForestierDecision(
            recommandation_id=uuid4(),
            decision=DecisionForestier.REFUSE,
            date_decision=datetime.now(UTC),
        )

        assert decision.justification_forestier is None

    def test_modification_sans_contenu_est_refusee(self) -> None:
        """Un écart dont le contenu est perdu ne documente rien."""
        with pytest.raises(ValidationError, match="modification"):
            ForestierDecision(
                recommandation_id=uuid4(),
                decision=DecisionForestier.MODIFIE,
                date_decision=datetime.now(UTC),
            )

    def test_modifications_sans_decision_modifie_sont_refusees(self) -> None:
        with pytest.raises(ValidationError, match="modifications"):
            ForestierDecision(
                recommandation_id=uuid4(),
                decision=DecisionForestier.ACCEPTE,
                modifications={"densite": "1100"},
                date_decision=datetime.now(UTC),
            )


class TestRequete:
    """§5 — la requête reprend les contraintes du forestier telles quelles."""

    def test_alternatives_demandees_par_defaut(self) -> None:
        requete = RecommendationRequest(
            requete_id=uuid4(),
            diagnostic_id=_DIAGNOSTIC,
            objectif_forestier=ObjectifForestier.PRODUCTION,
        )

        assert requete.alternatives_demandees is True

    def test_champ_inconnu_est_refuse(self) -> None:
        """`extra=forbid` : un champ mal orthographié doit échouer, pas être ignoré."""
        with pytest.raises(ValidationError):
            RecommendationRequest(
                requete_id=uuid4(),
                diagnostic_id=_DIAGNOSTIC,
                objectif_forestier=ObjectifForestier.MIXTE,
                objectif_secondaire="production",  # type: ignore[call-arg]
            )
