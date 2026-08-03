"""Assemble la documentation markdown du schéma GSIE à partir des CSV extraits par PostgreSQL.

Remplace SchemaSpy (incompatible PG16) et tbls (incompatible class-table inheritance).
"""
from __future__ import annotations

import csv
from pathlib import Path

TOOLS = Path(__file__).parent
OUTPUT = TOOLS.parent / "DOCUMENTATION" / "SCHEMA_DB.md"


def read_csv(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8") as f:
        return [row for row in csv.reader(f, delimiter="|") if row]


def main() -> None:
    schemas = read_csv(TOOLS / "schema_schemas.csv")
    tables = read_csv(TOOLS / "schema_tables.csv")
    columns = read_csv(TOOLS / "schema_columns.csv")

    lines: list[str] = [
        "# Documentation du schéma de base de données GSIE",
        "",
        "> Généré automatiquement par `TOOLS/generate_schema_doc.py`.",
        f"> {len(tables)} tables réparties sur {len(schemas)} schémas.",
        f"> {len(columns)} colonnes documentées.",
        "",
        "## Sommaire",
        "",
    ]

    for schema_name, comment, count in schemas:
        lines.append(f"- **{schema_name}** — {count} tables{f' : {comment}' if comment else ''}")

    lines.append("")

    # Grouper les tables par schéma
    tables_by_schema: dict[str, list[list[str]]] = {}
    for row in tables:
        schema_name = row[0]
        tables_by_schema.setdefault(schema_name, []).append(row)

    # Grouper les colonnes par (schéma, table)
    columns_by_table: dict[tuple[str, str], list[list[str]]] = {}
    for row in columns:
        key = (row[0], row[1])
        columns_by_table.setdefault(key, []).append(row)

    for schema_name, schema_tables in tables_by_schema.items():
        lines.append(f"## {schema_name}")
        lines.append("")

        for _, table_name, table_comment, table_size in schema_tables:
            lines.append(f"### {table_name}")
            lines.append("")
            if table_comment:
                lines.append(f"*{table_comment}*")
                lines.append("")

            cols = columns_by_table.get((schema_name, table_name), [])
            if cols:
                lines.append("| Colonne | Type | Not Null | Défaut | Commentaire |")
                lines.append("|---|---|---|---|---|")
                for _, _, col_name, col_type, not_null, default, comment in cols:
                    nn = "✓" if not_null.lower() == "true" else ""
                    lines.append(
                        f"| `{col_name}` | `{col_type}` | {nn} | {default} | {comment} |"
                    )
                lines.append("")

            lines.append(f"*Taille : {table_size}*")
            lines.append("")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Documentation générée : {OUTPUT} ({len(lines)} lignes)")


if __name__ == "__main__":
    main()
