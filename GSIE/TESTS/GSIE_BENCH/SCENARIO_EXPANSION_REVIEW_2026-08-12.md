# Revue d'expansion des scénarios GSIE-Bench - 12 août 2026

## Verdict

Les trois cas Parelle utilisés dans la première ébauche étaient utiles pour
tester le runner, mais ils ne constituaient pas des diagnostics stationnels
complets. Ils ne représentaient que quelques variables de pédologie : pH,
profondeur et engorgement.

Ils sont donc conservés comme **référence historique / micro-suite technique**
et ne peuvent pas être présentés comme trois vérités Gold forestières.

Le catalogue candidat est porté en version `0.2.0` et utilise trois dossiers
BTS comme sources internes à relire :

1. Forêt domaniale du Longeyroux, placette EIL, pessière de plateau granitique ;
2. Diagnostic autoécologique du hêtre en moyenne montagne ;
3. Hêtraie régulière de la forêt domaniale de la Vergne avec inventaire,
   régénération et analyse du martelage.

Le statut reste `pending_expert_review`. L'enrichissement ne certifie aucune
réponse automatiquement.

## Pourquoi l'ancienne tranche était insuffisante

Un diagnostic stationnel forestier doit relier au minimum :

- identité de la propriété, massif, unité de gestion et emprise ;
- altitude, position topographique, pente, exposition, vent et microrelief ;
- climat, période de référence, pluviométrie, température, saison de
  végétation, gel, neige et déficit hydrique ;
- roche mère, horizons, profondeur prospectée et profondeur exploitable,
  texture, structure, éléments grossiers, pH et méthode de mesure ;
- drainage, hydromorphie, régime hydrique, RU/RUM et obstacles racinaires ;
- humus, flore indicatrice, gradients hydrique/trophique/lumineux ;
- composition, origine, régime, traitement, âge, recouvrement, densité,
  surface terrière, hauteurs, diamètres, volume et échantillonnage ;
- qualité technologique, défauts, état sanitaire, stabilité et risques ;
- régénération, densité, répartition, qualité, concurrence et gibier ;
- historique des plantations, coupes, travaux, chablis et perturbations ;
- objectifs, contraintes, facteurs limitants, alternatives, actions et horizon
  de gestion ;
- méthode d'inventaire, formules de calcul, valeurs estimées et incertitudes.

## Correspondance des trois nouveaux candidats

| Candidat | Ce qu'il apporte | Ce qui manque encore avant Gold |
|---|---|---|
| `gold.longeyroux.001` | Plateau granitique, altitude 901 m, climat régional, vent, dysmoder, flore acidiphile, épicéa, G/N/hauteurs/diamètres, chablis et risques de tassement | âge, pH, texture, profondeur utile, RU mesurée, régénération, inventaire biodiversité, classe stationnelle validée |
| `gold.hetre.002` | Autécologie, altitude 900-1100 m, climat frais, RUM 175 mm, dysmoder, flore, couvert, régénération, abroutissement, changement climatique | station exacte, coordonnées, pH/méthode, inventaire dendrométrique, protocole climatique, seuils 2050 validés |
| `gold.vergne.003` | Futaie régulière, placette 900 m2, N/G/Hdom/volume, âge 80-90 ans, régénération 15 000-20 000 tiges/ha, qualité, gibier, martelage et trajectoire 15 ans | pédologie, climat, coordonnées, tarif de cubage, validation du volume mobilisable, prix, classe de fertilité et prescriptions opérationnelles |

## Schéma v2 utilisé

Chaque scénario possède maintenant les sections suivantes dans `inputs` :

```text
schema_version: station_diagnostic.v2
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

La section `provenance` sépare explicitement les valeurs :

- `observed` : observées ou mesurées dans le dossier ;
- `inferred` : déductions argumentées ;
- `hypothesis` : hypothèses à confirmer ;
- `missing` : données absentes ;
- `review_required` : points à trancher par l'expert.

Une donnée absente n'est pas remplacée silencieusement par une valeur par
défaut. Les variations de robustesse modifient une seule famille de preuves
à la fois et conservent le lignage vers le scénario parent.

## Qualification juridique et provenance

Les documents BTS sont traités comme des sources internes fournies par le
Fondateur. Le catalogue ne copie aucun PDF externe, ne déclenche aucun FETCH
et ne redistribue pas les documents. Leur régime est
`owner_provided_internal_pending_expert_review` jusqu'à validation explicite
de la provenance, de l'auteur, du droit d'annotation et du périmètre de
publication.

La publication Parelle reste classée `citation_and_derived_annotation_only`.
Elle ne sert plus de fondation unique aux trois Gold candidats. Elle peut
rester une micro-suite Silver ou un contrôle historique de l'engorgement entre
deux chênes blancs.

## Décision de gouvernance

- les nouveaux scénarios sont préparés, pas certifiés ;
- les familles de provenance restent visibles au relecteur ;
- le runner Closed reste bloqué tant que les scénarios sont
  `pending_expert_review` ;
- une relecture indépendante doit valider les seuils, les unités, les calculs,
  les alternatives acceptables et les facteurs limitants ;
- aucune IA, ingestion non qualifiée ou promotion automatique n'est autorisée
  par cette revue.

## Sources locales exploitées

- `E:\Documents\bts\FICHE DE DIAGNOSTIC STATIONNEL camille (Version Intégrée et Approfon.pdf` ;
- `E:\Documents\bts\Fiche Diagnostic Forestier Plus fiche térrain vierge.docx` ;
- `E:\Documents\bts\EIL Carto\Diagnostic_stationnel_Longeyroux_Placette_EIL.docx` ;
- `E:\Documents\bts\EIL Carto\Info pour Diagnostic stationnel.docx` ;
- `E:\Documents\bts\bio\Diagnostic stationnel Camille Perraudeau.docx` ;
- `E:\Documents\bts\Référentiel Par Défaut + Fiche Terrain A4 — Gradients Autoécologiques.docx` ;
- `E:\Documents\bts\pro madeyre\Parcelle forêt Domanial de la Vergne\Analyse de parcelle forestière.docx` ;
- `E:\Documents\bts\QGIS PROJET FIN D'ANNER\Réalisation d’un conseil sylvicole pour un propriétaire.pdf` ;
- `E:\Documents\bts\dendro\Dendro4-2009.docx` pour les principes de cubage et la
  distinction entre estimation, volume commercial et volume de référence ;
- `E:\Documents\bts\bio\Fiches_revision_pathogenes_forestiers_BTSA.docx` pour
  le registre des risques sanitaires à qualifier, sans transformer une liste
  de pathogènes en diagnostic de présence.
