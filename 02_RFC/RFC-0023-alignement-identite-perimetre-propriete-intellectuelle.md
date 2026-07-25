# RFC-0023 — Alignement de l'identité, du périmètre et de la propriété intellectuelle

| Champ | Valeur |
|---|---|
| **Statut** | Proposé — EN_REVUE, nouveau contre-audit requis |
| **Auteur** | Direction technique, sous autorité du Fondateur |
| **Date** | 2026-07-24 |
| **Décision liée** | `DEC-000033` — orientation uniquement, aucune adoption |
| **Périmètre** | Quintessences, GSIE, Forge, Hub et applications |
| **Nature** | Révision constitutionnelle préparatoire |
| **Snapshot de rédaction** | `77639a07beb2b5445134920b6f89ad3db5805630` |

## 1. Résumé

La présente RFC propose de réaligner les textes fondateurs avec l'identité
déjà décidée de l'écosystème :

- **Quintessences** est le programme de recherche et développement, la
  marque, l'écosystème technologique et la plateforme commune ;
- **GSIE** signifie **General System Intelligence Engine** et constitue le
  socle scientifique, documentaire, géospatial, de simulation et
  d'intelligence commun ;
- **GeoSylva** est la verticale forestière ;
- **Ignis** est la verticale incendie ;
- **Forge** est la fabrique de données fiables et versionnées ;
- **Hub** est l'interface de simulation, d'exploration, de visualisation et
  de coordination.

Elle propose également de remplacer l'obligation générale d'open source par
une politique de propriété intellectuelle décidée par composant, sans
affaiblir la transparence scientifique, la traçabilité, la sécurité ni les
droits des utilisateurs.

Cette RFC ne modifie aucun texte constitutionnel à elle seule et ne porte pas
le texte cible des nouvelles éditions. Les éditions complètes, leurs
différences et leur séquence de publication doivent être portées par
`RFC-0025`. Aucune décision ni publication d'un document `Locked` ne peut être
fondée sur la seule présente RFC.

## 2. Problème

### 2.1 Contradiction d'identité

Les documents verrouillés `GSIE-FND-001` et `GSIE-FND-002` définissent encore
GSIE comme **GeoSylva Intelligence Engine**, limité aux écosystèmes
forestiers.

Les décisions `DEC-000006` et `DEC-000013`, le `README.md` et l'architecture
courante définissent au contraire :

`Quintessences → GSIE général → verticales environnementales`

La décision plus récente ne peut pas corriger seule un texte constitutionnel
supérieur. La contradiction est donc réelle même si l'architecture et le
code ont déjà commencé à suivre la nouvelle identité.

### 2.2 Absence d'une vision canonique de niveau 0

La hiérarchie documentaire place la Vision au-dessus de la Constitution,
mais le registre `SOURCE_OF_TRUTH_REGISTRY.json` ne référence aucune vision
canonique actuelle. `VISION_HISTORY.md` ne contient que les visions
forestières V1 et V1.1 et reste un historique, pas une autorité normative.

Sans vision canonique, les futures décisions risquent de s'appuyer sur des
conversations, des brouillons ou des documents de rang inférieur.

### 2.3 Contradiction de propriété intellectuelle

`GSIE-CON-008` présente GSIE comme open source. Le dépôt racine déclare
actuellement une licence propriétaire, tandis que le Fondateur a validé une
stratégie dans laquelle certaines technologies peuvent rester fermées et
des services cloud propriétaires peuvent être utilisés temporairement.

Le projet ne dispose donc pas d'une règle cohérente permettant de décider ce
qui est ouvert, partagé, licencié, exploité comme service ou conservé comme
actif propriétaire.

## 3. Objectifs

1. créer une vision de niveau 0, actuelle, explicite et versionnée ;
2. aligner l'identité constitutionnelle avec Quintessences et GSIE ;
3. définir un périmètre environnemental général sans disperser les efforts ;
4. clarifier les rôles de Forge, GSIE, GeoSylva, Hub et Ignis ;
5. permettre une politique de licence adaptée à chaque composant ;
6. préserver les principes scientifiques, documentaires et humains ;
7. rendre détectables automatiquement les anciennes définitions
   contradictoires.

