# Audit qualité des 14 moteurs et de la chaîne GSIE — 2026-08-13

## Verdict

Les 14 moteurs disposent d'un module Python et d'un contrat API v1. La qualité
des contrats et des garde-fous est déjà solide, mais l'intégration automatique
des données dans un contexte stationnel complet reste une tranche distincte.
La rapidité n'est pas utilisée comme critère de passage avant la fiabilité,
la provenance et la validation.

## Matrice de maturité

| Moteur | Fonction actuelle | Persistance / branchement | Limite à traiter |
|---|---|---|---|
| Evidence | Qualification A–F, conflits, anti-invention | Pipeline Evidence → Knowledge | Qualification de toutes les sources réelles |
| Knowledge | Graphe, ingestion acceptée, révisions | PostgreSQL / Apache AGE | Alimenter le graphe avec des sources canoniques qualifiées |
| GIS | Cadastre et altitude IGN réels | Requête directe | Compléter les couches et le contexte stationnel |
| Climate | Observations Météo-France et limites physiques | Requête directe ; pas d'état par défaut | Versionner snapshots et qualité temporelle |
| Pedology | SoilGrids réel, unités et bornes | Requête directe ; FETCH séparé | Relier le micro-extrait WCS à un contexte explicite |
| Botanical | GBIF/TAXREF, indigénat, pipeline de preuve | PostgreSQL pour connaissances acceptées | Distinguer strictement espèces, occurrences et taxonomie |
| Correlation | Matrices, Pearson/Spearman, diagnostics | Calcul typé | Alimenter automatiquement les variables sourcées |
| Forest Dynamics | Indicateurs dendrométriques et dynamique | Calcul pur | Relier aux observations GeoSylva versionnées |
| Reasoning | Chaînage avant borné, règles explicables | Règles Knowledge possibles ; sortie non persistée | Récupération et qualification serveur des règles |
| Diagnostic | Synthèse contraintes/atouts/risques | Diagnostic persisté | Hydratation automatique du contexte |
| Recommendation | Alternatives justifiées et contournables | Recommandations et décisions persistées | Vérifier toutes les règles scientifiques de décision |
| Validation | Contrôles constitutionnels et blocages | Blocages/partiels persistables avec session | Couverture de toutes les sorties de l'orchestration |
| Simulation | Projections et scénarios | Calcul sans état | Brancher données versionnées et hypothèses explicites |
| Learning | Signaux d'apprentissage, propositions non autonomes | Alimenté par blocages/écarts validés | Raccord complet à l'orchestration et validation humaine |

## Preuves exécutées

- 316 tests du cœur moteurs/pipelines passants, 1 test ignoré explicitement ;
- 166 tests des moteurs domaine et adapters passants ;
- 44 tests de configuration et de cloisonnement passants ;
- 14 tests de pipeline/orchestration après renforcement passants ;
- Ruff et mypy strict propres sur les modules modifiés ;
- aucune donnée de production utilisée par les tests locaux.
- l'audit structurel `GSIE/API/scripts/audit_engines.py` confirme 14/14
  moteurs : package, schémas, routeur, point d'entrée et montage FastAPI.
- la campagne unitaire complète post-corrections passe 2 929 tests, avec 63
  tests explicitement ignorés par leurs marqueurs d'environnement et 13
  avertissements non bloquants.

## Chaîne d'orchestration vérifiée

```text
POST /api/v1/orchestration/analyse
    ↓
Reasoning
    ↓
Diagnostic persisté
    ↓
Recommendation persistée
    ↓
Validation avec la session DB partagée
    ↓
Réponse complète et traçable
```

La validation de l'orchestration reçoit désormais la même session DB que les
étapes précédentes. Une sortie bloquée ou partielle peut donc être persistée et
transmise au Learning Engine ; l'ancien appel sans session perdait cette trace.
Le niveau de preuve de la recommandation est également propagé depuis le
diagnostic au lieu d'être forcé à `B`.

## Cloisonnement des données

Le contrat d'environnement est décrit dans
`GSIE/API/docs/ENVIRONNEMENTS_DONNEES.md`. Les contrôles imposent un rôle et un
namespace distincts pour test, benchmark, staging et production. Les volumes
Compose sont nommés avec le namespace ; les bases et buckets des exemples sont
également suffixés par rôle. Le volume historique de développement est
conservé et aucune suppression ou migration implicite n'est exécutée.
Le profil HA propage aussi `GSIE_DATABASE_ROLE` et `GSIE_DATA_NAMESPACE` à
chaque replica ; il ne peut donc pas réutiliser silencieusement l'espace d'un
autre environnement.
La preuve `analysis_run` est append-only côté PostgreSQL (trigger de mutation
interdite vérifié en intégration), pas seulement protégée par convention dans
le service Python.

## Tranches suivantes

1. Construire le service d'hydratation `station_id → StationContexte` à partir
   de sources Registry qualifiées.
2. Ajouter des tests de non-régression DB réelle par environnement, avec
   checksum du manifeste et tête Alembic dans chaque preuve.
3. Compléter la persistance de l'analyse complète et son identifiant d'exécution.
4. Introduire les templates et vérificateurs par domaine après stabilisation
   des contrats, sans bypass de garde scientifique.
