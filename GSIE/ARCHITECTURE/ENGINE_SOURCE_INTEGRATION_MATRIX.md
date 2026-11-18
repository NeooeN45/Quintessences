# Matrice d'intégration moteurs GSIE et sources

**Statut :** active pour le contrôle structurel Phase 4
**Version :** 1.0.0
**Date :** 2026-08-30
**Source exécutable :** `GSIE/API/src/gsie_api/governance/engine_source_matrix.py`

## Objet

Cette matrice répond à une question précise : quelles dépendances de données
un moteur a-t-il le droit d'utiliser et par quel chemin contrôlé ? Elle ne
remplace ni le registre juridique SCI-001 ni la qualification métier d'une
source.

Une source peut être documentée sans être branchée. Une source branchée par un
adapter peut être interrogeable sans être téléchargeable. Un fichier archivé
par Forge peut être vérifié sans être promu dans un environnement de
production. Ces états restent volontairement distincts.

## Règles d'architecture

1. Les 14 contrats moteur sont définis une seule fois dans GSIE-Bench.
2. Un moteur domaine utilise un adapter ou le handoff Forge déclaré dans la
   matrice, jamais une URL fournisseur en dur.
3. Les moteurs transverses consomment des données déjà normalisées et
   qualifiées ; ils ne contournent pas le Data Registry.
4. Les noms de sources issus de la recherche sont des candidats tant qu'ils ne
   possèdent pas d'identifiant SCI-001 et d'une ligne de couverture
   opérationnelle.
5. `HISTORICAL`, `BLOCKED`, `METADATA_ONLY` et `PARTNER_GATE` ne sont jamais
   des voies d'exécution directe.
6. `FETCH` et la promotion restent des décisions distinctes de `QUERY`.

## État des dépendances directes

| Moteur | Chemin contrôlé | Sources actives | Manques déclarés |
|---|---|---|---|
| GIS | Adapter query | IGN API Carto cadastre | limites administratives, WFS par couche |
| Climate | Adapter query | Météo des forêts | SAFRAN, ARPEGE/AROME, observations sol |
| Pedology | Adapter query | SoilGrids WCS 2.0.1 | BDAT, BRGM, RMQS, GIS Sol |
| Botanical | Adapter query | GBIF Species, TAXREF miroir GBIF, Bellifa | occurrences GBIF et OpenObs |
| Forest Dynamics | Handoff Forge | IFN brut vérifié | BD Forêt, LiDAR HD, RENECOFOR |
| Evidence, Knowledge, Correlation, Reasoning, Diagnostic, Recommendation, Validation, Simulation, Learning | Registry indirect | données qualifiées transmises par le pipeline | sources candidates propres à chaque cas d'usage |

## Contrôle CI

Depuis `GSIE/API`, lancer :

```powershell
python scripts/audit_engine_source_matrix.py
```

Le contrôle est sans réseau, sans base et sans instanciation de client. Il
échoue si un moteur manque, si une source est inconnue, si une source
historique ou bloquée est utilisée, ou si le chemin déclaré ne correspond pas
à la matrice de couverture.

Le contrôle de couverture des 23 identifiants SCI-001 reste complémentaire :

```powershell
python scripts/audit_source_coverage.py
```

## Porte de promotion

Pour qu'une source passe de candidate à active, la fiche doit contenir la
distribution exacte, la version, le format, le schéma, le CRS si spatial, la
licence et sa preuve, la politique de quota, la qualité, la fréquence de mise
à jour, l'empreinte d'une copie éventuelle et la validation opérateur.

Pour qu'elle alimente l'entraînement, il faut en plus un manifeste de jeu,
une séparation entraînement-évaluation, un scénario GSIE-Bench reproductible,
une relecture experte et une décision explicite de promotion. Aucun moteur ne
peut déduire cette autorisation de la seule présence de la source dans un
catalogue.

## Évolution à long terme

La stabilité décennale repose sur les identifiants canoniques, les contrats de
capacité, les versions d'adapters, les manifests immuables et les aliases de
dépréciation. Les endpoints fournisseurs sont des détails remplaçables. Une
migration future doit ajouter un successeur, rejouer les tests de contrat et
conserver la provenance ; elle ne doit pas modifier silencieusement une
source historique.
