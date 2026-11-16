"""Preuves PostgreSQL réelles de la réconciliation des deux lignées d'intake.

Les historiques sont recréés avec les anciennes migrations figées, sans
``stamp`` ni ``create_all``. Les scénarios conservent les lignes complètes
et leurs identifiants physiques lors des passages de compatibilité.
"""

from __future__ import annotations

import ast
import asyncio
import hashlib
import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from gsie_api.core.config import get_settings
from tests.conftest import requires_docker
from tests.integration.test_migration_baseline import (
    _IMAGE_DB,
    _REQUIRE_IMAGE,
    _image_disponible,
    _nettoyer_extensions_preinstallees,
)

pytestmark = requires_docker

_RACINE_API = Path(__file__).resolve().parents[2]
_VERSIONS = _RACINE_API / "alembic" / "versions"
_FEAT_0051 = "20260823_0051"
_MAIN_0051 = "20260908_0051"
_FEAT_0059 = "20260929_0059"
_HEAD = "20261116_0060"
_DATE = datetime(2026, 8, 15, 12, 34, 56, 123456, tzinfo=UTC)
_RESOURCE_ID = UUID("00000000-0000-4000-8000-000000000001")
_SUBMITTER_ID = UUID("00000000-0000-4000-8000-000000000002")
_REVIEWER_ID = UUID("00000000-0000-4000-8000-000000000003")
_TABLES_SENTINELLES = ("resource", "gsie_rgpd_identites.user_account", "field_intake")
_TABLES_BFF = (
    "gsie_rgpd_identites.geosylva_analysis_job",
    "gsie_rgpd_identites.geosylva_cubage_session",
)

# Fichiers antérieurs à la réconciliation, copiés exactement depuis les SHA
# approuvés. Aucun accès à Git, au réseau ou à une ancienne branche au runtime.
# Les empreintes couvrent aussi les fichiers communs repris dans tmp_path.
_SHA_HISTORIQUES = {
    "main": "0daa315dfcb8475dda81076b0317b2bb0181a248303086c01a05da01eafd5f97",
    "feat": "5456232796d8bc4cee20999acbed08f7db86e450163f7659b3805c06aabdab23",
}

# main d7b400cb15d9f2216f3296d92754a6e67e55a63f.
_ANCIENNE_MAIN_0051 = '''"""Ajoute la table d intake applicatif en quarantaine.

Revision ID: 20260908_0051
Revises: 20260815_0050
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260908_0051"
down_revision: str | None = "20260815_0050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Persiste les soumissions terrain avant leur qualification canonique."""
    op.create_table(
        "field_intake",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_key", sa.String(length=100), nullable=False),
        sa.Column("client_event_id", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("target_resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('quarantined', 'accepted', 'rejected')",
            name="ck_field_intake_status",
        ),
        sa.ForeignKeyConstraint(["target_resource_id"], ["resource.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "application_key",
            "client_event_id",
            name="uq_field_intake_application_event",
        ),
    )
    op.create_index("ix_field_intake_submitted_by", "field_intake", ["submitted_by"])
    op.create_index("ix_field_intake_target_resource_id", "field_intake", ["target_resource_id"])
    op.create_index(
        "ix_field_intake_submitted_by_received",
        "field_intake",
        ["submitted_by", "received_at"],
    )
    op.create_index(
        "ix_field_intake_status_received",
        "field_intake",
        ["status", "received_at"],
    )


def downgrade() -> None:
    """Retire la table de quarantaine et ses index."""
    op.drop_index("ix_field_intake_status_received", table_name="field_intake")
    op.drop_index("ix_field_intake_submitted_by_received", table_name="field_intake")
    op.drop_index("ix_field_intake_target_resource_id", table_name="field_intake")
    op.drop_index("ix_field_intake_submitted_by", table_name="field_intake")
    op.drop_table("field_intake")
'''

