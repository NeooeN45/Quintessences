"""Contrat RGPD : couverture complète des données liées à user_account.

La finalisation de suppression de compte (fonction PostgreSQL installée
par les migrations 20260826_0055 puis 20260929_0058) purge ou anonymise
chaque table porteuse de données personnelles. Ce garde-fou garantit que
toute nouvelle table avec une FK vers ``user_account`` — ou toute colonne
d'identifiant soumis sans FK, comme ``field_intake.submitted_by`` — est
traitée explicitement : purgée dans la fonction, ou exemptée avec une
justification dans ``_EXEMPTIONS``.
"""

import re
from pathlib import Path

from gsie_api.infrastructure.models import Base

_FINALIZER_MIGRATION = Path("alembic/versions/20260929_0058_purge_geosylva_anonymisation_intake.py")

# Tables FK→user_account conservées par conception, avec la raison.
# Toute nouvelle exemption doit documenter la base légale de conservation.
_EXEMPTIONS: dict[str, str] = {
    "gsie_audit.audit_log": "preuve légale append-only ; actor_email anonymisé",
    "gsie_organisations.organisation": "entité partagée, survit au compte",
    "gsie_organisations.organisation_invitation": "invitation rattachée à l'organisation",
}


def _tables_avec_fk_vers_user_account() -> set[str]:
    """Tables déclarées avec une FK vers user_account.id."""
    tables: set[str] = set()
    for table in Base.metadata.tables.values():
        for fk in table.foreign_keys:
            if fk.column.table.name == "user_account":
                schema = table.schema or "public"
                tables.add(f"{schema}.{table.name}")
    return tables


def _tables_purgees_par_le_finaliseur() -> set[str]:
    """Tables ciblées par un DELETE FROM dans la migration du finaliseur."""
    source = _FINALIZER_MIGRATION.read_text(encoding="utf-8")
    return {
        f"{schema}.{table}" for schema, table in re.findall(r"DELETE FROM (\w+)\.(\w+)", source)
    }


def test_toute_table_fk_vers_user_account_est_purgee_ou_exemptee() -> None:
    non_couvertes = (
        _tables_avec_fk_vers_user_account() - _tables_purgees_par_le_finaliseur() - set(_EXEMPTIONS)
    )

    assert non_couvertes == set(), (
        "Tables rattachées à user_account absentes du finaliseur "
        f"(purge ni exemption documentée) : {sorted(non_couvertes)}"
    )


def test_geosylva_jobs_et_sessions_sont_purges() -> None:
    """Régression P0 : CASCADE jamais déclenché sur le tombstone (0058)."""
    purgees = _tables_purgees_par_le_finaliseur()

    assert "gsie_rgpd_identites.geosylva_analysis_job" in purgees
    assert "gsie_rgpd_identites.geosylva_cubage_session" in purgees


def test_field_intake_submitted_by_est_anonymise_par_sentinelle() -> None:
    """Décision Fondateur 2026-09-29 : conservation + UUID sentinelle nul."""
    source = _FINALIZER_MIGRATION.read_text(encoding="utf-8")

    assert "00000000-0000-0000-0000-000000000000" in source
    assert "UPDATE public.field_intake" in source
    assert re.search(r"SET submitted_by = '\{_ANONYMIZED_SUBMITTER\}'::uuid", source)


def test_chaque_exemption_justifie_une_conservation() -> None:
    """Une exemption sans justification est une fuite acceptée à l'aveugle."""
    assert all(_EXEMPTIONS.values())
    assert set(_EXEMPTIONS) <= _tables_avec_fk_vers_user_account()


def test_downgrade_restaure_le_finaliseur_d_origine() -> None:
    """Le downgrade doit réinstaller le corps de la révision 0055."""
    source = _FINALIZER_MIGRATION.read_text(encoding="utf-8")

    assert "op.execute(_finalizer_sql(_FINALIZER_BODY_0055))" in source
