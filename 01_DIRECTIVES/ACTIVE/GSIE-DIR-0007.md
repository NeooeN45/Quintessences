# ============================================================================
# GSIE KNOWLEDGE DIRECTIVE
# Directive ID : GSIE-DIR-0007
# Version : 1.0
# Statut : ACTIVE
# Priorité : CRITIQUE
# Classification : PHASE
# Auteur : Camille Perraudeau
# Date : 2026-07-13
# ============================================================================

# Titre : Lancement officiel de la Phase 3 — Connaissance

## Résumé exécutif

La Phase 3 « Connaissance » est officiellement lancée. Elle transforme
les fondations scientifiques et l'architecture définies en Phases 1 et 2
en une **base de connaissances structurée, sourcée et versionnée** — le
véritable produit de GSIE (CON-003).

Cette phase est composée de **8 livrables obligatoires** (301-308).

## Contexte

- **Phase 1 (Foundation)** : clôturée — 12 livrables Validated/Locked.
- **Phase 2 (Architecture)** : livrables 201-212 Draft complets. Les
  contrats d'interface (livrable 206) définissent les schémas de données
  que la base de connaissances doit produire (`KnowledgeObject`,
  `QualifiedKnowledge`, `EvidenceLevel`).
- **Constitution Scientifique** (S-1 à S-7) : définit les règles
  opérationnelles — sources acceptées, niveaux de preuve, conflits,
  révision, incertitude, domaines, patrimoine.
- **DIR-0006** : le moteur cognitif exige un graphe vivant, une
  assimilation probabiliste et un raisonnement multi-échelle. La base
  de connaissances doit supporter ces exigences.

## Décisions validées

1. La Phase 3 est composée de 8 livrables obligatoires (301-308).
2. Les livrables sont produits dans l'ordre défini ci-dessous.
3. Aucune connaissance n'entre dans la base sans source (S-1) et sans
   niveau de preuve (S-2).
4. La base de connaissances est le **véritable produit** de GSIE
   (CON-003).
5. Le code métier des moteurs reste interdit jusqu'en Phase 4.

## Les 8 livrables de la Phase 3

| # | Livrable | Fichier | Description |
|---|---|---|---|
| 301 | Research Method (détaillée) | `06_RESEARCH/RESEARCH_METHOD.md` | Pipeline complet : critères par étape, évaluation sources, assignation niveau de preuve, résolution conflits, surveillance scientifique |
| 302 | Knowledge Method (détaillée) | `07_KNOWLEDGE/KNOWLEDGE_METHOD.md` | Cycle de vie KnowledgeObject, versioning, domaines de validité, types de relations, mapping moteurs consommateurs |
| 303 | Forest Ontology | `07_KNOWLEDGE/FOREST_ONTOLOGY.md` | Ontologie complète : concepts par domaine (S-6), définitions, propriétés, relations |
| 304 | Knowledge Graph Spec | `07_KNOWLEDGE/KNOWLEDGE_GRAPH_SPECIFICATION.md` | Types de nœuds, types d'arêtes, propriétés, patterns de requête, versioning, support graphe vivant (DIR-0006) |
| 305 | Dataset Catalog | `08_DATASETS/DATASET_CATALOG.md` | Catalogue datasets : IGN, Météo-France, INRAE, ONF, GBIF, Copernicus — métadonnées complètes |
| 306 | Evidence Framework | `06_RESEARCH/EVIDENCE_FRAMEWORK.md` | Critères détaillés assignation niveaux A-F, exemples par domaine, cas limites, règles upgrade/downgrade |
| 307 | Sourcing Plan | `06_RESEARCH/SOURCING_PLAN.md` | Plan priorisé d'ingestion : quels domaines/sources en premier, aligné sur ordre développement moteurs |
| 308 | Knowledge Base Seed | `07_KNOWLEDGE/KNOWLEDGE_BASE_SEED.md` | Premières connaissances concrètes : autécologie essences, seuils pédologiques, modèles croissance |

## Ordre de production

```
301 (Research Method) ──┬── 306 (Evidence Framework) ──┐
302 (Knowledge Method) ─┤                              ├── 307 (Sourcing Plan) ── 308 (Seed)
                        ├── 303 (Forest Ontology) ─────┤
                        ├── 304 (Knowledge Graph) ─────┤
                        └── 305 (Dataset Catalog) ─────┘
```

301 et 302 sont fondamentaux (méthodes). 303-306 peuvent être
parallélisés. 307 dépend de 305+306. 308 dépend de tout.

## Critères de complétude Phase 3

- Le pipeline de recherche est détaillé étape par étape avec critères
  opérationnels.
- Le cycle de vie d'une connaissance est complet (création → révision →
  archivage).
- L'ontologie forestière couvre les 10 domaines scientifiques (S-6).
- Le graphe de connaissances supporte le raisonnement multi-échelle
  (DIR-0006).
- Au moins 10 datasets français sont catalogués avec métadonnées.
- Le framework de niveaux de preuve a des exemples concrets par domaine.
- Le plan de sourcing est priorisé et aligné sur l'ordre des moteurs.
- La base de connaissances contient au moins 20 connaissances validées
  (autécologie de 5 essences + seuils pédologiques + modèles croissance).

## Garde-fous

- La Constitution Scientifique (S-1 à S-7) prime sur tout.
- Aucune connaissance sans source (CON-002, S-1).
- Aucune connaissance sans niveau de preuve (S-2).
- Les conflits bibliographiques sont documentés, jamais résolus
  arbitrairement (S-3).
- L'historique des connaissances est conservé (CON-010, S-7).
- Le code métier reste interdit (Phase 4).

---

> La connaissance est le véritable produit. Le code n'est qu'un moyen.
