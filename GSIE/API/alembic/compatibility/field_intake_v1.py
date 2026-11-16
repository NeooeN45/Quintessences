"""Contrat gelé de ``public.field_intake`` commun aux deux révisions 0051.

Ce module appartient aux migrations, pas aux modèles de l'application. Il ne
doit plus évoluer avec ces modèles : un autre contrat nécessiterait une autre
version. La vérification ne lit aucune ligne métier et n'exécute aucun DDL.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, NoReturn

import sqlalchemy as sa

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection, RowMapping

# Type PostgreSQL rendu, nullabilité, présence du seul défaut autorisé : now().
_COLUMNS = {
    "id": ("uuid", False, False),
    "created_at": ("timestamp with time zone", False, True),
    "updated_at": ("timestamp with time zone", False, True),
    "submitted_by": ("uuid", False, False),
    "application_key": ("character varying(100)", False, False),
    "client_event_id": ("character varying(200)", False, False),
    "kind": ("character varying(40)", False, False),
    "observed_at": ("timestamp with time zone", False, False),
    "received_at": ("timestamp with time zone", False, True),
    "status": ("character varying(20)", False, False),
    "payload": ("jsonb", False, False),
    "provenance": ("jsonb", False, False),
    "payload_hash": ("character varying(64)", False, False),
    "target_resource_id": ("uuid", True, False),
    "review_notes": ("text", True, False),
    "reviewed_by": ("uuid", True, False),
    "reviewed_at": ("timestamp with time zone", True, False),
}
_READ_INDEXES = {
    "ix_field_intake_submitted_by": ("submitted_by",),
    "ix_field_intake_target_resource_id": ("target_resource_id",),
    "ix_field_intake_submitted_by_received": ("submitted_by", "received_at"),
    "ix_field_intake_status_received": ("status", "received_at"),
}
_UNIQUE_COLUMNS = ("application_key", "client_event_id")
_STATUS_LITERALS = frozenset({"'quarantined'", "'accepted'", "'rejected'"})
_SQL_TOKEN = re.compile(
    r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|[A-Za-z_][A-Za-z_0-9]*|::|[()[\],=.]"
)


def _refuse(detail: str) -> NoReturn:
    raise RuntimeError(
        f"Réconciliation refusée : public.field_intake — {detail}. "
        "Aucune conversion automatique du schéma ou des données n'est autorisée."
    )


def _tokens(expression: str) -> tuple[str, ...]:
    """Accepte uniquement les jetons nécessaires aux expressions historiques."""
    result = []
    position = 0
    while position < len(expression):
        if expression[position].isspace():
            position += 1
            continue
        match = _SQL_TOKEN.match(expression, position)
        if match is None:
            return ()
        token = match.group()
        result.append(token if token.startswith(("'", '"')) else token.lower())
        position = match.end()
    return tuple(result)


def _unwrapped(tokens: tuple[str, ...]) -> tuple[str, ...]:
    """Retire seulement les parenthèses qui entourent l'expression entière."""
    while len(tokens) >= 2 and tokens[0] == "(" and tokens[-1] == ")":
        depth = 0
        for position, token in enumerate(tokens):
            if token == "(":
                depth += 1
            elif token == ")":
                depth -= 1
            if depth == 0:
                if position != len(tokens) - 1:
                    return tokens
                break
        tokens = tokens[1:-1]
    return tokens


def _without_cast(
    tokens: tuple[str, ...], casts: tuple[tuple[str, ...], ...]
) -> tuple[str, ...]:
    tokens = _unwrapped(tokens)
    for cast in casts:
        if tokens[-len(cast) :] == cast:
            return _unwrapped(tokens[: -len(cast)])
    return tokens


def _is_now_default(expression: str | None) -> bool:
    if expression is None:
        return False
    return _unwrapped(_tokens(expression)) in {
        ("now", "(", ")"),
        ("pg_catalog", ".", "now", "(", ")"),
    }