# feat/schemas-de-domaine 9e6864b353c8c03d15c067dffd2b358f7a57d94f.
_ANCIENNE_FEAT_0051 = '''"""Ajoute la table d'intake stationnel et ses index de lecture.

Revision ID: 20260823_0051
Revises: 20260815_0050
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260823_0051"
down_revision: str | None = "20260815_0050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée le sas append-only des soumissions stationnelles."""
    op.create_table(
        "field_intake",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("submitted_by", PGUUID(as_uuid=True), nullable=False),
        sa.Column("application_key", sa.String(100), nullable=False),
        sa.Column("client_event_id", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("provenance", JSONB, nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column(
            "target_resource_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("resource.id"),
            nullable=True,
        ),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", PGUUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "application_key",
            "client_event_id",
            name="uq_field_intake_application_event",
        ),
        sa.CheckConstraint(
            "status IN ('quarantined', 'accepted', 'rejected')",
            name="ck_field_intake_status",
        ),
    )
    op.create_index("ix_field_intake_submitted_by", "field_intake", ["submitted_by"])
    op.create_index("ix_field_intake_target_resource_id", "field_intake", ["target_resource_id"])
    op.create_index(
        "ix_field_intake_submitted_by_received",
        "field_intake",
        ["submitted_by", "received_at"],
    )
    op.create_index(
        "ix_field_intake_status_received",
        "field_intake",
        ["status", "received_at"],
    )


def downgrade() -> None:
    """Retire la table d'intake lors d'un rollback explicite."""
    op.drop_index("ix_field_intake_status_received", table_name="field_intake")
    op.drop_index("ix_field_intake_submitted_by_received", table_name="field_intake")
    op.drop_index("ix_field_intake_target_resource_id", table_name="field_intake")
    op.drop_index("ix_field_intake_submitted_by", table_name="field_intake")
    op.drop_table("field_intake")
'''

# Son prédécesseur était A ; la réconciliation le place ensuite après B.
_ANCIENNE_FEAT_0052 = '''"""Rattrapage du droit USAGE du role applicatif sur la facturation.

La migration 0038 accordait les droits sur les tables de ``gsie_billing``
mais oubliait le droit de resolution du schema. Une base migree pouvait donc
installer un compte local, puis echouer lors de la creation de son abonnement
gratuit.

Revision: 20260826_0052
Precede: 20260823_0051
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260826_0052"
down_revision: str | None = "20260823_0051"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_billing"
_ROLE_APPLICATION = "gsie_application"


def upgrade() -> None:
    """Permettre au role applicatif d'adresser les tables deja protegees."""
    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")


def downgrade() -> None:
    """Retirer uniquement le droit ajoute par cette migration."""
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
'''


def _configuration_courante() -> Config:
    configuration = Config(str(_RACINE_API / "alembic.ini"))
    configuration.set_main_option("script_location", str(_RACINE_API / "alembic"))
    return configuration


def _identifiant_revision(source: str) -> str:
    for instruction in ast.parse(source).body:
        if (
            isinstance(instruction, ast.AnnAssign)
            and isinstance(instruction.target, ast.Name)
            and instruction.target.id == "revision"
            and isinstance(instruction.value, ast.Constant)
        ):
            return str(instruction.value.value)
    raise AssertionError("La fixture doit provenir d'une révision Alembic identifiée")


def _configuration_historique(repertoire: Path, lignee: str) -> Config:
    """Reconstruit la véritable chaîne antérieure, empreinte comprise."""
    versions = repertoire / lignee / "versions"
    versions.mkdir(parents=True)
    for chemin in _VERSIONS.glob("*.py"):
        source = chemin.read_text(encoding="utf-8")
        revision = _identifiant_revision(source)
        numero = int(revision.rsplit("_", maxsplit=1)[1])
        if numero <= 50 or (lignee == "feat" and 52 <= numero <= 59):
            if revision == "20260826_0052":
                source = _ANCIENNE_FEAT_0052
            (versions / chemin.name).write_text(source, encoding="utf-8")

    if lignee == "main":
        nom = "20260908_0051_field_intake.py"
        source = _ANCIENNE_MAIN_0051
    else:
        nom = "20260823_0051_field_intake.py"
        source = _ANCIENNE_FEAT_0051
    (versions / nom).write_text(source, encoding="utf-8")

    empreinte = hashlib.sha256()
    for chemin in sorted(versions.glob("*.py")):
        empreinte.update(chemin.name.encode() + b"\0" + chemin.read_bytes() + b"\0")
    assert empreinte.hexdigest() == _SHA_HISTORIQUES[lignee], (
        "La chaîne historique doit correspondre exactement au snapshot approuvé"
    )

    configuration = _configuration_courante()
    configuration.set_main_option("version_locations", str(versions))
    return configuration


