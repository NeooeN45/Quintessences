"""Garde-fous rapides autour de la nouvelle lignée Alembic."""

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

from gsie_api.infrastructure.knowledge_models import LegacyBase
from gsie_api.infrastructure.models import Base
from gsie_api.seeds.run_seeds import run_seeds

_BASELINE = "20260726_0001"
_HEAD = "20260823_0051"
_LEGACY_TABLES = frozenset(
    {
        "knowledge_mots_cles",
        "knowledge_domaines_validite",
        "knowledge_conflits",
        "knowledge_relations",
        "knowledge_history",
        "knowledge_objects",
        "ecosystem_groupes_ecologiques",
        "ecosystem_stations",
        "ecosystem_habitats",
        "botanical_essences",
        "botanical_genres",
        "botanical_familles",
    }
)


def test_baseline_est_la_base_unique_de_la_lignee() -> None:
    script = ScriptDirectory.from_config(Config("alembic.ini"))

    assert script.get_base() == _BASELINE
    assert script.get_revision(_BASELINE).down_revision is None


def test_lignee_lineaire_depuis_la_baseline() -> None:
    """Une seule tête, atteinte depuis la baseline sans embranchement.

    Les révisions postérieures s'empilent sur la baseline ; aucune ne la
    réécrit ni n'ouvre de branche parallèle.
    """
    script = ScriptDirectory.from_config(Config("alembic.ini"))

    assert list(script.get_heads()) == [_HEAD]
    revisions = [revision.revision for revision in script.walk_revisions()]
    # La lignée s'est allongée depuis l'introduction de ce garde-fou (RFC
    # audit sécurité/PostGIS du 2026-07-27) : on vérifie l'absence de
    # branche (une seule tête, un seul chemin jusqu'à la baseline) plutôt
    # qu'un nombre de révisions fige.
    assert revisions[0] == _HEAD
    assert revisions[-1] == _BASELINE
    assert len(revisions) == len(set(revisions))


def test_baseline_ne_depend_pas_des_modeles_applicatifs() -> None:
    source = Path("alembic/versions/20260726_0001_baseline_gsie_v6_2.py").read_text(
        encoding="utf-8"
    )

    assert "gsie_api.infrastructure.models" not in source
    assert "Base.metadata" not in source
    assert "create_all" not in source


def test_modeles_legacy_isoles_du_schema_courant() -> None:
    assert len(Base.metadata.tables) >= 130
    expected_new_tables = {
        "gsie_rgpd_identites.mfa_secret",
        "gsie_rgpd_identites.active_session",
        "gsie_organisations.organisation_invitation",
        "gsie_billing.plan",
        "gsie_billing.subscription",
        "gsie_billing.entitlement",
    }
    assert expected_new_tables <= set(Base.metadata.tables)
    assert frozenset(LegacyBase.metadata.tables) == _LEGACY_TABLES
    assert frozenset(Base.metadata.tables).isdisjoint(_LEGACY_TABLES)


def test_data_asset_accepte_les_assets_volumineux_et_refuse_les_tailles_negatives() -> None:
    """Le registre d'octets doit dépasser la limite d'un INTEGER PostgreSQL."""
    table = Base.metadata.tables["data_asset"]

    assert isinstance(table.c.size_bytes.type, sa.BigInteger)
    assert any(
        constraint.name == "ck_data_asset_size_non_negative" for constraint in table.constraints
    )


def test_migration_sync_force_rls_et_interdit_la_suppression_physique() -> None:
    source = Path("alembic/versions/20260803_0031_sync_parcelles_geosylva.py").read_text(
        encoding="utf-8"
    )

    assert "ENABLE ROW LEVEL SECURITY" in source
    assert "FORCE ROW LEVEL SECURITY" in source
    assert "CREATE POLICY geosylva_parcels_owner" in source
    assert "app.current_user_id" in source
    assert "GRANT SELECT, INSERT, UPDATE" in source
    assert "REVOKE DELETE" in source


@pytest.mark.asyncio
async def test_seed_legacy_refuse_toute_ecriture() -> None:
    with pytest.raises(RuntimeError, match="seed v6.1 retiré"):
        await run_seeds()
