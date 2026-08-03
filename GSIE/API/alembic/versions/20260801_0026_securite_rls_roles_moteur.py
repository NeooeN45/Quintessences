"""Securite — RLS bypass par appartenance exacte + roles moteur effectifs.

Audit securite 2026-08-01, constats E et F.

Constat E (RLS bypass par sous-chaîne) :
    Les six policies RLS de la migration 0004 utilisaient
    ``current_setting('app.current_user_roles', true) LIKE '%admin%'``
    — une correspondance de sous-chaîne, pas une appartenance à une liste.
    Tout rôle dont le nom contient ``admin`` (ex: ``admin_lecture_seule``,
    ``sous_admin``), ``dpo`` ou ``governance`` obtenait le bypass complet,
    en lecture comme en écriture. Aucun échappement des métacaractères LIKE
    n'était appliqué non plus.

    Cette migration remplace le prédicat par une appartenance exacte :
    ``EXISTS (SELECT 1 FROM unnest(string_to_array(..., ',')) AS r
              WHERE r IN ('admin','dpo','governance'))``

Constat F (roles moteur décoratifs) :
    La migration 0022 faisait ``GRANT gsie_application TO gsie_moteur_X``.
    Comme ``gsie_application`` détient déjà SELECT, INSERT, UPDATE sur les
    sept schémas de domaine (migrations 0013-0019) et que les rôles sont
    INHERIT par défaut, chaque rôle moteur héritait de la totalité des
    droits sur tous les domaines. Le GRANT USAGE ciblé n'ajoutait rien.

    Cette migration :
    1. REVOKE gsie_application de chaque rôle moteur (le lien d'héritage
       est supprimé — un rôle moteur n'est plus un sous-ensemble de
       l'application entière).
    2. Donne à chaque rôle moteur un accès direct au schéma public
       (USAGE + SELECT, INSERT, UPDATE sur tables et séquences, +
       ALTER DEFAULT PRIVILEGES pour les tables futures).
    3. Donne à chaque rôle moteur SELECT, INSERT, UPDATE sur son seul
       schéma de domaine (+ séquences + ALTER DEFAULT PRIVILEGES).

    ``gsie_application`` conserve l'accès à tous les domaines : l'API est
    un service unique qui sert les 14 moteurs. Un service dédié à un seul
    moteur (ex: un worker Climate autonome) utilisera ``gsie_moteur_climat``
    et n'aura accès qu'à ``public`` + ``gsie_climat``.

Constat supplémentaire (REVOKE SCHEMA public FROM PUBLIC) :
    Le schéma ``public`` n'était jamais révoqué à ``PUBLIC`` par une
    migration — le seul REVOKE se trouvait dans ``docker/init-roles.sql``
    qui n'est pas exécuté par le compose. PostgreSQL 16 a retiré CREATE
    de PUBLIC sur public, mais le défaut de la démarche « défense en
    profondeur » (migration 0020) reste à combler.

Revision ID: 20260801_0026
Revises: 20260801_0025
Create Date: 2026-08-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260801_0026"
down_revision: str | None = "20260801_0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ROLE_APPLICATION = "gsie_application"

# (role, schema) — un role par moteur de domaine.
_MOTEURS = (
    ("gsie_moteur_foret", "gsie_foret"),
    ("gsie_moteur_botanique", "gsie_botanique"),
    ("gsie_moteur_gouvernance", "gsie_gouvernance"),
    ("gsie_moteur_climat", "gsie_climat"),
    ("gsie_moteur_pedologie", "gsie_pedologie"),
    ("gsie_moteur_hydro", "gsie_hydro"),
    ("gsie_moteur_feu", "gsie_feu"),
)

_ECRITURE = "SELECT, INSERT, UPDATE"

# Tables portant une policy RLS (migration 0004), avec leur schéma courant.
# Les migrations 0011, 0021 et 0023 ont déplacé certaines de public vers
# gsie_rgpd ou gsie_rgpd_identites : il faut qualifier les noms.
_RLS_TABLES: tuple[tuple[str, str, str], ...] = (
    # (schema, table, colonne_propriétaire)
    ("gsie_rgpd", "consent", "data_subject_id"),
    ("gsie_rgpd_identites", "data_subject", "id"),
    ("gsie_rgpd", "sensitivity_classification", "classified_by"),
    ("gsie_rgpd", "access_policy", "principal"),
    ("public", "sample", "subject_id"),
    ("public", "observation", "subject_id"),
)

# Rôles qui contournent l'isolation par ligne.
_BYPASS_ROLES = ("admin", "dpo", "governance")


def _bypass_predicate_exact() -> str:
    """Construit la clause de bypass par appartenance exacte.

    Remplace le ``LIKE '%admin%'`` de 0004 par un test d'appartenance
    exacte dans la liste CSV des rôles. ``sous_admin`` ne déclenche plus
    le bypass ; ``admin`` seul le déclenche.
    """
    roles_sql = ", ".join(f"'{r}'" for r in _BYPASS_ROLES)
    return (
        "EXISTS (SELECT 1 FROM unnest(string_to_array("
        "current_setting('app.current_user_roles', true), ',')) AS r "
        f"WHERE trim(r) IN ({roles_sql}))"
    )


def _owner_predicate(table: str, column: str) -> str:
    """Construit la clause de comparaison propriétaire pour une table.

    Reprend les colonnes de 0004. ``principal`` est text, les autres sont
    des UUID comparées en texte.
    """
    text_columns = frozenset({"principal"})
    column_expr = column if column in text_columns else f"{column}::text"
    return f"{column_expr} = current_setting('app.current_user_id', true)"


def upgrade() -> None:
    # ── Constat E : RLS bypass par appartenance exacte ──────────────────
    bypass = _bypass_predicate_exact()
    for schema, table, column in _RLS_TABLES:
        qualified = f"{schema}.{table}"
        policy_name = f"{table}_isolation"
        owner_predicate = _owner_predicate(table, column)
        # Drop + recreate : ALTER POLICY ne permet pas de changer la
        # structure du USING, seulement l'expression.
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {qualified}")
        op.execute(
            f"CREATE POLICY {policy_name} ON {qualified} " f"USING ({bypass} OR {owner_predicate})"
        )

    # ── Constat F : Roles moteur effectifs ──────────────────────────────
    for role, schema in _MOTEURS:
        # 1. Couper l'héritage de gsie_application : un rôle moteur n'est
        #    plus un sous-ensemble de l'application entière.
        op.execute(f"REVOKE {_ROLE_APPLICATION} FROM {role}")

        # 2. Accès direct au noyau public (ce que gsie_application donnait
        #    par héritage, mais sans entraîner les sept domaines).
        op.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
        op.execute(f"GRANT {_ECRITURE} ON ALL TABLES IN SCHEMA public TO {role}")
        op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {role}")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public " f"GRANT {_ECRITURE} ON TABLES TO {role}"
        )

        # 3. Accès en écriture sur son seul schéma de domaine.
        #    USAGE était déjà accordé par 0022, mais pas les droits sur
        #    les tables — ils venaient de gsie_application par héritage.
        op.execute(f"GRANT {_ECRITURE} ON ALL TABLES IN SCHEMA {schema} TO {role}")
        op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO {role}")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} " f"GRANT {_ECRITURE} ON TABLES TO {role}"
        )

        op.execute(
            f"COMMENT ON ROLE {role} IS "
            f"'Moteur de domaine ({schema}). Acces direct a public + {schema} "
            f"seul. N''herite plus de {_ROLE_APPLICATION} (audit 2026-08-01).' "
        )

    # ── Constat supplémentaire : REVOKE SCHEMA public FROM PUBLIC ───────
    # PostgreSQL 16 a retiré CREATE de PUBLIC sur public, mais USAGE
    # reste : sans ce REVOKE, un rôle qui n'a aucun GRANT explicite peut
    # encore voir les objets de public si leur propriétaire a laissé les
    # ACL par défaut. La défense en profondeur (0020) couvre les sept
    # schémas de domaine ; public devait l'être aussi.
    op.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
    # gsie_application et les rôles moteur reçoivent USAGE explicitement
    # (ci-dessus pour les moteurs, migration 0012 pour gsie_application).
    # Les outils de visualisation le reçoivent par migration 0025.


def downgrade() -> None:
    # ── Restaurer le REVOKE public ──────────────────────────────────────
    # PUBLIC retrouve USAGE sur public (défaut PostgreSQL 16).
    op.execute("GRANT USAGE ON SCHEMA public TO PUBLIC")

    # ── Restaurer les rôles moteur comme dans 0022 ──────────────────────
    for role, schema in _MOTEURS:
        # Retirer les droits directs sur le domaine
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
            f"REVOKE {_ECRITURE} ON TABLES FROM {role}"
        )
        op.execute(f"REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} FROM {role}")
        op.execute(f"REVOKE {_ECRITURE} ON ALL TABLES IN SCHEMA {schema} FROM {role}")

        # Retirer les droits directs sur public
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            f"REVOKE {_ECRITURE} ON TABLES FROM {role}"
        )
        op.execute(f"REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public FROM {role}")
        op.execute(f"REVOKE {_ECRITURE} ON ALL TABLES IN SCHEMA public FROM {role}")
        op.execute(f"REVOKE USAGE ON SCHEMA public FROM {role}")

        # Restaurer l'héritage de gsie_application (état 0022)
        op.execute(f"GRANT {_ROLE_APPLICATION} TO {role}")
        op.execute(
            f"COMMENT ON ROLE {role} IS "
            f"'Moteur de domaine ({schema}). Herite de {_ROLE_APPLICATION} "
            f"(noyau sans DELETE, aucun acces RGPD). USAGE sur {schema}.' "
        )

    # ── Restaurer les policies RLS avec LIKE ────────────────────────────
    # ATTENTION : ce downgrade restaure la vulnérabilité E (LIKE '%admin%').
    clauses = [
        f"current_setting('app.current_user_roles', true) LIKE '%{r}%'" for r in _BYPASS_ROLES
    ]
    bypass_like = " OR ".join(clauses)
    for schema, table, column in _RLS_TABLES:
        qualified = f"{schema}.{table}"
        policy_name = f"{table}_isolation"
        owner_predicate = _owner_predicate(table, column)
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {qualified}")
        op.execute(
            f"CREATE POLICY {policy_name} ON {qualified} "
            f"USING ({bypass_like} OR {owner_predicate})"
        )