def _is_status_check(expression: str | None) -> bool:
    """Reconnaît IN et sa décompilation PostgreSQL en ANY, sans SQL arbitraire.

    PostgreSQL 16 convertit le IN de VARCHAR en comparaison textuelle avec
    ANY(ARRAY[...]). Seuls ces deux arbres et leurs casts texte/varchar sont
    admis ; une fonction, une autre colonne ou un opérateur ajouté sont refusés.
    """
    if expression is None:
        return False
    tokens = _unwrapped(_tokens(expression))
    depth = 0
    comparator = None
    for position, token in enumerate(tokens):
        if token in {"(", "["}:
            depth += 1
        elif token in {")", "]"}:
            depth -= 1
        elif depth == 0 and token in {"in", "="}:
            comparator = position
            break
    if comparator is None:
        return False
    column = _without_cast(tokens[:comparator], (("::", "text"),))
    if column not in {("status",), ('"status"',)}:
        return False
    values = _unwrapped(tokens[comparator + 1 :])
    if tokens[comparator] == "=":
        if not values or values[0] != "any":
            return False
        values = _without_cast(values[1:], (("::", "text", "[", "]"),))
        if len(values) < 3 or values[:2] != ("array", "[") or values[-1] != "]":
            return False
        values = values[2:-1]

    # Les seules virgules admises séparent trois littéraux éventuellement castés.
    parts: list[tuple[str, ...]] = []
    start = 0
    for position, token in enumerate(values):
        if token == ",":
            parts.append(values[start:position])
            start = position + 1
    parts.append(values[start:])
    literals = [
        _without_cast(part, (("::", "character", "varying"), ("::", "text")))
        for part in parts
    ]
    return (
        len(literals) == 3
        and all(len(literal) == 1 for literal in literals)
        and {literal[0] for literal in literals} == _STATUS_LITERALS
    )


def _read(connection: Connection, sql: str, table_oid: int) -> list[RowMapping]:
    return list(connection.execute(sa.text(sql), {"table_oid": table_oid}).mappings())


def _validate_columns(connection: Connection, table_oid: int) -> None:
    columns = _read(
        connection,
        """
        SELECT a.attname AS name,
               pg_catalog.format_type(a.atttypid, a.atttypmod) AS type,
               tn.nspname AS type_schema,
               NOT a.attnotnull AS nullable,
               pg_catalog.pg_get_expr(ad.adbin, ad.adrelid) AS default_expression,
               a.attidentity::text AS identity,
               a.attgenerated::text AS generated,
               a.attcollation = t.typcollation AS default_collation,
               NOT EXISTS (
                   SELECT 1 FROM pg_catalog.pg_depend AS d
                   WHERE d.classid = 'pg_catalog.pg_attrdef'::pg_catalog.regclass
                     AND d.objid = ad.oid
                     AND d.refclassid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                     AND d.refobjid <> 'pg_catalog.now()'::pg_catalog.regprocedure
               ) AS known_default_function
        FROM pg_catalog.pg_attribute AS a
        JOIN pg_catalog.pg_type AS t ON t.oid = a.atttypid
        JOIN pg_catalog.pg_namespace AS tn ON tn.oid = t.typnamespace
        LEFT JOIN pg_catalog.pg_attrdef AS ad
          ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
        WHERE a.attrelid = :table_oid AND a.attnum > 0 AND NOT a.attisdropped
        """,
        table_oid,
    )
    by_name = {column["name"]: column for column in columns}
    if set(by_name) != set(_COLUMNS):
        _refuse(
            "colonnes différentes du contrat v1 "
            f"(absentes={sorted(set(_COLUMNS) - set(by_name))}, "
            f"inconnues={sorted(set(by_name) - set(_COLUMNS))})"
        )
    for name, (expected_type, nullable, has_default) in _COLUMNS.items():
        column = by_name[name]
        if column["type_schema"] != "pg_catalog" or column["type"] != expected_type:
            _refuse(f"type ou taille de la colonne {name} différent de {expected_type}")
        if column["nullable"] is not nullable:
            _refuse(f"nullabilité de la colonne {name} différente du contrat v1")
        if column["identity"] or column["generated"] or not column["default_collation"]:
            _refuse(f"identité, génération ou collation inconnue sur la colonne {name}")
        default = column["default_expression"]
        if has_default:
            if not _is_now_default(default) or not column["known_default_function"]:
                _refuse(f"défaut de la colonne {name} différent de now()")
        elif default is not None:
            _refuse(f"défaut inattendu sur la colonne {name}")