@contextmanager
def _postgres_jetable() -> Generator[str, None, None]:
    """Ouvre uniquement une base créée par ce test, avec les deux URL isolées."""
    from testcontainers.postgres import PostgresContainer

    if not _image_disponible(_IMAGE_DB):
        message = f"image {_IMAGE_DB} absente ; construire GSIE/API/Dockerfile.db"
        if _REQUIRE_IMAGE:
            pytest.fail(message)
        pytest.skip(message)

    with PostgresContainer(
        image=_IMAGE_DB,
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_reconciliation_test",
    ).with_command("postgres -c shared_preload_libraries=age -c search_path=public") as postgres:
        url = postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        asyncio.run(_nettoyer_extensions_preinstallees(url))
        patch = pytest.MonkeyPatch()
        patch.setenv("GSIE_DATABASE_URL", url)
        patch.setenv("GSIE_MIGRATION_DATABASE_URL", url)
        patch.setenv("GSIE_DATABASE_ROLE", "test")
        patch.setenv("GSIE_DATA_NAMESPACE", "gsie-reconciliation-test")
        get_settings.cache_clear()
        try:
            yield url
        finally:
            patch.undo()
            get_settings.cache_clear()


@pytest.fixture
def base_reconciliation() -> Generator[str, None, None]:
    with _postgres_jetable() as url:
        yield url


def _requete(url: str, instruction: str, **parametres: Any) -> list[Any]:
    async def executer() -> list[Any]:
        moteur = create_async_engine(
            url,
            connect_args={"server_settings": {"search_path": "public"}},
        )
        try:
            async with moteur.begin() as connexion:
                resultat = await connexion.execute(text(instruction), parametres)
                return list(resultat.scalars()) if resultat.returns_rows else []
        finally:
            await moteur.dispose()

    return asyncio.run(executer())


def _executer(url: str, *instructions: str) -> None:
    async def executer() -> None:
        moteur = create_async_engine(url)
        try:
            async with moteur.begin() as connexion:
                for instruction in instructions:
                    await connexion.execute(text(instruction))
        finally:
            await moteur.dispose()

    asyncio.run(executer())


def _versions(url: str) -> list[str]:
    return _requete(url, "SELECT version_num FROM alembic_version ORDER BY version_num")


def _tables(url: str) -> list[str]:
    return _requete(
        url,
        "SELECT schemaname || '.' || tablename FROM pg_tables "
        "WHERE schemaname = 'public' OR schemaname LIKE 'gsie_%' ORDER BY 1",
    )


def _catalogue(url: str) -> dict[str, Any]:
    """Inclut les OID : recréer discrètement la table ou un index est visible."""
    ligne = _requete(
        url,
        """
        SELECT jsonb_build_object(
            'relation', (
                SELECT jsonb_build_object(
                    'oid', c.oid, 'kind', c.relkind,
                    'rls', c.relrowsecurity, 'force_rls', c.relforcerowsecurity
                )
                FROM pg_class c WHERE c.oid = to_regclass('public.field_intake')
            ),
            'colonnes', (
                SELECT jsonb_object_agg(a.attname, jsonb_build_object(
                    'type', format_type(a.atttypid, a.atttypmod),
                    'nullable', NOT a.attnotnull,
                    'default', pg_get_expr(d.adbin, d.adrelid)
                ))
                FROM pg_attribute a
                LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
                WHERE a.attrelid = to_regclass('public.field_intake')
                  AND a.attnum > 0 AND NOT a.attisdropped
            ),
            'contraintes', (
                SELECT jsonb_object_agg(c.conname, jsonb_build_object(
                    'definition', pg_get_constraintdef(c.oid),
                    'type', c.contype,
                    'validated', c.convalidated,
                    'deferrable', c.condeferrable,
                    'deferred', c.condeferred
                ))
                FROM pg_constraint c WHERE c.conrelid = to_regclass('public.field_intake')
            ),
            'index', (
                SELECT jsonb_object_agg(c.relname, jsonb_build_object(
                    'oid', i.indexrelid,
                    'definition', pg_get_indexdef(i.indexrelid),
                    'valid', i.indisvalid,
                    'ready', i.indisready
                ))
                FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
                WHERE i.indrelid = to_regclass('public.field_intake')
            )
        )::text
        """,
    )
    return json.loads(ligne[0])


