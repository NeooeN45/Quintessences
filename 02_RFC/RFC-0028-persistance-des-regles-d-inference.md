# RFC-0028 — Persistance et récupération des règles d'inférence

| Champ | Valeur |
|---|---|
| **ID** | RFC-0028 |
| **Statut** | Validée — `DEC-000038` (2026-07-28) |
| **Auteur** | Architecte, sous autorité du Fondateur |
| **Date** | 2026-07-28 |
| **Périmètre** | Knowledge Engine, Reasoning Engine, moteurs consommateurs |
| **Nature** | Décision d'architecture |
| **Précédents** | `ADR-002` (Temporal Engine), `ADR-009` (garde-fou anti-invention), `GSIE-PROMPT-0017` |

## 1. Objet

Le Reasoning Engine reçoit aujourd'hui ses règles **dans la requête**
(`ReasoningRequest.regles`). L'appelant doit donc les fournir lui-même.

C'était un choix assumé en v1 : `GSIE-PROMPT-0017` note que « le branchement
sur le Knowledge Engine se fera sans rupture de contrat ». Ce branchement n'a
pas été fait.

La présente RFC décide **où vit une règle, comment elle est récupérée, et
comment elle est dérivée d'un fait sourcé**.

## 2. Pourquoi c'est bloquant

Tant que les règles voyagent dans la requête :

1. **GeoSylva devrait embarquer la connaissance sylvicole.** Une application
   de terrain porterait les seuils autécologiques dans son code. Toute
   révision d'un seuil imposerait une mise à jour de l'application sur chaque
   téléphone — ce qui, en pratique, signifie que la connaissance ne serait
   jamais révisée.
2. **Aucune traçabilité de la règle appliquée.** `Conclusion.chaine_inference`
   cite une règle que rien ne permet de retrouver après coup : elle n'existe
   qu'à l'instant de la requête. C'est contraire à `CON-010`.
3. **Le Knowledge Engine ne sert à rien pour le raisonnement.** Il stocke des
   connaissances que le Reasoning Engine ne lit pas.
4. **La numérisation documentaire n'a pas de destination.** Extraire mille
   règles d'un catalogue de stations n'a aucun effet tant que rien ne peut
   les interroger.

## 3. Ce qui existe déjà

Le métamodèle est plus avancé que ne le laisse croire l'état du code.

| Élément | État | Rôle pour une règle |
|---|---|---|
| `ClaimKind.rule`, `ClaimKind.threshold` | présent | une règle **est** une Assertion |
| `RuleSubtype` (inference, scientific, business, regulatory) | présent | nature de la règle |
| `assertion.spatial_scope_id`, `temporal_context_id`, `scale_context_id` | présent | **domaine de validité** |
| `assertion.version`, `lifecycle_status` | présent | versionnement, cycle de vie |
| `assertion_qualifier` (key, value, unit_id) | présent | porter un seuil et son unité |
| `evidence_assessment` | présent | niveau de preuve de la règle |
| `autecology_profile` (variable, value_numeric, unit, evidence_level, source_id) | présent | **le fait dont la règle dérive** |

Rien de tout cela n'est utilisé pour le raisonnement. **La décision porte donc
sur l'usage de structures existantes, non sur leur création.**

## 4. Décision

### 4.1 Une règle est une Assertion, pas une table nouvelle

Une règle est persistée comme `assertion` avec `claim_kind = 'rule'` ou
`'threshold'`, son `rule_subtype`, son domaine de validité par les trois
`*_scope_id`, son niveau de preuve par `evidence_assessment`, et ses
paramètres numériques par `assertion_qualifier`.

Motif : une règle est une affirmation sur le monde. Lui donner un régime
séparé la sortirait de la traçabilité, du versionnement et du cycle de vie qui
s'appliquent à toute affirmation. Elle deviendrait citable sans être révisable
— exactement ce que `CON-010` interdit.

### 4.2 La condition exécutable est **dérivée**, pas stockée

