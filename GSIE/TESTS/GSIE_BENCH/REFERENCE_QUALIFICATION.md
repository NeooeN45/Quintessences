# Qualification des références - GSIE-Bench v0.2

## Statut

Les trois scénarios stationnels enrichis sont des **candidats Gold en attente
de relecture experte**. Ils ne peuvent pas encore alimenter un run Closed
officiel.

## Références locales principales

| Identifiant | Contenu utilisé | Régime actuel |
|---|---|---|
| `bts-eil-longeyroux-placette-2026` | Diagnostic stationnel de la pessière de Longeyroux : climat, topographie, humus, peuplement, risques et inconnues | Source interne fournie par le Fondateur, revue requise |
| `bts-diagnostic-hetre-fagus-2026` | Autécologie et diagnostic du hêtre : climat, RUM, humus, flore, régénération, gibier et adaptation | Source interne fournie par le Fondateur, revue requise |
| `bts-analyse-parcelle-vergne-hetraie-2026` | Hêtraie régulière : placette, dendrométrie, régénération, qualité, martelage, débouchés et trajectoire 15 ans | Source interne fournie par le Fondateur, revue requise |
| `bts-fiche-diagnostic-stationnel-camille-2026` | Trame complète de terrain et diagnostic approfondi : contexte, gradients, pédologie, biodiversité, peuplement et calculs | Source interne fournie par le Fondateur, revue requise |

Les documents exploités sont listés dans
`SCENARIO_EXPANSION_REVIEW_2026-08-12.md`. Aucun octet externe n'a été copié
dans le dépôt et aucun FETCH n'a été déclenché.

## Référence Parelle 2007

La publication Parelle et al. (2007) reste identifiée et citable pour sa
question précise sur la tolérance à l'engorgement de *Quercus robur* et
*Quercus petraea*. Elle est classée :

```text
citation_and_derived_annotation_only
```

Elle ne suffit pas à justifier à elle seule les seuils de pH, les règles de
profondeur, les diagnostics de peuplement ou les recommandations sylvicoles des
trois nouveaux cas. Elle doit donc rester une référence historique ou une
micro-suite Silver distincte.

## Contrôle de complétude

Chaque candidat v0.2 doit contenir les onze sections suivantes :

```text
contexte
topographie
climat
pedologie
flore_biodiversite
peuplement
regeneration
historique
gestion
mesures_et_calculs
provenance
```

La provenance sépare `observed`, `inferred`, `hypothesis`, `missing` et
`review_required`. Cette séparation est obligatoire : une estimation de RU,
un classement stationnel probable ou un risque sanitaire ne doivent pas être
présentés comme des mesures confirmées.

## Points scientifiques à qualifier

1. Vérifier les unités, méthodes et dates de chaque mesure.
2. Compléter pH, texture, horizons, structure, profondeur utile et hydrologie
   du candidat Longeyroux.
3. Vérifier la station exacte, le protocole climatique et les seuils de
   projection du candidat Hêtre.
4. Compléter pédologie, climat, coordonnées et tarif de cubage de la Vergne.
5. Recalculer G, N/ha, volumes, RU/RUM et volumes mobilisables avec une
   méthode adaptée et une tolérance explicitement fixée.
6. Distinguer observation sanitaire, facteur de risque et diagnostic de
   pathogène confirmé.
7. Définir les réponses alternatives acceptables, les abstentions et les
   vetos par famille de tâche.

## Points juridiques et de provenance

Les dossiers BTS sont considérés comme des sources internes fournies par le
Fondateur, mais leur usage dans un jeu fermé, leur transformation et leur
publication éventuelle doivent être confirmés par une décision explicite.
Tant que cette vérification n'est pas archivée, le statut reste
`owner_provided_internal_pending_expert_review`.

## Décision actuelle

```text
Gold candidats : pending_expert_review
Closed officiel : BLOQUÉ
FETCH : non requis et fermé
IA : non autorisée par cette tranche
Promotion : interdite
```

Le blocage du runner est donc attendu et doit rester en place pendant la
relecture experte.
