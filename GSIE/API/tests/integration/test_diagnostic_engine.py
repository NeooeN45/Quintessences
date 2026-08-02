"""Tests d'intégration — Diagnostic Engine persiste en PostgreSQL.

Le Diagnostic Engine assemble des conclusions qualifiées et écrit son
résultat (`resource(type=diagnostic)` + `DiagnosticModel`) pour rendre le
`diagnostic_id` résolvable — ce qu'exige le Recommendation Engine en entrée.

Les 50+ tests unitaires emploient un `AsyncMock` de session : ils vérifient
le mapping objectif → action sans base, et ne prouvent pas que l'écriture
survit à un `SELECT` réel. Sans ce module, un stub qui avale tout
masquerait exactement ce qu'il simplifie — l'erreur déjà commise dans ce
dépôt, où des tests SQLite laissaient passer des violations de clé
étrangère que PostgreSQL refusait.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.diagnostic.engine import (
    DiagnosticConflitError,
    DiagnosticEngine,
    DiagnosticEngineError,
)
from gsie_api.engines.diagnostic.schemas import (
    ContradictionDeclaree,
    DiagnosticRequest,
    DomaineElement,
    DomaineRisque,
    EtatGlobal,
    EtatGlobalDeclare,
    Probabilite,
    QualificationConclusion,
    RoleDiagnostic,
    TypeDiagnostic,
)
from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    SourceReference,
    SourceType,
)
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    Conclusion,
    EtapeInference,
    MethodeConfiance,
    SourceMoteurContexte,
    StationContexte,
)
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.diagnostic import DiagnosticModel
from gsie_api.infrastructure.models.enums import (
    DiagnosticGlobalState,
    DiagnosticType,
    DiagnosticValidationStatus,
)
from tests.conftest import requires_docker

pytestmark = requires_docker

# Identifiants et horloge fixes pour le déterminisme.
_REQUETE_ID = UUID("22222222-2222-4222-8222-222222222222")
_STATION_ID = UUID("33333333-3333-4333-8333-333333333333")
_DATE_DIAGNOSTIC = datetime(2026, 7, 25, 12, 0, 0, tzinfo=UTC)
_DATE_AUTRE = datetime(2026, 7, 26, 8, 30, 0, tzinfo=UTC)


# --- Fabriques de test -------------------------------------------------------


def _source(
    *,
    auteur: str = "Rameau et al.",
    reference: str = "doi:10.0000/test",
) -> SourceReference:
    """Crée une SourceReference de test reproductible."""
    return SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur=auteur,
        reference=reference,
    )


def _etape(
    *,
    ordre: int = 1,
    evidence_level: EvidenceLevel = EvidenceLevel.B,
    source: SourceReference | None = None,
    regle: str = "R_TEST",
    conclusion_locale: str = "Conclusion locale de test",
) -> EtapeInference:
    """Crée une EtapeInference valide de test."""
    return EtapeInference(
        ordre=ordre,
        regle_appliquee=regle,
        source_regle=source or _source(),
        premisses=["pH <= 6.0"],
        conclusion_locale=conclusion_locale,
        evidence_level=evidence_level,
    )


def _conclusion(
    *,
    conclusion_id: UUID | None = None,
    enonce: str = "Le sol est acide.",
    niveau_confiance: float = 0.8,
    evidence_level_plancher: EvidenceLevel = EvidenceLevel.B,
    chaine: list[EtapeInference] | None = None,
) -> Conclusion:
    """Crée une Conclusion valide minimale.

    L'`evidence_level_plancher` est propagé à l'étape générée pour
    respecter la cohérence imposée par `Conclusion._plancher_coherent`.
    """
    etapes = chaine if chaine is not None else [_etape(evidence_level=evidence_level_plancher)]
    sources = [e.source_regle for e in etapes]
    return Conclusion(
        conclusion_id=conclusion_id or uuid4(),
        enonce=enonce,
        niveau_confiance=niveau_confiance,
        methode_confiance=MethodeConfiance.fournie_par_regle,
        evidence_level_plancher=evidence_level_plancher,
        chaine_inference=etapes,
        sources_utilisees=sources,
    )


def _bloc(
    *,
    source_moteur: SourceMoteurContexte = SourceMoteurContexte.pedology,
) -> BlocContexte:
    """Crée un BlocContexte valide de test."""
    return BlocContexte(
        source_moteur=source_moteur,
        source=_source(),
        evidence_level=EvidenceLevel.B,
        valeurs={"pH": 5.2},
    )


def _contexte_climat_seul() -> StationContexte:
    """Contexte avec seul bloc climat — 4 blocs absents."""
    return StationContexte(climat=_bloc(source_moteur=SourceMoteurContexte.climate))


def _contexte_complet() -> StationContexte:
    """Contexte avec les 5 blocs — zéro incertitude."""
    return StationContexte(
        geographie=_bloc(source_moteur=SourceMoteurContexte.gis),
        climat=_bloc(source_moteur=SourceMoteurContexte.climate),
        pedologie=_bloc(source_moteur=SourceMoteurContexte.pedology),
        botanique=_bloc(source_moteur=SourceMoteurContexte.botanical),
        peuplement=_bloc(source_moteur=SourceMoteurContexte.forest_dynamics),
    )


def _qualification(
    *,
    conclusion_id: UUID | None = None,
    role: RoleDiagnostic = RoleDiagnostic.contrainte,
    domaine_element: DomaineElement | None = DomaineElement.pedologique,
    domaine_risque: DomaineRisque | None = None,
    probabilite: Probabilite | None = None,
    horizon: str | None = None,
) -> QualificationConclusion:
    """Crée une QualificationConclusion valide (contrainte par défaut)."""
    if role is RoleDiagnostic.risque:
        return QualificationConclusion(
            conclusion_id=conclusion_id or uuid4(),
            role=role,
            domaine_element=None,
            domaine_risque=domaine_risque or DomaineRisque.climatique,
            probabilite=probabilite or Probabilite.eleve,
            horizon=horizon or "10 ans",
        )
    return QualificationConclusion(
        conclusion_id=conclusion_id or uuid4(),
        role=role,
        domaine_element=domaine_element,
        domaine_risque=None,
        probabilite=None,
        horizon=None,
    )


def _etat_global(
    evidence_level: EvidenceLevel = EvidenceLevel.B,
) -> EtatGlobalDeclare:
    """Crée un EtatGlobalDeclare valide de test."""
    return EtatGlobalDeclare(
        etat=EtatGlobal.vigueur_reduite,
        justification="Vigueur réduite constatée",
        source=_source(),
        evidence_level=evidence_level,
    )


def _requete(
    *,
    conclusions: list[Conclusion] | None = None,
    qualifications: list[QualificationConclusion] | None = None,
    contradictions: list[ContradictionDeclaree] | None = None,
    contexte: StationContexte | None = None,
    requete_id: UUID = _REQUETE_ID,
    evidence_etat_global: EvidenceLevel = EvidenceLevel.B,
) -> DiagnosticRequest:
    """Crée une DiagnosticRequest valide de test."""
    if conclusions is None:
        conclusions = [_conclusion()]
    if qualifications is None:
        qualifications = [_qualification(conclusion_id=c.conclusion_id) for c in conclusions]
    return DiagnosticRequest(
        requete_id=requete_id,
        station_id=_STATION_ID,
        conclusions=conclusions,
        qualifications=qualifications,
        etat_global=_etat_global(evidence_etat_global),
        contradictions=contradictions or [],
        contexte=contexte or _contexte_climat_seul(),
        type_diagnostic=TypeDiagnostic.stationnel,
    )


# --- Tests -------------------------------------------------------------------


async def should_persist_diagnostic_with_resource_root_when_diagnostiquer_called(
    db_session: AsyncSession,
) -> None:
    """Le diagnostic et sa racine resource existent en base après l'appel.

    ADR-001 : toute table satellite pointe vers `resource(id)`. Le moteur
    crée lui-même cette racine — si l'insertion échoue ou est oubliée, la
    FK `DiagnosticModel.id → resource.id` rejette la ligne. Vérifier les
    deux tables prouve que le contrat ADR-001 est respecté.
    """
    diagnostic = await DiagnosticEngine(db_session).diagnostiquer(_requete(), _DATE_DIAGNOSTIC)

    resource = await db_session.get(ResourceModel, diagnostic.diagnostic_id)
    assert resource is not None, "la racine resource(type=diagnostic) n'a pas été créée"
    assert resource.type == "diagnostic"

    ligne = await db_session.get(DiagnosticModel, diagnostic.diagnostic_id)
    assert ligne is not None, "la ligne diagnostic n'a pas été persistée"


async def should_persist_brouillon_status_when_engine_produces_diagnostic(
    db_session: AsyncSession,
) -> None:
    """Un moteur ne produit que des diagnostics à l'état brouillon (GSIE-CON-001).

    Le statut `valide` exige une `ValidationHumaine` nommant une personne —
    une machine ne peut pas se valider elle-même. Si la colonne portait
    `valide`, un diagnostic non relu circulerait comme s'il était établi.
    """
    diagnostic = await DiagnosticEngine(db_session).diagnostiquer(_requete(), _DATE_DIAGNOSTIC)

    ligne = await db_session.get(DiagnosticModel, diagnostic.diagnostic_id)
    assert ligne is not None
    assert ligne.statut_validation == DiagnosticValidationStatus.brouillon


async def should_persist_minimum_confidence_when_conclusions_have_varying_confidence(
    db_session: AsyncSession,
) -> None:
    """La confiance persistée est le minimum des conclusions, pas une moyenne.

    ADR-009 : le moteur n'invente aucune table de conversion. Un diagnostic
    n'est pas plus assuré que sa conclusion la moins assurée — la colonne
    `confiance` doit porter exactement ce minimum.
    """
    conclusion_forte = _conclusion(niveau_confiance=0.9, enonce="Sol profond.")
    conclusion_faible = _conclusion(niveau_confiance=0.3, enonce="pH incertain.")
    requete = _requete(
        conclusions=[conclusion_forte, conclusion_faible],
        qualifications=[
            _qualification(conclusion_id=conclusion_forte.conclusion_id),
            _qualification(conclusion_id=conclusion_faible.conclusion_id),
        ],
    )

    diagnostic = await DiagnosticEngine(db_session).diagnostiquer(requete, _DATE_DIAGNOSTIC)

    ligne = await db_session.get(DiagnosticModel, diagnostic.diagnostic_id)
    assert ligne is not None
    assert ligne.confiance == pytest.approx(0.3)


async def should_persist_evidence_level_plancher_when_elements_have_varying_levels(
    db_session: AsyncSession,
) -> None:
    """Le plancher persisté est le plus faible niveau parmi tous les éléments.

    Le plancher inclut l'état global depuis le correctif du moteur : sans
    lui, un diagnostic pouvait annoncer un plancher B alors que son état
    reposait sur une observation isolée de niveau F.
    """
    conclusion_elevee = _conclusion(
        niveau_confiance=0.8,
        evidence_level_plancher=EvidenceLevel.A,
        enonce="Sol profond et fertile.",
    )
    conclusion_faible = _conclusion(
        niveau_confiance=0.5,
        evidence_level_plancher=EvidenceLevel.E,
        enonce="Drainage incertain.",
    )
    requete = _requete(
        conclusions=[conclusion_elevee, conclusion_faible],
        qualifications=[
            _qualification(conclusion_id=conclusion_elevee.conclusion_id),
            _qualification(conclusion_id=conclusion_faible.conclusion_id),
        ],
        evidence_etat_global=EvidenceLevel.B,
    )

    diagnostic = await DiagnosticEngine(db_session).diagnostiquer(requete, _DATE_DIAGNOSTIC)

    ligne = await db_session.get(DiagnosticModel, diagnostic.diagnostic_id)
    assert ligne is not None
    assert ligne.evidence_level_plancher == EvidenceLevel.E


async def should_persist_contradictions_when_caller_declares_them(
    db_session: AsyncSession,
) -> None:
    """Les contradictions déclarées apparaissent dans le contenu persisté.

    Le moteur ne les arbitre jamais (S-3) : il les traduit en
    `ContradictionDomaines` et les présente au forestier. Vérifier qu'elles
    survivent à la sérialisation JSONB et au rechargement.
    """
    conclusion_a = _conclusion(enonce="Climat favorable à l'essence.")
    conclusion_b = _conclusion(enonce="Risque de sécheresse croissante.")
    contradiction = ContradictionDeclaree(
        conclusion_a=conclusion_a.conclusion_id,
        conclusion_b=conclusion_b.conclusion_id,
        description="Climat favorable vs sécheresse croissante",
    )
    requete = _requete(
        conclusions=[conclusion_a, conclusion_b],
        qualifications=[
            _qualification(
                conclusion_id=conclusion_a.conclusion_id,
                role=RoleDiagnostic.atout,
                domaine_element=DomaineElement.climatique,
            ),
            _qualification(
                conclusion_id=conclusion_b.conclusion_id,
                role=RoleDiagnostic.risque,
                domaine_risque=DomaineRisque.climatique,
            ),
        ],
        contradictions=[contradiction],
    )

    diagnostic = await DiagnosticEngine(db_session).diagnostiquer(requete, _DATE_DIAGNOSTIC)

    ligne = await db_session.get(DiagnosticModel, diagnostic.diagnostic_id)
    assert ligne is not None
    contradictions_persistees = ligne.contenu.get("contradictions", [])
    assert len(contradictions_persistees) == 1
    assert "sécheresse" in contradictions_persistees[0]["description"]


async def should_return_same_diagnostic_id_when_same_request_played_twice(
    db_session: AsyncSession,
) -> None:
    """Deux exécutions identiques produisent le même diagnostic_id (uuid5).

    Le déterminisme est une garantie du moteur : `diagnostic_id` est dérivé
    par `uuid5` du contenu, jamais par `uuid4`. Un rejeu retourne le
    diagnostic déjà enregistré — l'idempotence est un cas normal.
    """
    requete = _requete()

    premier = await DiagnosticEngine(db_session).diagnostiquer(requete, _DATE_DIAGNOSTIC)
    second = await DiagnosticEngine(db_session).diagnostiquer(requete, _DATE_AUTRE)

    assert premier.diagnostic_id == second.diagnostic_id

    # Une seule ligne en base — le rejeu ne crée pas de doublon.
    total = (
        (
            await db_session.execute(
                select(DiagnosticModel).where(DiagnosticModel.id == premier.diagnostic_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(total) == 1


async def should_raise_conflict_error_when_same_id_different_content(
    db_session: AsyncSession,
) -> None:
    """Un diagnostic différent portant le même id est refusé, pas écrasé.

    `diagnostic_id` est dérivé de la requête, des conclusions, des
    qualifications et de l'état global — mais pas des contradictions
    déclarées. Deux requêtes identiques par ailleurs, déclarant des
    contradictions différentes, dérivent le même identifiant pour deux
    contenus distincts. Le moteur refuse plutôt que d'écraser.
    """
    conclusion_a = _conclusion(enonce="Climat favorable.")
    conclusion_b = _conclusion(enonce="Sécheresse croissante.")
    base_requete = _requete(
        conclusions=[conclusion_a, conclusion_b],
        qualifications=[
            _qualification(conclusion_id=conclusion_a.conclusion_id),
            _qualification(conclusion_id=conclusion_b.conclusion_id),
        ],
    )

    # Premier appel : sans contradiction.
    await DiagnosticEngine(db_session).diagnostiquer(base_requete, _DATE_DIAGNOSTIC)

    # Second appel : même requête, mais une contradiction déclarée.
    # Le diagnostic_id est identique (les contradictions n'entrent pas
    # dans la dérivation), mais le contenu diffère.
    requete_avec_contradiction = _requete(
        conclusions=base_requete.conclusions,
        qualifications=base_requete.qualifications,
        contradictions=[
            ContradictionDeclaree(
                conclusion_a=conclusion_a.conclusion_id,
                conclusion_b=conclusion_b.conclusion_id,
                description="Opposition déclarée",
            )
        ],
    )

    with pytest.raises(DiagnosticConflitError, match="contenu différent"):
        await DiagnosticEngine(db_session).diagnostiquer(requete_avec_contradiction, _DATE_AUTRE)


async def should_persist_full_contenu_when_diagnostiquer_called(
    db_session: AsyncSession,
) -> None:
    """Le contenu JSONB persisté est le Diagnostic sérialisé intégral.

    `contenu` est la seule source de relecture (docstring du modèle) : les
    colonnes scalaires en sont des projections. Vérifier que les champs
    structurants (id, station, type, état global) survivent au cycle
    écriture → rechargement sans divergence.
    """
    requete = _requete()
    diagnostic = await DiagnosticEngine(db_session).diagnostiquer(requete, _DATE_DIAGNOSTIC)

    ligne = await db_session.get(DiagnosticModel, diagnostic.diagnostic_id)
    assert ligne is not None
    assert ligne.contenu["diagnostic_id"] == str(diagnostic.diagnostic_id)
    assert ligne.contenu["station_id"] == str(_STATION_ID)
    assert ligne.contenu["type_diagnostic"] == DiagnosticType.stationnel.value
    assert ligne.contenu["etat_global"] == DiagnosticGlobalState.vigueur_reduite.value


async def should_raise_engine_error_when_empty_inference_chain(
    db_session: AsyncSession,
) -> None:
    """Une chaîne d'inférence vide est refusée par le moteur.

    Le contrat Reasoning l'interdit via `min_length=1`, mais le moteur
    vérifie défensivement (`_construire_element`). Si une conclusion
    malformée parvenait au moteur, il lèverait `DiagnosticEngineError`
    plutôt que de produire un élément sans source.

    On appelle directement `_construire_element` avec une conclusion
    contournée via `model_construct` : `DiagnosticRequest` revalide
    ses conclusions, ce qui rend impossible l'arrivée d'une chaîne vide
    par la voie normale — la garde défensive reste testée isolément.
    """
    from gsie_api.engines.diagnostic.engine import _construire_element

    conclusion = _conclusion()
    conclusion_cassee = conclusion.model_construct(
        conclusion_id=conclusion.conclusion_id,
        enonce=conclusion.enonce,
        niveau_confiance=conclusion.niveau_confiance,
        methode_confiance=conclusion.methode_confiance,
        evidence_level_plancher=conclusion.evidence_level_plancher,
        chaine_inference=[],
        sources_utilisees=[],
        connaissances_utilisees=[],
        moteurs_solicites=[],
    )
    qualification = _qualification(conclusion_id=conclusion.conclusion_id)

    with pytest.raises(DiagnosticEngineError, match="chaîne d'inférence vide"):
        _construire_element(conclusion_cassee, qualification)


async def should_persist_incertitudes_when_context_blocks_missing(
    db_session: AsyncSession,
) -> None:
    """Les blocs de contexte absents produisent des incertitudes persistées.

    Le moteur constate factuellement les blocs absents (« aucune donnée
    pédologique pour cette station »). Ces incertitudes doivent survivre
    dans le contenu JSONB pour que le forestier sache ce que le diagnostic
    ne sait pas.
    """
    # Contexte avec seul bloc climat — 4 blocs absents.
    requete = _requete(contexte=_contexte_climat_seul())

    diagnostic = await DiagnosticEngine(db_session).diagnostiquer(requete, _DATE_DIAGNOSTIC)

    ligne = await db_session.get(DiagnosticModel, diagnostic.diagnostic_id)
    assert ligne is not None
    incertitudes = ligne.contenu.get("incertitudes", [])
    assert len(incertitudes) == 4, (
        "4 blocs absents (geographie, pedologie, botanique, peuplement) "
        "doivent produire 4 incertitudes"
    )
    assert any("géographique" in inc for inc in incertitudes)
    assert any("pédologique" in inc for inc in incertitudes)


async def should_persist_zero_incertitudes_when_context_complete(
    db_session: AsyncSession,
) -> None:
    """Un contexte complet ne produit aucune incertitude.

    Réciproque du test précédent : si tous les blocs sont présents, la
    liste des incertitudes est vide. Vérifie que le moteur ne fabrique
    pas d'incertitudes pour des blocs renseignés.
    """
    requete = _requete(contexte=_contexte_complet())

    diagnostic = await DiagnosticEngine(db_session).diagnostiquer(requete, _DATE_DIAGNOSTIC)

    ligne = await db_session.get(DiagnosticModel, diagnostic.diagnostic_id)
    assert ligne is not None
    assert ligne.contenu.get("incertitudes", []) == []
