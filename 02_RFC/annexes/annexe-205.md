# Annexe RFC-0011 — Annotation du livrable 205 (Scientific Data Model)

| Champ | Valeur |
|---|---|
| **RFC** | RFC-0011 |
| **Document annoté** | 205 — Scientific Data Model (`GSIE/ARCHITECTURE/SCIENTIFIC_DATA_MODEL.md`) |
| **Statut du document** | Draft |
| **Action** | Annoté (pas supersédé — déjà Draft) |
| **Date** | 2026-07-15 |

---

## Ce qui change

Le livrable 205 (Draft) définit des entités scientifiques (Station,
Parcelle, Arbre, Peuplement) avec `evidence_level` comme champ direct
sur les entités.

Le métamodèle v6.1 remplace cela par :

| Élément 205 | Élément v6.1 |
|---|---|
| `evidence_level` direct sur entités | `EvidenceAssessment` sur les `Assertion` qui portent des affirmations sur ces entités |
| Station, Parcelle, Arbre, Peuplement | Profils métier (niveau B) spécialisant `Instance` (type 8) |
| Tables dédiées par entité | Tables de profil (FK vers `resource.id`) — Vague 2+ |

## Statut

Le livrable 205 est **Draft** — il n'est pas supersédé (pas Validated).
Il est annoté pour indiquer que les entités qu'il définit deviennent des
profils (niveau B) du métamodèle v6.1, et que `evidence_level` direct
est remplacé par `EvidenceAssessment`. Le contenu est conservé et sera
mis à jour lors de la définition des profils en Vague 2.
