# Quintessences — Property-Based Testing & Fuzzing Plan

## Objectif

Compléter les tests déterministes existants par des tests qui cherchent activement des contre-exemples. Le but n'est pas d'augmenter artificiellement le nombre de tests, mais de vérifier les invariants GSIE sur des espaces d'entrées trop grands pour être couverts manuellement.

## Principe

Un test property-based doit exprimer une propriété stable, par exemple :

- rejouer deux fois une opération idempotente produit le même état métier ;
- un UUID appartenant à un autre tenant n'est jamais visible ;
- une transformation CRS aller-retour reste dans une tolérance définie ;
- une recommandation ne dépasse pas la confiance de sa preuve sans règle explicite ;
- sérialiser puis désérialiser une ressource conserve les champs contractuels ;
- une donnée invalide est rejetée explicitement et ne devient jamais une valeur plausible inventée.

## Outil Python recommandé

**Hypothesis** est le candidat prioritaire pour GSIE/API car il s'intègre directement à pytest et permet le shrinking automatique des cas défaillants.

État actuel : **À INTÉGRER**. Ne pas considérer Hypothesis installé tant que `pyproject.toml` et le lockfile n'ont pas été mis à jour et que la CI n'a pas validé la suite.

## Priorité 1 — frontières de validation

Cibles :
- schémas Pydantic ;
- UUID ;
- timestamps ;
- enums ;
- chaînes limites ;
- listes vides / gigantesques bornées ;
- JSON imbriqué ;
- champs optionnels ;
- valeurs numériques extrêmes, NaN/Inf lorsque la couche peut les recevoir.

Propriétés :
1. aucune exception interne 500 pour une entrée utilisateur invalide ;
2. rejet déterministe ;
3. message d'erreur non sensible ;
4. aucune mutation partielle persistée après rejet.

## Priorité 2 — géospatial

Générer ou muter :
- latitude > 90 / < -90 ;
- longitude > 180 / < -180 ;
- géométries vides ;
- anneaux non fermés ;
- auto-intersections ;
- multipolygones complexes ;
- coordonnées très proches ;
- CRS incompatibles ;
- géométries très grandes mais bornées pour éviter un DoS du runner.

Propriétés :
- validation explicite ;
- pas de crash natif ;
- pas de consommation non bornée ;
- conservation du CRS/unité lorsque requis ;
- résultat géométrique valide ou échec explicite.

## Priorité 3 — idempotence et concurrence

Relier principalement à INV-004 et INV-005.

Scénarios :
- même requête répétée N fois ;
- retries avec ordre modifié ;
- création concurrente du même identifiant ;
- création concurrente avec même UUID mais type racine différent ;
- transaction interrompue entre resource et sous-type ;
- retry après timeout alors que le premier commit a réellement réussi.

Propriétés :
- une seule entité métier finale lorsque l'opération est idempotente ;
- aucune resource orpheline ;
- aucun sous-type orphelin ;
- collision sémantique détectée explicitement ;
- état final cohérent après rollback/retry.

## Priorité 4 — multi-tenant / RLS

Générer :
- organisations A/B ;
- workspaces A1/A2/B1 ;
- ressources réparties aléatoirement ;
- identifiants valides provenant d'un autre périmètre ;
- soft-delete ;
- combinaisons scopes/roles.

Propriété principale :

> Une requête exécutée dans le contexte du tenant T ne révèle aucune information sur une ressource hors périmètre, y compris via existence/non-existence, relations, recherche, export ou erreur différenciable non prévue.

## Priorité 5 — sérialisation / contrats

Cibles :
- Pydantic ↔ JSON ;
- OpenAPI ;
- DB ↔ modèle ;
- export/import GeoSylva ;
- événements ;
- messages de synchronisation.

Propriétés :
- round-trip stable ;
- champs obligatoires préservés ;
- version de schéma explicite ;
- inconnues traitées selon la politique documentée ;
- aucune perte silencieuse.

## Priorité 6 — calculs scientifiques

Le property-based ne remplace pas la validation scientifique. Il sert à vérifier les propriétés structurelles :
- monotonie lorsqu'elle est scientifiquement garantie ;
- bornes physiques ;
- invariance d'unité ;
- stabilité numérique ;
- comportement sur données absentes ;
- reproductibilité avec seed/version identiques.

Chaque propriété scientifique doit citer sa justification ; ne jamais inventer une loi pour satisfaire un test.

## Fuzzing sécurité

Cibles défensives, uniquement sur code/environnement contrôlé :
- paramètres URL ;
- noms de fichiers et chemins ;
- payloads JSON ;
- uploads ;
- WKT/GeoJSON ;
- XML/GRIB métadonnées lorsque pertinent ;
- headers ;
- WebSocket messages ;
- endpoints d'import.

Classes à rechercher :
- path traversal ;
- injection ;
- parsing différentiel ;
- crash ;
- consommation CPU/RAM disproportionnée ;
- erreurs révélant des données internes ;
- bypass de validation.

## Anti-DoS du pipeline de test

Le fuzzing lui-même doit être borné :
- taille maximale des payloads générés ;
- deadline adaptée ;
- nombre d'exemples par profil ;
- corpus de régression conservé ;
- tests lourds séparés de la CI rapide.

Profils proposés :
- `smoke`: 25–50 exemples ;
- `ci`: 100–300 exemples ;
- `nightly`: 1 000+ lorsque le temps le permet ;
- `beta`: campagnes ciblées longues sur composants critiques.

## Structure de tests proposée

```text
GSIE/API/tests/property/
  test_contract_properties.py
  test_idempotency_properties.py
  test_tenant_isolation_properties.py
  test_geo_properties.py
  test_serialization_properties.py
  test_scientific_invariants.py
```

## Critères d'acceptation de la première étape

1. Hypothesis ajouté comme dépendance dev avec lockfile cohérent.
2. CI verte.
3. Au moins 5 propriétés liées à des `INV-*`.
4. Au moins un test utilise PostgreSQL réel pour concurrence/intégrité.
5. Tout contre-exemple corrigé devient test de non-régression durable.
6. Les seeds/cas minimisés sont conservés lorsque nécessaire.

## Mesure de valeur

Suivre :
- nombre de contre-exemples uniques découverts ;
- P0/P1/P2 évités avant release ;
- invariants passant de MISSING/PARTIAL à COVERED ;
- temps CI ajouté ;
- faux positifs ;
- régressions redécouvertes.

Le succès n'est pas « 10 000 cas générés ». Le succès est de découvrir tôt des états que les tests manuels n'avaient pas envisagés.