def _verifier_contrat(url: str) -> None:
    catalogue = _catalogue(url)
    colonnes = {
        "id": ("uuid", False, None),
        "created_at": ("timestamp with time zone", False, "now()"),
        "updated_at": ("timestamp with time zone", False, "now()"),
        "submitted_by": ("uuid", False, None),
        "application_key": ("character varying(100)", False, None),
        "client_event_id": ("character varying(200)", False, None),
        "kind": ("character varying(40)", False, None),
        "observed_at": ("timestamp with time zone", False, None),
        "received_at": ("timestamp with time zone", False, "now()"),
        "status": ("character varying(20)", False, None),
        "payload": ("jsonb", False, None),
        "provenance": ("jsonb", False, None),
        "payload_hash": ("character varying(64)", False, None),
        "target_resource_id": ("uuid", True, None),
        "review_notes": ("text", True, None),
        "reviewed_by": ("uuid", True, None),
        "reviewed_at": ("timestamp with time zone", True, None),
    }
    assert {
        nom: (colonne["type"], colonne["nullable"], colonne["default"])
        for nom, colonne in catalogue["colonnes"].items()
    } == colonnes
    assert catalogue["relation"]["kind"] == "r"
    assert catalogue["relation"]["rls"] is False
    assert catalogue["relation"]["force_rls"] is False
    assert set(catalogue["contraintes"]) == {
        "field_intake_pkey",
        "field_intake_target_resource_id_fkey",
        "uq_field_intake_application_event",
        "ck_field_intake_status",
    }
    assert set(catalogue["index"]) == {
        "field_intake_pkey",
        "uq_field_intake_application_event",
        "ix_field_intake_submitted_by",
        "ix_field_intake_target_resource_id",
        "ix_field_intake_submitted_by_received",
        "ix_field_intake_status_received",
    }
    assert all(
        index["valid"] and index["ready"] for index in catalogue["index"].values()
    )


def _inserer_sentinelles(url: str, *, bff: bool = False) -> tuple[str, ...]:
    """Les trois statuts, les champs de revue et la provenance sont renseignés."""
    _requete(
        url,
        "INSERT INTO resource (id, type, metadata_json, created_at, updated_at) "
        "VALUES (:id, 'place', CAST(:metadata AS jsonb), :date, :date)",
        id=_RESOURCE_ID,
        metadata=json.dumps({"sentinelle": "GSIE-PROMPT-0033", "origine": "test synthétique"}),
        date=_DATE,
    )
    _requete(
        url,
        "INSERT INTO gsie_rgpd_identites.user_account "
        "(id, display_name, created_at, updated_at) VALUES (:id, :nom, :date, :date)",
        id=_SUBMITTER_ID,
        nom="Sentinelle synthétique de réconciliation",
        date=_DATE,
    )
    for numero, statut in enumerate(("quarantined", "accepted", "rejected"), start=10):
        _requete(
            url,
            """
            INSERT INTO field_intake (
                id, created_at, updated_at, submitted_by, application_key, client_event_id,
                kind, observed_at, received_at, status, payload, provenance, payload_hash,
                target_resource_id, review_notes, reviewed_by, reviewed_at
            ) VALUES (
                :id, :date, :date, :submitted_by, 'reconciliation-test', :event,
                'observation', :date, :date, :status, CAST(:payload AS jsonb),
                CAST(:provenance AS jsonb), :hash, :target, :notes, :reviewer, :reviewed_at
            )
            """,
            id=UUID(f"00000000-0000-4000-8000-{numero:012d}"),
            date=_DATE,
            submitted_by=_SUBMITTER_ID,
            event=f"sentinelle-{statut}",
            status=statut,
            payload=json.dumps(
                {"texte": "Forêt d’essai", "statut": statut, "mesures": [0, 5.25, None]}
            ),
            provenance=json.dumps(
                {"source": "GSIE-PROMPT-0033", "version": "v1", "trace": {"brute": True}}
            ),
            hash=str(numero % 10) * 64,
            target=None if statut == "quarantined" else _RESOURCE_ID,
            notes=None if statut == "quarantined" else f"Revue synthétique : {statut}",
            reviewer=None if statut == "quarantined" else _REVIEWER_ID,
            reviewed_at=None if statut == "quarantined" else _DATE,
        )

    if not bff:
        return _TABLES_SENTINELLES

    _requete(
        url,
        """
        INSERT INTO gsie_rgpd_identites.geosylva_analysis_job (
            id, account_id, request_id, request_fingerprint, station_id, status,
            request_payload, trace_id, next_attempt_at, expires_at, created_at, updated_at
        ) VALUES (
            :id, :account, :request, :hash, :station, 'pending',
            CAST(:payload AS jsonb), 'trace-reconciliation', :date, :date, :date, :date
        )
        """,
        id=UUID("00000000-0000-4000-8000-000000000020"),
        account=_SUBMITTER_ID,
        request=UUID("00000000-0000-4000-8000-000000000021"),
        hash="a" * 64,
        station=_RESOURCE_ID,
        payload=json.dumps({"sentinelle": "job GeoSylva"}),
        date=_DATE,
    )
    _requete(
        url,
        """
        INSERT INTO gsie_rgpd_identites.geosylva_cubage_session (
            session_id, account_id, calculation_id, idempotency_key,
            session_fingerprint, measurements_fingerprint, inputs_fingerprint,
            result_fingerprint, request_fingerprint, request_payload, trace_id,
            created_at, updated_at
        ) VALUES (
            :id, :account, :calculation, :key, :hash, :hash, :hash,
            :hash, :hash, CAST(:payload AS jsonb), 'trace-reconciliation', :date, :date
        )
        """,
        id=UUID("00000000-0000-4000-8000-000000000022"),
        account=_SUBMITTER_ID,
        calculation=UUID("00000000-0000-4000-8000-000000000023"),
        key="00000000-0000-4000-8000-000000000024",
        hash="b" * 64,
        payload=json.dumps({"sentinelle": "session de cubage GeoSylva"}),
        date=_DATE,
    )
    return (*_TABLES_SENTINELLES, *_TABLES_BFF)


