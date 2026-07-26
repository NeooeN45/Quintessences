"""Tests unitaires — invariants de `reasoning/schemas.py`.

Les garanties du §6 de `REASONING_ENGINE.md` sont encodées dans le typage
Pydantic. Ce module démontre que chaque invariant rejette ce qu'il doit
rejeter — et accepte ce qui est légitime. Un invariant trop strict est un bug.

Couvre : `Conclusion` (chaîne contiguë, sources fermées, plancher cohérent,
bornes de confiance), `EtapeInference`, `StationContexte`, `BlocContexte`,
`ContradictionDetectee`, `InferenceResult`, et la fonction `niveau_plancher`.

Références constitutionnelles : GSIE-CON-002 (« ce qui n'est pas sourcé
n'existe pas »), GSIE-CON-004 (explicabilité), ADR-009 (anti-invention).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    Conclusion,
    ContradictionDetectee,
    EtapeInference,
    InferenceResult,
    MethodeConfiance,
    SourceMoteurContexte,
    StationContexte,
    niveau_plancher,
)

# ---------------------------------------------------------------------------
# Fabriques — objets valides réutilisables, paramétrables par argument.
# ---------------------------------------------------------------------------


def _source(
    *,
    auteur: str = "Rameau et al.",
    reference: str = "doi:10.0000/test",
    type_source: SourceType = SourceType.peer_reviewed,
) -> SourceReference:
    """Construit une `SourceReference` valide par défaut."""
    return SourceReference(
        type_source=type_source,
        auteur=auteur,
        reference=reference,
    )


def _etape(
    *,
    ordre: int,
    source: SourceReference | None = None,
    evidence_level: EvidenceLevel = EvidenceLevel.B,
    premisses: list[str] | None = None,
) -> EtapeInference:
    """Construit une `EtapeInference` valide par défaut.

    `source_regle` est obligatoire (GSIE-CON-002) : si non fournie, une
    source par défaut est utilisée.
    """
    return EtapeInference(
        ordre=ordre,
        regle_appliquee="Règle de test",
        source_regle=source or _source(),
        premisses=premisses or ["fait observé"],
        conclusion_locale="conclusion locale",
        evidence_level=evidence_level,
    )


def _conclusion(
    *,
    etapes: list[EtapeInference],
    sources: list[SourceReference],
    niveau_confiance: float = 0.8,
    conclusion_id: UUID | None = None,
) -> Conclusion:
    """Construit une `Conclusion` valide à partir d'étapes et de sources.

    Le `evidence_level_plancher` est dérivé correctement via `niveau_plancher`
    pour éviter toute incohérence — sauf si le test vise justement à le
    falsifier, auquel cas l'appelant construit manuellement.
    """
    plancher = niveau_plancher([etape.evidence_level for etape in etapes])
    return Conclusion(
        conclusion_id=conclusion_id or uuid4(),
        enonce="Conclusion de test",
        niveau_confiance=niveau_confiance,
        methode_confiance=MethodeConfiance.fournie_par_regle,
        evidence_level_plancher=plancher,
        chaine_inference=etapes,
        sources_utilisees=sources,
    )


def _bloc(
    *,
    source_moteur: SourceMoteurContexte = SourceMoteurContexte.climate,
    valeurs: dict[str, float | int | str | bool] | None = None,
    evidence_level: EvidenceLevel = EvidenceLevel.B,
) -> BlocContexte:
    """Construit un `BlocContexte` valide par défaut."""
    return BlocContexte(
        source_moteur=source_moteur,
        source=_source(),
        evidence_level=evidence_level,
        valeurs=valeurs if valeurs is not None else {"temperature_moyenne": 12.5},
    )


# ---------------------------------------------------------------------------
# niveau_plancher — ordonnancement de l'échelle A–F
# ---------------------------------------------------------------------------


class TestNiveauPlancher:
    """Vérifie l'ordre complet A > B > C > D > E > F (A=meilleur, F=pire)."""

    def test_should_return_weakest_when_single_level(self) -> None:
        assert niveau_plancher([EvidenceLevel.D]) == EvidenceLevel.D

    def test_should_return_weakest_across_full_scale(self) -> None:
        """L'échelle complète : le plancher d'un ensemble contenant F est F."""
        tous = [
            EvidenceLevel.A,
            EvidenceLevel.B,
            EvidenceLevel.C,
            EvidenceLevel.D,
            EvidenceLevel.E,
            EvidenceLevel.F,
        ]
        assert niveau_plancher(tous) == EvidenceLevel.F

    def test_should_return_b_when_a_and_b(self) -> None:
        """A est plus fort que B : le plancher est B."""
        assert niveau_plancher([EvidenceLevel.A, EvidenceLevel.B]) == EvidenceLevel.B

    def test_should_return_d_when_b_and_d(self) -> None:
        """B est plus fort que D : le plancher est D."""
        assert niveau_plancher([EvidenceLevel.B, EvidenceLevel.D]) == EvidenceLevel.D

    def test_should_raise_when_empty(self) -> None:
        with pytest.raises(ValueError, match="aucun niveau"):
            niveau_plancher([])