## 4. Non-objectifs

Cette RFC ne :

- définit pas l'autonomie décisionnelle de GSIE, traitée par `RFC-0024` ;
- choisit pas le prix, l'abonnement ou le modèle commercial détaillé ;
- autorise pas l'ouverture de Forge à des partenaires ;
- transforme pas automatiquement Hydro, Flora ou Artemis en applications
  autonomes ;
- autorise pas la revente des données des utilisateurs ;
- réduit pas les exigences de preuve, d'explicabilité ou de traçabilité ;
- modifie pas directement un document `Locked`.

## 5. Vision proposée de niveau 0

Un document racine `VISION.md` devient la source canonique de niveau 0. Il
porte au minimum la vision suivante :

> Quintessences est un programme de recherche et développement, une marque,
> un écosystème technologique et une plateforme commune destinés à rattraper
> et dépasser le retard technologique des métiers de l'environnement.
> Quintessences relie des données fiables et documentées, des connaissances
> scientifiques, des moteurs spécialisés, des diagnostics, des
> recommandations, des simulations, des corrélations avancées, des services
> d'intelligence artificielle et des interfaces professionnelles.

> GSIE en est le socle scientifique et intelligent commun. Les applications
> et verticales rendent ce socle utile sur le terrain, dans la recherche,
> l'analyse, la formation, la simulation et la coordination opérationnelle.

La Vision conserve les engagements suivants :

- sécurité humaine ;
- qualité avant vitesse ;
- science et terrain avant affirmation ;
- accessibilité des outils ;
- données utilisateurs et dérivés identifiants ou ré-identifiables jamais
  cédés ni exploités par un tiers pour ses finalités propres, conformément
  au §7.2.1 ;
- incertitudes et limites toujours visibles ;
- pérennité et indépendance de la direction scientifique.

La Vision canonique et la Constitution appartiennent au même **bloc
fondateur**, avec une autorité de registre égale à `100`.

La Vision exprime la mission, l'ambition et le périmètre durable. La
Constitution définit les lois et garde-fous applicables. En cas de
contradiction, la Constitution prévaut jusqu'à révision formelle et cohérente
du bloc fondateur.

Le registre attribue à `VISION.md` un propriétaire `Fondateur`, un état
`canonique` et l'autorité `100`. Sa liste de précédence place la Constitution
avant la Vision uniquement pour résoudre les contradictions au sein du bloc
fondateur.

La revue annuelle de la Vision est un contrôle de fraîcheur sans pouvoir de
modification normative. Toute modification de son sens exige cumulativement :

1. une RFC portant le texte cible complet ;
2. un contre-audit indépendant ;
3. une décision explicite du Fondateur ;
4. une nouvelle édition versionnée ;
5. la conservation de l'édition antérieure ;
6. la mise à jour des sources dépendantes.

Cette règle applique l'arbitrage de `DEC-000033` et résout explicitement la
contradiction interne de `GSIE-CON-000` entre la Vision au niveau documentaire
0 et la Constitution comme plus haute autorité applicable.

## 6. Architecture d'identité proposée

### 6.1 Quintessences

Quintessences regroupe :

- le programme scientifique et technologique ;
- la marque de l'écosystème ;
- la plateforme reliant données, moteurs, IA et interfaces ;
- les méthodes, preuves, standards qualité et actifs communs ;
- les différentes verticales environnementales.

### 6.2 GSIE

GSIE signifie **General System Intelligence Engine**.

GSIE fournit notamment :

- preuves et connaissances versionnées ;
- données géospatiales et environnementales ;
- corrélations et raisonnements traçables ;
- diagnostics et recommandations ;
- modèles et simulations ;
- gestion des incertitudes et domaines de validité ;
- services d'IA spécialisés ;
- API et contrats communs.

GSIE n'est ni une application mobile ni un produit limité à la forêt.

### 6.3 Forge

Forge est la fabrique de données de Quintessences. Elle collecte, préserve,
qualifie, transforme, versionne et publie des capsules de données vers GSIE.
Elle sépare strictement données publiques, privées, quarantaines et
publiables.

Forge est d'abord renforcée pour l'usage interne. Son ouverture à des
partenaires nécessite une décision distincte.