def _validate_constraints(connection: Connection, table_oid: int) -> dict[int, str]:
    constraints = _read(
        connection,
        """
        SELECT c.conname AS name, c.contype::text AS kind,
               c.convalidated AS validated, c.condeferrable AS deferrable,
               c.condeferred AS deferred, c.connoinherit AS no_inherit,
               c.conislocal AS local, c.coninhcount AS inherit_count,
               c.conindid AS index_oid,
               ARRAY(
                   SELECT a.attname
                   FROM unnest(c.conkey) WITH ORDINALITY AS k(attnum, position)
                   JOIN pg_catalog.pg_attribute AS a
                     ON a.attrelid = c.conrelid AND a.attnum = k.attnum
                   ORDER BY k.position
               ) AS columns,
               rn.nspname AS referred_schema, r.relname AS referred_table,
               ARRAY(
                   SELECT a.attname
                   FROM unnest(c.confkey) WITH ORDINALITY AS k(attnum, position)
                   JOIN pg_catalog.pg_attribute AS a
                     ON a.attrelid = c.confrelid AND a.attnum = k.attnum
                   ORDER BY k.position
               ) AS referred_columns,
               c.confupdtype::text AS update_action,
               c.confdeltype::text AS delete_action,
               c.confmatchtype::text AS match_type,
               pg_catalog.pg_get_expr(c.conbin, c.conrelid) AS check_expression,
               (SELECT count(*) FROM pg_catalog.pg_trigger AS t
                WHERE t.tgconstraint = c.oid) AS trigger_count,
               NOT EXISTS (
                   SELECT 1 FROM pg_catalog.pg_trigger AS t
                   WHERE t.tgconstraint = c.oid
                     AND (NOT t.tgisinternal OR t.tgenabled <> 'O')
               ) AS default_triggers
        FROM pg_catalog.pg_constraint AS c
        LEFT JOIN pg_catalog.pg_class AS r ON r.oid = c.confrelid
        LEFT JOIN pg_catalog.pg_namespace AS rn ON rn.oid = r.relnamespace
        WHERE c.conrelid = :table_oid
        """,
        table_oid,
    )
    if sorted(constraint["kind"] for constraint in constraints) != ["c", "f", "p", "u"]:
        _refuse("jeu de contraintes différent de PK, FK, UNIQUE et CHECK du contrat v1")
    indexes: dict[int, str] = {}
    for constraint in constraints:
        name, kind = constraint["name"], constraint["kind"]
        if (
            not constraint["validated"]
            or constraint["deferrable"]
            or constraint["deferred"]
            # PostgreSQL marque PK/UQ/FK ordinaires non héritables ; le CHECK
            # historique, lui, n'a pas été déclaré avec NO INHERIT.
            or constraint["no_inherit"] is not (kind != "c")
            or not constraint["local"]
            or constraint["inherit_count"] != 0
            or not constraint["default_triggers"]
            or constraint["trigger_count"] != (4 if kind == "f" else 0)
        ):
            _refuse(
                "validation, différabilité, héritage ou déclencheurs inconnus "
                f"pour la contrainte {name}"
            )
        columns = tuple(constraint["columns"])
        if kind == "p":
            if columns != ("id",):
                _refuse("clé primaire différente de (id)")
            indexes[constraint["index_oid"]] = "p"
        elif kind == "u":
            if name != "uq_field_intake_application_event" or columns != _UNIQUE_COLUMNS:
                _refuse("contrainte UNIQUE différente de uq_field_intake_application_event")
            indexes[constraint["index_oid"]] = "u"
        elif kind == "f":
            if (
                columns != ("target_resource_id",)
                or constraint["referred_schema"] != "public"
                or constraint["referred_table"] != "resource"
                or tuple(constraint["referred_columns"]) != ("id",)
                or constraint["update_action"] != "a"
                or constraint["delete_action"] != "a"
                or constraint["match_type"] != "s"
            ):
                _refuse(
                    "clé étrangère différente de target_resource_id → public.resource.id NO ACTION"
                )
        elif name != "ck_field_intake_status" or not _is_status_check(
            constraint["check_expression"]
        ):
            _refuse(
                "contrainte CHECK ck_field_intake_status différente des trois statuts autorisés"
            )
    return indexes