# ---------------------------------------------------------------------------
# Conclusion._chaine_contigue
# ---------------------------------------------------------------------------


class TestChaineContigue:
    """La chaîne d'inférence doit être 1..N sans trou ni doublon."""

    def test_should_accept_chain_1_2_3(self) -> None:
        source = _source()
        etapes = [
            _etape(ordre=1, source=source),
            _etape(ordre=2, source=source),
            _etape(ordre=3, source=source),
        ]
        conclusion = _conclusion(etapes=etapes, sources=[source])
        assert len(conclusion.chaine_inference) == 3

    def test_should_reject_chain_with_gap(self) -> None:
        """Chaîne 1,3 : il manque l'étape 2 (trou)."""
        source = _source()
        etapes = [
            _etape(ordre=1, source=source),
            _etape(ordre=3, source=source),
        ]
        with pytest.raises(ValidationError, match="non contiguë"):
            _conclusion(etapes=etapes, sources=[source])

    def test_should_reject_chain_with_duplicate(self) -> None:
        """Chaîne 1,1 : doublon d'ordre."""
        source = _source()
        etapes = [
            _etape(ordre=1, source=source),
            _etape(ordre=1, source=source),
        ]
        with pytest.raises(ValidationError, match="non contiguë"):
            _conclusion(etapes=etapes, sources=[source])

    def test_should_reject_chain_not_starting_at_1(self) -> None:
        """Chaîne 2,3 : ne commence pas à 1."""
        source = _source()
        etapes = [
            _etape(ordre=2, source=source),
            _etape(ordre=3, source=source),
        ]
        with pytest.raises(ValidationError, match="non contiguë"):
            _conclusion(etapes=etapes, sources=[source])

    def test_should_reject_empty_chain(self) -> None:
        """Chaîne vide : rejetée par min_length=1 sur chaine_inference."""
        with pytest.raises(ValidationError, match="chaine_inference"):
            Conclusion(
                conclusion_id=uuid4(),
                enonce="Conclusion vide",
                niveau_confiance=0.5,
                methode_confiance=MethodeConfiance.fournie_par_regle,
                evidence_level_plancher=EvidenceLevel.A,
                chaine_inference=[],
                sources_utilisees=[_source()],
            )


# ---------------------------------------------------------------------------
# Conclusion._sources_fermees
# ---------------------------------------------------------------------------


