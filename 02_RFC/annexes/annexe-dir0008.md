# Annexe RFC-0011 — Amendement de la directive GSIE-DIR-0008

| Champ | Valeur |
|---|---|
| **RFC** | RFC-0011 |
| **Directive amendée** | GSIE-DIR-0008 — Encyclopédie de l'Écosystème |
| **Statut de la directive** | ACTIVE |
| **Action** | Amendée par DEC-000022 (§2.1, §2.3, §2.4) |
| **Date** | 2026-07-15 |

---

## Sections amendées

### §2.1 — Base de données graphe

**Texte original** :
> Technologie recommandée : Neo4j (graphe natif, Cypher, scalable,
> écosystème mature) ou alternative équivalente à évaluer en Phase 4.
> Scalabilité : capacité visée de 10 millions de nœuds minimum.

**Amendement** :
> PostgreSQL 16 + PostGIS 3.4 est la **vérité canonique** pour toutes
> les données de l'Encyclopédie. La topologie de graphe est implémentée
> via les tables `assertion` + `assertion_participant` (SQL). Pour les
> traversées profondes, l'extension Apache AGE est évaluée par benchmark
> en Vague 1 (ADR-003). Neo4j est **différé** et sera réintroduit
> uniquement si AGE ne passe pas le seuil mesuré. La capacité visée de
> 10 millions d'entrées minimum est maintenue.

### §2.3 — Triple store sémantique

**Texte original** :
> Au-dessus du graphe, une couche sémantique (RDF/OWL) permet
> l'interrogation SPARQL, l'alignement avec des ontologies externes
> (GBIF, ENVO, AGROVOC), la publication en Linked Open Data.

**Amendement** :
> La couche sémantique RDF/OWL (Apache Jena) est **différée**. Elle est
> une **projection régénérable** à partir de PostgreSQL, pas une source
> de vérité. Elle sera implémentée lorsque le besoin SPARQL ou
> l'alignement Linked Open Data sera confirmé par un cas d'usage réel.
> Les types `Concept` (3), `ControlledTerm` (7) et `Vocabulary` (5) du
> métamodèle v6.1 préparent cette projection.

### §2.4 — API et exposition

**Texte original** :
> API REST/GraphQL : interrogation programmatique par les moteurs et
> les applications clientes.

**Amendement** :
> L'API est exposée via **REST** (FastAPI) en Vague 1. **GraphQL** est
> différé et sera évalué si les consommateurs de l'API expriment le
> besoin de requêtes flexibles multi-ressources. L'identifiant résolvable
> `gsie://K-XXXXXXXXXX` est préservé (champ `gsie_id` sur la table
> racine `resource`).

## Sections non amendées (valides)

- §1 (Vision) — l'Encyclopédie comme produit principal : **inchangé**
- §1.2 (Périmètre) — tout l'écosystème : **inchangé**
- §1.3 (Ambition de marché) : **inchangé**
- §2.2 (Identifiants uniques stables) : **inchangé** (format GSIE-XXX préservé)
- §3 (Collecte massive) : **inchangé** (stratégie d'ingestion validée,
  enrichie par `Distribution.access_method` et `Source.source_nature`)
- §4 (Extrême structuration) : **inchangé** (dimensions de classification
  préservées via `AssertionQualifier`)
- §5 (Technologies cibles) : **amendé implicitement** — les technologies
  candidates sont remplacées par les ADR-001 à ADR-006
- §6 (Gouvernance) : **inchangé**
- §7 (Impact sur les phases) : **amendé implicitement** — Vague 0 ajoutée
- §8 (Décisions validées) : **inchangé** (les 10 décisions restent valides)
- §9 (Garde-fous) : **inchangé**

## Statut de la directive

La directive GSIE-DIR-0008 reste **ACTIVE**. Elle n'est pas Locked —
un amendement par DEC est possible (gouvernance GSIE). Le contenu
historique est conservé intact. L'amendement est annoté dans la directive
par une note de bas de page référençant RFC-0011 / DEC-000022.