### 6.4 GeoSylva

GeoSylva est la verticale forestière complète de Quintessences :

- application Android de terrain ;
- services forestiers de GSIE ;
- synchronisation et fonctionnement hors ligne ;
- analyses, diagnostics et simulations forestières ;
- visualisations forestières dans le Hub.

### 6.5 Hub

Le Hub est l'interface de simulation, d'exploration et de coordination. Il
combine selon les usages :

- jumeau numérique 3D ;
- carte 2D ;
- schémas et graphes ;
- comparaison de scénarios ;
- vues de formation et de commandement.

### 6.6 Ignis

Ignis est la verticale incendie. Sa première preuve scientifique porte sur
la reproduction d'un incendie historique et la comparaison aux observations
réelles. Les drones, communications alternatives et actions physiques
restent soumis à des décisions et garde-fous spécifiques.

### 6.7 Futurs domaines

L'eau, la flore, la faune et les autres domaines commencent comme données,
moteurs, corrélations et couches de GSIE. Une application autonome n'est
créée qu'après validation d'un utilisateur, d'un problème et d'un parcours
métier distincts.

## 7. Politique de propriété intellectuelle proposée

### 7.1 Décision par composant

Aucune licence unique n'est imposée constitutionnellement à tout
Quintessences. Chaque composant reçoit une décision documentée prenant en
compte :

- intérêt scientifique et reproductibilité ;
- sécurité et souveraineté ;
- droits sur les données et modèles ;
- avantage stratégique ;
- obligations des dépendances ;
- financement et modèle économique ;
- capacité de maintenance.

Les catégories possibles comprennent :

- ouvert et réutilisable ;
- source visible avec droits limités ;
- licence commerciale ;
- service propriétaire ;
- composant interne confidentiel ;
- publication scientifique ou standard ouvert.

### 7.2 Éléments non négociables

Ces obligations s'appliquent quel que soit le régime de licence, le montage
contractuel, la contrepartie, le financeur ou le fournisseur technique.

#### 7.2.1 Protection des données utilisateurs

Les données utilisateurs comprennent les données fournies, observées,
créées ou corrigées par un utilisateur ou pour son compte, notamment les
identifiants, géolocalisations, relevés métier, traces d'usage, annotations
et exports.

La même protection couvre tout dérivé permettant raisonnablement
d'identifier, de distinguer, de profiler ou de ré-identifier une personne,
une organisation, une propriété, une parcelle ou une opération. Sont
notamment concernés les données pseudonymisées, petits agrégats, profils,
inférences, représentations vectorielles, extraits, jeux dérivés et modèles
susceptibles de mémoriser ces informations.

Il est interdit :

- de vendre, céder, concéder sous licence, louer, échanger, partager,
  transférer ou mettre ces données ou dérivés à disposition d'un tiers pour
  ses finalités propres ;
- de contourner cette interdiction par une prestation gratuite, un échange
  de services, un financement, un produit dérivé, une anonymisation
  insuffisante ou une contrepartie indirecte ;
- de permettre à un fournisseur, partenaire ou financeur de les réutiliser
  pour entraîner ses modèles, constituer son propre corpus, profiler les
  utilisateurs, faire de la publicité ou développer une offre concurrente ;
- de traiter les données utilisateurs comme un actif librement transférable
  lors d'une cession d'activité, d'actifs ou de contrôle.

Un traitement par un tiers n'est pas une cession uniquement si toutes les
conditions suivantes sont satisfaites :

1. il est strictement nécessaire à une finalité demandée par l'utilisateur
   ou au fonctionnement documenté du service ;
2. le tiers agit exclusivement sur instruction de Quintessences ou de
   l'utilisateur concerné, sans finalité propre ni droit de réutilisation ;
3. les données sont minimisées et l'accès est limité dans le temps ;
4. un contrat impose confidentialité, sécurité, suppression ou restitution,
   absence d'entraînement et droit d'audit ;
5. le flux, sa finalité, ses catégories de données, son destinataire et sa
   durée de conservation sont inscrits dans un registre auditable ;
6. les droits applicables d'accès, d'export, de correction et de suppression
   restent effectifs.

