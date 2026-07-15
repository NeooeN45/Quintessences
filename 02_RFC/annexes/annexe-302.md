# Annexe RFC-0011 — Superseding du livrable 302 (Knowledge Method)

| Champ | Valeur |
|---|---|
| **RFC** | RFC-0011 |
| **Document supersédé** | 302 — Knowledge Method (`GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md`) |
| **Statut du document supersédé** | Validated |
| **Action** | Supersédé par DEC-000022 |
| **Date** | 2026-07-15 |

---

## Ce qui change

Le livrable 302 définit la structure `KnowledgeObject` avec 6 types
(concept, relation, regle, seuil, modele, classification) et
`evidence_level` comme champ direct obligatoire.

Le métamodèle v6.1 remplace cette structure par :

| Élément 302 | Élément v6.1 | Type |
|---|---|---|
| `KnowledgeObject` | `Assertion` (type 9) + types spécialisés | Noyau |
| `type` enum 6 valeurs | `claim_kind` enum 7 valeurs (§3.3 métamodèle) | Assertion |
| `evidence_level` (champ direct) | `EvidenceAssessment` (type 13, multiple) | Noyau |
| `source` (champ direct) | `Citation` (type 24) → `Source` (type 23) | Noyau |
| `contenu` (dict libre) | `AssertionParticipant` (type 10) + `AssertionQualifier` (type 11) | Noyau |
| `historique` (liste VersionEntry) | `Revision` (type 29, append-only) | Noyau |
| `domaines_validite` (liste) | `AssertionQualifier` (key=domaine) | Noyau |
| `conflits` (liste ConflitBibliographique) | `ConflictCluster` (type 42) | Noyau |
| `type=concept` | `Concept` (type 3) — n'est plus une assertion | Noyau |

## Ce qui est conservé

- Le cycle de vie (Création → Validation → Intégration → Utilisation →
  Révision → Archivage) reste conceptuellement valide.
- Le versionnement CON-010 (version incrémentée, ancienne archivée,
  jamais supprimée) est préservé via `Revision`.
- Les 6 types de contenu (concept, relation, regle, seuil, modele,
  classification) sont mappés 1:1 vers `claim_kind` (avec ajout de
  `observation` et `absence`).

## Impact sur le code existant

- `GSIE/API/src/gsie_api/engines/knowledge/schemas.py` —
  `KnowledgeObject` Pydantic → `Assertion` + `EvidenceAssessment`
- `GSIE/API/src/gsie_api/engines/knowledge/engine.py` — store in-memory
  → repository sur schéma v6.1 (Vague 0/1)
- `GSIE/API/src/gsie_api/infrastructure/knowledge_models.py` — tables
  `knowledge_objects` → `resource` + `assertion` + tables associées
- `GSIE/API/alembic/versions/0001_initial_knowledge_botanical_ecosystem.py`
  — migration de schéma (ADR-004)

## Migration

Voir ADR-004 (migration schéma). Les 25 connaissances seed (livrable
308) sont migrées vers le schéma v6.1 par script de migration. Tests
avant/après pour vérifier la préservation des données.

## Statut du document 302

Le fichier `KNOWLEDGE_METHOD.md` est **conservé intact** dans
`GSIE/KNOWLEDGE/`. Son en-tête est annoté pour indiquer qu'il est
supersédé par RFC-0011 / DEC-000022. Il reste consultable pour
traçabilité historique (CON-010).