class TestSourcesFermees:
    """Toute source citée par une étape est déclarée, et réciproquement."""

    def test_should_accept_when_source_cited_and_declared(self) -> None:
        source = _source()
        etapes = [_etape(ordre=1, source=source)]
        conclusion = _conclusion(etapes=etapes, sources=[source])
        assert len(conclusion.sources_utilisees) == 1

    def test_should_reject_when_source_cited_but_not_declared(self) -> None:
        """L'étape cite une source que sources_utilisees ne déclare pas."""
        source_citee = _source(auteur="Auteur A", reference="ref-a")
        source_declaree = _source(auteur="Auteur B", reference="ref-b")
        etapes = [_etape(ordre=1, source=source_citee)]
        with pytest.raises(ValidationError, match="non déclarées"):
            _conclusion(etapes=etapes, sources=[source_declaree])

    def test_should_reject_when_source_declared_but_unused(self) -> None:
        """Une source déclarée mais non utilisée par la chaîne est orpheline."""
        source_utilisee = _source(auteur="Auteur A", reference="ref-a")
        source_orpheline = _source(auteur="Auteur B", reference="ref-b")
        etapes = [_etape(ordre=1, source=source_utilisee)]
        with pytest.raises(ValidationError, match="non utilisées"):
            _conclusion(etapes=etapes, sources=[source_utilisee, source_orpheline])

    def test_should_accept_when_two_steps_share_one_declared_source(self) -> None:
        """Deux étapes peuvent partager la même source, déclarée une fois."""
        source = _source()
        etapes = [
            _etape(ordre=1, source=source),
            _etape(ordre=2, source=source),
        ]
        conclusion = _conclusion(etapes=etapes, sources=[source])
        assert len(conclusion.sources_utilisees) == 1
        assert len(conclusion.chaine_inference) == 2


# ---------------------------------------------------------------------------
# Conclusion._plancher_coherent
# ---------------------------------------------------------------------------


class TestPlancherCoherent:
    """Le plancher déclaré doit être le plus faible maillon de la chaîne."""

    def test_should_accept_single_step_d_plancher_d(self) -> None:
        source = _source()
        etapes = [_etape(ordre=1, source=source, evidence_level=EvidenceLevel.D)]
        conclusion = _conclusion(etapes=etapes, sources=[source])
        assert conclusion.evidence_level_plancher == EvidenceLevel.D

    def test_should_accept_steps_b_and_d_plancher_d(self) -> None:
        """B plus fort que D : le plancher est D."""
        source = _source()
        etapes = [
            _etape(ordre=1, source=source, evidence_level=EvidenceLevel.B),
            _etape(ordre=2, source=source, evidence_level=EvidenceLevel.D),
        ]
        conclusion = _conclusion(etapes=etapes, sources=[source])
        assert conclusion.evidence_level_plancher == EvidenceLevel.D

    def test_should_reject_steps_b_and_d_plancher_b(self) -> None:
        """Plancher déclaré B alors que la chaîne contient D : incohérent."""
        source = _source()
        etapes = [
            _etape(ordre=1, source=source, evidence_level=EvidenceLevel.B),
            _etape(ordre=2, source=source, evidence_level=EvidenceLevel.D),
        ]
        with pytest.raises(ValidationError, match="plancher incohérent"):
            Conclusion(
                conclusion_id=uuid4(),
                enonce="Conclusion incohérente",
                niveau_confiance=0.5,
                methode_confiance=MethodeConfiance.fournie_par_regle,
                evidence_level_plancher=EvidenceLevel.B,
                chaine_inference=etapes,
                sources_utilisees=[source],
            )


# ---------------------------------------------------------------------------
# Conclusion.niveau_confiance — bornes du contrat §5
# ---------------------------------------------------------------------------


class TestNiveauConfiance:
    """Le niveau de confiance est un décimal borné entre 0,0 et 1,0."""

    def test_should_accept_zero(self) -> None:
        source = _source()
        etapes = [_etape(ordre=1, source=source)]
        conclusion = _conclusion(etapes=etapes, sources=[source], niveau_confiance=0.0)
        assert conclusion.niveau_confiance == 0.0

    def test_should_accept_one(self) -> None:
        source = _source()
        etapes = [_etape(ordre=1, source=source)]
        conclusion = _conclusion(etapes=etapes, sources=[source], niveau_confiance=1.0)
        assert conclusion.niveau_confiance == 1.0

    def test_should_reject_below_zero(self) -> None:
        source = _source()
        etapes = [_etape(ordre=1, source=source)]
        with pytest.raises(ValidationError, match="niveau_confiance"):
            _conclusion(etapes=etapes, sources=[source], niveau_confiance=-0.1)

    def test_should_reject_above_one(self) -> None:
        source = _source()
        etapes = [_etape(ordre=1, source=source)]
        with pytest.raises(ValidationError, match="niveau_confiance"):
            _conclusion(etapes=etapes, sources=[source], niveau_confiance=1.1)