def _capturer(
    url: str,
    tables: tuple[str, ...],
    *,
    table_intake: str = "field_intake",
) -> dict[str, Any]:
    donnees = {}
    for table in tables:
        nom = table_intake if table == "field_intake" else table
        valeur = _requete(
            url,
            "SELECT COALESCE(jsonb_agg(ligne ORDER BY ligne::text), '[]'::jsonb)::text "
            f"FROM (SELECT to_jsonb(t) AS ligne FROM {nom} t) AS lignes",
        )
        donnees[table] = json.loads(valeur[0])
    return donnees


def _verifier_contraintes_reelles(url: str) -> None:
    """Une erreur refusée ne doit ni altérer la sentinelle ni empêcher la reprise."""
    projection = (
        "id, submitted_by, application_key, client_event_id, kind, observed_at, "
        "status, payload, provenance, payload_hash"
    )
    selection = (
        "gen_random_uuid(), submitted_by, application_key, client_event_id, kind, "
        "observed_at, status, payload, provenance, payload_hash"
    )
    with pytest.raises(IntegrityError, match="uq_field_intake_application_event"):
        _requete(
            url,
            f"INSERT INTO field_intake ({projection}) SELECT {selection} "
            "FROM field_intake LIMIT 1",
        )
    with pytest.raises(IntegrityError, match="ck_field_intake_status"):
        _requete(
            url,
            f"INSERT INTO field_intake ({projection}) "
            "SELECT gen_random_uuid(), submitted_by, application_key, "
            "client_event_id || '-statut', kind, observed_at, "
            "'invente', payload, provenance, payload_hash FROM field_intake LIMIT 1",
        )
    with pytest.raises(IntegrityError, match="field_intake_target_resource_id_fkey"):
        _requete(
            url,
            f"INSERT INTO field_intake ({projection}, target_resource_id) "
            "SELECT gen_random_uuid(), submitted_by, application_key, "
            "client_event_id || '-cible', kind, observed_at, "
            "status, payload, provenance, payload_hash, gen_random_uuid() "
            "FROM field_intake LIMIT 1",
        )
    assert _requete(url, "SELECT 1") == [1]


@pytest.mark.parametrize(
    ("lignee", "revision"),
    [("feat", _FEAT_0051), ("main", _MAIN_0051), ("feat", _FEAT_0059)],
    ids=["feat-0051", "main-0051", "feat-0059"],
)
def should_preserve_complete_historical_rows_when_upgrading_to_the_reconciled_head(
    base_reconciliation: str,
    tmp_path: Path,
    lignee: str,
    revision: str,
) -> None:
    url = base_reconciliation
    historique = _configuration_historique(tmp_path, lignee)
    command.upgrade(historique, revision)
    assert _versions(url) == [revision]
    tables = _inserer_sentinelles(url, bff=revision == _FEAT_0059)
    avant = _capturer(url, tables)
    catalogue = _catalogue(url)

    command.upgrade(_configuration_courante(), "head")

    assert _versions(url) == [_HEAD]
    assert _capturer(url, tables) == avant
    assert _catalogue(url) == catalogue
    _verifier_contrat(url)
    _verifier_contraintes_reelles(url)
    assert _capturer(url, tables) == avant

    command.upgrade(_configuration_courante(), "head")

    assert _versions(url) == [_HEAD]
    assert _capturer(url, tables) == avant
    assert _catalogue(url) == catalogue


