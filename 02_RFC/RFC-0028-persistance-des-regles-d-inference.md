# RFC-0028 — Persistance et récupération des règles d'inférence

| Champ | Valeur |
|---|---|
| **ID** | RFC-0028 |
| **Statut** | Brouillon — soumis au Fondateur |
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

## 4. Décision proposée

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
- son domaine de validité contient le contexte, ou n'est pas renseigné ;
- son niveau de preuve atteint le plancher demandé par l'appelant.

Une règle dont le domaine de validité **ne contient pas** le contexte n'est pas
retournée. L'extrapolation hors domaine est une invention (`ADR-009`).

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
4. Une variable hors vocabulaire est refusée à l'ingestion, jamais devinée.
5. Une unité non convertible écarte la règle avec un motif, sans comparaison.
6. Le harnais de mutation couvre chacune de ces gardes, et chaque mutation
   est vue survivre avant correctif puis mourir après.

## 8. Périmètre du premier lot

Conformément au principe d'une chaîne complète avant tout élargissement :

**une essence** (chêne sessile), **une variable** (réserve utile maximale),
**un territoire**, de bout en bout — document → fait sourcé → règle dérivée →
observation GeoSylva → conclusion tracée.

Élargir ensuite relève de la répétition, non de la conception.

## 9. Questions ouvertes

1. **Le domaine de validité non renseigné vaut-il « partout » ou « nulle
   part » ?** La proposition retient « partout » pour ne pas bloquer
   l'amorçage, mais l'inverse est plus sûr. Arbitrage du Fondateur.
2. **Faut-il un niveau de preuve plancher par défaut**, ou l'appelant doit-il
   toujours le déclarer ?
3. **Que faire d'une règle `accepted` dont la source est invalidée
   ultérieurement ?** `CON-010` impose de réviser sans supprimer — le
   comportement de sélection pendant la révision reste à définir.