# ---------------------------------------------------------------------------
# EtapeInference
# ---------------------------------------------------------------------------


class TestEtapeInference:
    """Une étape sans prémisse ou sans source de règle n'est pas une déduction."""

    def test_should_reject_empty_premisses(self) -> None:
        with pytest.raises(ValidationError, match="premisses"):
            EtapeInference(
                ordre=1,
                regle_appliquee="Règle",
                source_regle=_source(),
                premisses=[],
                conclusion_locale="conclusion",
                evidence_level=EvidenceLevel.B,
            )

    def test_should_reject_missing_source_regle(self) -> None:
        """source_regle absente : règle inventée, interdite par CON-002."""
        data: dict[str, object] = {
            "ordre": 1,
            "regle_appliquee": "Règle",
            "premisses": ["fait"],
            "conclusion_locale": "conclusion",
            "evidence_level": EvidenceLevel.B,
        }
        with pytest.raises(ValidationError, match="source_regle"):
            EtapeInference.model_validate(data)  # type: ignore[arg-type]

    def test_should_reject_ordre_zero(self) -> None:
        """ordre=0 : la chaîne commence à 1, pas à 0."""
        with pytest.raises(ValidationError, match="ordre"):
            EtapeInference(
                ordre=0,
                regle_appliquee="Règle",
                source_regle=_source(),
                premisses=["fait"],
                conclusion_locale="conclusion",
                evidence_level=EvidenceLevel.B,
            )


# ---------------------------------------------------------------------------
# StationContexte
# ---------------------------------------------------------------------------


class TestStationContexte:
    """Au moins un bloc de contexte est requis — on ne raisonne pas sur le vide."""

    def test_should_reject_when_no_block(self) -> None:
        with pytest.raises(ValidationError, match="au moins un bloc"):
            StationContexte()

    def test_should_accept_single_climat_block(self) -> None:
        contexte = StationContexte(climat=_bloc())
        assert contexte.climat is not None

    def test_should_accept_only_correlations(self) -> None:
        """Une station caractérisée uniquement par des corrélations est valide."""
        bloc_corr = _bloc(source_moteur=SourceMoteurContexte.correlation)
        contexte = StationContexte(correlations=[bloc_corr])
        assert len(contexte.correlations) == 1

    def test_should_return_stable_order_from_blocs_presents(self) -> None:
        """blocs_presents() retourne un ordre stable et reproductible.

        L'ordre est : geographie, climat, pedologie, botanique, peuplement,
        puis correlations — déterminisme exigé par §6.
        """
        geographie = _bloc(source_moteur=SourceMoteurContexte.gis)
        climat = _bloc(source_moteur=SourceMoteurContexte.climate)
        peuplement = _bloc(source_moteur=SourceMoteurContexte.forest_dynamics)
        corr1 = _bloc(source_moteur=SourceMoteurContexte.correlation)
        corr2 = _bloc(source_moteur=SourceMoteurContexte.correlation)

        contexte = StationContexte(
            geographie=geographie,
            climat=climat,
            peuplement=peuplement,
            correlations=[corr1, corr2],
        )

        resultat_1 = contexte.blocs_presents()
        resultat_2 = contexte.blocs_presents()

        # Reproductibilité : deux appels successifs donnent le même résultat.
        assert resultat_1 == resultat_2
        # Ordre stable : blocs nommés d'abord, puis correlations dans l'ordre.
        assert resultat_1 == [geographie, climat, peuplement, corr1, corr2]


# ---------------------------------------------------------------------------
# BlocContexte
# ---------------------------------------------------------------------------


class TestBlocContexte:
    """ADR-009 : aucun bloc sans donnée, sans source ni niveau de preuve."""

    def test_should_reject_empty_valeurs(self) -> None:
        """valeurs vide : un bloc sans donnée est un bloc inventé (ADR-009)."""
        with pytest.raises(ValidationError, match="valeurs"):
            _bloc(valeurs={})

    def test_should_reject_missing_source_and_evidence_level(self) -> None:
        """Sans source ni evidence_level : inconstructible (ADR-009)."""
        data: dict[str, object] = {
            "source_moteur": SourceMoteurContexte.climate,
            "valeurs": {"temperature": 12.5},
        }
        with pytest.raises(ValidationError):
            BlocContexte.model_validate(data)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ContradictionDetectee
