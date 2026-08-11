# Data Selection Engine GSIE — Phase 5

**Statut :** implémenté en tranche contrôlée

**Date :** 2026-08-10
**Contrat de référence :** RFC-0038 v1.2.0 / DEC-000059

## 1. Périmètre livré

Le `Data Selection Engine` est une couche interne de l'API, exposée par
`POST /api/v1/data/resolve`. Il ne contacte aucun fournisseur et ne génère
aucune URL présignée. Il consomme les projections du Data Registry et applique
une politique déterministe avant de classer les candidats.

La route est authentifiée, protégée par le RBAC `dataset:read`, soumise au
rate limiting commun et corrélée par `X-Trace-Id`. Les erreurs de contrat ne
révèlent ni SQL, ni chemin local, ni secret.

## 2. Ordre de décision

1. Les filtres de thème, période, emprise et grain réduisent le catalogue.
2. Les contraintes sont vérifiées avant tout score : statut selon `display` ou
   `inference`, qualification Registry A–F, licence commerciale, qualité
   explicitement mesurée et archive requise pour l'inférence.
3. Les blocages portent des codes stables (`EVIDENCE_MISSING`,
   `EVIDENCE_INSUFFICIENT`, `QUALITY_MISSING`, `QUALITY_BELOW_MINIMUM`,
   `STATUS_NOT_PRODUCTION`, `ASSET_NOT_ARCHIVED`, etc.). Ils restent visibles
   quand aucun candidat n'est admissible.
4. Les candidats admissibles sont classés par une politique versionnée
   `data-resolver-1`. Les préférences disponibles sont `freshness`, `quality`
   et `offline_availability`, avec pondérations 0,4 / 0,4 / 0,2 et
   renormalisation sur les dimensions connues. Une qualité ou une fraîcheur
   inconnue n'est jamais transformée silencieusement en mesure réelle.
5. L'ordre final est stable : score, qualification Registry, date de version,
   puis identifiants. Le fallback est désactivé par défaut et, s'il est
   demandé avec `allow_fallback=true`, il est évalué par la même politique.

## 3. Réponse explicable

La réponse contient les candidats évalués, leur admissibilité, les blocages,
les critères et scores, la sélection principale, le fallback éventuel, la
version de politique, la version de vocabulaire de domaines et le `trace_id`.
Les métadonnées de fraîcheur proviennent de `DatasetHealth` quand la
préférence est demandée ; la disponibilité offline provient des `DataAsset`
archivés et vérifiables.

## 4. Limites assumées de la tranche

- aucune récupération réseau ni ingestion n'est déclenchée par le resolver ;
- les scores de qualité sont lus lorsqu'ils sont explicitement présents dans
  `DatasetVersion.stats`, en attendant la projection complète des
  `QualityAssessment` dans la campagne de qualification ;
- la persistance périodique des rapports `DatasetHealth` et le manifeste
  d'ingestion sont les prochaines étapes ;
- l'absence de catalogue qualifié renvoie une décision vide explicable, jamais
  une source fournisseur implicite.

## 5. Preuves

- tests unitaires `tests/unit/test_data_registry_resolver.py` ;
- tests de service Registry et enregistrement de route ;
- Ruff et mypy `--strict` sur `gsie_api.data` ;
- aucune connexion sortante dans les tests.
