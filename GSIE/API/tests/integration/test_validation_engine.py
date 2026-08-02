"""Tests d'intégration — le Validation Engine bloque ou valide selon la constitution.

Le moteur est le dernier rempart avant l'utilisateur (GSIE-CON-005). Ces
tests vérifient que chaque contrôle constitutionnel produit le bon statut
et la bonne cause de blocage, sur des structures réelles — pas des mocks.

Le fixture ``db_session`` garantit que Docker (PostgreSQL via testcontainers)
est disponible, conformément au contrat des tests d'intégration. La session
est passée au ValidationEngine pour la persistance des résultats bloqués
(RFC-0028, migration 0028) — le Learning Engine lit ces patterns pour
détecter les blocages récurrents.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.validation.engine import ValidationEngine
from gsie_api.engines.validation.schemas import (
    TypeCauseBlocage,
    TypeSortie,
    ValidationRequest,
    ValidationResult,
    ValidationStatut,
)
from gsie_api.infrastructure.models import ResourceModel
from tests.conftest import requires_docker

pytestmark = requires_docker

_CHAINE_INFERENCE = [{"nom": "identification_taxonomique"}]


async def _seed_resource(db_session: AsyncSession) -> UUID:
    """Crée une resource racine en base pour satisfaire la FK revision_target_id.

    Le ValidationEngine persiste les résultats bloqués/partiels via une
    RevisionModel dont target_id pointe vers resource.id (RFC-0028). Sans
    resource existante, la FK revision_target_id_fkey rejette l'insert.
    """
    resource_id = uuid4()
    db_session.add(
        ResourceModel(
            id=resource_id,
            type="diagnostic",
            metadata_json={},
        )
    )
    await db_session.flush()
    return resource_id


# --- Fabriques ---


def _diagnostic_valide() -> dict[str, Any]:
    """Contenu de diagnostic conforme à tous les contrôles."""
    return {
        "evidence_level": "b",
        "source": "GBIF Backbone Taxonomy",
        "justification": "Diagnostic basé sur les données dendrométriques.",
    }


def _recommandation_valide() -> dict[str, Any]:
    """Contenu de recommandation conforme à tous les contrôles."""
    return {
        "evidence_level": "b",
        "source": "GBIF",
        "recommandations": [
            {
                "contournable": True,
                "justification": {"texte": "Éclaircie recommandée.", "sources": ["RFC-0012"]},
            },
        ],
    }


def _requete_diagnostic(
    contenu: dict[str, Any], resource_id: UUID | None = None
) -> ValidationRequest:
    return ValidationRequest(
        requete_id=resource_id or uuid4(),
        type_sortie=TypeSortie.diagnostic,
        contenu=contenu,
        chaines_inference=_CHAINE_INFERENCE,
    )


def _requete_recommandation(
    contenu: dict[str, Any], resource_id: UUID | None = None
) -> ValidationRequest:
    return ValidationRequest(
        requete_id=resource_id or uuid4(),
        type_sortie=TypeSortie.recommandation,
        contenu=contenu,
    )


def _requete_ensemble(
    contenu: dict[str, Any], resource_id: UUID | None = None
) -> ValidationRequest:
    return ValidationRequest(
        requete_id=resource_id or uuid4(),
        type_sortie=TypeSortie.ensemble_complet,
        contenu=contenu,
        chaines_inference=_CHAINE_INFERENCE,
    )


def _causes(result: ValidationResult) -> set[TypeCauseBlocage]:
    """Extrait l'ensemble des types de causes de blocage d'un résultat."""
    return {c.type_cause for c in result.causes_blocage}


# --- Tests diagnostic ---


async def should_validate_diagnostic_with_evidence_level_and_sources(
    db_session: AsyncSession,
) -> None:
    """Un diagnostic conforme (niveau, source, chaîne, justification) est valide."""
    # Arrange
    request = _requete_diagnostic(_diagnostic_valide())

    # Act
    result = await ValidationEngine(session=db_session).validate(request)

    # Assert
    assert result.statut == ValidationStatut.valide
    assert result.causes_blocage == []


async def should_block_diagnostic_without_evidence_level(
    db_session: AsyncSession,
) -> None:
    """Sans niveau de preuve, le diagnostic est bloqué (GSIE-CON-002)."""
    # Arrange
    resource_id = await _seed_resource(db_session)
    contenu = _diagnostic_valide()
    contenu.pop("evidence_level")
    request = _requete_diagnostic(contenu, resource_id=resource_id)

    # Act
    result = await ValidationEngine(session=db_session).validate(request)

    # Assert
    assert result.statut == ValidationStatut.bloque
    assert TypeCauseBlocage.sans_niveau_preuve in _causes(result)


async def should_block_diagnostic_without_sources(
    db_session: AsyncSession,
) -> None:
    """Sans source identifiable, le diagnostic est bloqué (GSIE-CON-002)."""
    # Arrange
    resource_id = await _seed_resource(db_session)
    contenu = _diagnostic_valide()
    contenu.pop("source")
    request = _requete_diagnostic(contenu, resource_id=resource_id)

    # Act
    result = await ValidationEngine(session=db_session).validate(request)

    # Assert
    assert result.statut == ValidationStatut.bloque
    assert TypeCauseBlocage.sans_source in _causes(result)


async def should_block_diagnostic_without_chaine_inference(
    db_session: AsyncSession,
) -> None:
    """Sans chaîne d'inférence, le diagnostic est bloqué (GSIE-CON-004)."""
    # Arrange
    resource_id = await _seed_resource(db_session)
    request = ValidationRequest(
        requete_id=resource_id,
        type_sortie=TypeSortie.diagnostic,
        contenu=_diagnostic_valide(),
        chaines_inference=[],
    )

    # Act
    result = await ValidationEngine(session=db_session).validate(request)

    # Assert
    assert result.statut == ValidationStatut.bloque
    assert TypeCauseBlocage.sans_chaine_inference in _causes(result)