Restent possibles, sans créer de droit général d'exploitation pour un tiers :

- un export ou partage déclenché par l'utilisateur vers un destinataire et
  une finalité qu'il choisit explicitement ;
- une communication strictement imposée par la loi, documentée et limitée
  au minimum requis ;
- la publication de statistiques réellement anonymes après une analyse
  documentée du risque de ré-identification et une approbation indépendante.

La pseudonymisation seule n'est jamais considérée comme une anonymisation.
Les données dont les droits ne sont pas formellement vérifiés restent en
quarantaine privée et ne sont ni publiées, ni partagées, ni utilisées pour
entraîner un modèle.

Une opération de cession d'activité, d'actifs ou de contrôle ne transfère
aucun droit d'exploitation propre sur les données utilisateurs. Toute
continuité de service exige le maintien des mêmes finalités et garanties,
ainsi que le renouvellement ou transfert valable de la relation avec
l'utilisateur ; à défaut, les données restent isolées ou sont supprimées
selon les obligations applicables.

#### 7.2.2 Absence d'exclusivité

Aucun organisme, client, partenaire ou financeur ne reçoit une exclusivité,
totale ou partielle, sur :

- Quintessences, GSIE ou Forge ;
- une application, une verticale métier ou un domaine environnemental ;
- une capacité scientifique, un moteur, un modèle, une API ou un standard
  d'interopérabilité essentiel ;
- un territoire, une catégorie d'utilisateurs ou un type d'usage ;
- un corpus commun, un résultat de recherche ou une évolution financée dans
  le cadre de l'écosystème.

Est interdite toute clause qui empêche ou limite Quintessences dans sa
capacité à rechercher, développer, exploiter, publier ou proposer une
fonction identique ou équivalente avec d'autres acteurs.

Ne constituent pas une exclusivité :

- la confidentialité des données propres d'un client ;
- une intégration ou une configuration spécifique à son système ;
- une licence non exclusive ;
- une priorité de planification ou un pilote limité dans le temps, à
  condition qu'aucun tiers ne soit juridiquement ou techniquement empêché de
  mener une recherche ou un projet équivalent.

Toute clause ambiguë ou produisant un effet équivalent à une exclusivité est
présumée interdite jusqu'à une revue juridique indépendante et une décision
motivée du Fondateur. Cette décision ne peut déroger aux interdictions
ci-dessus ; elle peut seulement confirmer que la clause n'est pas exclusive.

#### 7.2.3 Vérifiabilité externe des composants scientifiques

Tout composant dont la sortie conditionne une affirmation scientifique
publiée, un niveau de preuve, un diagnostic validé, une recommandation ou
une connaissance canonique doit pouvoir être vérifié et contesté par un
tiers qualifié indépendant.

Cette exigence s'applique également aux composants propriétaires,
confidentiels ou fournis comme service. La vérification peut être organisée
par l'une des modalités suivantes :

- code, règles et jeux de conformité ouverts ;
- audit contrôlé du code, des règles, des données autorisées et des
  configurations sous accord de confidentialité ;
- implémentation de référence indépendante accompagnée de vecteurs de test
  et de critères de conformité publics.

Le tiers doit pouvoir au minimum :

- identifier la version exacte du composant et de ses dépendances ;
- examiner les sources, licences, règles, seuils et transformations qui
  déterminent la sortie ;
- reproduire un échantillon représentatif de résultats ;
- tester les cas limites, contradictions, biais et modes de défaillance ;
- contester un résultat et obtenir une réponse versionnée ;
- vérifier que les corrections approuvées sont effectivement appliquées.

La vérification est renouvelée après toute modification susceptible
d'affecter les résultats. Son périmètre, l'identité et l'indépendance du
vérificateur, les preuves examinées, les réserves et leur traitement sont
conservés dans un rapport auditable.

Un composant qui ne satisfait pas cette exigence peut rester un prototype
interne, mais il ne peut être l'autorité unique d'une sortie présentée comme
scientifiquement validée ou canonique. Son résultat reste explicitement non
validé jusqu'à l'intervention d'un mécanisme vérifiable et d'une validation
humaine compétente.

#### 7.2.4 Autres invariants