C'est le point central de cette RFC, et le plus discutable.

Deux voies étaient possibles :

| | Stocker la condition (`"reserve_utile_mm < 120"`) | Dériver la condition du fait |
|---|---|---|
| Expressivité | totale | limitée aux formes dérivables |
| Cohérence fait / règle | deux sources de vérité, dérive possible | une seule source |
| Révision d'un seuil | modifier le fait **et** la chaîne | modifier le fait suffit |
| Surface d'exécution | chaîne exécutable persistée | aucune |

**La dérivation est retenue.** Une chaîne exécutable stockée en base peut
diverger du fait qu'elle est censée traduire : on corrigerait le seuil
autécologique sans corriger la règle, et le moteur continuerait d'appliquer
l'ancien seuil tout en citant la source révisée. Ce mode de défaillance est
silencieux et produit une conclusion fausse mais sourcée — le pire cas pour ce
projet.

La condition est donc **construite à la lecture**, à partir de
`assertion_qualifier` (opérateur, valeur, unité) et du nom de variable
normalisé. Le Reasoning Engine continue de recevoir des `RegleInference` : son
contrat ne change pas.

**Limite assumée** : les règles non dérivables — conjonctions complexes,
conditions non numériques — ne sont pas couvertes par cette RFC. Elles
continuent de passer par `ReasoningRequest.regles`. Une RFC ultérieure
tranchera si le besoin est démontré par des cas réels, pas par anticipation.

### 4.3 Récupération par contexte

Le Knowledge Engine expose une nouvelle opération : récupérer les règles
applicables à un contexte (essence, territoire, variables disponibles).

La sélection retient une règle si :

- son `claim_kind` est `rule` ou `threshold` ;
- son `lifecycle_status` est `accepted` ;
- son domaine de validité est **renseigné** et **contient** le contexte ;
- son niveau de preuve atteint le plancher demandé par l'appelant, s'il en a
  déclaré un (§9.2 — aucun plancher par défaut).

Une règle dont le domaine de validité **ne contient pas** le contexte n'est pas
retournée. L'extrapolation hors domaine est une invention (`ADR-009`).

**Un domaine non renseigné vaut « nulle part », jamais « partout ».**

Le silence ne peut pas valoir universalité. Une règle extraite du catalogue de
stations de Haute-Normandie ne porte pas la mention « ceci vaut en
Haute-Normandie » : c'est le titre du document, pas une phrase du texte. Si le
silence valait « partout », cette règle serait appliquée à une chênaie verte
de l'Hérault, et la conclusion citerait le catalogue normand — source réelle,
chaîne complète, niveau de preuve B. Personne ne verrait l'erreur.

Les deux échecs possibles ne se valent pas :

| | Conséquence pour le forestier |
|---|---|
| Silence = « partout » | une réponse **fausse portant une citation vérifiable** — il a toutes les raisons de la croire |
| Silence = « nulle part » | **aucune réponse** — il consulte son catalogue papier, comme aujourd'hui |

Une décision sylvicole engage des décennies. Une absence de réponse est
récupérable ; un conseil faux et sourcé ne l'est pas.

Le coût de ce choix est plus faible qu'il n'y paraît : **la règle hérite du
domaine de sa source à l'ingestion**. Un catalogue de stations est régional par
construction, un guide CNPF couvre une région, une publication déclare sa zone
d'étude. `source_id` étant déjà obligatoire partout, le territoire est toujours
connaissable — il n'a pas à être saisi à la main.

Reste possible le cas d'une connaissance véritablement universelle : elle
déclare un domaine explicite (« national », « toutes zones »), jamais un champ
vide. **Déclarer l'universalité est un acte ; laisser le champ vide est un
oubli.** Le moteur ne doit pas confondre les deux.

### 4.3 bis Le territoire devient obligatoire sur les deux types porteurs

Le schéma exige déjà un territoire là où il définit l'objet :
`station_type.validity_zone_description`, `fertility_class.calibration_region`,
`provenance_material.provenance_region`.

