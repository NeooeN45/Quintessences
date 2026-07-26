"""Tests unitaires — DiagnosticEngine.diagnostiquer.

Mission R3 : essayer de faire mentir le moteur. On cherche où il produit
une sortie fausse, non traçable, non reproductible — ou validée.

Pas de DB requise : ``diagnostiquer`` écrit désormais son résultat, mais un
``AsyncMock`` de session suffit pour observer ces écritures. La vérification
du schéma réel relève des tests d'intégration.

Valeurs métier utilisées (ADR-007) :
- pH 4,5–6,0 pour sol acide — source : Rameau et al., 2018.
- Précipitations ≥ 700 mm/an — source : ONF, 2020.
- Profondeur de sol ≥ 40 cm — source : Référentiel Pédologique Français, 2008.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from gsie_api.engines.diagnostic.engine import (
    DiagnosticConflitError,
    DiagnosticEngine,
    DiagnosticEngineError,
)
from gsie_api.engines.diagnostic.schemas import (
    ContradictionDeclaree,
    Diagnostic,
    DiagnosticRequest,
    DomaineElement,
    DomaineRisque,
    EtatGlobal,
    EtatGlobalDeclare,
    Probabilite,
    QualificationConclusion,
    RoleDiagnostic,
    StatutValidation,
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

# Identifiants et horloge fixes pour les tests de déterminisme.
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

    Par défaut, une chaîne à une seule étape. Pour tester l'attribution de
    source par la dernière étape, passer ``chaine`` avec plusieurs étapes.
    """
    etapes = chaine if chaine is not None else [_etape()]
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


def _etat_global() -> EtatGlobalDeclare:
    """Crée un EtatGlobalDeclare valide de test."""
    return EtatGlobalDeclare(
        etat=EtatGlobal.vigueur_reduite,
        justification="Vigueur réduite constatée",
        source=_source(),
        evidence_level=EvidenceLevel.B,
    )


def _requete(
    *,
    conclusions: list[Conclusion] | None = None,
    qualifications: list[QualificationConclusion] | None = None,
    contradictions: list[ContradictionDeclaree] | None = None,
    contexte: StationContexte | None = None,
    requete_id: UUID = _REQUETE_ID,
) -> DiagnosticRequest:
    """Crée une DiagnosticRequest valide de test.

    Si ``qualifications`` n'est pas fourni, en génère une par conclusion
    (bijection exigée par le validateur).
    """
    if conclusions is None:
        conclusions = [_conclusion()]
    if qualifications is None:
        qualifications = [_qualification(conclusion_id=c.conclusion_id) for c in conclusions]
    return DiagnosticRequest(
        requete_id=requete_id,
        station_id=_STATION_ID,
        conclusions=conclusions,
        qualifications=qualifications,
        etat_global=_etat_global(),
        contradictions=contradictions or [],
        contexte=contexte or _contexte_climat_seul(),
        type_diagnostic=TypeDiagnostic.stationnel,
    )


def _engine(session: AsyncMock | None = None) -> DiagnosticEngine:
    """Crée un moteur avec une session mockée.

    Depuis la persistance des diagnostics, ``diagnostiquer`` écrit : la
    session doit être un ``AsyncMock`` (``get`` et ``flush`` sont attendus).
    ``get`` retourne ``None`` par défaut — aucun diagnostic préexistant.
    """
    if session is None:
        session = AsyncMock()
        session.get.return_value = None
        session.add = Mock()
    return DiagnosticEngine(session=session)


async def _diagnostiquer(
    *,
    conclusions: list[Conclusion] | None = None,
    qualifications: list[QualificationConclusion] | None = None,
    contradictions: list[ContradictionDeclaree] | None = None,
    contexte: StationContexte | None = None,
    requete_id: UUID = _REQUETE_ID,
    date_diagnostic: datetime = _DATE_DIAGNOSTIC,
) -> object:
    """Exécute le moteur avec une requête de test et retourne le Diagnostic.

    Retourne ``object`` pour que les tests vérifient le type via isinstance,
    pas via annotation — c'est un test, pas une déclaration de confiance.
    """
    requete = _requete(
        conclusions=conclusions,
        qualifications=qualifications,
        contradictions=contradictions,
        contexte=contexte,
        requete_id=requete_id,
    )
    return await _engine().diagnostiquer(requete, date_diagnostic)


# ---------------------------------------------------------------------------
# Déterminisme — obligatoire, et le premier à écrire
# ---------------------------------------------------------------------------