def should_preserve_rows_and_relation_oids_when_replaying_compatibility_boundaries(
    base_reconciliation: str,
    tmp_path: Path,
) -> None:
    url = base_reconciliation
    command.upgrade(_configuration_historique(tmp_path, "main"), _MAIN_0051)
    tables = _inserer_sentinelles(url)
    avant = _capturer(url, tables)
    catalogue = _catalogue(url)

    for sens, revision in (
        ("downgrade", _FEAT_0051),
        ("upgrade", _MAIN_0051),
        ("upgrade", "head"),
        ("downgrade", _FEAT_0059),
        ("upgrade", "head"),
    ):
        getattr(command, sens)(_configuration_courante(), revision)
        assert _versions(url) == [_HEAD if revision == "head" else revision]
        assert _capturer(url, tables) == avant
        assert _catalogue(url) == catalogue


def should_complete_a_fresh_upgrade_downgrade_and_reupgrade_without_stamping(
    base_reconciliation: str,
) -> None:
    url = base_reconciliation
    command.upgrade(_configuration_courante(), "head")
    assert _versions(url) == [_HEAD]
    _verifier_contrat(url)

    # Ce seul scénario vide peut franchir la frontière destructive 0050.
    command.downgrade(_configuration_courante(), "base")
    assert _versions(url) == []
    assert _requete(url, "SELECT to_regclass('public.field_intake')") == [None]
    assert not any(table.endswith(".field_intake") for table in _tables(url))
    assert {"postgis", "age"} <= set(_requete(url, "SELECT extname FROM pg_extension"))
    assert _requete(
        url,
        "SELECT count(*) FROM ag_catalog.ag_graph WHERE name = 'gsie_knowledge_graph'",
    ) == [0]

    command.upgrade(_configuration_courante(), "head")
    assert _versions(url) == [_HEAD]
    _verifier_contrat(url)


@dataclass(frozen=True)
class _Derive:
    identifiant: str
    appliquer: tuple[str, ...]
    restaurer: tuple[str, ...]
    table_donnees: str = "field_intake"


_FK = "field_intake_target_resource_id_fkey"
_UQ = "uq_field_intake_application_event"
_CK = "ck_field_intake_status"
_STATUTS = "'quarantined', 'accepted', 'rejected'"


def _derive_contrainte(
    identifiant: str, nom: str, definition: str, originale: str
) -> _Derive:
    suppression = f"ALTER TABLE field_intake DROP CONSTRAINT {nom}"
    return _Derive(
        identifiant,
        (suppression, f"ALTER TABLE field_intake ADD CONSTRAINT {nom} {definition}"),
        (suppression, f"ALTER TABLE field_intake ADD CONSTRAINT {nom} {originale}"),
    )


def _derive_index(identifiant: str, definition: str) -> _Derive:
    nom = "ix_field_intake_submitted_by_received"
    return _Derive(
        identifiant,
        (f"DROP INDEX {nom}", f"CREATE {definition}"),
        (f"DROP INDEX {nom}", f"CREATE INDEX {nom} ON field_intake (submitted_by, received_at)"),
    )