Il ne l'exige pas sur `silvicultural_rule` ni `autecology_profile` — c'est-à-dire
précisément sur les deux types dont dérivent les règles appliquées à une
station. Cette asymétrie ressemble à un oubli plutôt qu'à une décision.

La présente RFC l'aligne : le territoire devient un champ obligatoire de ces
deux types. C'est une modification de contrat, elle relève donc de cette RFC et
non d'un correctif.

### 4.4 Le vocabulaire contrôlé fait le lien

`autecology_profile.variable` est du texte libre ; la condition référence un
nom de fait. Rien ne garantit aujourd'hui que « RUM », « réserve utile » et
`reserve_utile_mm` désignent la même grandeur.

Les types `vocabulary` et `controlled_term` existent et ne sont pas utilisés.
Cette RFC décide qu'ils **deviennent obligatoires** pour toute variable
entrant dans une règle : une variable hors vocabulaire est refusée à
l'ingestion, jamais devinée.

### 4.5 Les unités sont réconciliées ou la règle est refusée

Si l'unité du fait et celle de l'observation diffèrent, la conversion est
appliquée quand elle est connue, et **la règle est écartée avec un motif**
sinon. Comparer sans convertir est interdit.

## 5. Ce qui ne change pas

- `ReasoningRequest.regles` reste accepté. Une requête qui fournit ses règles
  continue de fonctionner à l'identique. La récupération depuis le Knowledge
  Engine s'ajoute, elle ne remplace pas.
- Le contrat de `RegleInference` est inchangé.
- Le Diagnostic Engine n'arbitre toujours aucune contradiction
  (`SCIENTIFIC_CONSTITUTION` S-3) : deux règles contradictoires applicables
  sont **toutes deux** retournées, et présentées.

## 6. Conséquences

**Favorables**

- GeoSylva n'embarque plus aucune connaissance sylvicole ;
- réviser un seuil met à jour le comportement de tous les clients sans
  déploiement ;
- `chaine_inference` devient réellement remontable jusqu'à la source ;
- la numérisation documentaire acquiert une destination opérationnelle.

**Coûts**

- le vocabulaire contrôlé devient un préalable à toute ingestion de règle :
  c'est un travail de fond, non contournable ;
- les règles complexes restent hors périmètre, donc portées par l'appelant ;
- un contexte de requête plus riche est nécessaire pour la sélection.

**Risque principal**

Une sélection trop permissive retournerait des règles hors domaine, et le
Reasoning Engine produirait des conclusions extrapolées avec une source
valide. C'est le mode de défaillance à surveiller : **une conclusion fausse
mais sourcée est plus dangereuse qu'une absence de conclusion.**

Mitigation : la sélection refuse par défaut, et un test d'invariant vérifie
qu'aucune règle hors domaine n'est jamais retournée.

## 7. Critères d'acceptation

1. Une règle ingérée depuis un document est récupérable par contexte, avec sa
   source et son niveau de preuve.
2. Une requête de raisonnement **sans** `regles` produit la même conclusion
   qu'une requête les portant explicitement — vérifié sur un cas réel.
3. Une règle hors domaine de validité n'est jamais retournée — test
   d'invariant, vérifié en le débranchant.
4. Une règle **sans domaine déclaré** n'est jamais retournée non plus, et
   l'ingestion refuse de créer une règle sans territoire (§4.3, §4.3 bis).
5. Une variable hors vocabulaire est refusée à l'ingestion, jamais devinée.
6. Une unité non convertible écarte la règle avec un motif, sans comparaison.
7. Toute réponse porte son `evidence_level_plancher` — une réponse qui
   l'omettrait est un défaut, pas une commodité (§9.2).
8. Invalider une source permet d'**énumérer les conclusions passées** qui
   citaient ses règles, et la règle cesse d'être sélectionnée dans le même
   geste (§9.3).