class TestDeterminisme:
    """Mêmes entrées et même horloge → sortie identique."""

    async def test_dix_executions_sorties_identiques(self) -> None:
        """Dix exécutions sur la même requête et la même horloge donnent des
        sorties strictement égales.

        Rend impossible : un moteur non déterministe — un diagnostic qui
        change entre deux exécutions identiques n'est pas reproductible,
        donc pas auditable.
        """
        from gsie_api.engines.diagnostic.schemas import Diagnostic

        conclusions = [
            _conclusion(conclusion_id=UUID(f"00000000-0000-4000-8000-{i:012d}")) for i in range(3)
        ]
        qualifications = [_qualification(conclusion_id=c.conclusion_id) for c in conclusions]
        requete = _requete(conclusions=conclusions, qualifications=qualifications)

        premier = await _engine().diagnostiquer(requete, _DATE_DIAGNOSTIC)
        for _ in range(9):
            suivant = await _engine().diagnostiquer(requete, _DATE_DIAGNOSTIC)
            assert suivant == premier
            assert isinstance(suivant, Diagnostic)

    async def test_permutation_conclusions_sortie_inchangee(self) -> None:
        """Permuter l'ordre des conclusions dans la requête ne change pas la
        sortie.

        Rend impossible : une dépendance à l'ordre d'itération des
        conclusions — le moteur doit trier, pas subir l'ordre d'arrivée.
        """
        c1 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000001"))
        c2 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000002"))
        q1 = _qualification(conclusion_id=c1.conclusion_id)
        q2 = _qualification(conclusion_id=c2.conclusion_id)

        diag_a = await _diagnostiquer(conclusions=[c1, c2], qualifications=[q1, q2])
        diag_b = await _diagnostiquer(conclusions=[c2, c1], qualifications=[q2, q1])
        assert diag_a == diag_b

    async def test_permutation_qualifications_sortie_inchangee(self) -> None:
        """Permuter l'ordre des qualifications ne change pas la sortie.

        Rend impossible : une dépendance à l'ordre des qualifications —
        les qualifications sont triées par conclusion_id avant traitement.
        """
        c1 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000001"))
        c2 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000002"))
        q1 = _qualification(conclusion_id=c1.conclusion_id)
        q2 = _qualification(conclusion_id=c2.conclusion_id)

        diag_a = await _diagnostiquer(conclusions=[c1, c2], qualifications=[q1, q2])
        diag_b = await _diagnostiquer(conclusions=[c1, c2], qualifications=[q2, q1])
        assert diag_a == diag_b

    async def test_permutation_contradictions_sortie_inchangee(self) -> None:
        """Permuter l'ordre des contradictions déclarées ne change pas la
        sortie.

        Rend impossible : une dépendance à l'ordre des contradictions —
        elles sont triées par (conclusion_a, conclusion_b).
        """
        c1 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000001"))
        c2 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000002"))
        c3 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000003"))
        q1 = _qualification(
            conclusion_id=c1.conclusion_id, domaine_element=DomaineElement.pedologique
        )
        q2 = _qualification(
            conclusion_id=c2.conclusion_id, domaine_element=DomaineElement.climatique
        )
        q3 = _qualification(
            conclusion_id=c3.conclusion_id, domaine_element=DomaineElement.botanique
        )

        contra1 = ContradictionDeclaree(
            conclusion_a=c1.conclusion_id,
            conclusion_b=c2.conclusion_id,
            description="Sol favorable, climat défavorable",
        )
        contra2 = ContradictionDeclaree(
            conclusion_a=c1.conclusion_id,
            conclusion_b=c3.conclusion_id,
            description="Sol favorable, botanique défavorable",
        )

        diag_a = await _diagnostiquer(
            conclusions=[c1, c2, c3],
            qualifications=[q1, q2, q3],
            contradictions=[contra1, contra2],
        )
        diag_b = await _diagnostiquer(
            conclusions=[c1, c2, c3],
            qualifications=[q1, q2, q3],
            contradictions=[contra2, contra1],
        )
        assert diag_a == diag_b

    async def test_horloges_differentes_seul_date_diagnostic_change(self) -> None:
        """Deux horloges différentes ne changent QUE date_diagnostic.

        Rend impossible : un diagnostic_id ou un contenu qui dépendrait de
        l'horloge — l'horloge est une entrée pour la trace, pas pour le
        calcul.
        """
        cid = UUID("00000000-0000-4000-8000-000000000001")
        conclusion = _conclusion(conclusion_id=cid)
        requete = _requete(
            conclusions=[conclusion],
            qualifications=[_qualification(conclusion_id=cid)],
        )
        diag_a = await _engine().diagnostiquer(requete, _DATE_DIAGNOSTIC)
        diag_b = await _engine().diagnostiquer(requete, _DATE_AUTRE)

        # date_diagnostic change.
        assert diag_a.date_diagnostic == _DATE_DIAGNOSTIC
        assert diag_b.date_diagnostic == _DATE_AUTRE
        # Tout le reste est identique.
        assert diag_a.diagnostic_id == diag_b.diagnostic_id
        assert diag_a.contraintes == diag_b.contraintes
        assert diag_a.atouts == diag_b.atouts
        assert diag_a.risques == diag_b.risques
        assert diag_a.contradictions == diag_b.contradictions
        assert diag_a.incertitudes == diag_b.incertitudes
        assert diag_a.conclusions_source == diag_b.conclusions_source
        assert diag_a.confiance == diag_b.confiance


# ---------------------------------------------------------------------------
# Attribution de la source — le point le plus surveillé
# ---------------------------------------------------------------------------


class TestAttributionSource:
    """La source d'un élément est celle de la dernière étape de la chaîne."""

    async def test_chaine_une_etape_source_de_cette_etape(self) -> None:
        """Chaîne à une seule étape : la source de l'élément est celle-là.

        Rend impossible : l'attribution à une source absente — avec une
        seule étape, il n'y a pas d'ambiguïté, et toute erreur est visible.
        """
        source_attendue = _source(auteur="Dupont et al.", reference="doi:10.0001/unique")
        conclusion = _conclusion(
            chaine=[_etape(source=source_attendue)],
        )
        diag = await _diagnostiquer(
            conclusions=[conclusion],
            qualifications=[_qualification(conclusion_id=conclusion.conclusion_id)],
        )
        assert len(diag.contraintes) == 1  # type: ignore[attr-defined]
        assert diag.contraintes[0].source == source_attendue  # type: ignore[attr-defined]

    async def test_chaine_trois_etapes_source_de_la_troisieme(self) -> None:
        """Chaîne à trois étapes avec trois sources différentes : la source
        de l'élément est celle de la troisième, pas de la première.

        Rend impossible : l'attribution à une étape intermédiaire —
        l'affirmation portée par l'élément est celle produite par la règle
        terminale. Attribuer à la première étape ferait porter l'assertion
        par un travail qui ne l'a pas produite.
        """
        s1 = _source(auteur="Auteur 1", reference="ref-1")
        s2 = _source(auteur="Auteur 2", reference="ref-2")
        s3 = _source(auteur="Auteur 3", reference="ref-3")
        conclusion = _conclusion(
            chaine=[
                _etape(ordre=1, source=s1),
                _etape(ordre=2, source=s2),
                _etape(ordre=3, source=s3),
            ],
            evidence_level_plancher=EvidenceLevel.B,
        )
        diag = await _diagnostiquer(
            conclusions=[conclusion],
            qualifications=[_qualification(conclusion_id=conclusion.conclusion_id)],
        )
        assert diag.contraintes[0].source == s3  # type: ignore[attr-defined]
        assert diag.contraintes[0].source != s1  # type: ignore[attr-defined]

    async def test_deux_conclusions_source_terminale_partagee(self) -> None:
        """Deux conclusions partageant leur source terminale : les deux
        éléments portent la même source, sans déduplication abusive.

        Rend impossible : une fusion de deux éléments distincts sous prétexte
        qu'ils partagent une source — ce sont deux conclusions différentes.
        """
        source_partagee = _source(auteur="Source commune", reference="ref-commune")
        c1 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000001"),
            enonce="Le sol est acide.",
            chaine=[_etape(source=source_partagee)],
        )
        c2 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000002"),
            enonce="Le sol est profond.",
            chaine=[_etape(source=source_partagee)],
        )
        diag = await _diagnostiquer(
            conclusions=[c1, c2],
            qualifications=[
                _qualification(conclusion_id=c1.conclusion_id),
                _qualification(conclusion_id=c2.conclusion_id),
            ],
        )
        assert len(diag.contraintes) == 2  # type: ignore[attr-defined]
        assert diag.contraintes[0].source == source_partagee  # type: ignore[attr-defined]
        assert diag.contraintes[1].source == source_partagee  # type: ignore[attr-defined]
        assert diag.contraintes[0].description != diag.contraintes[1].description  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Niveau de preuve — jamais surévalué