Quel que soit le composant :

- les sources scientifiques et licences des données restent traçables ;
- les résultats affichent provenance, incertitude et domaine de validité ;
- la qualité scientifique n'est pas diminuée pour accélérer une livraison ;
- aucun financeur ne contrôle seul la direction scientifique ;
- aucune publicité n'est intégrée aux outils métier ;
- les utilisateurs conservent les droits prévus sur leurs données et
  exports.

### 7.3 Services propriétaires temporaires

La présente RFC n'autorise immédiatement aucun service cloud ou modèle
propriétaire. Après adoption du cadre final par `RFC-0025`, leur usage
temporaire pourra faire l'objet d'une décision documentée par composant si
les conditions cumulatives suivantes sont satisfaites :

- leur usage est documenté et budgété ;
- aucun secret n'est exposé ;
- les données envoyées sont autorisées et minimisées ;
- un mode local ou dégradé existe pour les fonctions critiques ;
- le fournisseur ne devient pas une source de vérité ;
- les contrats restent suffisamment indépendants du fournisseur.

## 8. Révisions constitutionnelles proposées

La présente RFC ne porte aucune édition constitutionnelle cible.
`RFC-0025 — Éditions fondatrices d'identité, de périmètre et de propriété
intellectuelle` doit contenir le texte complet et le diff vérifiable des
nouvelles éditions. Son périmètre minimal comprend :

- `GSIE-FND-001` — identité, ambition, champ environnemental et
  déclaration fondatrice ;
- `GSIE-FND-002` — définition officielle et champ d'application ;
- `GSIE-CON-008` — vision multi-domaines et propriété intellectuelle ;
- `GSIE-CON-009` — articulation entre ouverture, reproductibilité
  scientifique et licence par composant ;
- `SCIENTIFIC_CONSTITUTION.md` — domaines de connaissance et distinction
  entre ouverture scientifique et licence logicielle ;
- `GSIE-CON-000` — anciennes mentions d'identité et formalisation du bloc
  fondateur, sans affaiblir la primauté de la Constitution en cas de conflit.

`RFC-0025` doit être contre-auditée indépendamment avant toute décision
d'adoption. Les anciennes éditions sont conservées pour audit. Aucun
historique n'est supprimé.

## 9. Registre et documents impactés

Après adoption de `RFC-0025` et publication atomique du bloc fondateur :

1. ajouter `VISION.md` au registre avec l'autorité `100`, dans le même bloc
   que la Constitution, et conserver la Constitution avant la Vision dans la
   précédence de résolution des conflits ;
2. inclure tous les documents constitutionnels, pas uniquement
   `GSIE-CON-0*.md`, dans le corpus constitutionnel ;
3. mettre à jour `VISION_HISTORY.md` avec la nouvelle vision adoptée ;
4. produire la décision d'adoption ;
5. aligner directives, mémoire, roadmap, changelog et README ;
6. réviser les spécifications et plans de portefeuille concernés ;
7. ajouter un contrôle détectant les anciennes définitions actives de GSIE.

## 10. Séquence d'adoption

1. correction des constats P0 et P1 de la présente RFC ;
2. contre-audit constitutionnel, juridique, scientifique et technique de la
   RFC corrigée ;
3. rédaction de `RFC-0025` avec le texte complet et le diff de chaque édition
   cible, sans modifier les documents `Locked` en vigueur ;
4. contre-audit indépendant de `RFC-0025` et reproduction des preuves par
   Codex ;
5. validation explicite du Fondateur par une décision d'adoption nommant les
   RFC, versions et empreintes des textes cibles ;
6. conservation des éditions antérieures ;
7. publication atomique de la nouvelle Vision et des nouvelles éditions
   constitutionnelles ;
8. mise à jour descendante de toutes les sources dépendantes ;
9. exécution des contrôles documentaires et de la CI ;
10. revue indépendante du diff final publié.

`DEC-000033` autorise la correction de la présente RFC et exige un nouveau
contre-audit avant toute présentation au Fondateur. La préparation de
`RFC-0025` reste sans effet normatif. Elle n'autorise ni adoption, ni
publication, ni modification d'un document `Locked`.

