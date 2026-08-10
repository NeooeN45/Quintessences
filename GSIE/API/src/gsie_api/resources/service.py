"""Service CRUD générique — opérations sur toutes les resources via le registry.

Le service utilise RESOURCE_TYPES pour router vers le bon modèle SQLAlchemy
selon le type demandé. Les champs spécifiques sont stockés dans la table
du type (class-table inheritance ADR-001).

CON-010 : jamais UPDATE ni DELETE physique.
- create  → insère resource + ligne type + Revision v1
- update  → insère nouvelle Revision + ResourceDiff + modifie les colonnes
- delete  → soft delete (deleted_at + Revision finale)
"""

import re
from collections.abc import AsyncIterator, Collection
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.data.lifecycle import InvalidDatasetTransition, transition_status
from gsie_api.infrastructure.models import RESOURCE_TYPES, ResourceModel
from gsie_api.infrastructure.models.enums import DatasetStatus
from gsie_api.infrastructure.models.outbox import OutboxEvent
from gsie_api.infrastructure.models.temporal_engine import (
    ResourceDiffModel,
    RevisionModel,
)
from gsie_api.resources.coercion import coercer_donnees, serialiser_valeur
from gsie_api.resources.schemas import (
    ResourceCreate,
    ResourceListResponse,
    ResourceRead,
    ResourceUpdate,
    RevisionRead,
)
from gsie_api.resources.validators import (
    ResourceValidationError,
    validate_resource_data,
    validate_resource_payload,
    validate_resource_state,
)
from gsie_api.websocket.events import EventType, WSEvent

logger = get_logger("gsie_api.resources.service")


def _champ_de_reference_fautif(exc: IntegrityError) -> str | None:
    """Extrait la colonne d'une violation de clé étrangère, si c'en est une.

    SQLAlchemy n'expose pas directement l'erreur asyncpg : `exc.orig` est le
    wrapper `AsyncAdapt_asyncpg_dbapi.IntegrityError`, et la véritable
    `ForeignKeyViolationError` — seule à porter le `detail` exploitable — se
    trouve plus loin dans la chaîne des causes. On la cherche donc au lieu de
    ne regarder que le premier maillon.

    asyncpg décrit la violation ainsi :
    ``Key (source_id)=(...) is not present in table "resource".``
    """
    violation = None
    courante: BaseException | None = getattr(exc, "orig", None) or exc
    vues: set[int] = set()
    while courante is not None and id(courante) not in vues:
        vues.add(id(courante))
        if type(courante).__name__ == "ForeignKeyViolationError":
            violation = courante
            break
        courante = courante.__cause__ or courante.__context__

    if violation is None:
        return None
    detail = str(getattr(violation, "detail", "") or "")
    correspondance = re.search(r"Key \(([^)]+)\)=", detail)
    if correspondance is None:
        return None
    colonnes = [c.strip() for c in correspondance.group(1).split(",")]
    return colonnes[0] if len(colonnes) == 1 else None


# Champs que la protection mass-assignment interdit par leur nom, mais qui sont
# de vrais champs métier pour certains types : `version` est le numéro de
# version sémantique d'un modèle ou d'un jeu de données, pas le compteur
# système d'`assertion`. Sans cette levée ciblée, ces types sont NOT NULL sur
# une colonne systématiquement filtrée, donc impossibles à créer (500).
_CHAMPS_METIER_AUTORISES: dict[str, frozenset[str]] = {
    "model_version": frozenset({"version"}),
    "dataset_version": frozenset({"version"}),
    "vocabulary_release": frozenset({"version"}),
    "diagnostic_protocol": frozenset({"version"}),
    "temporal_context": frozenset({"valid_time_start", "valid_time_end"}),
}

# Constantes
_GSIE_ID_SUFFIX_LENGTH = 8