# ---------------------------------------------------------------------------


class TestNiveauPreuve:
    """L'evidence_level d'un élément est le plancher, pas la dernière étape."""

    async def test_evidence_level_est_plancher_pas_derniere_etape(self) -> None:
        """Conclusion dont la dernière étape est en A mais le plancher en D :
        l'élément doit être en D.

        Rend impossible : la surévaluation d'une preuve — afficher A
        alors que le plus faible maillon est D donnerait une confiance
        que la chaîne ne soutient pas.
        """
        conclusion = _conclusion(
            chaine=[
                _etape(ordre=1, evidence_level=EvidenceLevel.D),
                _etape(ordre=2, evidence_level=EvidenceLevel.A),
            ],
            evidence_level_plancher=EvidenceLevel.D,
        )
        diag = await _diagnostiquer(
            conclusions=[conclusion],
            qualifications=[_qualification(conclusion_id=conclusion.conclusion_id)],
        )
        assert diag.contraintes[0].evidence_level is EvidenceLevel.D  # type: ignore[attr-defined]

    async def test_plancher_diagnostic_tient_compte_des_risques(self) -> None:
        """Le plancher du diagnostic tient compte des risques autant que des
        contraintes et atouts.

        Rend impossible : l'oubli des risques dans le calcul du plancher —
        un diagnostic dont le seul élément faible est un risque doit avoir
        ce plancher-là, pas un plancher tiré vers le haut par les atouts.
        """
        # Contrainte en A (preuve forte), risque en D (preuve faible).
        c_contrainte = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000001"),
            enonce="Sol profond.",
            evidence_level_plancher=EvidenceLevel.A,
            chaine=[_etape(evidence_level=EvidenceLevel.A)],
        )
        c_risque = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000002"),
            enonce="Risque de dépérissement.",
            evidence_level_plancher=EvidenceLevel.D,
            chaine=[_etape(evidence_level=EvidenceLevel.D)],
        )
        diag = await _diagnostiquer(
            conclusions=[c_contrainte, c_risque],
            qualifications=[
                _qualification(conclusion_id=c_contrainte.conclusion_id, role=RoleDiagnostic.atout),
                _qualification(
                    conclusion_id=c_risque.conclusion_id,
                    role=RoleDiagnostic.risque,
                    domaine_risque=DomaineRisque.sanitaire,
                ),
            ],
        )
        # Le plancher doit être D (le risque), pas A (l'atout).
        assert diag.evidence_level_plancher is EvidenceLevel.D  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Confiance — minimum, jamais moyenne
# ---------------------------------------------------------------------------


class TestConfiance:
    """confiance = minimum des niveau_confiance, jamais moyenne."""

    async def test_confiance_minimum_trois_conclusions(self) -> None:
        """Trois conclusions à 0.9, 0.4, 0.7 : confiance = 0.4.

        Rend impossible : une confiance supérieure à la conclusion la moins
        assurée — un diagnostic n'est pas plus confiant que son maillon
        faible.
        """
        c1 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000001"),
            niveau_confiance=0.9,
        )
        c2 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000002"),
            niveau_confiance=0.4,
        )
        c3 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000003"),
            niveau_confiance=0.7,
        )
        diag = await _diagnostiquer(
            conclusions=[c1, c2, c3],
            qualifications=[_qualification(conclusion_id=c.conclusion_id) for c in [c1, c2, c3]],
        )
        assert diag.confiance == 0.4  # type: ignore[attr-defined]

    async def test_confiance_une_seule_conclusion(self) -> None:
        """Une seule conclusion : confiance = sa propre confiance.

        Rend impossible : une transformation d'une confiance unique —
        avec une seule conclusion, min() = cette conclusion, pas autre chose.
        """
        conclusion = _conclusion(niveau_confiance=0.65)
        diag = await _diagnostiquer(
            conclusions=[conclusion],
            qualifications=[_qualification(conclusion_id=conclusion.conclusion_id)],
        )
        assert diag.confiance == 0.65  # type: ignore[attr-defined]

    async def test_confiance_pas_de_moyenne(self) -> None:
        """0.9 et 0.1 donnent 0.1, pas 0.5.

        Rend impossible : le calcul d'une moyenne — une moyenne fabriquerait
        un nombre nouveau, non sourcé, interdit par ADR-007. Le minimum
        sélectionne une valeur existante.
        """
        c1 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000001"),
            niveau_confiance=0.9,
        )
        c2 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000002"),
            niveau_confiance=0.1,
        )
        diag = await _diagnostiquer(
            conclusions=[c1, c2],
            qualifications=[_qualification(conclusion_id=c.conclusion_id) for c in [c1, c2]],
        )
        assert diag.confiance == 0.1  # type: ignore[attr-defined]
        assert diag.confiance != 0.5  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Contradictions — déclarées ou absentes, jamais devinées
