-- Documentation du schéma GSIE — génère un markdown complet
-- Compatible PostgreSQL 16 (remplace SchemaSpy)
\pset format unaligned
\pset tuples_only on

-- Récupérer les infos dans un fichier
\o /tmp/schema_schemas.csv
SELECT n.nspname || '|' || COALESCE(obj_description(n.oid), '') || '|' || count(t.tablename)::text
FROM pg_namespace n
JOIN pg_tables t ON t.schemaname = n.nspname
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'ag_catalog')
GROUP BY n.nspname, n.oid
ORDER BY n.nspname;
\o

\o /tmp/schema_tables.csv
SELECT t.schemaname || '|' || t.tablename || '|' || COALESCE(obj_description(format('%I.%I', t.schemaname, t.tablename)::regclass), '') || '|' || pg_size_pretty(pg_total_relation_size(format('%I.%I', t.schemaname, t.tablename)::regclass))
FROM pg_tables t
WHERE t.schemaname NOT IN ('pg_catalog', 'information_schema', 'ag_catalog')
ORDER BY t.schemaname, t.tablename;
\o

\o /tmp/schema_columns.csv
SELECT n.nspname || '|' || c.relname || '|' || a.attname || '|' || format_type(a.atttypid, a.atttypmod) || '|' || a.attnotnull || '|' || COALESCE(pg_get_expr(d.adbin, d.adrelid), '') || '|' || COALESCE(col_description(c.oid, a.attnum), '')
FROM pg_attribute a
JOIN pg_class c ON a.attrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
LEFT JOIN pg_attrdef d ON a.attrelid = d.adrelid AND a.attnum = d.adnum
WHERE a.attnum > 0 AND NOT a.attisdropped
  AND n.nspname NOT IN ('pg_catalog', 'information_schema', 'ag_catalog')
ORDER BY n.nspname, c.relname, a.attnum;
\o

\echo 'Données extraites. Génération du markdown...'
