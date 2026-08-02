"""Tests unitaires — couverture complète de resources/service.py.

Cible les branches non couvertes du service CRUD générique en mockant
la session DB avec AsyncMock/MagicMock — aucune DB réelle nécessaire.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from gsie_api.resources.schemas import ResourceUpdate
from gsie_api.resources.service import ResourceService, _champ_de_reference_fautif
from gsie_api.resources.validators import ResourceValidationError

# --- Helpers ---


class ForeignKeyViolationError(Exception):
    """Simule l'exception asyncpg ForeignKeyViolationError.

    Le service détecte cette violation par le nom de la classe (pas par
    isinstance) car asyncpg n'est pas disponible en test unitaire.
    Le nom de la classe DOIT être exactement ``ForeignKeyViolationError``.
    """

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail)
        self.detail = detail


class _FakeTypeInstance:
    """Instance type minimale pour _compute_field_changes.

    MagicMock répond True à hasattr pour tout ; cette classe n'expose
    que les attributs réellement présents sur le modèle.
    """

    name = "old_name"


def _make_service() -> ResourceService:
    """Crée un ResourceService avec une session entièrement mockée.

    `session.add` est synchrone (MagicMock) ; les autres méthodes sont
    async (AsyncMock).
    """
    session = AsyncMock()
    session.add = MagicMock()
    return ResourceService(session)


# --- Tests ---


class TestChampDeReferenceFautif:
    """Couverture de _champ_de_reference_fautif — ligne 77."""

    def should_return_none_when_detail_does_not_match_regex(self) -> None:
        # Arrange — violation trouvée mais detail sans le pattern "Key (col)="
        violation = ForeignKeyViolationError(detail="constraint violation without key pattern")
        exc = IntegrityError("INSERT", params=None, orig=violation)

        # Act
        result = _champ_de_reference_fautif(exc)

        # Assert
        assert result is None


class TestReferencesNommees:
    """Couverture du context manager _references_nommees — lignes 168-173."""

    async def should_reraise_integrity_error_when_champ_is_none(self) -> None:
        # Arrange — detail sans pattern → champ None → re-raise IntegrityError
        service = _make_service()
        violation = ForeignKeyViolationError(detail="no key pattern here")
        exc = IntegrityError("INSERT", params=None, orig=violation)

        # Act & Assert
        with pytest.raises(IntegrityError):
            async with service._references_nommees("assertion", {"claim_kind": "relation"}):
                raise exc

        service._session.rollback.assert_awaited_once()

    async def should_reraise_integrity_error_when_champ_not_in_safe_data(self) -> None:
        # Arrange — champ trouvé mais absent du payload utilisateur → re-raise
        violation = ForeignKeyViolationError(
            detail='Key (internal_id)=(...) is not present in table "resource".'
        )
        exc = IntegrityError("INSERT", params=None, orig=violation)
        service = _make_service()

        # Act & Assert
        with pytest.raises(IntegrityError):
            async with service._references_nommees("assertion", {"claim_kind": "relation"}):
                raise exc

        service._session.rollback.assert_awaited_once()

    async def should_raise_validation_error_when_champ_in_safe_data(self) -> None:
        # Arrange — champ fautif présent dans le payload → 422 (ligne 173)
        violation = ForeignKeyViolationError(
            detail='Key (source_id)=(...) is not present in table "resource".'
        )
        exc = IntegrityError("INSERT", params=None, orig=violation)
        service = _make_service()

        # Act & Assert
        with pytest.raises(ResourceValidationError, match="source_id"):
            async with service._references_nommees("observation", {"source_id": uuid4()}):
                raise exc

        service._session.rollback.assert_awaited_once()


class TestFiltrerEtCoercer:
    """Couverture de _filtrer_et_coercer — ligne 191."""

    def should_raise_validation_error_when_coercion_fails(self) -> None:
        # Arrange — valeur non-UUID pour une colonne UUID → erreur de coercion
        service = _make_service()
        model_cls = service._get_model_cls("observation")
        data = {"subject_id": "not-a-uuid"}

        # Act & Assert
        with pytest.raises(ResourceValidationError, match="subject_id"):
            service._filtrer_et_coercer("observation", model_cls, data)


class TestEnsureAuthorResource:
    """Couverture de _ensure_author_resource — lignes 258-269."""

    async def should_create_agent_when_author_id_not_found(self) -> None:
        # Arrange — author_id non trouvé en base → création de l'agent
        service = _make_service()
        author_id = uuid4()
        service._session.get = AsyncMock(return_value=None)

        # Act
        await service._ensure_author_resource(author_id)

        # Assert — ResourceModel racine + AgentModel ajoutés, flush appelé
        assert service._session.add.call_count == 2
        service._session.flush.assert_awaited_once()

    async def should_skip_creation_when_author_already_exists(self) -> None:
        # Arrange — author_id déjà présent en base → pas de création (ligne 259)
        service = _make_service()
        author_id = uuid4()
        service._session.get = AsyncMock(return_value=MagicMock())

        # Act
        await service._ensure_author_resource(author_id)

        # Assert — rien n'est ajouté, flush jamais appelé
        service._session.add.assert_not_called()
        service._session.flush.assert_not_awaited()


class TestRechargerSiExpire:
    """Couverture de _recharger_si_expire — lignes 332, 337."""

    async def should_return_early_when_instance_is_none(self) -> None:
        # Arrange
        service = _make_service()

        # Act
        await service._recharger_si_expire(None)

        # Assert — refresh jamais appelé
        service._session.refresh.assert_not_awaited()

    async def should_refresh_instance_when_expired(self) -> None:
        # Arrange — instance expirée après commit → refresh explicite
        service = _make_service()
        instance = MagicMock()
        etat = MagicMock()
        etat.expired = True
        etat.expired_attributes = set()

        with patch("gsie_api.resources.service.inspect", return_value=etat):
            # Act
            await service._recharger_si_expire(instance)

        # Assert
        service._session.refresh.assert_awaited_once_with(instance)


class TestComputeFieldChanges:
    """Couverture de _compute_field_changes — ligne 391."""

    def should_skip_field_when_type_instance_lacks_attribute(self) -> None:
        # Arrange — safe_data contient un champ absent du modèle → skip
        service = _make_service()
        safe_data = {"name": "new_name", "nonexistent_field": "value"}

        # Act
        changes = service._compute_field_changes(_FakeTypeInstance(), safe_data)

        # Assert — seul "name" a été traité, "nonexistent_field" ignoré
        assert len(changes) == 1
        assert changes[0]["field"] == "name"
        assert changes[0]["old_value"] == "old_name"
        assert changes[0]["new_value"] == "new_name"


class TestGetType:
    """Couverture de get_type — lignes 458-462."""

    async def should_return_type_when_resource_exists(self) -> None:
        # Arrange
        service = _make_service()
        resource_id = uuid4()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = "assertion"
        service._session.execute = AsyncMock(return_value=result_mock)

        # Act
        result = await service.get_type(resource_id)

        # Assert
        assert result == "assertion"

    async def should_return_none_when_resource_not_found(self) -> None:
        # Arrange
        service = _make_service()
        resource_id = uuid4()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        service._session.execute = AsyncMock(return_value=result_mock)

        # Act
        result = await service.get_type(resource_id)

        # Assert
        assert result is None


class TestUpdate:
    """Couverture de update — ligne 515."""

    async def should_return_none_when_type_instance_missing(self) -> None:
        # Arrange — resource existe mais ligne type absente → return None
        service = _make_service()
        resource_id = uuid4()
        resource = MagicMock()
        resource.type = "assertion"
        resource.deleted_at = None
        service._session.get = AsyncMock(side_effect=[resource, None])

        request = ResourceUpdate(data={"claim_kind": "relation"}, justification="test")

        # Act
        result = await service.update(resource_id, request)

        # Assert
        assert result is None


class TestRefuserGrainAbsent:
    """Couverture de _refuser_grain_absent — lignes 569-576."""

    async def should_return_early_when_distribution_has_no_scale_context(self) -> None:
        # Arrange — distribution sans scale_context_id → pas de vérification
        service = _make_service()

        # Act
        await service._refuser_grain_absent("distribution", {})

        # Assert — session.get jamais appelé
        service._session.get.assert_not_awaited()

    async def should_raise_when_scale_context_has_no_grain(self) -> None:
        # Arrange — distribution avec scale_context_id dont grain_m2 est None
        service = _make_service()
        scale_context_id = uuid4()
        echelle = MagicMock()
        echelle.grain_m2 = None
        service._session.get = AsyncMock(return_value=echelle)

        # Act & Assert
        with pytest.raises(ResourceValidationError, match="grain_m2"):
            await service._refuser_grain_absent(
                "distribution", {"scale_context_id": scale_context_id}
            )

    async def should_not_raise_when_scale_context_has_grain(self) -> None:
        # Arrange — distribution avec scale_context_id dont grain_m2 est défini
        service = _make_service()
        scale_context_id = uuid4()
        echelle = MagicMock()
        echelle.grain_m2 = 100.0
        service._session.get = AsyncMock(return_value=echelle)

        # Act & Assert — aucune exception levée
        await service._refuser_grain_absent("distribution", {"scale_context_id": scale_context_id})

    async def should_not_raise_when_scale_context_not_found(self) -> None:
        # Arrange — scale_context_id référencé mais absent en base
        # (la référence pendante est gérée par _references_nommees)
        service = _make_service()
        scale_context_id = uuid4()
        service._session.get = AsyncMock(return_value=None)

        # Act & Assert — aucune exception levée
        await service._refuser_grain_absent("distribution", {"scale_context_id": scale_context_id})


class TestAddResourceDiff:
    """Couverture de _add_resource_diff — garde du type resource_diff."""

    async def should_create_diff_with_resource_diff_type_when_updating(self) -> None:
        # Arrange — revision et diff_data minimales
        service = _make_service()
        revision = MagicMock()
        revision.id = 1
        diff_data: dict[str, object] = {}

        # Act
        await service._add_resource_diff(revision, diff_data)

        # Assert — le premier objet ajouté est un ResourceModel de type
        # "resource_diff" (type 61 du métamodèle). Sans cette ligne racine,
        # le ResourceDiff n'est pas rattaché au bon type et la mise à jour
        # échoue en violation de clé étrangère.
        assert service._session.add.call_count == 2
        first_added = service._session.add.call_args_list[0].args[0]
        assert first_added.type == "resource_diff"