# ---------------------------------------------------------------------------


class TestContradictions:
    """Les contradictions sont déclarées, jamais déduites du texte."""

    async def test_deux_contraintes_domaines_differents_produite(self) -> None:
        """Contradiction entre deux contraintes de domaines différents :
        produite.

        Rend impossible : l'invisibilité d'une contradiction inter-domaines
        — sol favorable et climat défavorable est une information que le
        forestier doit voir.
        """
        c1 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000001"))
        c2 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000002"))
        contra = ContradictionDeclaree(
            conclusion_a=c1.conclusion_id,
            conclusion_b=c2.conclusion_id,
            description="Sol favorable, climat défavorable",
        )
        diag = await _diagnostiquer(
            conclusions=[c1, c2],
            qualifications=[
                _qualification(
                    conclusion_id=c1.conclusion_id, domaine_element=DomaineElement.pedologique
                ),
                _qualification(
                    conclusion_id=c2.conclusion_id, domaine_element=DomaineElement.climatique
                ),
            ],
            contradictions=[contra],
        )
        assert len(diag.contradictions) == 1  # type: ignore[attr-defined]
        assert diag.contradictions[0].description == "Sol favorable, climat défavorable"  # type: ignore[attr-defined]

    async def test_atout_contre_risque_produite(self) -> None:
        """Contradiction entre un atout et un risque : produite.

        Rend impossible : l'invisibilité de la contradiction la plus
        fréquente — un atout pédologique contre un risque climatique.
        L'ancien contrat rendait ce cas inexprimable.
        """
        c_atout = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000001"),
            enonce="Sol profond et fertile.",
        )
        c_risque = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000002"),
            enonce="Déficit hydrique croissant.",
        )
        contra = ContradictionDeclaree(
            conclusion_a=c_atout.conclusion_id,
            conclusion_b=c_risque.conclusion_id,
            description="Sol favorable mais déficit hydrique croissant",
        )
        diag = await _diagnostiquer(
            conclusions=[c_atout, c_risque],
            qualifications=[
                _qualification(conclusion_id=c_atout.conclusion_id, role=RoleDiagnostic.atout),
                _qualification(
                    conclusion_id=c_risque.conclusion_id,
                    role=RoleDiagnostic.risque,
                    domaine_risque=DomaineRisque.climatique,
                ),
            ],
            contradictions=[contra],
        )
        assert len(diag.contradictions) == 1  # type: ignore[attr-defined]
        assert diag.contradictions[0].description == "Sol favorable mais déficit hydrique croissant"  # type: ignore[attr-defined]

    async def test_meme_domaine_produite_avec_domaines_egaux(self) -> None:
        """Contradiction entre deux conclusions projetant sur le même domaine
        : produite, avec domaine_a == domaine_b.

        Rend impossible : l'invisibilité d'un conflit bibliographique au sein
        d'une même discipline — deux affirmations pédologiques opposées sont
        le cas normal des contradictions intra-domaine que
        SCIENTIFIC_CONSTITUTION S-3 demande de faire remonter. L'ancien
        contrat rejetait ce cas ; il est désormais légitime et produit.
        """
        from gsie_api.engines.diagnostic.schemas import Domaine

        c1 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000001"),
            enonce="Le sol est profond et fertile.",
        )
        c2 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000002"),
            enonce="Le sol est superficiel et pauvre.",
        )
        contra = ContradictionDeclaree(
            conclusion_a=c1.conclusion_id,
            conclusion_b=c2.conclusion_id,
            description="Conflit bibliographique sur la fertilité du sol",
        )
        diag = await _diagnostiquer(
            conclusions=[c1, c2],
            qualifications=[
                _qualification(
                    conclusion_id=c1.conclusion_id, domaine_element=DomaineElement.pedologique
                ),
                _qualification(
                    conclusion_id=c2.conclusion_id, domaine_element=DomaineElement.pedologique
                ),
            ],
            contradictions=[contra],
        )
        assert len(diag.contradictions) == 1  # type: ignore[attr-defined]
        contradiction = diag.contradictions[0]  # type: ignore[attr-defined]
        assert contradiction.description == "Conflit bibliographique sur la fertilité du sol"
        assert contradiction.domaine_a is Domaine.pedologique
        assert contradiction.domaine_b is Domaine.pedologique
        # Assertion plus forte : domaine_a == domaine_b est désormais légitime.
        assert contradiction.domaine_a == contradiction.domaine_b

    async def test_atout_contre_risque_meme_domaine_climatique(self) -> None:
        """Contradiction entre un atout climatique et un risque climatique :
        produite, les deux projections sur Domaine.climatique.

        Rend impossible : l'invisibilité du cas réel le plus fréquent —
        « climat favorable à l'essence » contre « risque de sécheresse
        croissante ». L'ancien contrat interdisait ce cas en rejetant toute
        contradiction intra-domaine ; c'était une erreur de conception qui
        masquait le cœur du sujet forestier.
        """
        from gsie_api.engines.diagnostic.schemas import Domaine

        c_atout = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000001"),
            enonce="Le climat est favorable à l'essence chêne sessile.",
        )
        c_risque = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000002"),
            enonce="Le risque de sécheresse croissante menace l'essence.",
        )
        contra = ContradictionDeclaree(
            conclusion_a=c_atout.conclusion_id,
            conclusion_b=c_risque.conclusion_id,
            description="Climat favorable mais sécheresse croissante",
        )
        diag = await _diagnostiquer(
            conclusions=[c_atout, c_risque],
            qualifications=[
                _qualification(
                    conclusion_id=c_atout.conclusion_id,
                    role=RoleDiagnostic.atout,
                    domaine_element=DomaineElement.climatique,
                ),
                _qualification(
                    conclusion_id=c_risque.conclusion_id,
                    role=RoleDiagnostic.risque,
                    domaine_risque=DomaineRisque.climatique,
                ),
            ],
            contradictions=[contra],
        )
        assert len(diag.contradictions) == 1  # type: ignore[attr-defined]
        contradiction = diag.contradictions[0]  # type: ignore[attr-defined]
        assert contradiction.description == "Climat favorable mais sécheresse croissante"
        assert contradiction.domaine_a is Domaine.climatique
        assert contradiction.domaine_b is Domaine.climatique
        # Le cas autrefois interdit est désormais le cas réel central.
        assert contradiction.domaine_a == contradiction.domaine_b

    async def test_aucune_contradiction_liste_vide(self) -> None:
        """Aucune contradiction déclarée : liste vide, pas d'erreur.

        Rend impossible : l'invention d'une contradiction — l'absence de
        contradiction déclarée est un résultat honnête, pas une panne.
        """
        diag = await _diagnostiquer()
        assert diag.contradictions == []  # type: ignore[attr-defined]

    async def test_oppositions_non_declarees_ne_produisent_rien(self) -> None:
        """Deux conclusions manifestement opposées mais non déclarées ne
        produisent RIEN.

        Rend impossible : la détection de contradiction par analyse du
        texte — le moteur ne compare aucun énoncé. Deviner une opposition
        serait de l'invention (GSIE-CON-002).
        """
        c1 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000001"),
            enonce="Le sol est profond et fertile.",
        )
        c2 = _conclusion(
            conclusion_id=UUID("00000000-0000-4000-8000-000000000002"),
            enonce="Le sol est superficiel et pauvre.",
        )
        # Aucune contradiction déclarée — les énoncés sont opposés, mais
        # le moteur ne doit pas le deviner.
        diag = await _diagnostiquer(
            conclusions=[c1, c2],
            qualifications=[
                _qualification(
                    conclusion_id=c1.conclusion_id, domaine_element=DomaineElement.pedologique
                ),
                _qualification(
                    conclusion_id=c2.conclusion_id, domaine_element=DomaineElement.pedologique
                ),
            ],
        )
        assert diag.contradictions == []  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Incertitudes — constats factuels d'absence, jamais d'invention