# --- Tests recommandation ---


async def should_validate_recommendation_with_justification_and_contournable(
    db_session: AsyncSession,
) -> None:
    """Une recommandation contournable et justifiée passe tous les contrôles."""
    # Arrange
    request = _requete_recommandation(_recommandation_valide())

    # Act
    result = await ValidationEngine(session=db_session).validate(request)

    # Assert
    assert result.statut == ValidationStatut.valide
    assert result.causes_blocage == []


async def should_block_recommendation_non_contournable(
    db_session: AsyncSession,
) -> None:
    """Une recommandation non contournable est bloquée (GSIE-CON-001)."""
    # Arrange
    resource_id = await _seed_resource(db_session)
    contenu = _recommandation_valide()
    contenu["recommandations"][0]["contournable"] = False
    request = _requete_recommandation(contenu, resource_id=resource_id)

    # Act
    result = await ValidationEngine(session=db_session).validate(request)

    # Assert
    assert result.statut == ValidationStatut.bloque
    assert TypeCauseBlocage.recommandation_non_contournable in _causes(result)


async def should_block_recommendation_without_justification(
    db_session: AsyncSession,
) -> None:
    """Sans justification, la recommandation est bloquée (GSIE-CON-004)."""
    # Arrange
    resource_id = await _seed_resource(db_session)
    contenu = _recommandation_valide()
    contenu["recommandations"][0].pop("justification")
    request = _requete_recommandation(contenu, resource_id=resource_id)

    # Act
    result = await ValidationEngine(session=db_session).validate(request)

    # Assert
    assert result.statut == ValidationStatut.bloque
    assert TypeCauseBlocage.explicabilite_insuffisante in _causes(result)


# --- Tests ensemble complet ---


async def should_partially_validate_ensemble_with_only_non_critical_failures(
    db_session: AsyncSession,
) -> None:
    """Un ensemble avec seulement un échec non critique (explicabilité) est
    partiellement valide — pas bloqué."""
    # Arrange — source et niveau présents (critiques), contournable (critique),
    # chaîne fournie (non critique), mais aucune justification (non critique).
    resource_id = await _seed_resource(db_session)
    contenu = {
        "diagnostic": _diagnostic_valide(),
        "recommandations": [{"contournable": True}],
        "evidence_level": "b",
        "source": "GBIF",
    }
    request = _requete_ensemble(contenu, resource_id=resource_id)

    # Act
    result = await ValidationEngine(session=db_session).validate(request)

    # Assert
    assert result.statut == ValidationStatut.partiellement_valide
    assert TypeCauseBlocage.explicabilite_insuffisante in _causes(result)


async def should_block_ensemble_with_critical_failure(
    db_session: AsyncSession,
) -> None:
    """Un ensemble avec une défaillance critique (sans source) est bloqué."""
    # Arrange — aucune source au niveau racine ni dans les recommandations.
    resource_id = await _seed_resource(db_session)
    contenu = {
        "diagnostic": _diagnostic_valide(),
        "recommandations": [
            {"contournable": True, "justification": {"texte": "Éclaircie."}},
        ],
        "evidence_level": "b",
    }
    request = _requete_ensemble(contenu, resource_id=resource_id)

    # Act
    result = await ValidationEngine(session=db_session).validate(request)

    # Assert
    assert result.statut == ValidationStatut.bloque
    assert TypeCauseBlocage.sans_source in _causes(result)


# --- Test métadonnées ---


async def should_return_validation_id_and_timestamp(
    db_session: AsyncSession,
) -> None:
    """Le résultat porte toujours un validation_id (UUID) et un date_validation."""
    # Arrange
    request = _requete_diagnostic(_diagnostic_valide())

    # Act
    result = await ValidationEngine(session=db_session).validate(request)

    # Assert
    assert isinstance(result.validation_id, UUID)
    assert isinstance(result.date_validation, datetime)