def _validate_indexes(
    connection: Connection, table_oid: int, constraint_indexes: dict[int, str]
) -> None:
    indexes = _read(
        connection,
        """
        SELECT i.indexrelid AS index_oid, r.relname AS name, am.amname AS method,
               i.indisunique AS unique, i.indisprimary AS primary,
               i.indisvalid AS valid, i.indisready AS ready, i.indislive AS live,
               i.indimmediate AS immediate, i.indisexclusion AS exclusion,
               i.indnullsnotdistinct AS nulls_not_distinct,
               i.indnatts AS attribute_count, i.indnkeyatts AS key_count,
               i.indexprs IS NULL AS no_expression, i.indpred IS NULL AS no_predicate,
               i.indoption::smallint[] AS key_options, r.reloptions AS options,
               ARRAY(
                   SELECT a.attname
                   FROM unnest(i.indkey) WITH ORDINALITY AS k(attnum, position)
                   LEFT JOIN pg_catalog.pg_attribute AS a
                     ON a.attrelid = i.indrelid AND a.attnum = k.attnum
                   ORDER BY k.position
               ) AS columns,
               ARRAY(
                   SELECT opc.opcdefault AND n.nspname = 'pg_catalog'
                   FROM unnest(i.indclass) WITH ORDINALITY AS k(opclass_oid, position)
                   JOIN pg_catalog.pg_opclass AS opc ON opc.oid = k.opclass_oid
                   JOIN pg_catalog.pg_namespace AS n ON n.oid = opc.opcnamespace
                   ORDER BY k.position
               ) AS default_opclasses,
               ARRAY(
                   SELECT k.collation_oid = a.attcollation
                   FROM unnest(i.indkey::smallint[], i.indcollation::oid[])
                        WITH ORDINALITY AS k(attnum, collation_oid, position)
                   LEFT JOIN pg_catalog.pg_attribute AS a
                     ON a.attrelid = i.indrelid AND a.attnum = k.attnum
                   ORDER BY k.position
               ) AS default_collations
        FROM pg_catalog.pg_index AS i
        JOIN pg_catalog.pg_class AS r ON r.oid = i.indexrelid
        JOIN pg_catalog.pg_am AS am ON am.oid = r.relam
        WHERE i.indrelid = :table_oid
        """,
        table_oid,
    )
    if len(indexes) != len(_READ_INDEXES) + 2:
        _refuse("jeu d'index différent des quatre index de lecture et des supports PK/UNIQUE")
    seen_reads = set()
    seen_constraints = set()
    for index in indexes:
        name, index_oid = index["name"], index["index_oid"]
        kind = constraint_indexes.get(index_oid)
        expected_columns: tuple[str, ...]
        if kind is not None:
            expected_columns = ("id",) if kind == "p" else _UNIQUE_COLUMNS
            seen_constraints.add(index_oid)
        else:
            if name not in _READ_INDEXES:
                _refuse(f"index inconnu {name}")
            expected_columns = _READ_INDEXES[name]
            seen_reads.add(name)
        key_count = len(expected_columns)
        if (
            tuple(index["columns"]) != expected_columns
            or index["unique"] is not (kind is not None)
            or index["primary"] is not (kind == "p")
            or index["method"] != "btree"
            or index["attribute_count"] != key_count
            or index["key_count"] != key_count
            or not index["no_expression"]
            or not index["no_predicate"]
            or index["key_options"] != [0] * key_count
            or index["default_opclasses"] != [True] * key_count
            or index["default_collations"] != [True] * key_count
            or index["options"]
            or index["nulls_not_distinct"]
            or index["exclusion"]
            or not all(index[flag] for flag in ("valid", "ready", "live", "immediate"))
        ):
            _refuse(f"définition ou disponibilité de l'index {name} différente du contrat v1")
    if seen_reads != set(_READ_INDEXES) or seen_constraints != set(constraint_indexes):
        _refuse("index de lecture ou support de contrainte absent du contrat v1")


def validate_field_intake_v1(connection: Connection) -> None:
    """Refuse toute table absente ou différente sans modifier schéma ni données."""
    if connection.dialect.name != "postgresql":
        _refuse("la vérification du contrat v1 exige une connexion PostgreSQL")
    tables = list(
        connection.execute(
            sa.text(
                """
                SELECT c.oid AS table_oid, c.relkind::text AS kind,
                       c.relpersistence::text AS persistence,
                       c.relispartition AS partition,
                       c.relrowsecurity AS row_security, c.relforcerowsecurity AS force_rls,
                       EXISTS (
                           SELECT 1 FROM pg_catalog.pg_inherits AS i
                           WHERE i.inhrelid = c.oid OR i.inhparent = c.oid
                       ) AS inheritance,
                       EXISTS (
                           SELECT 1 FROM pg_catalog.pg_trigger AS t
                           WHERE t.tgrelid = c.oid AND NOT t.tgisinternal
                       ) AS user_triggers,
                       EXISTS (SELECT 1 FROM pg_catalog.pg_policy AS p
                               WHERE p.polrelid = c.oid) AS policies,
                       EXISTS (SELECT 1 FROM pg_catalog.pg_rewrite AS r
                               WHERE r.ev_class = c.oid) AS rules
                FROM pg_catalog.pg_class AS c
                JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'field_intake'
                """
            )
        ).mappings()
    )
    if len(tables) != 1:
        _refuse("table attendue absente")
    table = tables[0]
    if (
        table["kind"] != "r"
        or table["persistence"] != "p"
        or any(
            table[flag]
            for flag in (
                "partition", "inheritance", "row_security", "force_rls",
                "user_triggers", "policies", "rules",
            )
        )
    ):
        _refuse("nature de table, héritage, partitionnement, RLS, règles ou déclencheurs inconnus")
    table_oid = table["table_oid"]
    _validate_columns(connection, table_oid)
    constraint_indexes = _validate_constraints(connection, table_oid)
    _validate_indexes(connection, table_oid, constraint_indexes)