# ---------------------------------------------------------------------------


class TestIncertitudes:
    """Les incertitudes constatent l'absence de blocs, rien d'autre."""

    async def test_contexte_climat_seul_quatre_constats(self) -> None:
        """Un contexte avec le seul bloc climat produit quatre constats
        d'absence.

        Rend impossible : l'oubli d'un bloc absent — le forestier doit savoir
        que le diagnostic manque de données géographiques, pédologiques,
        botaniques et de peuplement.
        """
        diag = await _diagnostiquer(contexte=_contexte_climat_seul())
        assert len(diag.incertitudes) == 4  # type: ignore[attr-defined]
        # Vérifie qu'aucun constat ne mentionne le climat (présent).
        for incertitude in diag.incertitudes:  # type: ignore[attr-defined]
            assert "climatique" not in incertitude

    async def test_contexte_complet_zero_constat(self) -> None:
        """Un contexte complet produit zéro constat d'absence.

        Rend impossible : un faux constat d'absence sur un bloc présent —
        un diagnostic ne doit pas signaler de manque là où il y a des données.
        """
        diag = await _diagnostiquer(contexte=_contexte_complet())
        assert diag.incertitudes == []  # type: ignore[attr-defined]

    async def test_liste_triee(self) -> None:
        """La liste des incertitudes est triée (ordre des blocs figé).

        Rend impossible : un ordre non déterministe — deux exécutions
        doivent produire la même liste dans le même ordre.
        """
        diag = await _diagnostiquer(contexte=_contexte_climat_seul())
        # L'ordre attendu : géographique, pédologique, botanique, peuplement
        # (climat est présent, donc absent de la liste).
        attendu = [
            "aucune donnée géographique pour cette station",
            "aucune donnée pédologique pour cette station",
            "aucune donnée botanique pour cette station",
            "aucune donnée de peuplement pour cette station",
        ]
        assert diag.incertitudes == attendu  # type: ignore[attr-defined]

    async def test_aucune_incertitude_metier_inventee(self) -> None:
        """Aucune incertitude « métier » inventée n'apparaît.

        Rend impossible : l'invention d'une incertitude non factuelle —
        le moteur ne produit que des constats d'absence de blocs, pas
        d'analyses de risque ou de jugements sur la qualité des données.
        """
        diag = await _diagnostiquer(contexte=_contexte_complet())
        # Contexte complet → zéro incertitude. Si le moteur inventait des
        # incertitudes « métier », elles apparaîtraient même avec un
        # contexte complet.
        assert diag.incertitudes == []  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Traçabilité — chaque élément remonte à une conclusion réelle
# ---------------------------------------------------------------------------


