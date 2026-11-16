"""Contrat PostgreSQL de la lignée unique d'intake (GSIE-PROMPT-0034).

La compatibilité B/0060 a été retirée par décision explicite. Les garanties
conservées portent sur le schéma canonique, les données, les migrations,
la restauration et l'exécution sûre du SQL hors ligne de 0027.
"""

from __future__ import annotations

import asyncio
import json
from contextlib import contextmanager
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import Generator

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from gsie_api.core.config import get_settings
from tests.conftest import requires_docker
from tests.integration.test_migration_baseline import (
    _IMAGE_DB,
    _REQUIRE_IMAGE,
    _image_disponible,
    _nettoyer_extensions_preinstallees,
    _verifier_schema_courant,
)

pytestmark = requires_docker

_RACINE_API = Path(__file__).resolve().parents[2]
_INTAKE = "20260823_0051"
_HEAD = "20260929_0059"
_DATE = datetime(2026, 8, 15, 12, 34, 56, 123456, tzinfo=UTC)
_RESOURCE_ID = UUID("00000000-0000-4000-8000-000000000001")
_SUBMITTER_ID = UUID("00000000-0000-4000-8000-000000000002")
_REVIEWER_ID = UUID("00000000-0000-4000-8000-000000000003")
_TABLES_SENTINELLES = ("resource", "gsie_rgpd_identites.user_account", "field_intake")
_TABLES_BFF = (
    "gsie_rgpd_identites.geosylva_analysis_job",
    "gsie_rgpd_identites.geosylva_cubage_session",
)


