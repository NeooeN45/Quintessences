"""Import persistant et contrôlé des bundles d'analyse Forge.

Ce chemin est volontairement limité à GSIE TEST. Il persiste le bundle
canonique dans le sas field_intake en statut quarantined : la présence
d'une preuve de source qualifiée ne vaut ni acceptation métier, ni hydratation,
ni promotion. La table existante est réutilisée pour conserver une seule clé
d'idempotence et éviter une base parallèle par fournisseur.
"""

from __future__ import annotations

from datetime import UTC
from typing import TYPE_CHECKING, Literal
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from gsie_api.data.analysis_bundle import (
    ForgeAnalysisBundle,
    canonical_analysis_bundle_payload,
)
from gsie_api.data.field_intake import (
    FieldIntakeConflict,
    FieldIntakeService,
    FieldIntakeSubmission,
)

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

FORGE_ANALYSIS_BUNDLE_APPLICATION_KEY = "forge-analysis-bundle-v1"
FORGE_ANALYSIS_BUNDLE_IMPORT_POLICY = "test_quarantine_v1"
DEFAULT_FORGE_ANALYSIS_BUNDLE_PROFILE = "geosylva.station.analysis"
FORGE_ANALYSIS_BUNDLE_IMPORT_ROLES = frozenset({"writer", "admin"})


class AnalysisBundleImportError(ValueError):
    """Le bundle est valide mais ne peut pas être importé dans ce contexte."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class AnalysisBundleImportResponse(BaseModel):
    """Accusé de réception stable du sas Forge → GSIE."""

    model_config = ConfigDict(frozen=True)

    schema_version: Literal["forge_analysis_bundle_import.v1"] = "forge_analysis_bundle_import.v1"
    bundle_id: UUID
    station_id: UUID
    profile_id: str
    bundle_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    field_intake_id: UUID
    status: Literal["quarantined"]
    duplicate: bool


class ForgeAnalysisBundleImporter:
    """Persiste un bundle validé dans le sas, avec des garde-fous explicites."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        database_role: str,
        allowed_profiles: Iterable[str] | None = None,
    ) -> None:
        self._session = session
        self._database_role = database_role
        profiles = (
            (DEFAULT_FORGE_ANALYSIS_BUNDLE_PROFILE,)
            if allowed_profiles is None
            else allowed_profiles
        )
        self._allowed_profiles = frozenset(
            profile.strip().lower() for profile in profiles if profile.strip()
        )

    async def import_bundle(
        self,
        bundle: ForgeAnalysisBundle,
        *,
        submitted_by: UUID,
        authorized_roles: Collection[str],
        application_version: str = "unknown",
        trace_id: str = "",
    ) -> AnalysisBundleImportResponse:
        """Valide la politique puis persiste une seule version en quarantaine."""

        self._require_test_database()
        self._require_profile(bundle)
        self._require_authorization(authorized_roles)

        fingerprint = bundle.fingerprint()
        canonical_bundle = canonical_analysis_bundle_payload(bundle)
        submission = FieldIntakeSubmission(
            application_key=FORGE_ANALYSIS_BUNDLE_APPLICATION_KEY,
            client_event_id=str(bundle.bundle_id),
            kind="analysis_bundle",
            observed_at=bundle.generated_at.astimezone(UTC),
            payload={
                "schema_version": bundle.schema_version,
                "bundle_id": str(bundle.bundle_id),
                "station_id": str(bundle.station_id),
                "profile_id": bundle.profile_id,
                "bundle_fingerprint": fingerprint,
                "analysis_bundle": canonical_bundle,
            },
            provenance={
                "source": "Forge",
                "bundle_schema_version": bundle.schema_version,
                "bundle_hash": fingerprint,
                "profile_id": bundle.profile_id,
                "import_policy": FORGE_ANALYSIS_BUNDLE_IMPORT_POLICY,
                "authorization_policy": "dataset.write",
            },
            target_resource_id=bundle.station_id,
        )
        try:
            persisted = await FieldIntakeService(self._session).submit(
                submission,
                submitted_by=submitted_by,
                application_version=application_version,
                trace_id=trace_id,
            )
        except FieldIntakeConflict:
            raise AnalysisBundleImportError(
                "FORGE_ANALYSIS_BUNDLE_IDEMPOTENCY_CONFLICT",
                "bundle_id déjà utilisé avec une empreinte différente",
            ) from None

        return AnalysisBundleImportResponse(
            bundle_id=bundle.bundle_id,
            station_id=bundle.station_id,
            profile_id=bundle.profile_id,
            bundle_fingerprint=fingerprint,
            field_intake_id=persisted.id,
            status=persisted.status,
            duplicate=persisted.duplicate,
        )

    def _require_test_database(self) -> None:
        if self._database_role != "test":
            raise AnalysisBundleImportError(
                "FORGE_ANALYSIS_BUNDLE_TEST_ONLY",
                "import du bundle Forge refusé : database_role doit être 'test'",
            )

    def _require_profile(self, bundle: ForgeAnalysisBundle) -> None:
        if bundle.profile_id not in self._allowed_profiles:
            allowed = ", ".join(sorted(self._allowed_profiles)) or "aucun"
            raise AnalysisBundleImportError(
                "FORGE_ANALYSIS_BUNDLE_PROFILE_NOT_ALLOWED",
                f"profil Forge non autorisé : {bundle.profile_id!r}; attendus : {allowed}",
            )

    @staticmethod
    def _require_authorization(authorized_roles: Collection[str]) -> None:
        if not FORGE_ANALYSIS_BUNDLE_IMPORT_ROLES.intersection(authorized_roles):
            raise AnalysisBundleImportError(
                "FORGE_ANALYSIS_BUNDLE_UNAUTHORIZED",
                "l'import Forge exige le rôle writer ou admin",
            )


__all__ = [
    "AnalysisBundleImportError",
    "AnalysisBundleImportResponse",
    "DEFAULT_FORGE_ANALYSIS_BUNDLE_PROFILE",
    "FORGE_ANALYSIS_BUNDLE_APPLICATION_KEY",
    "FORGE_ANALYSIS_BUNDLE_IMPORT_POLICY",
    "FORGE_ANALYSIS_BUNDLE_IMPORT_ROLES",
    "ForgeAnalysisBundleImporter",
]