class TestTraceabilite:
    """Chaque élément est traçable à sa conclusion d'origine."""

    async def test_conclusions_source_exactes_et_triees(self) -> None:
        """conclusions_source contient exactement les identifiants des
        conclusions fournies, triés, sans doublon.

        Rend impossible : la perte d'une conclusion dans la trace — un
        élément produit sans que sa conclusion d'origine apparaisse dans
        conclusions_source serait non traçable.
        """
        ids = [
            UUID("00000000-0000-4000-8000-000000000003"),
            UUID("00000000-0000-4000-8000-000000000001"),
            UUID("00000000-0000-4000-8000-000000000002"),
        ]
        conclusions = [_conclusion(conclusion_id=cid) for cid in ids]
        diag = await _diagnostiquer(
            conclusions=conclusions,
            qualifications=[_qualification(conclusion_id=c.conclusion_id) for c in conclusions],
        )
        # Trié, sans doublon, exactement les IDs fournis.
        assert diag.conclusions_source == sorted(ids)  # type: ignore[attr-defined]
        assert len(diag.conclusions_source) == 3  # type: ignore[attr-defined]
        assert len(set(diag.conclusions_source)) == 3  # type: ignore[attr-defined]

    async def test_description_egale_enonce_mot_pour_mot(self) -> None:
        """La description d'un élément est l'énoncé de sa conclusion, mot
        pour mot : aucune reformulation, aucune troncature, aucune
        majuscule ajoutée.

        Rend impossible : la reformulation d'un énoncé — reformuler serait
        interpréter, et interpréter est interdit (GSIE-CON-002). Le
        forestier doit lire exactement ce que le Reasoning Engine a produit.
        """
        enonce_original = "Le sol est acide, pH 5,2, avec une profondeur de 60 cm."
        conclusion = _conclusion(enonce=enonce_original)
        diag = await _diagnostiquer(
            conclusions=[conclusion],
            qualifications=[_qualification(conclusion_id=conclusion.conclusion_id)],
        )
        assert diag.contraintes[0].description == enonce_original  # type: ignore[attr-defined]
        assert diag.contraintes[0].description is conclusion.enonce  # type: ignore[attr-defined]

    async def test_diagnostic_passe_les_validateurs(self) -> None:
        """Tout Diagnostic produit passe les validateurs de schemas.py.

        Rend impossible : un moteur qui construirait un objet que le contrat
        rejette — si le Diagnostic passe la construction Pydantic, c'est que
        les validateurs l'ont accepté. Un échec ici signifie que le moteur
        contourne une garantie.
        """
        from gsie_api.engines.diagnostic.schemas import Diagnostic

        diag = await _diagnostiquer()
        # Si le moteur a produit un objet, c'est un Diagnostic validé par
        # Pydantic. Vérifier explicitement le type et le statut.
        assert isinstance(diag, Diagnostic)
        assert diag.statut_validation is StatutValidation.brouillon
        assert diag.validation is None


# ---------------------------------------------------------------------------
# Identifiant — uuid5 déterministe
# ---------------------------------------------------------------------------


class TestIdentifiant:
    """diagnostic_id est déterministe et ne dépend pas de l'horloge."""

    async def test_diagnostic_id_stable_entre_executions(self) -> None:
        """diagnostic_id est stable entre deux exécutions identiques.

        Rend impossible : un identifiant aléatoire — un diagnostic_id qui
        change entre deux exécutions identiques rendrait la traçabilité
        impossible.
        """
        cid = UUID("00000000-0000-4000-8000-000000000001")
        conclusion = _conclusion(conclusion_id=cid)
        requete = _requete(
            conclusions=[conclusion],
            qualifications=[_qualification(conclusion_id=cid)],
        )
        diag_a = await _engine().diagnostiquer(requete, _DATE_DIAGNOSTIC)
        diag_b = await _engine().diagnostiquer(requete, _DATE_DIAGNOSTIC)
        assert diag_a.diagnostic_id == diag_b.diagnostic_id

    async def test_diagnostic_id_change_si_conclusions_changent(self) -> None:
        """diagnostic_id change si les conclusions changent.

        Rend impossible : deux diagnostics différents avec le même ID —
        cela créerait une collision dans la traçabilité.
        """
        c1 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000001"))
        c2 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000002"))
        diag_a = await _diagnostiquer(conclusions=[c1])
        diag_b = await _diagnostiquer(conclusions=[c2])
        assert diag_a.diagnostic_id != diag_b.diagnostic_id  # type: ignore[attr-defined]

    async def test_diagnostic_id_inchange_si_horloge_change(self) -> None:
        """diagnostic_id ne change pas si seule l'horloge change.

        Rend impossible : un identifiant qui dépendrait de l'horloge —
        l'horloge est une entrée pour la trace, pas pour l'identité du
        diagnostic.
        """
        cid = UUID("00000000-0000-4000-8000-000000000001")
        conclusion = _conclusion(conclusion_id=cid)
        requete = _requete(
            conclusions=[conclusion],
            qualifications=[_qualification(conclusion_id=cid)],
        )
        diag_a = await _engine().diagnostiquer(requete, _DATE_DIAGNOSTIC)
        diag_b = await _engine().diagnostiquer(requete, _DATE_AUTRE)
        assert diag_a.diagnostic_id == diag_b.diagnostic_id


# ---------------------------------------------------------------------------
# Robustesse — erreurs explicites et terminaison
# ---------------------------------------------------------------------------


class TestRobustesse:
    """Le moteur lève des erreurs explicites et termine sur les cas limites."""

    async def test_chaine_vide_erreur_explicite(self) -> None:
        """Une conclusion à chaîne vide : erreur explicite.

        Rend impossible : un crash silencieux (IndexError) sur une chaîne
        vide — le moteur vérifie défensivement et lève une erreur nommant
        la conclusion. Le contrat Reasoning l'interdit, mais ce moteur ne
        suppose pas : il vérifie.

        Note : Conclusion.model_construct() contourne la validation Pydantic
        (min_length=1 sur chaine_inference) pour tester le chemin défensif
        du moteur. C'est le seul moyen d'atteindre ce code.
        """
        cid = UUID("00000000-0000-4000-8000-000000000001")
        # model_construct contourne la validation Pydantic (min_length=1 sur
        # chaine_inference). DiagnosticRequest.model_construct() contourne
        # aussi la re-validation des Conclusion imbriquées — sans quoi
        # Pydantic revaliderait la conclusion et lèverait ValidationError
        # avant que le moteur ne voie la chaîne vide.
        conclusion_vide = Conclusion.model_construct(
            conclusion_id=cid,
            enonce="Conclusion à chaîne vide",
            niveau_confiance=0.5,
            methode_confiance=MethodeConfiance.fournie_par_regle,
            evidence_level_plancher=EvidenceLevel.B,
            chaine_inference=[],
            sources_utilisees=[],
            connaissances_utilisees=[],
            moteurs_solicites=[],
        )
        requete = DiagnosticRequest.model_construct(
            requete_id=_REQUETE_ID,
            station_id=_STATION_ID,
            conclusions=[conclusion_vide],
            qualifications=[_qualification(conclusion_id=cid)],
            etat_global=_etat_global(),
            contradictions=[],
            contexte=_contexte_climat_seul(),
            type_diagnostic=TypeDiagnostic.stationnel,
        )
        with pytest.raises(DiagnosticEngineError, match="chaîne d'inférence vide"):
            await _engine().diagnostiquer(requete, _DATE_DIAGNOSTIC)

    async def test_un_seul_element_diagnostic_valide(self) -> None:
        """Un seul élément, aucun risque, aucune contradiction : diagnostic
        valide.

        Rend impossible : le rejet d'un diagnostic minimal — un diagnostic
        fondé sur une seule contrainte est légitime et honnête.
        """
        diag = await _diagnostiquer()
        assert len(diag.contraintes) == 1  # type: ignore[attr-defined]
        assert diag.atouts == []  # type: ignore[attr-defined]
        assert diag.risques == []  # type: ignore[attr-defined]
        assert diag.contradictions == []  # type: ignore[attr-defined]

    async def test_vingt_conclusions_terminaison_rapide(self) -> None:
        """Vingt conclusions qualifiées : terminaison rapide, sortie cohérente.

        Rend impossible : une explosion combinatoire ou une boucle infinie
        — le moteur est linéaire en nombre de conclusions.
        """
        conclusions = [
            _conclusion(conclusion_id=UUID(f"00000000-0000-4000-8000-{i:012d}")) for i in range(20)
        ]
        qualifications = [_qualification(conclusion_id=c.conclusion_id) for c in conclusions]
        diag = await _diagnostiquer(conclusions=conclusions, qualifications=qualifications)
        assert len(diag.contraintes) == 20  # type: ignore[attr-defined]
        assert len(diag.conclusions_source) == 20  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Garantie constitutionnelle — GSIE-CON-001