def _configuration_courante() -> Config:
    configuration = Config(str(_RACINE_API / "alembic.ini"))
    configuration.set_main_option("script_location", str(_RACINE_API / "alembic"))
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
    """Lit la structure effective ; les OID permettent de repérer une recréation."""
    ligne = _requete(
        url,
        """
        SELECT jsonb_build_object(
            'relation', (
                SELECT jsonb_build_object(
                    'oid', c.oid, 'kind', c.relkind, 'persistence', c.relpersistence,
                    'partition', c.relispartition,
                    'rls', c.relrowsecurity, 'force_rls', c.relforcerowsecurity
                )
                FROM pg_catalog.pg_class c
                WHERE c.oid = pg_catalog.to_regclass('public.field_intake')
            ),
            'colonnes', (
                SELECT jsonb_object_agg(a.attname, jsonb_build_object(
                    'type', pg_catalog.format_type(a.atttypid, a.atttypmod),
                    'nullable', NOT a.attnotnull,
                    'default', pg_catalog.pg_get_expr(d.adbin, d.adrelid),
                    'identity', a.attidentity, 'generated', a.attgenerated,
                    'default_collation', a.attcollation = t.typcollation
                ))
                FROM pg_catalog.pg_attribute a
                JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
                LEFT JOIN pg_catalog.pg_attrdef d
                  ON d.adrelid = a.attrelid AND d.adnum = a.attnum
                WHERE a.attrelid = pg_catalog.to_regclass('public.field_intake')
                  AND a.attnum > 0 AND NOT a.attisdropped
            ),
            'contraintes', (
                SELECT jsonb_object_agg(c.conname, jsonb_build_object(
                    'definition', pg_catalog.pg_get_constraintdef(c.oid),
                    'type', c.contype, 'validated', c.convalidated,
                    'deferrable', c.condeferrable, 'deferred', c.condeferred,
                    'no_inherit', c.connoinherit,
                    'local', c.conislocal, 'inherit_count', c.coninhcount,
                    'colonnes', ARRAY(
                        SELECT a.attname
                        FROM pg_catalog.unnest(c.conkey) WITH ORDINALITY AS k(attnum, position)
                        JOIN pg_catalog.pg_attribute a
                          ON a.attrelid = c.conrelid AND a.attnum = k.attnum
                        ORDER BY k.position
                    ),
                    'schema_reference', n.nspname, 'table_reference', r.relname,
                    'colonnes_reference', ARRAY(
                        SELECT a.attname
                        FROM pg_catalog.unnest(c.confkey) WITH ORDINALITY AS k(attnum, position)
                        JOIN pg_catalog.pg_attribute a
                          ON a.attrelid = c.confrelid AND a.attnum = k.attnum
                        ORDER BY k.position
                    ),
                    'update_action', c.confupdtype, 'delete_action', c.confdeltype,
                    'match_type', c.confmatchtype
                ))
                FROM pg_catalog.pg_constraint c
                LEFT JOIN pg_catalog.pg_class r ON r.oid = c.confrelid
                LEFT JOIN pg_catalog.pg_namespace n ON n.oid = r.relnamespace
                WHERE c.conrelid = pg_catalog.to_regclass('public.field_intake')
            ),
            'index', (
                SELECT jsonb_object_agg(c.relname, jsonb_build_object(
                    'oid', i.indexrelid, 'definition', pg_catalog.pg_get_indexdef(i.indexrelid),
                    'unique', i.indisunique, 'primary', i.indisprimary, 'method', am.amname,
                    'valid', i.indisvalid, 'ready', i.indisready, 'live', i.indislive,
                    'immediate', i.indimmediate, 'exclusion', i.indisexclusion,
                    'nulls_not_distinct', i.indnullsnotdistinct,
                    'attributes', i.indnatts, 'keys', i.indnkeyatts,
                    'no_expression', i.indexprs IS NULL, 'no_predicate', i.indpred IS NULL,
                    'key_options', i.indoption::smallint[], 'options', c.reloptions,
                    'colonnes', ARRAY(
                        SELECT a.attname
                        FROM pg_catalog.unnest(i.indkey) WITH ORDINALITY AS k(attnum, position)
                        JOIN pg_catalog.pg_attribute a
                          ON a.attrelid = i.indrelid AND a.attnum = k.attnum
                        ORDER BY k.position
                    ),
                    'default_opclasses', ARRAY(
                        SELECT opc.opcdefault AND n.nspname = 'pg_catalog'
                        FROM pg_catalog.unnest(i.indclass) WITH ORDINALITY AS k(oid, position)
                        JOIN pg_catalog.pg_opclass opc ON opc.oid = k.oid
                        JOIN pg_catalog.pg_namespace n ON n.oid = opc.opcnamespace
                        ORDER BY k.position
                    ),
                    'default_collations', ARRAY(
                        SELECT k.collation_oid = a.attcollation
                        FROM ROWS FROM (
                            pg_catalog.unnest(i.indkey::smallint[]),
                            pg_catalog.unnest(i.indcollation::oid[])
                        ) WITH ORDINALITY AS k(attnum, collation_oid, position)
                        JOIN pg_catalog.pg_attribute a
                          ON a.attrelid = i.indrelid AND a.attnum = k.attnum
                        ORDER BY k.position
                    )
                ))
                FROM pg_catalog.pg_index i
                JOIN pg_catalog.pg_class c ON c.oid = i.indexrelid
                JOIN pg_catalog.pg_am am ON am.oid = c.relam
                WHERE i.indrelid = pg_catalog.to_regclass('public.field_intake')
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
    assert all(
        not colonne["identity"] and not colonne["generated"] and colonne["default_collation"]
        for colonne in catalogue["colonnes"].values()
    )
    relation = catalogue["relation"]
    assert relation["kind"] == "r"
    assert relation["persistence"] == "p"
    assert relation["partition"] is False
    assert relation["rls"] is False
    assert relation["force_rls"] is False
    contraintes = {
        "field_intake_pkey": ("p", ["id"]),
        "field_intake_target_resource_id_fkey": ("f", ["target_resource_id"]),
        "uq_field_intake_application_event": ("u", ["application_key", "client_event_id"]),
        "ck_field_intake_status": ("c", ["status"]),
    }
    assert set(catalogue["contraintes"]) == set(contraintes)
    for nom, (type_, cles) in contraintes.items():
        contrainte = catalogue["contraintes"][nom]
        assert (contrainte["type"], contrainte["colonnes"]) == (type_, cles), nom
        assert contrainte["validated"] is True, nom
        assert contrainte["deferrable"] is False, nom
        assert contrainte["deferred"] is False, nom
        assert contrainte["no_inherit"] is (type_ != "c"), nom
        assert contrainte["local"] is True and contrainte["inherit_count"] == 0, nom
    fk = catalogue["contraintes"]["field_intake_target_resource_id_fkey"]
    assert (fk["schema_reference"], fk["table_reference"], fk["colonnes_reference"]) == (
        "public",
        "resource",
        ["id"],
    )
    assert (fk["update_action"], fk["delete_action"], fk["match_type"]) == ("a", "a", "s")
    index_attendus = {
        "field_intake_pkey": ["id"],
        "uq_field_intake_application_event": ["application_key", "client_event_id"],
        "ix_field_intake_submitted_by": ["submitted_by"],
        "ix_field_intake_target_resource_id": ["target_resource_id"],
        "ix_field_intake_submitted_by_received": ["submitted_by", "received_at"],
        "ix_field_intake_status_received": ["status", "received_at"],
    }
    assert set(catalogue["index"]) == set(index_attendus)
    for nom, cles in index_attendus.items():
        index = catalogue["index"][nom]
        assert index["colonnes"] == cles, nom
        assert index["unique"] is (
            nom in {"field_intake_pkey", "uq_field_intake_application_event"}
        )
        assert index["primary"] is (nom == "field_intake_pkey"), nom
        assert index["method"] == "btree", nom
        assert all(index[cle] for cle in ("valid", "ready", "live", "immediate")), nom
        assert index["exclusion"] is False and index["nulls_not_distinct"] is False, nom
        assert index["attributes"] == index["keys"] == len(cles), nom
        assert index["no_expression"] is True and index["no_predicate"] is True, nom
        assert index["key_options"] == [0] * len(cles), nom
        assert index["default_opclasses"] == [True] * len(cles), nom
        assert index["default_collations"] == [True] * len(cles), nom
        assert index["options"] is None, nom


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


def _commande_sauvegarde(conteneur: Any, arguments: list[str]) -> bytes:
    """Exige le succès effectif du binaire PostgreSQL, sans tolérer d'erreur."""
    resultat = conteneur.exec_run(arguments, demux=True)
    sortie, erreur = resultat.output
    assert resultat.exit_code == 0, (
        f"Échec de {arguments[0]} : " f"{(erreur or b'').decode('utf-8', errors='replace')}"
    )
    return sortie or b""


def _ordre_physique_intake(url: str) -> list[str]:
    return _requete(
        url,
        "SELECT attname FROM pg_catalog.pg_attribute "
        "WHERE attrelid = 'public.field_intake'::pg_catalog.regclass "
        "AND attnum > 0 AND NOT attisdropped ORDER BY attnum",
    )


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


@pytest.mark.parametrize("revision", [_INTAKE, _HEAD], ids=["creation-A", "tete-0059"])
def should_preserve_complete_rows_and_intake_oids_when_upgrading_to_head(
    base_reconciliation: str, revision: str
) -> None:
    url = base_reconciliation
    command.upgrade(_configuration_courante(), revision)
    assert _versions(url) == [revision]
    tables = _inserer_sentinelles(url, bff=revision == _HEAD)
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


def should_preserve_intake_rows_when_rolling_back_to_creation_and_reupgrading(
    base_reconciliation: str,
) -> None:
    url = base_reconciliation
    command.upgrade(_configuration_courante(), _INTAKE)
    tables = _inserer_sentinelles(url)
    avant = _capturer(url, tables)
    catalogue = _catalogue(url)

    for direction, revision in (("upgrade", "head"), ("downgrade", _INTAKE), ("upgrade", "head")):
        getattr(command, direction)(_configuration_courante(), revision)
        assert _versions(url) == [_HEAD if revision == "head" else revision]
        assert _capturer(url, tables) == avant
        assert _catalogue(url) == catalogue
        _verifier_contrat(url)


def should_create_drop_and_recreate_empty_intake_without_losing_existing_resources(
    base_reconciliation: str,
) -> None:
    url = base_reconciliation
    command.upgrade(_configuration_courante(), "20260815_0050")
    _requete(
        url,
        "INSERT INTO resource (id, type, metadata_json) "
        "VALUES (:id, 'place', CAST(:metadata AS jsonb))",
        id=_RESOURCE_ID,
        metadata=json.dumps({"synthetique": True, "objet": "cycle de création intake"}),
    )
    ressource = _capturer(url, ("resource",))
    assert _requete(url, "SELECT to_regclass('public.field_intake')") == [None]

    command.upgrade(_configuration_courante(), _INTAKE)
    assert _versions(url) == [_INTAKE]
    _verifier_contrat(url)
    assert _requete(url, "SELECT count(*) FROM field_intake") == [0]

    # Le retrait explicite de la table est testé uniquement lorsqu'elle est vide.
    command.downgrade(_configuration_courante(), "20260815_0050")
    assert _versions(url) == ["20260815_0050"]
    assert _requete(url, "SELECT to_regclass('public.field_intake')") == [None]
    assert _capturer(url, ("resource",)) == ressource

    command.upgrade(_configuration_courante(), _INTAKE)
    assert _versions(url) == [_INTAKE]
    _verifier_contrat(url)
    assert _requete(url, "SELECT count(*) FROM field_intake") == [0]
    assert _capturer(url, ("resource",)) == ressource


def _sql_hors_ligne(direction: str, intervalle: str) -> str:
    buffer = StringIO()
    configuration = _configuration_courante()
    configuration.output_buffer = buffer
    getattr(command, direction)(configuration, intervalle, sql=True)
    return buffer.getvalue()


def _executer_sql_hors_ligne(url: str, sql: str) -> None:
    """Exécute tout le script généré, y compris ses bornes transactionnelles."""

    async def executer() -> None:
        dsn = make_url(url).set(drivername="postgresql").render_as_string(hide_password=False)
        connexion = await asyncpg.connect(dsn)
        try:
            await connexion.execute(sql)
        finally:
            if connexion.is_in_transaction():
                await connexion.execute("ROLLBACK")
            await connexion.close()

    asyncio.run(executer())


def should_execute_the_complete_offline_upgrade_downgrade_and_reupgrade(
    base_reconciliation: str,
    tmp_path: Path,
) -> None:
    url = base_reconciliation
    upgrade = _sql_hors_ligne("upgrade", "base:head")
    downgrade = _sql_hors_ligne("downgrade", "head:base")
    (tmp_path / "base-vers-head.sql").write_text(upgrade, encoding="utf-8")
    (tmp_path / "head-vers-base.sql").write_text(downgrade, encoding="utf-8")

    _executer_sql_hors_ligne(url, upgrade)
    assert _versions(url) == [_HEAD]
    _verifier_contrat(url)
    _verifier_schema_courant(url)

    _executer_sql_hors_ligne(url, downgrade)
    assert _requete(url, "SELECT to_regclass('public.field_intake')") == [None]
    assert _requete(url, "SELECT to_regclass('public.alembic_version')") == [None]
    assert _tables(url) == ["public.spatial_ref_sys"]
    assert {"postgis", "age"} <= set(_requete(url, "SELECT extname FROM pg_extension"))

    _executer_sql_hors_ligne(url, upgrade)
    assert _versions(url) == [_HEAD]
    _verifier_contrat(url)
    _verifier_schema_courant(url)


def _inserer_doublons_alias(url: str) -> None:
    _requete(
        url,
        "INSERT INTO resource (id, type, metadata_json) "
        "VALUES (:id, 'entity', CAST(:metadata AS jsonb))",
        id=_RESOURCE_ID,
        metadata=json.dumps({"synthetique": True, "objet": "garde de migration 0027"}),
    )
    _requete(url, "INSERT INTO entity (id, entity_subtype) VALUES (:id, 'test')", id=_RESOURCE_ID)
    for numero in range(7):
        _requete(
            url,
            """
            WITH ressources_alias AS (
                INSERT INTO resource (id, type, metadata_json)
                SELECT gen_random_uuid(), 'entity_alias', '{"synthetique": true}'::jsonb
                FROM pg_catalog.generate_series(1, :occurrences)
                RETURNING id
            )
            INSERT INTO entity_alias (id, entity_id, namespace, external_id)
            SELECT id, :entite, 'qa-0034', :externe FROM ressources_alias
            """,
            occurrences=numero + 2,
            entite=_RESOURCE_ID,
            externe=f"doublon-{numero}",
        )


@pytest.mark.parametrize("mode", ["en-ligne", "hors-ligne"])
def should_reject_real_duplicate_aliases_and_allow_upgrade_after_explicit_test_data_repair(
    base_reconciliation: str,
    tmp_path: Path,
    mode: str,
) -> None:
    url = base_reconciliation
    command.upgrade(_configuration_courante(), "20260801_0026")
    _inserer_doublons_alias(url)
    tables = ("resource", "entity", "entity_alias")
    avant = _capturer(url, tables)
    tables_avant = _tables(url)
    sql = _sql_hors_ligne("upgrade", "20260801_0026:20260801_0027")
    (tmp_path / f"0027-{mode}.sql").write_text(sql, encoding="utf-8")

    if mode == "hors-ligne":
        with pytest.raises(
            asyncpg.exceptions.RaiseError, match="entity_alias porte 7 paire"
        ) as error:
            _executer_sql_hors_ligne(url, sql)
        assert error.value.sqlstate == "P0001"
        message = str(error.value)
    else:
        with pytest.raises(RuntimeError, match="entity_alias porte 7 paire") as error:
            command.upgrade(_configuration_courante(), "20260801_0027")
        message = str(error.value)

    assert "idx_entity_alias_ns_extid" in message
    assert "Dedoublonnez avant de rejouer" in message
    assert "qa-0034/doublon-0" not in message
    assert "qa-0034/doublon-1" not in message
    for numero in range(2, 7):
        assert f"qa-0034/doublon-{numero} ×{numero + 2}" in message
    assert _versions(url) == ["20260801_0026"]
    assert _capturer(url, tables) == avant
    assert _tables(url) == tables_avant
    assert _requete(url, "SELECT to_regclass('public.idx_entity_alias_ns_extid')") == [None]

    # Réparation explicite des seules données synthétiques par le test ;
    # la migration ne déduplique et ne supprime jamais de ligne elle-même.
    _requete(url, "UPDATE entity_alias SET external_id = external_id || ':' || id::text")
    reparees = _capturer(url, tables)
    assert len(reparees["entity_alias"]) == len(avant["entity_alias"]) == 35
    assert reparees["resource"] == avant["resource"]
    assert reparees["entity"] == avant["entity"]

    if mode == "hors-ligne":
        _executer_sql_hors_ligne(url, sql)
    else:
        command.upgrade(_configuration_courante(), "20260801_0027")

    assert _versions(url) == ["20260801_0027"]
    assert _capturer(url, tables) == reparees
    assert _requete(url, "SELECT to_regclass('public.idx_entity_alias_ns_extid')") == [
        "idx_entity_alias_ns_extid"
    ]
    with pytest.raises(IntegrityError, match="idx_entity_alias_ns_extid"):
        _requete(
            url,
            """
            UPDATE entity_alias SET external_id = (
                SELECT external_id FROM entity_alias ORDER BY id LIMIT 1
            ) WHERE id = (SELECT id FROM entity_alias ORDER BY id OFFSET 1 LIMIT 1)
            """,
        )
    assert _capturer(url, tables) == reparees


@pytest.mark.parametrize("revision", [_INTAKE, _HEAD], ids=["creation-A", "tete-0059"])
def should_restore_intake_backups_and_preserve_all_values_when_upgrading_to_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    revision: str,
) -> None:
    """Deux bases neuves du même cluster jetable ; les rôles restent partagés."""
    from testcontainers.postgres import PostgresContainer

    assert _image_disponible(_IMAGE_DB), f"Image de migration absente : {_IMAGE_DB}"
    base_source = "gsie_reconciliation_backup_source"
    base_restauree = "gsie_reconciliation_backup_restauree"
    chemin_dump = "/tmp/gsie_reconciliation_intake.dump"
    with PostgresContainer(
        image=_IMAGE_DB,
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname=base_source,
    ).with_command("postgres -c shared_preload_libraries=age -c search_path=public") as postgres:
        url_source = postgres.get_connection_url().replace(
            "postgresql+psycopg2", "postgresql+asyncpg"
        )
        url_restauree = (
            make_url(url_source).set(database=base_restauree).render_as_string(hide_password=False)
        )
        asyncio.run(_nettoyer_extensions_preinstallees(url_source))
        monkeypatch.setenv("GSIE_DATABASE_URL", url_source)
        monkeypatch.setenv("GSIE_MIGRATION_DATABASE_URL", url_source)
        monkeypatch.setenv("GSIE_DATABASE_ROLE", "test")
        monkeypatch.setenv("GSIE_DATA_NAMESPACE", "gsie-reconciliation-backup-test")
        get_settings.cache_clear()
        try:
            command.upgrade(_configuration_courante(), revision)
            assert _requete(url_source, "SELECT current_database()") == [base_source]
            assert _versions(url_source) == [revision]
            tables = _inserer_sentinelles(url_source, bff=revision == _HEAD)
            source = _capturer(url_source, tables)
            assert len(source["field_intake"]) == 3
            assert all(len(ligne) == 17 for ligne in source["field_intake"])
            acceptee = next(
                ligne for ligne in source["field_intake"] if ligne["status"] == "accepted"
            )
            assert all(valeur is not None for valeur in acceptee.values())
            ordre = _ordre_physique_intake(url_source)
            assert len(ordre) == 17
            _verifier_contrat(url_source)

            conteneur = postgres.get_wrapped_container()
            _commande_sauvegarde(
                conteneur,
                [
                    "pg_dump",
                    "--username",
                    "gsie",
                    "--dbname",
                    base_source,
                    "--format=custom",
                    "--file",
                    chemin_dump,
                ],
            )
            archive = _commande_sauvegarde(conteneur, ["cat", chemin_dump])
            assert archive.startswith(b"PGDMP")
            assert len(archive) > 5
            (tmp_path / f"intake-{revision}.dump").write_bytes(archive)
            manifeste = _commande_sauvegarde(conteneur, ["pg_restore", "--list", chemin_dump])
            assert b"TABLE DATA public field_intake " in manifeste
            _commande_sauvegarde(
                conteneur,
                ["createdb", "--username", "gsie", "--template", "template0", base_restauree],
            )
            _commande_sauvegarde(
                conteneur,
                [
                    "pg_restore",
                    "--username",
                    "gsie",
                    "--dbname",
                    base_restauree,
                    "--exit-on-error",
                    "--single-transaction",
                    chemin_dump,
                ],
            )

            assert _requete(url_restauree, "SELECT current_database()") == [base_restauree]
            assert _versions(url_restauree) == [revision]
            assert _capturer(url_restauree, tables) == source
            assert _ordre_physique_intake(url_restauree) == ordre
            _verifier_contrat(url_restauree)
            _verifier_contraintes_reelles(url_restauree)
            assert _capturer(url_restauree, tables) == source
            catalogue_restaure = _catalogue(url_restauree)
            monkeypatch.setenv("GSIE_DATABASE_URL", url_restauree)
            monkeypatch.setenv("GSIE_MIGRATION_DATABASE_URL", url_restauree)
            get_settings.cache_clear()

            command.upgrade(_configuration_courante(), "head")

            assert _versions(url_restauree) == [_HEAD]
            assert _capturer(url_restauree, tables) == source
            assert _ordre_physique_intake(url_restauree) == ordre
            assert _catalogue(url_restauree) == catalogue_restaure
            _verifier_contrat(url_restauree)
            _verifier_contraintes_reelles(url_restauree)
            assert _capturer(url_restauree, tables) == source
            assert _versions(url_source) == [revision]
            assert _capturer(url_source, tables) == source
        finally:
            get_settings.cache_clear()
