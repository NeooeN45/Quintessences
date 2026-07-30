"""Tests d'intégration — la chaîne tourne avec les sorties réelles des moteurs.

    Reasoning → Diagnostic → Recommendation → Décision → Validation

Ce que la couverture existante ne prouvait pas : `test_pipeline_cross_engine.py`
construit `Diagnostic`, `RecommendationSet` et `Conclusion` par instanciation
directe. Chaque moteur y est donc alimenté par un objet écrit à la main, jamais
par la sortie du précédent. Si le Diagnostic Engine produisait un objet que
`diagnostic_to_validation_request` ne sait pas convertir, aucun test ne tomberait.

C'est le premier obstacle qu'un client — l'application GeoSylva — rencontrerait :
il n'existe aucun endpoint d'orchestration, `pipeline.py` ne couvrant
qu'Evidence → Knowledge et n'étant exposé nulle part. Le client doit donc
enchaîner les moteurs lui-même, et chaque passage de main est un point de
rupture que rien ne surveille.

Chaque test ci-dessous prend la **sortie réelle** du moteur amont. Aucun objet
intermédiaire n'est fabriqué. La base est réelle : le diagnostic et les
recommandations sont persistés, avec leurs clés étrangères.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.diagnostic.engine import DiagnosticEngine
from gsie_api.engines.diagnostic.schemas import (
    DiagnosticRequest,
    DomaineElement,
    EtatGlobal,
    EtatGlobalDeclare,
    QualificationConclusion,
    RoleDiagnostic,
    TypeDiagnostic,
)
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.reasoning.engine import ReasoningEngine
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    ReasoningRequest,
    RegleInference,
    SourceMoteurContexte,
    StationContexte,
)
from gsie_api.engines.recommendation.engine import RecommendationEngine
from gsie_api.engines.recommendation.schemas import (
    ObjectifForestier,
    RecommendationRequest,
)
from gsie_api.engines.validation.engine import ValidationEngine
from gsie_api.engines.validation.schemas import ValidationStatut
from gsie_api.engines.validation_pipeline import (
    diagnostic_to_validation_request,
    ensemble_complet_to_validation_request,
)
from tests.conftest import requires_docker

pytestmark = requires_docker


def _source() -> SourceReference:
    """Référentiel pédologique français — source réelle, pas un placeholder."""
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="INRAE (2008)",
        date_publication="2008",
        reference="Référentiel pédologique français, édition 2008",
    )


def _regle_acidite() -> RegleInference:
    """Règle sourcée dont la condition porte sur un fait du contexte.

    La règle est fournie dans la requête plutôt que lue en base : ce module
    éprouve les **passages de main** entre moteurs, et faire dépendre le test
    d'un territoire enregistré y mêlerait une seconde exigence.
    """
    return RegleInference(
        identifiant="regle-acidite-01",
        condition="pedologie_pH < 5.5",
        enonce_conclusion="Le sol est acide.",
        source=_source(),
        evidence_level=EvidenceLevel.B,
        niveau_confiance=0.85,
    )


def _regle_profondeur() -> RegleInference:
    """Seconde règle, sur un autre fait du même bloc.

    Deux règles, donc **deux** conclusions. Ce n'est pas un détail : avec une
    conclusion unique, une troncature de `conclusions_source` à un élément est
    un non-événement, et le test qui vérifie la correspondance ne peut pas
    échouer. Le harnais de mutation l'a établi — `diagnostic_detache_de_ses_
    conclusions` avait survécu.
    """
    return RegleInference(
        identifiant="regle-profondeur-01",
        condition="pedologie_profondeur_cm > 50",
        enonce_conclusion="Le sol est profond.",
        source=_source(),
        evidence_level=EvidenceLevel.B,
        niveau_confiance=0.80,
    )


def _contexte() -> StationContexte:
    """Station acide — le fait qui déclenche la règle."""
    return StationContexte(
        pedologie=BlocContexte(
            source_moteur=SourceMoteurContexte.pedology,
            source=_source(),
            evidence_level=EvidenceLevel.B,
            valeurs={"pH": 5.2, "profondeur_cm": 80},
        )
    )


async def _inferer(session: AsyncSession):
    """Étape 1 — le Reasoning Engine produit de vraies conclusions."""
    requete = ReasoningRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        contexte=_contexte(),
        question="Le sol est-il acide ?",
        regles=[_regle_acidite(), _regle_profondeur()],
        profondeur_max=5,
    )
    resultat = await ReasoningEngine(session).infer(requete, datetime.now(UTC))
    assert len(resultat.conclusions) >= 2, (
        f"{len(resultat.conclusions)} conclusion(s) produite(s). La chaîne en "
        "exige au moins deux : avec une seule, une troncature de "
        "`conclusions_source` est indétectable, et les assertions en aval "
        "passent sans rien établir. Le harnais l'a démontré."
    )
    return resultat


async def _diagnostiquer(session: AsyncSession, inference):
    """Étape 2 — le Diagnostic Engine consomme les conclusions telles quelles."""
    conclusions = inference.conclusions
    requete = DiagnosticRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        conclusions=conclusions,
        qualifications=[
            QualificationConclusion(
                conclusion_id=conclusion.conclusion_id,
                role=RoleDiagnostic.contrainte,
                domaine_element=DomaineElement.pedologique,
            )
            for conclusion in conclusions
        ],
        etat_global=EtatGlobalDeclare(
            etat=EtatGlobal.vigueur_reduite,
            justification="Acidité marquée constatée sur la station",
            source=_source(),
            evidence_level=EvidenceLevel.B,
        ),
        contexte=_contexte(),
        type_diagnostic=TypeDiagnostic.stationnel,
    )
    return await DiagnosticEngine(session).diagnostiquer(requete, datetime.now(UTC))


@pytest.mark.asyncio
async def test_les_conclusions_du_raisonnement_alimentent_le_diagnostic(
    db_session: AsyncSession,
) -> None:
    """Le Diagnostic Engine accepte les `Conclusion` que le Reasoning produit.

    Le passage de main le plus fragile : `Conclusion` porte une chaîne
    d'inférence, un plancher de preuve et une méthode de confiance, et le
    Diagnostic Engine valide la bijection conclusions ↔ qualifications.
    """
    inference = await _inferer(db_session)

    diagnostic = await _diagnostiquer(db_session, inference)

    assert diagnostic.contraintes, "les conclusions n'ont pas produit de contrainte"
    assert set(diagnostic.conclusions_source) == {
        conclusion.conclusion_id for conclusion in inference.conclusions
    }, "le diagnostic ne référence pas les conclusions dont il est issu"


@pytest.mark.asyncio
async def test_le_plancher_du_diagnostic_ne_depasse_pas_celui_des_conclusions(
    db_session: AsyncSession,
) -> None:
    """Le plancher reste borné par ce que le raisonnement a réellement établi.

    Vérifié sur les vraies valeurs, et non sur un niveau déclaré à la main : une
    surestimation ici se lirait comme une fondation plus solide qu'elle n'est.
    """
    inference = await _inferer(db_session)

    diagnostic = await _diagnostiquer(db_session, inference)

    niveaux_conclusions = {c.evidence_level_plancher for c in inference.conclusions}
    assert diagnostic.evidence_level_plancher.value >= min(
        niveau.value for niveau in niveaux_conclusions
    ), (
        f"plancher du diagnostic {diagnostic.evidence_level_plancher} plus fort "
        f"que celui des conclusions {sorted(n.value for n in niveaux_conclusions)}"
    )


@pytest.mark.asyncio
async def test_le_diagnostic_reel_se_convertit_en_requete_de_validation(
    db_session: AsyncSession,
) -> None:
    """La sortie réelle du Diagnostic Engine passe le convertisseur de validation.

    Le convertisseur n'était éprouvé que sur des `Diagnostic` écrits à la main.
    Un champ que le moteur remplit autrement — ou ne remplit pas — n'aurait été
    découvert qu'en production.
    """
    inference = await _inferer(db_session)
    diagnostic = await _diagnostiquer(db_session, inference)

    requete = diagnostic_to_validation_request(diagnostic, inference.conclusions)
    resultat = await ValidationEngine().validate(requete)

    assert resultat.statut is not ValidationStatut.bloque, (
        "un diagnostic produit par le moteur est bloqué par la validation : "
        f"causes = {[c.description for c in resultat.causes_blocage]}"
    )


@pytest.mark.asyncio
async def test_la_chaine_complete_aboutit_a_une_sortie_validee(
    db_session: AsyncSession,
) -> None:
    """Reasoning → Diagnostic → Recommendation → Décision → Validation.

    Chaque étape reçoit la sortie réelle de la précédente. C'est le chemin qu'un
    client GeoSylva doit pouvoir suivre : aucun endpoint ne l'orchestre, donc
    aucun test ne l'établissait de bout en bout.
    """
    inference = await _inferer(db_session)
    diagnostic = await _diagnostiquer(db_session, inference)

    ensemble = await RecommendationEngine(db_session).recommend(
        RecommendationRequest(
            requete_id=uuid4(),
            diagnostic_id=diagnostic.diagnostic_id,
            objectif_forestier=ObjectifForestier.PRODUCTION,
            alternatives_demandees=True,
        )
    )

    assert (
        ensemble.diagnostic_source == diagnostic.diagnostic_id
    ), "l'ensemble ne se rattache pas au diagnostic dont il est issu"

    requete = ensemble_complet_to_validation_request(diagnostic, ensemble, inference.conclusions)
    resultat = await ValidationEngine().validate(requete)

    assert resultat.statut is not ValidationStatut.bloque, (
        "la chaîne complète est bloquée par la validation : "
        f"causes = {[c.description for c in resultat.causes_blocage]}"
    )
    # Toute sortie non bloquee doit rester explicable : c'est ce que la
    # validation controle, et c'est ce que le forestier lira.
    assert resultat.controles, "aucun contrôle exécuté — le résultat ne dit rien"
