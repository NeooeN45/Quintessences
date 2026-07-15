# ADR-001 — Racine Resource : class-table inheritance et FK fortes

| Champ | Valeur |
|---|---|
| **ID** | ADR-001 |
| **Statut** | Proposé |
| **Date** | 2026-07-15 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Décision liée** | DEC-000022, RFC-0011 |

## Contexte

Le métamodèle v6.2 définit 65 types. Plusieurs types (QualityAssessment,
Citation, Revision, ConflictCluster) doivent référencer n'importe quel
type cible. Dans le schéma v5 et dans le code actuel, cela se faisait
par **FK polymorphique** (`target_type VARCHAR, target_id UUID`) — ce
qui viole l'intégrité référentielle SQL (aucune FK ne peut vérifier un
target polymorphe) et rend les jointures fragiles.

L'audit v6.1 (F-P1-03) exige la suppression de toute FK polymorphe.

## Options envisagées

1. **Single-table inheritance** — une table unique avec 42+ colonnes
   sparse (la plupart NULL pour chaque ligne). Avantage : une seule
   table, FK simple. Inconvénient : indexation inefficace, contraintes
   CHECK complexes, migration difficile, colonnes majoritairement NULL.

2. **Class-table inheritance avec racine Resource** — une table racine
   `resource(id, type, created_at, gsie_id)` + une table par type (42
   tables), chacune avec `id` comme PK et FK vers `resource(id)`. Les
   références polymorphiques pointent vers `resource(id)` — FK forte
   garantie. Avantage : intégrité référentielle, clarté, indexation par
   table. Inconvénient : 42 tables + 1 racine = 43 tables.

3. **Tables séparées sans racine** — chaque type a sa propre table, les
   références polymorphiques restent `target_type/target_id`. Avantage :
   pas de table racine. Inconvénient : le problème polymorphe persiste.

## Décision

**Option 2 : class-table inheritance avec racine Resource.**

```sql
CREATE TABLE resource (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type       VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    gsie_id    VARCHAR(32) UNIQUE
);

-- Chaque type hérite via FK
CREATE TABLE assertion (
    id   UUID PRIMARY KEY REFERENCES resource(id),
    -- champs spécifiques...
);
```

Toute référence "polymorphe" (QualityAssessment.target, Citation.target,
Revision.target, ConflictCluster membres) pointe vers `resource(id)` —
FK forte garantie par PostgreSQL.

## Conséquences

- **Positives** : intégrité référentielle SQL complète, pas de FK
  polymorphe, indexation efficace par table, schéma lisible, migration
  par table possible.
- **Négatives** : 66 tables (65 types + racine) — plus de DDL à
  maintenir. Jointures multi-tables pour récupérer une entité complète
  (mais rare en pratique — on interroge par type).
- **Impact moteurs** : les repositories moteurs interrogent par type
  (ex. `SELECT * FROM assertion JOIN assertion_participant ...`). Pas
  d'impact sur les contrats d'interface.

## Statut de suivi

- 2026-07-15 : Proposé (RFC-0011 / DEC-000022)