# ---------------------------------------------------------------------------


class TestGarantieConstitutionnelle:
    """Le moteur ne produit JAMAIS un diagnostic autre que brouillon."""

    async def test_statut_validation_toujours_brouillon(self) -> None:
        """Quel que soit le contenu de la requête, statut_validation reste
        brouillon.

        Rend impossible : un moteur qui produirait un diagnostic validé —
        c'est la garantie GSIE-CON-001 : le forestier décide, la machine
        propose. Un diagnostic validé par la machine est le défaut le plus
        grave que ce projet puisse contenir.
        """
        # Cas nominal.
        diag = await _diagnostiquer()
        assert diag.statut_validation is StatutValidation.brouillon  # type: ignore[attr-defined]

        # Cas avec contradictions.
        c1 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000001"))
        c2 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000002"))
        contra = ContradictionDeclaree(
            conclusion_a=c1.conclusion_id,
            conclusion_b=c2.conclusion_id,
            description="Opposition test",
        )
        diag_avec_contra = await _diagnostiquer(
            conclusions=[c1, c2],
            qualifications=[
                _qualification(
                    conclusion_id=c1.conclusion_id, domaine_element=DomaineElement.pedologique
                ),
                _qualification(
                    conclusion_id=c2.conclusion_id, domaine_element=DomaineElement.climatique
                ),
            ],
            contradictions=[contra],
        )
        assert diag_avec_contra.statut_validation is StatutValidation.brouillon  # type: ignore[attr-defined]

        # Cas avec risque.
        c_risque = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000003"))
        diag_avec_risque = await _diagnostiquer(
            conclusions=[c1, c_risque],
            qualifications=[
                _qualification(conclusion_id=c1.conclusion_id),
                _qualification(
                    conclusion_id=c_risque.conclusion_id,
                    role=RoleDiagnostic.risque,
                    domaine_risque=DomaineRisque.sanitaire,
                ),
            ],
        )
        assert diag_avec_risque.statut_validation is StatutValidation.brouillon  # type: ignore[attr-defined]

    async def test_aucun_bloc_validation(self) -> None:
        """Aucun Diagnostic produit ne porte de bloc ValidationHumaine.

        Rend impossible : une validation humaine fabriquée par le moteur —
        un bloc validation exige une identité humaine nominative, et la
        machine ne peut pas en produire une sans mentir de façon traçable
        (GSIE-CON-001, GSIE-CON-005).
        """
        diag = await _diagnostiquer()
        assert diag.validation is None  # type: ignore[attr-defined]

        # Vérifie sur un cas plus complexe.
        c1 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000001"))
        c2 = _conclusion(conclusion_id=UUID("00000000-0000-4000-8000-000000000002"))
        diag_complexe = await _diagnostiquer(
            conclusions=[c1, c2],
            qualifications=[
                _qualification(conclusion_id=c1.conclusion_id, role=RoleDiagnostic.atout),
                _qualification(
                    conclusion_id=c2.conclusion_id,
                    role=RoleDiagnostic.risque,
                    domaine_risque=DomaineRisque.climatique,
                ),
            ],
        )
        assert diag_complexe.validation is None  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Persistance — ce qui rend `diagnostic_id` résolvable
# ---------------------------------------------------------------------------


