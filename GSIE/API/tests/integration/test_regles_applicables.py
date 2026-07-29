"""Récupération des règles par contexte — RFC-0028 §4.3, DEC-000038.

Le Reasoning Engine recevait ses règles dans la requête : GeoSylva aurait dû
embarquer la connaissance sylvicole, et toute révision d'un seuil aurait exigé
une mise à jour de l'application sur chaque téléphone.

Ces tests exercent la sélection sur une base PostGIS réelle, avec de vraies
géométries — la containment est du `ST_Contains`, pas une comparaison de
libellés.

Le cas décisif est le troisième : une règle **hors domaine** ne doit jamais
sortir. Si elle sortait, elle produirait une conclusion fausse citant une
source réelle, avec une chaîne d'inférence complète et un niveau de preuve
intact. Personne ne verrait l'erreur.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.evidence.schemas import EvidenceLevel as EvidenceLevelSchema
from gsie_api.engines.knowledge.engine import KnowledgeEngine
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.assertion import (
    AssertionModel,
    AssertionQualifierModel,
    EvidenceAssessmentModel,
)
from gsie_api.infrastructure.models.enums import (
    CitationRole,
    ClaimKind,
    EvidenceLevel,
    LifecycleStatus,
    SourceNature,
    SourceSubtype,
)
from gsie_api.infrastructure.models.prov import CitationModel, SourceModel
from gsie_api.infrastructure.models.spatial_temporal import PlaceModel
from tests.conftest import requires_docker

pytestmark = requires_docker

# Correspondance code -> nom du fait : le contexte prefixe par bloc.
_VOCABULAIRE = {"reserve_utile_mm": "pedologie_reserve_utile_mm"}

# Deux polygones disjoints en Lambert-93 : le second ne contient pas le premier.
_PARCELLE = (
    "SRID=2154;POLYGON((650000 6860000, 650100 6860000, "
    "650100 6860100, 650000 6860100, 650000 6860000))"
)
_REGION_CONTENANTE = (
    "SRID=2154;POLYGON((640000 6850000, 660000 6850000, "
    "660000 6870000, 640000 6870000, 640000 6850000))"
)
_REGION_AILLEURS = (
    "SRID=2154;POLYGON((700000 6300000, 720000 6300000, "
    "720000 6320000, 700000 6320000, 700000 6300000))"
)


async def _place(session: AsyncSession, geometrie: str, label: str) -> PlaceModel:
    resource = ResourceModel(type="place", gsie_id=f"place:{label}:{uuid4().hex[:8]}")
    session.add(resource)
    await session.flush()
    place = PlaceModel(id=resource.id, geometry=geometrie, srid=2154, label=label)
    session.add(place)
    await session.flush()
    return place


async def _source(session: AsyncSession, *, citable: bool = True) -> SourceModel:
    resource = ResourceModel(type="source", gsie_id=f"source:{uuid4().hex[:8]}")
    session.add(resource)
    await session.flush()
    source = SourceModel(
        id=resource.id,
        title="Catalogue des stations forestières de Haute-Normandie",
        subtype=SourceSubtype.publication,
        source_nature=SourceNature.reference,
        auteur="CRPF Normandie" if citable else None,
        date_publication="2019" if citable else None,
    )
    session.add(source)
    await session.flush()
    return source


async def _regle(
    session: AsyncSession,
    *,
    domaine: PlaceModel | None,
    source: SourceModel | None,
    niveau: EvidenceLevel = EvidenceLevel.b,
    qualificateurs: dict[str, str] | None = None,
    statut: LifecycleStatus = LifecycleStatus.accepted,
) -> AssertionModel:
    """Crée une règle sourcée, avec son domaine de validité et son niveau."""
    resource = ResourceModel(type="assertion", gsie_id=f"assertion:{uuid4().hex[:8]}")
    session.add(resource)
    await session.flush()

    assertion = AssertionModel(
        id=resource.id,
        claim_kind=ClaimKind.threshold,
        lifecycle_status=statut,
        spatial_scope_id=domaine.id if domaine is not None else None,
        version=1,
    )
    session.add(assertion)
    await session.flush()

    for cle, valeur in (
        qualificateurs
        or {
            "variable": "reserve_utile_mm",
            "operateur": "<",
            "valeur": "120",
            "enonce_conclusion": "contrainte hydrique pour le chêne sessile",
            "niveau_confiance": "0.8",
        }
    ).items():
        session.add(AssertionQualifierModel(assertion_id=assertion.id, key=cle, value=valeur))

    evidence_resource = ResourceModel(
        type="evidence_assessment", gsie_id=f"evidence:{uuid4().hex[:8]}"
    )
    session.add(evidence_resource)
    await session.flush()
    session.add(
        EvidenceAssessmentModel(
            id=evidence_resource.id,
            assertion_id=assertion.id,
            level=niveau,
            method="jugement du curateur",
            evaluated_at=datetime.now(UTC),
        )
    )

    if source is not None:
        citation_resource = ResourceModel(type="citation", gsie_id=f"citation:{uuid4().hex[:8]}")
        session.add(citation_resource)
        await session.flush()
        session.add(
            CitationModel(
                id=citation_resource.id,
                source_id=source.id,
                target_id=assertion.id,
                citation_role=CitationRole.primary,
            )
        )

    await session.flush()
    return assertion


class TestSelectionParDomaine:
    """`ST_Contains` sur géométries réelles — pas une comparaison de libellés."""

    async def test_une_regle_du_bon_territoire_est_retournee(
        self, db_session: AsyncSession
    ) -> None:
        parcelle = await _place(db_session, _PARCELLE, "parcelle")
        region = await _place(db_session, _REGION_CONTENANTE, "haute-normandie")
        await _regle(db_session, domaine=region, source=await _source(db_session))

        regles, ecartees = await KnowledgeEngine(db_session).regles_applicables(
            parcelle.id, variables_connues=_VOCABULAIRE
        )

        assert len(regles) == 1, ecartees
        assert regles[0].condition == "pedologie_reserve_utile_mm < 120"
        assert regles[0].niveau_confiance == 0.8
        assert regles[0].source.auteur == "CRPF Normandie"

    async def test_une_regle_hors_domaine_ne_sort_jamais(self, db_session: AsyncSession) -> None:
        """Le cas décisif : elle produirait une conclusion fausse mais sourcée."""
        parcelle = await _place(db_session, _PARCELLE, "parcelle")
        ailleurs = await _place(db_session, _REGION_AILLEURS, "mediterranee")
        await _regle(db_session, domaine=ailleurs, source=await _source(db_session))

        regles, _ = await KnowledgeEngine(db_session).regles_applicables(
            parcelle.id, variables_connues=_VOCABULAIRE
        )

        assert regles == []

    async def test_une_regle_sans_domaine_ne_sort_jamais(self, db_session: AsyncSession) -> None:
        """Un domaine absent vaut « nulle part », jamais « partout » (DEC-000038)."""
        parcelle = await _place(db_session, _PARCELLE, "parcelle")
        await _regle(db_session, domaine=None, source=await _source(db_session))

        regles, _ = await KnowledgeEngine(db_session).regles_applicables(
            parcelle.id, variables_connues=_VOCABULAIRE
        )

        assert regles == []


class TestExigencesDeSortie:
    """Ce qui manque écarte la règle, et l'écartement est dit."""

    async def test_une_regle_non_sourcee_ne_sort_pas(self, db_session: AsyncSession) -> None:
        parcelle = await _place(db_session, _PARCELLE, "parcelle")
        region = await _place(db_session, _REGION_CONTENANTE, "region")
        await _regle(db_session, domaine=region, source=None)

        regles, _ = await KnowledgeEngine(db_session).regles_applicables(
            parcelle.id, variables_connues=_VOCABULAIRE
        )

        assert regles == []

    async def test_un_brouillon_ne_raisonne_pas(self, db_session: AsyncSession) -> None:
        parcelle = await _place(db_session, _PARCELLE, "parcelle")
        region = await _place(db_session, _REGION_CONTENANTE, "region")
        await _regle(
            db_session,
            domaine=region,
            source=await _source(db_session),
            statut=LifecycleStatus.draft,
        )

        regles, _ = await KnowledgeEngine(db_session).regles_applicables(
            parcelle.id, variables_connues=_VOCABULAIRE
        )

        assert regles == []

    async def test_une_variable_hors_vocabulaire_est_ecartee_et_dite(
        self, db_session: AsyncSession
    ) -> None:
        """L'écartement est retourné : une règle mal formée doit être corrigeable."""
        parcelle = await _place(db_session, _PARCELLE, "parcelle")
        region = await _place(db_session, _REGION_CONTENANTE, "region")
        await _regle(
            db_session,
            domaine=region,
            source=await _source(db_session),
            qualificateurs={
                "variable": "RUM",
                "operateur": "<",
                "valeur": "120",
                "enonce_conclusion": "contrainte",
                "niveau_confiance": "0.8",
            },
        )

        regles, ecartees = await KnowledgeEngine(db_session).regles_applicables(
            parcelle.id, variables_connues=_VOCABULAIRE
        )

        assert regles == []
        assert any("hors vocabulaire" in motif for motif in ecartees)

    @pytest.mark.parametrize(
        ("niveau", "plancher", "attendu"),
        [
            (EvidenceLevel.b, EvidenceLevelSchema.C, 1),
            (EvidenceLevel.e, EvidenceLevelSchema.B, 0),
        ],
    )
    async def test_le_plancher_de_preuve_filtre(
        self,
        db_session: AsyncSession,
        niveau: EvidenceLevel,
        plancher: EvidenceLevelSchema,
        attendu: int,
    ) -> None:
        parcelle = await _place(db_session, _PARCELLE, "parcelle")
        region = await _place(db_session, _REGION_CONTENANTE, "region")
        await _regle(db_session, domaine=region, source=await _source(db_session), niveau=niveau)

        regles, _ = await KnowledgeEngine(db_session).regles_applicables(
            parcelle.id, variables_connues=_VOCABULAIRE, evidence_min=plancher
        )

        assert len(regles) == attendu