_DERIVES = (
    _Derive(
        "colonne-renommee",
        ("ALTER TABLE field_intake RENAME COLUMN review_notes TO review_notes_conservees",),
        ("ALTER TABLE field_intake RENAME COLUMN review_notes_conservees TO review_notes",),
    ),
    _Derive(
        "colonne-inconnue",
        ("ALTER TABLE field_intake ADD COLUMN champ_inconnu text",),
        ("ALTER TABLE field_intake DROP COLUMN champ_inconnu",),
    ),
    _Derive(
        "type-et-longueur",
        ("ALTER TABLE field_intake ALTER COLUMN payload_hash TYPE varchar(65)",),
        ("ALTER TABLE field_intake ALTER COLUMN payload_hash TYPE varchar(64)",),
    ),
    _Derive(
        "type-json",
        ("ALTER TABLE field_intake ALTER COLUMN payload TYPE json USING payload::json",),
        ("ALTER TABLE field_intake ALTER COLUMN payload TYPE jsonb USING payload::jsonb",),
    ),
    _Derive(
        "nullabilite",
        ("ALTER TABLE field_intake ALTER COLUMN payload_hash DROP NOT NULL",),
        ("ALTER TABLE field_intake ALTER COLUMN payload_hash SET NOT NULL",),
    ),
    _Derive(
        "defaut-manquant",
        ("ALTER TABLE field_intake ALTER COLUMN received_at DROP DEFAULT",),
        ("ALTER TABLE field_intake ALTER COLUMN received_at SET DEFAULT now()",),
    ),
    _Derive(
        "defaut-different",
        ("ALTER TABLE field_intake ALTER COLUMN received_at SET DEFAULT clock_timestamp()",),
        ("ALTER TABLE field_intake ALTER COLUMN received_at SET DEFAULT now()",),
    ),
    _derive_contrainte(
        "pk-colonnes", "field_intake_pkey", "PRIMARY KEY (id, kind)", "PRIMARY KEY (id)"
    ),
    _derive_contrainte(
        "pk-differee",
        "field_intake_pkey",
        "PRIMARY KEY (id) DEFERRABLE INITIALLY DEFERRED",
        "PRIMARY KEY (id)",
    ),
    _derive_contrainte(
        "fk-cible",
        _FK,
        "FOREIGN KEY (target_resource_id) "
        "REFERENCES gsie_rgpd_identites.user_account(id) NOT VALID",
        "FOREIGN KEY (target_resource_id) REFERENCES public.resource(id)",
    ),
    _derive_contrainte(
        "fk-suppression",
        _FK,
        "FOREIGN KEY (target_resource_id) REFERENCES public.resource(id) ON DELETE CASCADE",
        "FOREIGN KEY (target_resource_id) REFERENCES public.resource(id)",
    ),
    _derive_contrainte(
        "fk-mise-a-jour",
        _FK,
        "FOREIGN KEY (target_resource_id) REFERENCES public.resource(id) ON UPDATE CASCADE",
        "FOREIGN KEY (target_resource_id) REFERENCES public.resource(id)",
    ),
    _derive_contrainte(
        "fk-differee",
        _FK,
        "FOREIGN KEY (target_resource_id) REFERENCES public.resource(id) "
        "DEFERRABLE INITIALLY DEFERRED",
        "FOREIGN KEY (target_resource_id) REFERENCES public.resource(id)",
    ),
    _derive_contrainte(
        "fk-non-validee",
        _FK,
        "FOREIGN KEY (target_resource_id) REFERENCES public.resource(id) NOT VALID",
        "FOREIGN KEY (target_resource_id) REFERENCES public.resource(id)",
    ),
    _derive_contrainte(
        "unicite-ordre",
        _UQ,
        "UNIQUE (client_event_id, application_key)",
        "UNIQUE (application_key, client_event_id)",
    ),
    _derive_contrainte(
        "unicite-differee",
        _UQ,
        "UNIQUE (application_key, client_event_id) DEFERRABLE INITIALLY DEFERRED",
        "UNIQUE (application_key, client_event_id)",
    ),
    _derive_contrainte(
        "check-statuts",
        _CK,
        f"CHECK (status IN ({_STATUTS}, 'invente'))",
        f"CHECK (status IN ({_STATUTS}))",
    ),
    _derive_contrainte(
        "check-non-valide",
        _CK,
        f"CHECK (status IN ({_STATUTS})) NOT VALID",
        f"CHECK (status IN ({_STATUTS}))",
    ),
    _derive_index(
        "index-ordre",
        "INDEX ix_field_intake_submitted_by_received ON field_intake (received_at, submitted_by)",
    ),
    _derive_index(
        "index-colonne",
        "INDEX ix_field_intake_submitted_by_received ON field_intake (reviewed_by, received_at)",
    ),
    _derive_index(
        "index-unique",
        "UNIQUE INDEX ix_field_intake_submitted_by_received ON field_intake (submitted_by, status)",
    ),
    _derive_index(
        "index-partiel",
        "INDEX ix_field_intake_submitted_by_received ON field_intake "
        "(submitted_by, received_at) WHERE status = 'accepted'",
    ),
    _derive_index(
        "index-descendant",
        "INDEX ix_field_intake_submitted_by_received ON field_intake "
        "(submitted_by, received_at DESC)",
    ),
    _derive_index(
        "index-inclusion",
        "INDEX ix_field_intake_submitted_by_received ON field_intake "
        "(submitted_by, received_at) INCLUDE (kind)",
    ),
    _Derive(
        "table-manquante",
        ("ALTER TABLE field_intake RENAME TO field_intake_conserve",),
        ("ALTER TABLE field_intake_conserve RENAME TO field_intake",),
        table_donnees="field_intake_conserve",
    ),
    _Derive(
        "vue",
        (
            "ALTER TABLE field_intake RENAME TO field_intake_conserve",
            "CREATE VIEW field_intake AS SELECT * FROM field_intake_conserve",
        ),
        ("DROP VIEW field_intake", "ALTER TABLE field_intake_conserve RENAME TO field_intake"),
        table_donnees="field_intake_conserve",
    ),
    _Derive(
        "rls",
        ("ALTER TABLE field_intake ENABLE ROW LEVEL SECURITY",),
        ("ALTER TABLE field_intake DISABLE ROW LEVEL SECURITY",),
    ),
    _Derive(
        "policy",
        ("CREATE POLICY reconciliation_lecture ON field_intake USING (true)",),
        ("DROP POLICY reconciliation_lecture ON field_intake",),
    ),
    _Derive(
        "heritage",
        ("CREATE TABLE intake_derivee () INHERITS (field_intake)",),
        ("DROP TABLE intake_derivee",),
    ),
)