class TestPersistance:
    """Le diagnostic rendu est exactement le diagnostic écrit.

    Un `diagnostic_id` que le Recommendation Engine résoudrait vers un
    contenu différent de celui rendu à l'appelant serait pire qu'un
    identifiant non résolvable : le forestier contesterait un diagnostic
    qu'il n'a jamais lu.
    """

    @staticmethod
    def _session() -> AsyncMock:
        session = AsyncMock()
        session.get.return_value = None
        session.add = Mock()
        return session

    @staticmethod
    def _requete_fixe() -> DiagnosticRequest:
        """Requête à identifiants figés — `diagnostic_id` reproductible.

        Les fabriques par défaut tirent un `conclusion_id` aléatoire : deux
        appels dériveraient deux identifiants, et les tests d'idempotence
        comme de conflit porteraient sur des diagnostics distincts.
        """
        conclusion = _conclusion(conclusion_id=UUID("44444444-4444-4444-8444-444444444444"))
        return _requete(conclusions=[conclusion])

    async def _diagnostiquer_avec(self, session: AsyncMock) -> object:
        return await _engine(session).diagnostiquer(self._requete_fixe(), _DATE_DIAGNOSTIC)

    @staticmethod
    def _lignes(session: AsyncMock) -> tuple[ResourceModel, DiagnosticModel]:
        ajouts = [appel.args[0] for appel in session.add.call_args_list]
        ressources = [ligne for ligne in ajouts if isinstance(ligne, ResourceModel)]
        diagnostics = [ligne for ligne in ajouts if isinstance(ligne, DiagnosticModel)]
        assert (
            len(ressources) == 1
        ), f"une seule ligne resource attendue, {len(ressources)} ajoutée(s)"
        assert (
            len(diagnostics) == 1
        ), f"une seule ligne diagnostic attendue, {len(diagnostics)} ajoutée(s)"
        return ressources[0], diagnostics[0]

    async def test_ecrit_resource_et_satellite_sous_le_meme_id(self) -> None:
        """Rend impossible : un diagnostic rendu mais non résolvable.

        Les deux lignes portent l'identifiant rendu à l'appelant — sans
        quoi le `diagnostic_id` d'une réponse HTTP ne désignerait rien.
        """
        session = self._session()
        diag = await self._diagnostiquer_avec(session)
        resource, satellite = self._lignes(session)

        assert resource.type == "diagnostic"
        assert resource.id == diag.diagnostic_id  # type: ignore[attr-defined]
        assert satellite.id == diag.diagnostic_id  # type: ignore[attr-defined]

    async def test_contenu_persiste_relit_le_diagnostic_rendu(self) -> None:
        """Rend impossible : une relecture divergente de la sortie rendue.

        Le contenu stocké se revalide en un `Diagnostic` égal à celui
        retourné, champ pour champ — troncation ou reformulation comprises.
        """
        session = self._session()
        diag = await self._diagnostiquer_avec(session)
        _, satellite = self._lignes(session)

        assert Diagnostic.model_validate(satellite.contenu) == diag

    async def test_colonnes_projettent_le_contenu_sans_diverger(self) -> None:
        """Rend impossible : des colonnes d'index mentant sur le corps.

        Les colonnes scalaires servent aux requêtes ; si elles s'écartaient
        du contenu, une recherche par état global ramènerait des
        diagnostics disant autre chose.
        """
        session = self._session()
        diag = await self._diagnostiquer_avec(session)
        _, satellite = self._lignes(session)

        assert satellite.requete_origine == diag.requete_origine  # type: ignore[attr-defined]
        assert satellite.station_id == diag.station_id  # type: ignore[attr-defined]
        assert satellite.type_diagnostic == diag.type_diagnostic  # type: ignore[attr-defined]
        assert satellite.etat_global == diag.etat_global  # type: ignore[attr-defined]
        assert satellite.confiance == diag.confiance  # type: ignore[attr-defined]
        assert satellite.date_diagnostic == diag.date_diagnostic  # type: ignore[attr-defined]
        # La valeur stockée est celle du type PostgreSQL `evidence_level`
        # (majuscules), pas le nom du membre Python.
        assert satellite.evidence_level_plancher.value == (
            diag.evidence_level_plancher.value  # type: ignore[attr-defined]
        )

    async def test_statut_persiste_toujours_brouillon(self) -> None:
        """Rend impossible : un diagnostic validé écrit par la machine.

        La garantie `GSIE-CON-001` doit tenir dans la base, pas seulement
        dans la réponse HTTP — c'est la base que relira le Recommendation
        Engine.
        """
        session = self._session()
        await self._diagnostiquer_avec(session)
        _, satellite = self._lignes(session)

        assert satellite.statut_validation is StatutValidation.brouillon
        assert satellite.contenu["statut_validation"] == "brouillon"
        assert satellite.contenu["validation"] is None

    async def test_le_moteur_ne_commit_jamais(self) -> None:
        """Rend impossible : un diagnostic survivant à une réponse en échec.

        La transaction appartient à la requête HTTP (`get_db`). Un commit
        dans le moteur laisserait en base un diagnostic dont l'appelant
        n'a jamais reçu l'identifiant.
        """
        session = self._session()
        await self._diagnostiquer_avec(session)

        session.commit.assert_not_called()

    async def test_rejouer_la_meme_requete_n_ecrit_pas_deux_fois(self) -> None:
        """Rend impossible : un doublon sur un identifiant déterministe.

        `diagnostic_id` étant dérivé du contenu, rejouer une requête est
        un cas normal : le moteur constate l'identité et n'écrit rien.
        """
        session = self._session()
        diag = await self._diagnostiquer_avec(session)
        _, satellite = self._lignes(session)

        rejeu = self._session()
        rejeu.get.return_value = satellite
        diag_rejeu = await self._diagnostiquer_avec(rejeu)

        assert diag_rejeu == diag
        rejeu.add.assert_not_called()

    async def test_meme_id_contenu_different_leve_et_n_ecrit_rien(self) -> None:
        """Rend impossible : l'écrasement silencieux d'un diagnostic émis.

        Deux requêtes partageant `requete_id` et les mêmes conclusions
        dérivent le même identifiant, même si leurs qualifications
        diffèrent. Le moteur nomme le conflit au lieu de réécrire un
        diagnostic déjà cité (`CODE_QUALITY_STANDARD` §3.5).
        """
        session = self._session()
        await self._diagnostiquer_avec(session)
        _, satellite = self._lignes(session)

        divergent = self._session()
        autre = Mock()
        autre.contenu = dict(satellite.contenu) | {"etat_global": "critique"}
        divergent.get.return_value = autre

        with pytest.raises(DiagnosticConflitError) as exc:
            await self._diagnostiquer_avec(divergent)

        assert str(satellite.id) in str(exc.value)
        divergent.add.assert_not_called()

    async def test_le_conflit_reste_une_erreur_du_moteur(self) -> None:
        """Le routeur traite `DiagnosticEngineError` : le conflit en hérite.

        Rend impossible : un conflit remontant en erreur 500 non qualifiée
        parce qu'il échapperait au `except` du routeur.
        """
        assert issubclass(DiagnosticConflitError, DiagnosticEngineError)