## 11. Critères d'acceptation

- une seule identité actuelle de GSIE existe dans les sources canoniques ;
- la Vision est enregistrée avec l'autorité `100`, dans le même bloc que la
  Constitution, avec primauté de la Constitution en cas de conflit ;
- sa revue annuelle ne permet aucune modification de sens hors RFC ;
- `RFC-0025` contient les textes cibles complets et leurs différences
  vérifiables ;
- les rôles de Quintessences, GSIE, Forge, GeoSylva, Hub et Ignis sont
  non ambigus ;
- aucune application future n'est créée sans validation métier ;
- la politique de licence par composant est compatible avec les
  non-négociables du Fondateur ;
- aucun flux tiers de données utilisateurs ou de dérivés identifiants ou
  ré-identifiables ne poursuit une finalité propre au tiers ;
- chaque traitement tiers autorisé est minimisé, contractuellement borné et
  inscrit dans un registre auditable, sans droit d'entraînement ou de
  réutilisation ;
- aucune clause contractuelle n'accorde directement ou indirectement une
  exclusivité totale ou partielle interdite par le §7.2.2 ;
- chaque composant qui conditionne une sortie scientifique validée possède
  une modalité de vérification externe, un vérificateur indépendant et un
  rapport à jour ;
- une sortie issue d'un composant non vérifiable ne peut recevoir un statut
  scientifique validé ou canonique ;
- chaque ancienne édition constitutionnelle est copiée octet pour octet
  sous `00_CONSTITUTION/ARCHIVED/` et possède une entrée complète dans
  `ARCHIVE_MANIFEST.json` ;
- `ACTIVE_IDENTITY_PATHS.json` classe tous les documents portant l'identité
  comme actifs, historiques ou explicitement étrangers à l'identité ;
- `python3 tools/check_active_identity.py` réussit ;
- les tests démontrent qu'une ancienne définition échoue dans un chemin
  actif, réussit dans une archive manifestée et échoue dans un chemin non
  classé ;
- toutes les éditions antérieures restent auditables ;
- `python3 tools/check_source_of_truth.py` réussit ;
- `python3 tools/check_governance_consistency.py` réussit.

## 12. Risques et mesures

| Risque | Mesure |
|---|---|
| Refondation trop large | Deux RFC séparées ; autonomie exclue de celle-ci |
| Réécriture de l'histoire | Conservation des éditions et décisions antérieures |
| Exploitation indirecte des données utilisateurs | Interdiction étendue aux cessions, licences, partages et dérivés ré-identifiables ; traitements tiers strictement bornés |
| Exclusivité partielle déguisée | Interdiction par composant, verticale, territoire, usage et effet contractuel équivalent |
| Fermeture scientifique excessive | Vérification indépendante obligatoire ou impossibilité de publier la sortie comme validée ou canonique |
| Dispersion vers trop d'applications | Règle domaine d'abord, application après preuve métier |
| Contrôle anti-régression incompatible avec les archives | Manifeste actif/historique exhaustif, archives octet pour octet, empreintes et tests positifs et négatifs |
| Dépendance cloud | Contrats neutres, budgets, modes local et dégradé |
| Communication trompeuse | Statuts, preuves et limites obligatoires |

## 13. Retour arrière

Tant qu'aucune décision n'est adoptée, cette RFC peut être rejetée sans effet
sur les sources canoniques.

Après adoption, toute remise en cause passe par une nouvelle RFC et une
nouvelle décision. Les éditions antérieures restent disponibles pour
comprendre et, si nécessaire, reconstruire l'état précédent.

## 14. Arbitrage du Fondateur déjà recueilli

Le 24 juillet 2026, le Fondateur a validé dans `DEC-000033` la stratégie
suivante :

- procéder à la refondation multi-domaines ;
- traiter séparément l'autonomie décisionnelle ;
- conserver cette autonomie comme programme de recherche encadré tant que
  sa sécurité et sa qualité ne sont pas démontrées.

Cet arbitrage autorise la correction et le contre-audit de la présente RFC,
ainsi que la préparation de `RFC-0025`. Il ne vaut ni adoption du texte final,
ni autorisation de modifier les documents constitutionnels.