@pytest.fixture(
    scope="module",
    params=[
        ("feat", _FEAT_0051, _MAIN_0051),
        ("main", _MAIN_0051, "head"),
        ("feat", _FEAT_0059, "head"),
    ],
    ids=["alias-feat-0051", "tete-main-0051", "tete-feat-0059"],
)
def base_historique_pour_derives(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[tuple[str, str, str, tuple[str, ...]], None, None]:
    lignee, revision, cible = request.param
    with _postgres_jetable() as url:
        repertoire = tmp_path_factory.mktemp(f"reconciliation-{revision}")
        command.upgrade(_configuration_historique(repertoire, lignee), revision)
        tables = _inserer_sentinelles(url, bff=revision == _FEAT_0059)
        assert _versions(url) == [revision]
        yield url, revision, cible, tables


@pytest.mark.parametrize("derive", _DERIVES, ids=lambda derive: derive.identifiant)
def should_refuse_schema_drift_without_modifying_versions_or_data_and_allow_recovery(
    base_historique_pour_derives: tuple[str, str, str, tuple[str, ...]],
    derive: _Derive,
) -> None:
    url, revision, cible, tables = base_historique_pour_derives
    donnees_initiales = _capturer(url, tables)
    _executer(url, *derive.appliquer)
    avant = _capturer(url, tables, table_intake=derive.table_donnees)
    catalogue = _catalogue(url)
    tables_avant = _tables(url)
    try:
        with pytest.raises(RuntimeError, match=r"public\.field_intake"):
            command.upgrade(_configuration_courante(), cible)

        assert _versions(url) == [revision], derive.identifiant
        assert _capturer(url, tables, table_intake=derive.table_donnees) == avant
        assert _catalogue(url) == catalogue
        assert _tables(url) == tables_avant
    finally:
        _executer(url, *derive.restaurer)
        # Une éventuelle absence de refus reste un échec ; ce retour Alembic
        # explicite permet seulement aux autres cas de conserver leur isolation.
        if _versions(url) != [revision]:
            command.downgrade(_configuration_courante(), revision)
        assert _capturer(url, tables) == donnees_initiales
        _verifier_contrat(url)


@pytest.mark.parametrize(
    ("lignee", "revision", "cible"),
    [
        ("feat", _FEAT_0051, _MAIN_0051),
        ("main", _MAIN_0051, "head"),
        ("feat", _FEAT_0059, "head"),
    ],
    ids=["alias-feat-0051", "tete-main-0051", "tete-feat-0059"],
)
def should_resume_the_real_upgrade_after_a_rejected_schema_has_been_restored(
    base_reconciliation: str,
    tmp_path: Path,
    lignee: str,
    revision: str,
    cible: str,
) -> None:
    url = base_reconciliation
    command.upgrade(_configuration_historique(tmp_path, lignee), revision)
    tables = _inserer_sentinelles(url, bff=revision == _FEAT_0059)
    donnees = _capturer(url, tables)
    catalogue = _catalogue(url)
    tables_avant = _tables(url)
    _executer(
        url,
        "ALTER TABLE field_intake ALTER COLUMN received_at SET DEFAULT clock_timestamp()",
    )

    with pytest.raises(RuntimeError, match=r"public\.field_intake.*received_at"):
        command.upgrade(_configuration_courante(), cible)

    assert _versions(url) == [revision]
    assert _capturer(url, tables) == donnees
    assert _tables(url) == tables_avant
    _executer(url, "ALTER TABLE field_intake ALTER COLUMN received_at SET DEFAULT now()")

    command.upgrade(_configuration_courante(), "head")

    assert _versions(url) == [_HEAD]
    assert _capturer(url, tables) == donnees
    assert _catalogue(url) == catalogue
    _verifier_contrat(url)