# ---------------------------------------------------------------------------


class TestContradictionDetectee:
    """Les contradictions sont signalées, jamais résolues (CON-002, S-3)."""

    def test_should_reject_when_same_conclusion(self) -> None:
        """conclusion_a == conclusion_b : une conclusion ne se contredit pas."""
        meme_id = uuid4()
        with pytest.raises(ValidationError, match="se contredire"):
            ContradictionDetectee(
                conclusion_a=meme_id,
                conclusion_b=meme_id,
                description="Contradiction de test",
            )

    def test_should_accept_when_distinct_conclusions(self) -> None:
        contradiction = ContradictionDetectee(
            conclusion_a=uuid4(),
            conclusion_b=uuid4(),
            description="Contradiction valide",
        )
        assert contradiction.conclusion_a != contradiction.conclusion_b

    def test_should_have_no_resolution_field(self) -> None:
        """Aucun champ de résolution n'existe sur le modèle (CON-002, S-3).

        Vérification par introspection : les champs du modèle doivent être
        exactement {conclusion_a, conclusion_b, description}, et aucun nom
        de champ ne doit évoquer une résolution, un arbitrage ou une décision
        de triage automatique.
        """
        champs = set(ContradictionDetectee.model_fields.keys())
        assert champs == {"conclusion_a", "conclusion_b", "description"}

        termes_interdits = (
            "resolution",
            "resolu",
            "resolue",
            "arbitrage",
            "arbitre",
            "decision",
            "decide",
            "tranch",
            "verdict",
            "priorite",
            "prioritaire",
            "choix",
            "selection",
        )
        for champ in champs:
            champ_lower = champ.lower()
            for terme in termes_interdits:
                assert terme not in champ_lower, (
                    f"Champ '{champ}' évoque une résolution — " f"violation de CON-002/S-3"
                )


# ---------------------------------------------------------------------------
# InferenceResult
# ---------------------------------------------------------------------------


class TestInferenceResult:
    """L'absence de résultat est un résultat honnête (CON-002)."""

    def test_should_accept_empty_conclusions(self) -> None:
        """Aucune conclusion : l'absence de résultat est un résultat honnête."""
        result = InferenceResult(
            resultat_id=uuid4(),
            requete_origine=uuid4(),
            conclusions=[],
            contradictions=[],
            date_inference=datetime.now(UTC),
        )
        assert len(result.conclusions) == 0

    def test_should_reject_contradiction_referencing_absent_conclusion(self) -> None:
        """Une contradiction ne peut désigner que des conclusions présentes."""
        source = _source()
        conclusion_presente = _conclusion(
            etapes=[_etape(ordre=1, source=source)],
            sources=[source],
        )
        contradiction = ContradictionDetectee(
            conclusion_a=conclusion_presente.conclusion_id,
            conclusion_b=uuid4(),  # conclusion absente
            description="Contradiction avec une conclusion inconnue",
        )
        with pytest.raises(ValidationError, match="conclusions absentes"):
            InferenceResult(
                resultat_id=uuid4(),
                requete_origine=uuid4(),
                conclusions=[conclusion_presente],
                contradictions=[contradiction],
                date_inference=datetime.now(UTC),
            )

    def test_should_reject_duplicate_conclusion_ids(self) -> None:
        """Deux conclusions de même identifiant : rejeté."""
        source = _source()
        meme_id = uuid4()
        conclusion_1 = _conclusion(
            etapes=[_etape(ordre=1, source=source)],
            sources=[source],
            conclusion_id=meme_id,
        )
        conclusion_2 = _conclusion(
            etapes=[_etape(ordre=1, source=source)],
            sources=[source],
            conclusion_id=meme_id,
        )
        with pytest.raises(ValidationError, match="même identifiant"):
            InferenceResult(
                resultat_id=uuid4(),
                requete_origine=uuid4(),
                conclusions=[conclusion_1, conclusion_2],
                contradictions=[],
                date_inference=datetime.now(UTC),
            )