9. Le harnais de mutation couvre chacune de ces gardes, et chaque mutation
   est vue survivre avant correctif puis mourir après.

## 8. Périmètre du premier lot

Conformément au principe d'une chaîne complète avant tout élargissement :

**une essence** (chêne sessile), **une variable** (réserve utile maximale),
**un territoire**, de bout en bout — document → fait sourcé → règle dérivée →
observation GeoSylva → conclusion tracée.

Élargir ensuite relève de la répétition, non de la conception.

## 9. Trois arbitrages, tranchés sur la qualité pour l'utilisateur

Ces trois points étaient ouverts. Le Fondateur a fixé le critère de
décision : **ce qui sert le mieux le forestier**. Ils sont tranchés ci-dessous
selon ce seul critère.

### 9.1 Domaine non renseigné → « nulle part »

Tranché au §4.3. Une absence de réponse est récupérable ; un conseil faux
portant une citation vérifiable ne l'est pas.

### 9.2 Pas de plancher de preuve par défaut, mais un niveau toujours affiché

Deux erreurs possibles, et une seule est grave.

Refuser par défaut tout ce qui est sous un certain niveau priverait le
forestier d'une information qu'il sait pondérer lui-même. S'il n'existe qu'un
avis d'expert non publié (niveau E) sur une station, **le lui dire est plus
utile que se taire** — à condition qu'il voie que c'est du E.

Le danger n'a jamais été la connaissance faible : c'est la connaissance faible
**présentée comme forte**. `Conclusion.evidence_level_plancher` traite déjà ce
risque, à condition d'être exposé.

Décision :

- aucun plancher par défaut — tout ce qui est applicable est retourné ;
- `evidence_level_plancher` est **obligatoire dans la réponse**, jamais
  facultatif ni omissible ;
- l'appelant peut relever le plancher explicitement, jamais l'inverse ;
- deux règles applicables de niveaux différents sont **toutes deux**
  retournées : c'est ainsi qu'une contradiction devient visible plutôt
  qu'arbitrée (`SCIENTIFIC_CONSTITUTION` S-3).

### 9.3 Source invalidée : la règle sort du service, et le forestier est prévenu

`CON-010` impose de réviser sans supprimer. Reste à définir l'effet sur la
sélection, et surtout sur les conclusions déjà rendues.

Décision, en deux temps :

**1. La règle cesse immédiatement d'être sélectionnée.** Son
`lifecycle_status` passe à `deprecated`. Aucune conclusion nouvelle ne peut
s'appuyer sur une règle dont la source est invalidée.

**2. Les conclusions passées qui la citaient restent retrouvables, et sont
signalées.** C'est le point décisif pour l'utilisateur, et le plus facile à
négliger.

Un forestier a martelé une parcelle en mars sur la foi d'une recommandation.
En septembre, la source de la règle est invalidée. Un outil qui se corrige
silencieusement le laisse dans l'erreur ; un outil honnête lui dit : *« le
conseil du 12 mars reposait sur une source depuis invalidée ».*

`chaine_inference` cite les règles utilisées et les révisions sont
append-only : la recherche inverse — quelles conclusions citaient cette
règle — est donc possible sans structure nouvelle. Cette RFC la rend
**obligatoire** : invalider une source impose de pouvoir énumérer les
conclusions affectées.

C'est ce qui distingue un outil d'aide à la décision d'un moteur qui donne des
réponses. Le forestier reste le décideur (`GSIE-CON-001`) — encore faut-il
qu'il apprenne quand le sol se dérobe sous une décision passée.

## 10. Ce que cette RFC ne tranche pas

- la représentation des règles non dérivables (conjonctions, conditions non
  numériques) — reportée jusqu'à ce que des cas réels la justifient ;
- le format d'extraction documentaire vers `autecology_profile` — relève du
  chantier d'ingestion, pas de l'architecture du raisonnement ;
- l'ordre de présentation de deux règles contradictoires — question
  d'interface, à trancher avec un forestier devant l'écran.