class TestChaineComplete:
    """Le Reasoning Engine va chercher ses règles quand l'appelant n'en donne pas.

    C'est la promesse de `GSIE-PROMPT-0017` — « le branchement sur le Knowledge
    Engine se fera sans rupture de contrat » — tenue deux ans plus tard.
    """

    @staticmethod
    def _requete(station_id: object, regles: list[object] | None = None) -> object:
        from gsie_api.engines.evidence.schemas import SourceReference, SourceType
        from gsie_api.engines.reasoning.schemas import (
            BlocContexte,
            ReasoningRequest,
            SourceMoteurContexte,
            StationContexte,
        )

        bloc = BlocContexte(
            source_moteur=SourceMoteurContexte.pedology,
            source=SourceReference(
                type_source=SourceType.observation_terrain,
                auteur="Relevé terrain",
                reference="sondage tarière, parcelle test",
            ),
            evidence_level=EvidenceLevelSchema.F,
            valeurs={"reserve_utile_mm": 85.0},
        )
        return ReasoningRequest(
            requete_id=uuid4(),
            station_id=station_id,
            contexte=StationContexte(pedologie=bloc),
            regles=regles or [],
            question="La station présente-t-elle une contrainte hydrique ?",
            profondeur_max=3,
        )

    async def test_le_moteur_recupere_ses_regles_et_conclut(self, db_session: AsyncSession) -> None:
        """Document → règle → observation → conclusion tracée, sans règle fournie."""
        from gsie_api.engines.reasoning.engine import ReasoningEngine

        parcelle = await _place(db_session, _PARCELLE, "parcelle")
        region = await _place(db_session, _REGION_CONTENANTE, "haute-normandie")
        await _regle(db_session, domaine=region, source=await _source(db_session))
        await db_session.commit()

        resultat = await ReasoningEngine(db_session).infer(
            self._requete(parcelle.id), datetime.now(UTC)
        )

        # 85 mm observés contre un seuil à 120 : la contrainte est établie.
        assert len(resultat.conclusions) == 1, resultat
        conclusion = resultat.conclusions[0]
        assert "contrainte hydrique" in conclusion.enonce
        # La conclusion remonte à la source, sans quoi elle serait incitable.
        assert conclusion.sources_utilisees
        # Le plancher de preuve est celui du maillon le plus faible : le relevé
        # terrain (F) et non la règle (B).
        assert conclusion.evidence_level_plancher is EvidenceLevelSchema.F

    async def test_une_regle_hors_domaine_ne_produit_aucune_conclusion(
        self, db_session: AsyncSession
    ) -> None:
        """Le refus se propage jusqu'au bout : pas de règle, donc pas de conclusion."""
        from gsie_api.engines.reasoning.engine import ReasoningEngine

        parcelle = await _place(db_session, _PARCELLE, "parcelle")
        ailleurs = await _place(db_session, _REGION_AILLEURS, "mediterranee")
        await _regle(db_session, domaine=ailleurs, source=await _source(db_session))
        await db_session.commit()

        resultat = await ReasoningEngine(db_session).infer(
            self._requete(parcelle.id), datetime.now(UTC)
        )

        assert resultat.conclusions == []