class ResourceService:
    """Service CRUD générique pour les types enregistrés du métamodèle."""

    # Champs système non modifiables par l'utilisateur (mass assignment protection)
    _FORBIDDEN_FIELDS: frozenset[str] = frozenset(
        {
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
            "revision_id",
            "version",
            "author_id",
            "transaction_time",
            "valid_time_start",
            "valid_time_end",
        }
    )

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- Helpers privés ---

    def _get_model_cls(self, type_name: str) -> type[Any]:
        """Récupère la classe modèle SQLAlchemy pour un type donné."""
        if type_name not in RESOURCE_TYPES:
            # Ne pas énumérer les types : le message d'erreur renvoyé au
            # client exposait les 90 types du registre, y compris les 4
            # que /resources/types censure pour les non-RGPD-managers
            # (audit 2026-08-01, constat K).
            raise ValueError(
                f"Type inconnu : {type_name}. "
                "Consultez GET /resources/types pour la liste autorisée."
            )
        return RESOURCE_TYPES[type_name]

    def _filter_data(
        self, model_cls: type[Any], data: dict[str, Any], type_name: str | None = None
    ) -> dict[str, Any]:
        """Filtre les champs interdits (mass assignment protection, OWASP A01)."""
        allowed_columns = {col.name for col in model_cls.__table__.columns if col.name != "id"}
        interdits = self._FORBIDDEN_FIELDS - _CHAMPS_METIER_AUTORISES.get(
            type_name or "", frozenset()
        )
        return {k: v for k, v in data.items() if k in allowed_columns and k not in interdits}

    @asynccontextmanager
    async def _references_nommees(
        self, type_name: str, safe_data: dict[str, Any]
    ) -> AsyncIterator[None]:
        """Traduit une référence pendante en 422, où qu'elle soit détectée.

        Les champs de référence (`source_id`, `target_id`, `station_id`…) sont
        des clés étrangères vers `resource(id)`. Pointer une resource qui
        n'existe pas est une faute de l'appelant, pas une panne du serveur :
        la laisser remonter produisait un 500 opaque.

        Le bloc couvre toute l'opération, pas seulement le `commit` : la
        violation est le plus souvent levée bien avant, lors de l'`autoflush`
        déclenché par la première requête qui suit l'insertion.

        On ne traduit que si la colonne fautive vient de la charge utile. Une
        violation portant sur une colonne que le service gère lui-même reste
        une anomalie interne et doit continuer à remonter en 500, plutôt que
        d'être maquillée en erreur client.
        """
        try:
            yield
        except IntegrityError as exc:
            await self._session.rollback()
            champ = _champ_de_reference_fautif(exc)
            if champ is None or champ not in safe_data:
                raise
            raise ResourceValidationError(
                type_name,
                [f"Référence inexistante pour {champ} : aucune resource ne porte cet identifiant"],
            ) from exc

    def _filtrer_et_coercer(
        self, type_name: str, model_cls: type[Any], data: dict[str, Any]
    ) -> dict[str, Any]:
        """Filtre les champs interdits puis convertit les valeurs vers leurs types SQL.

        Sans cette conversion, une chaîne ISO destinée à un `timestamptz`
        traversait la porte de validation et n'échouait qu'au niveau du pilote
        asyncpg : le client recevait un 500 opaque. Toute conversion impossible
        devient ici une erreur de validation, donc un 422 explicable.
        """
        safe_data = self._filter_data(model_cls, data, type_name)
        converti, erreurs = coercer_donnees(model_cls, safe_data)
        if erreurs:
            raise ResourceValidationError(type_name, erreurs)
        return converti

    @staticmethod
    def _generate_gsie_id(type_name: str) -> str:
        """Génère un identifiant lisible (ex. assertion:2026:a1b2c3d4)."""
        year = datetime.now(UTC).year
        short_uuid = uuid4().hex[:_GSIE_ID_SUFFIX_LENGTH]
        return f"{type_name}:{year}:{short_uuid}"

    async def _get_next_version(self, resource_id: UUID) -> int:
        """Récupère le numéro de version suivant pour une resource.

        Verrou sur la resource (SELECT ... FOR UPDATE) pour sérialiser
        l'allocation du numéro de version : sans ce verrou, deux écritures
        concurrentes calculeraient toutes deux max()+1 et produiraient deux
        révisions de même numéro (audit 2026-08-02, 3ᵉ passe).
        """
        await self._session.execute(
            select(ResourceModel).where(ResourceModel.id == resource_id).with_for_update()
        )
        current = (
            await self._session.execute(
                select(func.max(RevisionModel.version)).where(
                    RevisionModel.target_id == resource_id
                )
            )
        ).scalar_one()
        return (current or 0) + 1

    async def _create_revision(
        self,
        resource_id: UUID,
        version: int,
        justification: str,
        author_id: UUID | None = None,
        diff_data: dict[str, Any] | None = None,
    ) -> RevisionModel:
        """Crée une Revision (append-only, CON-010)."""
        now = datetime.now(UTC)
        await self._ensure_author_resource(author_id)
        revision = RevisionModel(
            target_id=resource_id,
            version=version,
            author_id=author_id,
            justification=justification,
            valid_time_start=now,
            transaction_time=now,
        )
        self._session.add(revision)
        await self._session.flush()
        if diff_data:
            await self._add_resource_diff(revision, diff_data)
        return revision

    async def _ensure_author_resource(self, author_id: UUID | None) -> None:
        """Garantit que l'auteur existe comme Agent avant de le citer.

        `revision.author_id` est une clé étrangère vers `resource(id)` : le
        métamodèle veut un Agent (type 9), pas un identifiant flottant. Le
        router dérive un UUID déterministe du sujet JWT ; sans cette ligne
        parente, PostgreSQL refuse la Revision et toute écriture authentifiée
        échoue. On matérialise donc l'Agent une seule fois, sans rien inventer
        d'autre que son identité technique (CON-010 : l'auteur reste traçable).
        """
        if author_id is None:
            return
        if await self._session.get(ResourceModel, author_id) is not None:
            return
        agent_cls = self._get_model_cls("agent")
        self._session.add(
            ResourceModel(
                id=author_id,
                type="agent",
                gsie_id=f"agent:{author_id}",
            )
        )
        self._session.add(agent_cls(id=author_id, name=str(author_id), type="person"))
        await self._session.flush()

    async def _add_resource_diff(self, revision: RevisionModel, diff_data: dict[str, Any]) -> None:
        """Ajoute un ResourceDiff à une Revision.

        `resource_diff` suit l'héritage par table (ADR-001) : c'est le type 61
        du métamodèle, donc sa clé primaire est une clé étrangère vers
        `resource(id)`. Forger un UUID sans créer la ligne racine produisait une
        violation de clé étrangère à chaque mise à jour (ADR-002).
        """
        diff_resource = ResourceModel(
            type="resource_diff",
            gsie_id=self._generate_gsie_id("resource_diff"),
        )
        self._session.add(diff_resource)
        await self._session.flush()
        resource_diff = ResourceDiffModel(
            id=diff_resource.id,
            to_revision_id=revision.id,
            field_changes=diff_data.get("field_changes", []),
            added_relations=diff_data.get("added_relations", []),
            removed_relations=diff_data.get("removed_relations", []),
        )
        self._session.add(resource_diff)
        revision.diff_id = resource_diff.id

    def _enqueue_event(
        self,
        event_type: EventType,
        resource_id: UUID,
        resource_type: str,
        data: dict[str, Any],
    ) -> None:
        """Ajoute un événement à l'outbox dans la transaction métier courante."""
        event_id = uuid4()
        event = WSEvent(
            event_id=event_id,
            event_type=event_type,
            resource_id=resource_id,
            resource_type=resource_type,
            data=data,
            timestamp=datetime.now(UTC).isoformat(),
        )
        self._session.add(
            OutboxEvent(
                id=event_id,
                aggregate_id=resource_id,
                aggregate_type=resource_type,
                event_type=event_type.value,
                payload=event.model_dump(mode="json"),
            )
        )

    async def _recharger_si_expire(self, instance: Any) -> None:
        """Recharge explicitement une instance expirée avant de lire ses champs.

        Après un commit, les colonnes portant `onupdate=func.now()` sont
        expirées par SQLAlchemy pour forcer la relecture. En asynchrone, y
        toucher déclencherait un chargement paresseux hors greenlet
        (`MissingGreenlet`) : la lecture qui suit une écriture doit donc
        demander son entrée/sortie explicitement.
        """
        if instance is None:
            return
        etat = inspect(instance)
        # `expired` ne vaut que pour un objet entièrement expiré ; après un
        # UPDATE, seules les colonnes `onupdate` le sont, d'où `expired_attributes`.
        if etat.expired or etat.expired_attributes:
            await self._session.refresh(instance)

    async def _build_resource_read(self, resource: ResourceModel) -> ResourceRead:
        """Construit un ResourceRead depuis un ResourceModel + sa ligne type."""
        model_cls = self._get_model_cls(resource.type)
        type_result = await self._session.get(model_cls, resource.id)
        await self._recharger_si_expire(resource)
        await self._recharger_si_expire(type_result)
        type_data: dict[str, Any] = {}
        if type_result is not None:
            type_data = {
                col.name: serialiser_valeur(getattr(type_result, col.name))
                for col in type_result.__table__.columns
                if col.name != "id"
            }
        return ResourceRead(
            id=resource.id,
            type=resource.type,
            gsie_id=resource.gsie_id,
            organisation_id=resource.organisation_id,
            workspace_id=resource.workspace_id,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
            metadata_json=resource.metadata_json,
            data=type_data,
        )

    @staticmethod
    def _to_resource_read(resource: ResourceModel, data: dict[str, Any]) -> ResourceRead:
        """Construit un ResourceRead léger (sans fetch de la ligne type)."""
        return ResourceRead(
            id=resource.id,
            type=resource.type,
            gsie_id=resource.gsie_id,
            organisation_id=resource.organisation_id,
            workspace_id=resource.workspace_id,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
            metadata_json=resource.metadata_json,
            data=data,
        )

    @staticmethod
    def _current_state(type_instance: Any) -> dict[str, Any]:
        """Relit l'état courant complet de la ligne du type (hors `id`)."""
        return {
            col.name: serialiser_valeur(getattr(type_instance, col.name))
            for col in type_instance.__table__.columns
            if col.name != "id"
        }

    def _compute_field_changes(
        self, type_instance: Any, safe_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Calcule le diff entre les valeurs actuelles et les nouvelles valeurs."""
        changes: list[dict[str, Any]] = []
        for key, new_value in safe_data.items():
            if not hasattr(type_instance, key):
                continue
            old_value = getattr(type_instance, key)
            if old_value != new_value:
                changes.append(
                    {
                        "field": key,
                        "old_value": str(old_value) if old_value is not None else None,
                        "new_value": str(new_value) if new_value is not None else None,
                    }
                )
                setattr(type_instance, key, new_value)
        return changes

    # --- Opérations CRUD publiques ---

    async def create(self, request: ResourceCreate, author_id: UUID | None = None) -> ResourceRead:
        """Crée une resource + sa ligne dans la table du type + Revision v1."""
        model_cls = self._get_model_cls(request.type)
        errors = validate_resource_data(request.type, request.data)
        if errors:
            raise ResourceValidationError(request.type, errors)

        safe_data = self._filtrer_et_coercer(request.type, model_cls, request.data)
        await self._refuser_grain_absent(request.type, safe_data)
        gsie_id = request.gsie_id or self._generate_gsie_id(request.type)

        async with self._references_nommees(request.type, safe_data):
            resource = await self._insert_resource(request.type, gsie_id, model_cls, safe_data)
            await self._create_revision(
                resource_id=resource.id,
                version=1,
                justification="Création initiale",
                author_id=author_id,
            )
            self._enqueue_event(
                EventType.resource_created,
                resource.id,
                request.type,
                {"gsie_id": gsie_id},
            )
            await self._session.commit()

        logger.info(
            "resource_created", resource_id=str(resource.id), type=request.type, gsie_id=gsie_id
        )
        return await self._build_resource_read(resource)

    async def _insert_resource(
        self, type_name: str, gsie_id: str, model_cls: type, safe_data: dict[str, Any]
    ) -> ResourceModel:
        """Insère la ligne racine resource + la ligne dans la table du type."""
        resource = ResourceModel(
            type=type_name,
            gsie_id=gsie_id,
            organisation_id=self._session.info.get("organisation_id"),
            workspace_id=self._session.info.get("workspace_id"),
        )
        self._session.add(resource)
        await self._session.flush()
        type_instance = model_cls(id=resource.id, **safe_data)
        self._session.add(type_instance)
        return resource

    async def get(self, resource_id: UUID) -> ResourceRead | None:
        """Récupère une resource par son ID (exclut les soft-deleted)."""
        result = await self._session.get(ResourceModel, resource_id)
        if result is None or result.deleted_at is not None:
            return None
        return await self._build_resource_read(result)

    async def get_type(self, resource_id: UUID) -> str | None:
        """Retourne uniquement le type d'une resource active pour autoriser avant lecture."""
        query = select(ResourceModel.type).where(
            ResourceModel.id == resource_id,
            ResourceModel.deleted_at.is_(None),
        )
        return (await self._session.execute(query)).scalar_one_or_none()

    async def list_resources(
        self,
        type_filter: str | None = None,
        page: int = 1,
        size: int = 20,
        excluded_types: Collection[str] | None = None,
    ) -> ResourceListResponse:
        """Liste paginée de resources, optionnellement filtrée par type."""
        query = select(ResourceModel).where(ResourceModel.deleted_at.is_(None))
        count_query = (
            select(func.count())
            .select_from(ResourceModel)
            .where(ResourceModel.deleted_at.is_(None))
        )
        if type_filter:
            query = query.where(ResourceModel.type == type_filter)
            count_query = count_query.where(ResourceModel.type == type_filter)

        excluded = tuple(sorted(excluded_types or ()))
        if excluded:
            query = query.where(ResourceModel.type.not_in(excluded))
            count_query = count_query.where(ResourceModel.type.not_in(excluded))

        total = (await self._session.execute(count_query)).scalar_one()
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(ResourceModel.created_at.desc())
        results = (await self._session.execute(query)).scalars().all()
        items = [self._to_resource_read(r, {}) for r in results]

        return ResourceListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            type_filter=type_filter,
        )

    async def update(
        self,
        resource_id: UUID,
        request: ResourceUpdate,
        author_id: UUID | None = None,
    ) -> ResourceRead | None:
        """Met à jour une resource — crée une Revision + ResourceDiff (CON-010)."""
        resource = await self._session.get(ResourceModel, resource_id)
        if resource is None or resource.deleted_at is not None:
            return None

        model_cls = self._get_model_cls(resource.type)
        type_instance = await self._session.get(model_cls, resource_id)
        if type_instance is None:
            return None

        safe_data = self._filtrer_et_coercer(resource.type, model_cls, request.data)
        # La validation porte sur l'état final, avant toute mutation : un
        # patch partiel ne peut pas rendre la resource invalide en silence,
        # et un patch refusé ne laisse ni Revision ni événement d'outbox.
        await self._reject_invalid_update(resource.type, type_instance, request.data, safe_data)
        await self._refuser_grain_absent(resource.type, safe_data)

        async with self._references_nommees(resource.type, safe_data):
            field_changes = self._compute_field_changes(type_instance, safe_data)
            next_version = await self._get_next_version(resource_id)

            await self._create_revision(
                resource_id=resource_id,
                version=next_version,
                justification=request.justification,
                author_id=author_id,
                diff_data={"field_changes": field_changes},
            )
            self._enqueue_event(
                EventType.resource_updated,
                resource_id,
                resource.type,
                {
                    "version": next_version,
                    "changed_fields": sorted(change["field"] for change in field_changes),
                },
            )
            await self._session.commit()

        logger.info(
            "resource_updated",
            resource_id=str(resource_id),
            type=resource.type,
            version=next_version,
            justification=request.justification,
        )
        result = await self.get(resource_id)
        return result

    async def _refuser_grain_absent(self, type_name: str, safe_data: dict[str, Any]) -> None:
        """Une distribution qui déclare une échelle exige son grain.

        `scale_context` porte la résolution native d'une source
        (`NOMENCLATURE_SOURCES.md` §4). S'y rattacher sans renseigner le grain
        laisserait la résolution implicite, donc inexploitable : deux sources
        ne sont comparables que si leur grain est un nombre.

        Le contrôle ne peut pas vivre dans la porte de validation pure — il
        exige de relire la resource référencée.
        """
        if type_name != "distribution":
            return
        scale_context_id = safe_data.get("scale_context_id")
        if scale_context_id is None:
            return

        echelle = await self._session.get(self._get_model_cls("scale_context"), scale_context_id)
        # Une référence pendante est nommée par `_references_nommees`.
        if echelle is not None and echelle.grain_m2 is None:
            raise ResourceValidationError(
                type_name,
                [
                    "scale_context_id désigne une échelle sans grain_m2 : la "
                    "résolution native d'une source doit être un nombre, jamais "
                    "laissée implicite"
                ],
            )

    async def _reject_invalid_update(
        self,
        type_name: str,
        type_instance: Any,
        raw_data: dict[str, Any],
        safe_data: dict[str, Any],
    ) -> None:
        """Refuse une mise à jour dont l'état final violerait les invariants.

        Les bornes de transport sont jugées sur le corps reçu, les invariants
        sur l'état courant fusionné avec le patch filtré — c'est exactement ce
        qui serait écrit. La session est remise à plat avant de lever, pour
        qu'aucune mutation partielle ni aucun événement ne survive à l'échec.
        """
        errors = validate_resource_payload(raw_data)
        current_state = self._current_state(type_instance)
        final_state = {**current_state, **safe_data}
        errors.extend(validate_resource_state(type_name, final_state))
        if type_name == "dataset_version" and "status" in safe_data:
            current_status = current_state.get("status")
            target_status = safe_data["status"]
            if (
                current_status != target_status
                and isinstance(current_status, DatasetStatus | str)
                and isinstance(target_status, DatasetStatus | str)
            ):
                try:
                    transition_status(current_status, target_status)
                except InvalidDatasetTransition as exc:
                    errors.append(f"DATASET_STATUS_TRANSITION_INVALID: {exc}")
                if target_status in {DatasetStatus.staging, DatasetStatus.production}:
                    errors.append(
                        "DATASET_PROMOTION_REQUIRES_DEDICATED_SERVICE: "
                        "la promotion exige qualité, droits, actif RAW et validation opérateur"
                    )
        if not errors:
            return

        await self._session.rollback()
        logger.warning(
            "resource_update_rejected",
            type=type_name,
            error_count=len(errors),
            fields=sorted(safe_data),
        )
        raise ResourceValidationError(type_name, errors)

    async def delete(
        self,
        resource_id: UUID,
        justification: str = "Suppression",
        author_id: UUID | None = None,
    ) -> bool:
        """Soft delete — marque deleted_at + crée une Revision finale (CON-010)."""
        resource = await self._session.get(ResourceModel, resource_id)
        if resource is None or resource.deleted_at is not None:
            return False

        resource.deleted_at = datetime.now(UTC)
        next_version = await self._get_next_version(resource_id)

        await self._create_revision(
            resource_id=resource_id,
            version=next_version,
            justification=f"[DELETED] {justification}",
            author_id=author_id,
        )
        self._enqueue_event(
            EventType.resource_deleted,
            resource_id,
            resource.type,
            {"version": next_version},
        )
        await self._session.commit()

        logger.info("resource_soft_deleted", resource_id=str(resource_id), version=next_version)
        return True

    async def list_revisions(self, resource_id: UUID) -> list[RevisionRead]:
        """Liste l'historique des révisions d'une resource."""
        result = await self._session.execute(
            select(RevisionModel)
            .where(RevisionModel.target_id == resource_id)
            .order_by(RevisionModel.version.desc())
        )
        return [
            RevisionRead(
                id=r.id,
                target_id=r.target_id,
                version=r.version,
                author_id=r.author_id,
                justification=r.justification,
                valid_time_start=r.valid_time_start,
                valid_time_end=r.valid_time_end,
                transaction_time=r.transaction_time,
                created_at=r.created_at,
            )
            for r in result.scalars().all()
        ]

    @staticmethod
    def list_types() -> list[str]:
        """Retourne la liste des types disponibles."""
        return sorted(RESOURCE_TYPES.keys())
