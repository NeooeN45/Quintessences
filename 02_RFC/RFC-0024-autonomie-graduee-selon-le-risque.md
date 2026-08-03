# RFC-0024 — Programme de recherche pour une autonomie graduée selon le risque

| Champ | Valeur |
|---|---|
| **ID** | RFC-0024 |
| **Statut** | Proposé — EN_REVUE, aucune autonomie critique autorisée |
| **Auteur** | Direction technique, sous autorité du Fondateur |
| **Date** | 2026-07-24 |
| **Décision liée** | `DEC-000033` — orientation uniquement, aucune adoption |
| **Périmètre** | GSIE, applications, Hub, Ignis, IA et systèmes physiques |
| **Nature** | Révision constitutionnelle et cadre de recherche préparatoire |
| **Snapshot de rédaction** | `77639a07beb2b5445134920b6f89ad3db5805630` |

## 1. Résumé

La présente RFC propose un programme de recherche permettant d'étudier une
autonomie progressive de GSIE sans confondre calcul, recommandation, décision
et action.

Le cadre proposé :

- classe les fonctions selon leur risque ;
- prévoit qu'une décision future puisse autoriser les calculs et simulations
  réversibles dans les limites du §7 ;
- maintient les diagnostics et recommandations dans un régime supervisé ;
- impose une validation humaine préalable pour les décisions critiques ;
- interdit toute action physique liée au feu, aux drones ou à la sécurité
  sans autorisation humaine explicite et mécanisme d'arrêt ;
- soumet toute progression d'autonomie à des preuves reproductibles.

Cette RFC ne déploie aucun « pilote automatique ». Elle transforme une
ambition future en programme expérimental contrôlé.

## 2. Problème

### 2.1 Interdiction absolue actuelle

`GSIE-CON-001`, `GSIE-FND-001` et `AI_CONSTITUTION.md` disposent que l'IA
ne décide jamais, qu'aucun pilote automatique ne peut exister et qu'aucun
diagnostic ne peut être publié sans validation humaine.

Le Fondateur envisage à long terme que certaines décisions puissent être
prises automatiquement, à condition :

- que leur qualité soit démontrée par de nombreux tests ;
- que la décision et sa justification restent visibles ;
- que l'utilisateur puisse corriger le système ;
- que les décisions critiques et actions physiques conservent des
  validations et arrêts de sécurité adaptés.

Cette ambition est incompatible avec l'interdiction absolue actuelle, mais
elle ne justifie pas une autorisation générale d'autonomie.

### 2.2 Vocabulaire insuffisant

Les documents actuels utilisent parfois les mots « sortie », « diagnostic »,
« recommandation », « décision » et « action » sans distinguer :

- un calcul automatique ;
- un brouillon visible ;
- une publication validée ;
- une décision numérique réversible ;
- une action ayant un effet matériel ou humain.

Sans taxonomie précise, les équipes peuvent soit bloquer des automatisations
inoffensives, soit autoriser involontairement une action dangereuse.

### 2.3 Explicabilité des modèles modernes

`AI_CONSTITUTION.md` exige une « chaîne de raisonnement » et interdit les
modèles dont le raisonnement interne n'est pas auditable.

Cette formulation peut être incompatible avec des modèles modernes dont les
états internes ou chaînes de pensée privées ne sont ni accessibles ni des
preuves scientifiques fiables. L'exigence utile doit porter sur les éléments
auditables de la sortie :

- données et sources utilisées ;
- version des modèles ;
- calculs et outils appelés ;
- hypothèses ;
- alternatives ;
- incertitudes ;
- domaine de validité ;
- journaux et validations.

## 3. Objectifs

1. définir un vocabulaire commun de l'automatisation et de l'autonomie ;
2. classer les usages selon leur risque et leur réversibilité ;
3. préserver l'autorité humaine et la sécurité ;
4. autoriser les calculs automatiques utiles sans ambiguïté ;
5. créer une progression expérimentale fondée sur des preuves ;
6. définir les interfaces de supervision, correction et arrêt ;
7. remplacer l'obligation de révéler un raisonnement interne par une
   justification externe, sourcée et reproductible ;
8. préparer une éventuelle révision constitutionnelle sans l'anticiper.

## 4. Non-objectifs

Cette RFC :

- n'autorise pas GSIE à remplacer un forestier, un chercheur ou un
  commandant d'intervention ;
- n'autorise pas une décision matérielle, financière ou opérationnelle
  critique sans validation humaine préalable ;
- n'autorise pas de vol, guidage, largage ou action drone autonome ;
- n'autorise pas de commande automatique d'un système physique ;
- n'autorise pas d'alerte directe automatique à la population ;
- n'autorise pas la promotion automatique d'une connaissance comme vérité
  scientifique canonique ;
- ne prétend pas certifier GeoSylva, GSIE ou Ignis ;
- ne supprime pas le droit humain de refuser, corriger ou reprendre la main.

## 4 bis. Termes réservés

Deux mots circulent dans `RFC-0023` à `RFC-0027` avec des sens distincts, sans
que rien ne signale le glissement. Le lecteur qui applique la règle ne sait
pas laquelle il applique.

> La numérotation « bis » évite de décaler les sections 5 à 21, que les
> rapports de contre-audit citent par leur numéro. Renuméroter invaliderait
> les citations sans rien clarifier.

### 4 bis.1 « Capacité »

Employé seul dans `RFC-0024` et `RFC-0027`, le mot désigne **exclusivement**
une fonction du système inscrite au registre versionné du §6.2 et classée de
R0 à R5. C'est l'objet que la présente RFC gouverne.

Deux autres sens circulent dans `RFC-0023` et n'entrent jamais au registre :

| Sens | Où | Comment l'écrire désormais |
|---|---|---|
| Aptitude d'une personne morale à agir | `RFC-0023` §7.2.2 | « liberté de » |
| Élément d'offre — moteur, modèle, API | `RFC-0023` §7.2.1, §6 | « composant » |

Un emploi non qualifié vaut le sens gouverné. Un composant n'est soumis à
aucune classe de risque tant qu'il n'est pas inscrit au registre : confondre
les deux ferait croire qu'un catalogue d'offre est classé, et qu'une aptitude
juridique pourrait l'être.

### 4 bis.2 « Publication »

Le mot porte deux sens sans rapport entre eux :

| Sens | Définition | Classe |
|---|---|---|
| **Notion de la taxonomie** | §5.5 — passage d'un résultat de l'état brouillon à un état présenté comme validé | R4, R5 si alerte à la population |
| **Édition documentaire** | mise à disposition d'un texte de gouvernance dans le dépôt | sans objet |

Employé seul, le mot désigne la notion de la taxonomie. L'acte éditorial se
dit **« édition documentaire »**.

Sans cette distinction, la lecture littérale du §16 classerait en R4 l'édition
d'un texte constitutionnel — un acte de gouvernance humain qui n'est pas une
sortie du système, et que la matrice du §6.1 n'a jamais eu pour objet de
couvrir.

## 5. Taxonomie normative proposée

### 5.1 Calcul

Transformation déterministe ou probabiliste d'entrées en sorties, sans
choisir ni exécuter une action.

Exemples : cubage, corrélation, projection climatique, simulation de
propagation.

### 5.2 Analyse

Organisation ou interprétation de résultats sans choix exécutoire.

Exemples : détection d'une anomalie, comparaison de scénarios, carte de
l'ignorance.

### 5.3 Diagnostic brouillon

Conclusion proposée par le système, clairement étiquetée comme non validée,
accompagnée de ses preuves, limites et alternatives.

### 5.4 Recommandation

Option d'action proposée à un utilisateur. Elle reste contournable et ne
produit aucun effet par elle-même.

### 5.5 Publication

Passage d'un résultat de l'état brouillon à un état présenté comme validé
pour son public et son domaine d'usage.

### 5.6 Décision

Sélection d'une option qui engage une suite d'actions, des ressources ou une
responsabilité.

### 5.7 Exécution numérique réversible

Action limitée à un système numérique, automatiquement journalisée et
annulable sans préjudice significatif.

Exemples possibles : créer un brouillon, classer une tâche, préparer un
scénario, relancer un calcul.

### 5.8 Action critique

Action susceptible d'affecter :

- la sécurité ou la santé humaine ;
- un écosystème ou un bien matériel ;
- une opération de secours ;
- une dépense ou un engagement contractuel significatif ;
- un système physique ;
- un droit, une publication officielle ou une connaissance canonique.

## 6. Classes de risque

| Classe | Nature | Régime proposé |
|---|---|---|
| **R0** | Calcul, formatage, contrôle technique sans effet métier | Automatique, testé et journalisé |
| **R1** | Analyse ou simulation réversible | Automatique, provenance et incertitude obligatoires |
| **R2** | Diagnostic ou recommandation brouillon | Génération automatique, statut visible, correction humaine |
| **R3** | Exécution numérique bornée, faible risque et réversible | Recherche seulement, délégation explicite et retour arrière requis |
| **R4** | Décision matérielle, financière, juridique ou opérationnelle critique | Validation humaine préalable obligatoire |
| **R5** | Sécurité humaine, incendie opérationnel, drone ou système physique | Aucune autorisation actuelle ; les exigences opérationnelles applicables — habilitation nominative, arrêt borné, journal indépendant — sont portées par `RFC-0027`, dormante |

Une fonction est classée selon son impact maximal raisonnablement
prévisible, pas selon son fonctionnement nominal.

En cas de doute entre deux classes, la classe la plus élevée s'applique.

### 6.1 Matrice normative entre notions et classes

La classe ne dépend ni du nom commercial de la fonction ni de l'étape
technique isolée. Elle correspond au plus haut effet raisonnablement
prévisible de la capacité dans son contexte d'usage autorisé.

| Notion du §5 | Classe minimale | Escalade obligatoire |
|---|---|---|
| **Calcul** | R0 | R1 dès qu'il s'agit d'une simulation, d'une projection probabiliste ou d'un calcul métier dont l'incertitude influence l'usage |
| **Analyse** | R1 | R2 si la sortie formule une conclusion diagnostique ou une option d'action |
| **Diagnostic brouillon** | R2 | R4 s'il est présenté comme validé ou directement employé pour une décision critique ; R5 dans un contexte de sécurité humaine, d'incendie opérationnel, de drone ou de système physique |
| **Recommandation** | R2 | R4 si elle engage ou pilote une décision matérielle, financière, juridique ou opérationnelle critique ; R5 si son usage concerne la sécurité humaine, un incendie réel, un drone ou un système physique |
| **Publication** | R4 | R5 pour une alerte à la population ou une publication opérationnelle directement liée à une urgence de sécurité |
| **Décision** | R3 | R4 dès que l'effet n'est plus numérique, borné, de faible risque et réversible ; R5 dans les domaines de sécurité humaine, d'incendie opérationnel, de drone ou de système physique |
| **Exécution numérique réversible** | R3 | R4 ou R5 si l'annulation ne supprime pas le préjudice raisonnablement prévisible ou si le contexte d'usage relève d'une classe supérieure |
| **Action critique** | R4 | R5 lorsqu'elle touche la sécurité humaine, un incendie opérationnel, un drone ou un système physique |

Lorsqu'une capacité combine plusieurs notions, sa classe est la plus élevée
obtenue dans la matrice. Une chaîne de capacités est classée selon son effet
de bout en bout : la découper en étapes de risque inférieur ne réduit pas la
classe du service rendu.

La classe minimale n'est jamais une autorisation. Les règles du §7, le niveau
de maturité, les preuves, la décision applicable et les Constitutions en
vigueur restent cumulatifs.

### 6.2 Registre versionné des capacités

Avant T0, toutes les capacités comprises dans le périmètre expérimental
doivent être inscrites dans
`23_QUALITY_MANAGEMENT/AUTONOMY_CAPABILITY_REGISTRY.json` et valider le
schéma versionné
`23_QUALITY_MANAGEMENT/autonomy-capability-registry.schema.json`.

Le registre contient au minimum, pour chaque capacité :

- un identifiant stable, une version et le composant responsable ;
- un propriétaire humain nommé par rôle ;
- une description des entrées, sorties et effets de bout en bout ;
- les notions du §5 applicables, la classe R0 à R5 retenue et sa
  justification par l'impact maximal raisonnablement prévisible ;
- le niveau A0 à A4, le domaine, les populations, les utilisateurs et les
  contextes autorisés ;
- les validations humaines, limites, mécanismes de journalisation, de
  suspension et de retour arrière applicables ;
- les preuves et décisions d'autorisation référencées ;
- le statut de la capacité, ses dates d'effet et de prochaine revue ainsi
  que la version qu'elle remplace, le cas échéant ;
- le proposant, les contre-relecteurs indépendants, l'autorité de
  classification et leurs rôles respectifs ;
- l'historique des classements et reclassements, avec motifs, désaccords,
  recours, dates et preuves associés.

Les règles suivantes sont obligatoires :

1. une capacité activée correspond à une et une seule entrée active ;
2. une capacité absente, expirée, ambiguë ou non conforme au schéma est
   interdite d'activation ;
3. toute modification de périmètre, d'effet, de classe ou de niveau produit
   une nouvelle version et conserve l'historique ;
4. le fractionnement d'une capacité ne peut contourner la classe calculée de
   bout en bout ;
5. la découverte d'un impact supérieur suspend la capacité jusqu'à son
   reclassement et à l'obtention des autorisations correspondantes ;
6. la CI valide le registre avec
   `python3 tools/check_autonomy_capability_registry.py` avant toute
   expérimentation.

La présente RFC spécifie ce registre mais ne le crée pas comme source
canonique et n'active aucune capacité. Sa création relève de la Porte A du
§17 et entraîne la mise à jour du registre des sources de vérité.

### 6.3 Autorité et procédure de classification

La classification est une décision de gouvernance distincte de
l'autorisation d'expérimenter, d'activer, de publier ou de déployer une
capacité. L'approbation d'une classe ne confère aucun droit d'usage.

#### 6.3.1 Séparation des rôles

Le propriétaire du composant propose la classe et produit le dossier
d'impact. Il ne peut ni assurer seul la contre-revue ni approuver seul son
propre classement.

Pour un même dossier, et **à partir de la classe R2**, une personne ne peut
cumuler aucun de ces rôles : proposant, contre-relecteur ou autorité de
classification. Le seuil applicable en R0 et R1 est défini au §6.3.1 bis.

L'indépendance n'est pas déclarative. Elle est établie par au moins deux
critères vérifiables parmi : absence de lien hiérarchique direct avec le
proposant, absence de responsabilité sur le délai de livraison de la capacité,
mandat ou budget distinct, déclaration d'absence de conflit d'intérêts datée et
versionnée au registre. Un intitulé de poste ne suffit jamais, et une
affirmation d'indépendance sans critère cité est réputée absente.

| Classe proposée | Contre-revue indépendante minimale | Autorité de classification |
|---|---|---|
| **R0–R1** | Relecteur technique n'ayant pas produit la capacité | Direction technique |
| **R2** | Expert métier ou scientifique indépendant et contrôle de complétude QMS | Direction technique et responsable métier ou scientifique, conjointement |
| **R3** | Revue technique, métier et qualité | Fondateur, après avis documentés |
| **R4** | Revue technique, métier ou scientifique, qualité et, selon l'impact, juridique ou sécurité | Fondateur, après avis documentés |
| **R5** | Revue technique, métier, qualité, sécurité opérationnelle et juridique applicable | Fondateur, après avis documentés de personnes qualifiées |

Toute fonction Ignis ou liée à un système physique proposée en R0, R1 ou R2
reçoit en plus une contre-revue indépendante de sécurité opérationnelle. Son
auteur, son propriétaire et les personnes responsables de son délai de
livraison ne peuvent constituer à eux seuls cette contre-revue.

Un agent IA peut préparer le dossier, rechercher des preuves ou signaler un
risque. Il n'est jamais l'autorité humaine de classification.

À partir de la classe R2, si la séparation des rôles ou une compétence
obligatoire n'est pas disponible, le classement reste provisoire et la
capacité ne peut pas être activée. En R0 et R1, le §6.3.1 bis s'applique.
En cas de désaccord, la classe la plus élevée raisonnablement soutenue
s'applique jusqu'à arbitrage.

#### 6.3.1 bis Seuil applicable à un effectif réduit

Lorsqu'aucun relecteur indépendant n'est disponible, une capacité **R0 ou R1**
peut être classée par son propriétaire seul, à quatre conditions cumulatives :

1. le classement est inscrit au registre avec la mention explicite
   `contre_revue: absente` ;
2. le dossier d'impact justifie pourquoi l'impact maximal raisonnablement
   prévisible ne dépasse pas R1 ;
3. le classement est réexaminé dès qu'un relecteur indépendant devient
   disponible, et au plus tard à l'échéance périodique du §6.3.3 ;
4. la capacité n'est ni rattachée à Ignis, ni liée à un système physique, ni
   connectée à une publication, une décision, un actionneur ou un usage en
   temps réel.

Cette dérogation ne s'applique jamais à partir de R2 et ne dispense d'aucune
autre exigence de la présente RFC. Elle est levée de plein droit dès qu'un
relecteur indépendant est disponible.

**Justification.** Une règle de séparation qu'aucune personne présente ne peut
exécuter n'est pas une protection : elle est contournée, puis ignorée, et son
existence donne l'illusion d'un contrôle. Le seuil place la contrainte là où le
risque la justifie, et laisse un calcul sans effet métier être automatisé par
l'équipe qui en répond.

#### 6.3.2 Procédure

Chaque classification suit les étapes suivantes :

1. le propriétaire ouvre une demande liée à l'identifiant stable de la
   capacité et décrit son scénario de bout en bout ;
2. le dossier inventorie les entrées, sorties, utilisateurs, populations,
   systèmes aval, modes dégradés, défaillances et impacts maximaux
   raisonnablement prévisibles ;
3. le propriétaire propose les notions du §5, la classe issue du §6.1, les
   classes alternatives écartées et les preuves justifiant ce choix ;
4. le responsable qualité vérifie la complétude, la séparation des rôles et
   l'identité des contre-relecteurs requis ;
5. les contre-relecteurs consignent leur avis, leurs réserves et tout
   désaccord sans modifier la proposition d'origine ;
6. l'autorité compétente approuve, relève ou rejette la classe et fixe les
   conditions ainsi que la prochaine date de revue ;
7. le registre reçoit une nouvelle version contenant le dossier, les avis,
   l'arbitrage et leurs références immuables ;
8. une autorisation distincte applique ensuite, le cas échéant, les portes,
   preuves et limites prévues par la présente RFC.

Une absence d'avis, une preuve manquante ou une identité de rôle ambiguë
interdit de conclure la procédure par défaut.

#### 6.3.3 Réexamen obligatoire

Une nouvelle version de classification est ouverte avant tout usage modifié
et dès que survient l'un des événements suivants :

- changement d'entrée, de sortie, de modèle, de règle ou de source de
  données déterminante ;
- nouveau public, population, territoire, domaine, contexte ou finalité ;
- changement de statut affiché, notamment brouillon vers validé ;
- intégration à une nouvelle chaîne métier ou à un consommateur aval ;
- connexion à une décision, une publication, un actionneur, un système
  physique ou un usage en temps réel ;
- diminution de la réversibilité ou augmentation de la portée d'une erreur ;
- incident, presque-incident, dérive, cas hors domaine ou désaccord métier
  significatif ;
- évolution scientifique, réglementaire, juridique ou de sécurité pouvant
  modifier l'impact ;
- atteinte de la date de prochaine revue inscrite au registre.

L'intervalle maximal de revue est de douze mois pour R0–R1, six mois pour
R2, et avant chaque décision d'expérimentation ou d'activation pour R3–R5.

Un classement peut être relevé provisoirement dès la découverte d'un impact
supérieur. Son abaissement exige la procédure complète, des preuves nouvelles
et l'approbation de l'autorité compétente ; il n'est jamais déduit de
l'absence récente d'incident.

#### 6.3.4 Contestation et arbitrage

Tout utilisateur, expert, relecteur, responsable qualité ou membre du projet
peut contester un classement en déposant un motif et ses preuves dans le
registre.

Pendant le recours :

- la classe la plus élevée raisonnablement soutenue reste applicable ;
- aucune nouvelle autorisation fondée sur la classe contestée n'est émise ;
- la capacité est suspendue si ses protections ne satisfont pas la classe
  provisoire.

Le Fondateur constitue l'autorité de recours finale. Son arbitrage est écrit,
motivé, lié aux avis divergents et versionné dans le registre. Il détermine
la classe, pas l'autorisation d'usage, qui reste une décision séparée.

## 7. Régime expérimental proposé après adoption

Le présent régime n'est pas en vigueur. Il ne pourrait commencer qu'après une
décision explicite adoptant la présente RFC comme programme de recherche.

La décision d'adoption doit fixer :

- **T0**, horodatage de début inclusif, qui ne peut pas précéder la
  publication de la décision ;
- **T1**, horodatage de fin exclusif, qui ne peut pas être postérieur à six
  mois calendaires après T0 ;
- les deux horodatages au format RFC3339 avec leur fuseau ;
- les capacités, populations, domaines et contextes couverts.

Le régime s'applique uniquement sur l'intervalle **[T0, T1)**.

### 7.1 Capacités qui seraient autorisées entre T0 et T1

- traitements de données R0 après validation du pipeline ;
- contrôles de qualité, détection de doublons et mise en quarantaine ;
- calculs et simulations R1 automatiques, journalisés et reproductibles ;
- diagnostics et recommandations R2 présentés comme brouillons explicables ;
- comparaison de scénarios dans le Hub ;
- rejeu historique Ignis sans effet opérationnel ;
- collecte volontaire des corrections et désaccords.

### 7.2 Capacités qui resteraient non autorisées

- promotion automatique d'une connaissance en vérité canonique ;
- publication d'un diagnostic validé sans règle de validation approuvée ;
- décision R3 exécutée en usage réel ;
- toute décision R4 sans validation humaine préalable ;
- toute action R5 sans autorisation humaine explicite ;
- apprentissage modifiant automatiquement une règle scientifique ;
- présentation d'un prototype comme système opérationnel certifié.

### 7.3 Échéance, revue et absence de reconduction tacite

Une revue de sortie commence trente jours calendaires avant T1, ou à T0 si
la durée fixée entre T0 et T1 est inférieure à trente jours calendaires.
Elle examine au minimum les incidents et presque-incidents, les erreurs
graves, la calibration, les cas hors domaine, les corrections humaines, les
biais observés et le respect des conditions d'interface.

Toute prolongation exige, avant T1, une nouvelle décision explicite indiquant
les capacités concernées et de nouveaux horodatages. Une prolongation ne peut
ni élargir le périmètre ni augmenter le niveau d'autonomie sans nouvelle RFC.

En l'absence de nouvelle décision publiée avant T1 :

- le régime expérimental prend fin automatiquement à T1 ;
- les capacités A2 spécifiques à l'expérimentation sont suspendues ;
- le système revient au régime A0–A1 compatible avec les Constitutions en
  vigueur ;
- aucune capacité R3, R4 ou R5 n'est autorisée par défaut.

Une suspension anticipée reste obligatoire dans les cas définis au §15.

## 8. Niveaux de maturité de l'autonomie

| Niveau | Description | Compatibilité ou cible initiale |
|---|---|---|
| **A0 — Calculateur** | Calcule et simule sans recommander | Compatible avec les Constitutions en vigueur |
| **A1 — Assistant** | Produit analyses, diagnostics brouillons et alternatives | Compatible sous supervision et avec statut brouillon visible |
| **A2 — Copilote** | Priorise et recommande, l'humain décide avant effet | Cible expérimentale possible entre T0 et T1 après décision d'adoption |
| **A3 — Autonomie bornée** | Exécute certaines actions R3 explicitement déléguées | Recherche uniquement |
| **A4 — Autonomie critique** | Intervient sur R4 ou R5 | Hors périmètre ; nouvelle RFC et autorisations requises |

Le passage d'un niveau à l'autre n'est jamais automatique. Il exige une
décision formelle limitée à une capacité, une population, un domaine et un
contexte précis.

## 9. Conditions minimales pour expérimenter A3

Une capacité R3 ne peut entrer en expérimentation contrôlée que si :

1. son périmètre et ses non-objectifs sont écrits ;
2. son domaine de validité est mesurable ;
3. une mesure initiale humaine ou système de référence existe ;
4. les jeux de validation sont indépendants des jeux d'entraînement ;
5. les erreurs acceptables et inacceptables sont définies ;
6. le mode ombre a été exécuté sans effet réel ;
7. la calibration et les cas hors distribution sont évalués ;
8. les biais et groupes insuffisamment couverts sont connus ;
9. chaque action est journalisée et attribuable ;
10. le retour arrière a été testé ;
11. la reprise humaine reste immédiate ;
12. un responsable humain accepte l'expérimentation ;
13. la sécurité et la conformité juridique sont revues ;
14. un mécanisme d'arrêt automatique et manuel existe ;
15. une décision formelle autorise uniquement cette capacité.

## 10. Preuves exigées

Chaque revendication d'autonomie suit :

**mesure initiale → cible justifiée → protocole reproductible → test
indépendant → revue humaine → décision limitée**

Les preuves comprennent selon le risque :

- tests unitaires, d'intégration et fonctionnels ;
- simulation et rejeu historique ;
- mode ombre ;
- benchmark aveugle contre plusieurs experts ;
- tests adversariaux et cas limites ;
- mesure des faux positifs et faux négatifs ;
- calibration des probabilités ;
- tests hors domaine ;
- interruptions, reprise et fonctionnement dégradé ;
- audit de sécurité ;
- journal d'incidents et presque-incidents ;
- examen métier, scientifique, juridique et éthique.

Une moyenne globale ne suffit pas. Les erreurs graves, minoritaires ou
localisées restent visibles.

## 11. Explicabilité et justification

### 11.1 Éléments obligatoires

Toute sortie R1 ou supérieure expose selon son public :

- identité et version du moteur ou modèle ;
- date et contexte d'exécution ;
- données d'entrée et provenance ;
- sources scientifiques utilisées ;
- transformations et outils appelés ;
- hypothèses et contraintes ;
- résultat et unités ;
- incertitudes décomposées ;
- domaine de validité ;
- alternatives pertinentes ;
- contrôles et validations appliqués ;
- statut : brouillon, validé, simulé ou observé.

### 11.2 Raisonnement interne

Le système n'est pas tenu d'afficher une chaîne de pensée privée ou des états
internes non vérifiables. Il doit fournir une justification externe
suffisante pour :

- reproduire les calculs déterminants ;
- retrouver les preuves ;
- comprendre les hypothèses ;
- contester la sortie ;
- identifier les limites ;
- attribuer la responsabilité de la validation.

Un modèle opaque ne peut jamais être l'unique autorité d'une sortie R4 ou R5.

## 12. Exigences d'interface

L'interface doit toujours rendre visible :

- ce qui est observé, calculé, simulé, recommandé ou décidé ;
- le statut de validation ;
- le niveau de risque ;
- les incertitudes et données manquantes ;
- l'auteur ou moteur de la sortie ;
- les actions disponibles : accepter, refuser, corriger, comparer,
  demander une explication, reprendre la main.

Le contrat d'arrêt d'urgence propre aux capacités R5 — délai maximal chiffré,
canal indépendant du chemin de commande, moyen matériel lorsqu'un effet
physique existe — est porté par `RFC-0027`, dormante.

Pour R3 et au-delà :

- la délégation est explicite, limitée et révocable ;
- un mode manuel reste disponible ;
- l'historique des actions est consultable ;
- l'arrêt d'urgence est accessible et testé ;
- l'interface ne dissimule jamais une automatisation active.

## 13. Connaissances et apprentissage

- Une donnée peut être contrôlée et mise en quarantaine automatiquement.
- Une connaissance scientifique canonique exige une validation humaine
  conforme au processus de connaissance.
- Un retour utilisateur n'est pas automatiquement une vérité.
- Les corrections peuvent alimenter un corpus avec consentement,
  traçabilité et qualification.
- Un modèle entraîné reçoit une version, une fiche de données, un domaine
  d'usage et des résultats de validation.
- Aucun apprentissage en production ne modifie une règle, un seuil, une
  connaissance canonique, un modèle ou une configuration de décision active.
  Il produit uniquement une proposition inactive soumise à validation
  humaine conformément à `AI_CONSTITUTION.md` IA-4.

### 13.1 Séparation entre apprentissage et état actif

Le processus d'apprentissage, son compte de service et ses agents ne
disposent d'aucun droit d'écriture, de remplacement ou de suppression sur :

- les règles et seuils actifs ;
- le corpus scientifique canonique ;
- les artefacts, alias et configurations des modèles servis ;
- le registre des versions autorisées ;
- les décisions et preuves de validation.

Toute sortie d'apprentissage est écrite dans un espace de proposition
séparé, avec un identifiant et une version immuables, au statut
`PROPOSÉE`. Une journalisation, même complète, ne constitue ni une
validation ni une autorisation.

L'apprentissage en ligne qui ajuste directement les paramètres ou le
comportement de la version servie est interdit. Un calcul de métriques, une
détection de dérive, un entraînement hors ligne ou une évaluation en mode
ombre peuvent fonctionner automatiquement s'ils ne modifient pas l'état
actif.

### 13.2 Dossier de proposition

Chaque proposition issue de l'apprentissage contient au minimum :

- les données, sources, licences, consentements et critères d'inclusion ;
- les versions du code, des données, du modèle de départ et des outils ;
- le changement exact proposé ou l'empreinte de l'artefact candidat ;
- la justification scientifique ou technique et les hypothèses ;
- le domaine d'usage, la classe de risque et les impacts possibles ;
- les évaluations indépendantes, régressions, biais, incertitudes et cas
  hors domaine ;
- les résultats comparés à la version active et au système de référence ;
- les avis, désaccords, validations et décisions requis ;
- le plan de déploiement progressif, de surveillance et de retour arrière.

Une proposition incomplète reste en quarantaine. Elle ne peut être rendue
active par expiration d'un délai, absence d'objection ou atteinte automatique
d'un seuil de performance.

### 13.3 Validation et activation

Une modification de règle, de seuil ou de connaissance scientifique suit une
RFC et la validation humaine du comité scientifique prévues par IA-4 et
`GSIE-CON-002`.

Un nouvel artefact de modèle ou une nouvelle configuration exige une
validation indépendante et une décision humaine formelle proportionnée à sa
classe. Une RFC supplémentaire est obligatoire si le changement modifie une
règle scientifique, le domaine autorisé, la classe de risque, les garanties
ou les invariants approuvés.

L'activation :

1. crée une nouvelle version immuable au lieu de modifier la version active
   en place ;
2. référence les preuves, contre-revues et décisions d'autorisation ;
3. conserve la version précédente et son historique ;
4. utilise un déploiement progressif et des seuils d'arrêt lorsque le risque
   l'exige ;
5. vérifie le retour arrière avant exposition à un usage réel.

Le producteur de la proposition ne la valide jamais seul. La promotion
automatique d'un candidat est interdite. Un retour automatique vers une
version antérieure déjà autorisée reste possible comme mesure d'échec sûr ;
il ne peut jamais promouvoir une version nouvelle ou non validée.

## 14. Cas particuliers critiques

### 14.1 Ignis

Le rejeu historique et la simulation sans effet réel relèvent de R1.

Les recommandations destinées au SDIS relèvent au minimum de R2 et peuvent
être reclassées R4 selon leur usage.

Toute commande de drone, trajectoire opérationnelle, largage, guidage de
moyen ou recommandation exécutée pendant un incendie réel relève de R5.

### 14.2 GeoSylva

Les calculs de cubage et simulations relèvent de R0 ou R1 si leurs sources,
unités et limites sont documentées.

Un diagnostic ou choix sylvicole reste R2 tant qu'il ne déclenche aucune
action. Une décision de gestion ayant un impact matériel relève de R4.

### 14.3 Forge et GSIE

La déduplication, le contrôle de format et la quarantaine peuvent relever de
R0. La publication d'une donnée ou connaissance comme canonique relève au
minimum de R4 au regard de la responsabilité scientifique.

## 15. Incidents et arrêt

Une capacité autonome ou semi-autonome est suspendue lorsque :

- son domaine de validité est dépassé ;
- les données requises sont absentes ou périmées ;
- une dérive de performance est détectée ;
- un contrôle de sécurité échoue ;
- la journalisation devient indisponible ;
- un utilisateur déclenche l'arrêt ;
- une erreur grave ou un presque-incident survient.

L'échec doit être sûr : le système revient à un mode manuel ou à une
abstention explicite, jamais à une action par défaut.

Les exigences de journalisation propres aux capacités R5 — enregistreur
indépendant du composant surveillé, inaltérabilité, détection bornée d'une
perte de journalisation, rétention et restauration testée — sont portées par
`RFC-0027`, dormante. Aucune capacité R5 ne peut être expérimentée avant son
réveil et son adoption.

## 16. Révisions constitutionnelles envisagées

La présente RFC ne porte aucun texte constitutionnel cible et ne peut
autoriser la modification ou l'édition documentaire d'un document `Locked`
(§4 bis.2).

Son adoption éventuelle ne peut autoriser que les recherches et usages
compatibles avec les Constitutions en vigueur. Toute évolution
constitutionnelle liée à l'autonomie doit être portée par
`RFC-0026 — Éditions constitutionnelles de l'autonomie graduée`, rédigée
uniquement après obtention de preuves suffisantes et contenant le texte
complet ainsi que le diff vérifiable de chaque édition cible.

Le périmètre minimal de `RFC-0026` comprend :

- `GSIE-CON-001` — remplacer l'interdiction absolue par une autorité humaine,
  une délégation bornée et des interdictions graduées selon le risque ;
- `GSIE-CON-004` — remplacer « la chaîne de raisonnement, étape par étape »
  par une justification externe reproductible conforme au §11, sans
  affaiblir les cinq questions fondamentales, les sources, les règles, les
  calculs, les hypothèses, les incertitudes ni les limites ;
- `AI_CONSTITUTION.md` — réviser le préambule, IA-1, IA-2, IA-3, IA-4,
  IA-5, IA-8, les anti-lois et la déclaration finale ;
- `PACT_FOR_AI_AGENTS.md` — remplacer l'exigence de « chaîne de raisonnement »
  du § *Cas concrets d'application* par la justification externe reproductible
  définie au §11, sans affaiblir le rejet d'une sortie non justifiée ;
- `GSIE-FND-001` — clarifier que l'IA n'est jamais une autorité
  scientifique autonome, même lorsqu'une exécution bornée est autorisée.

La séquence constitutionnelle obligatoire est :

1. démontrer les critères de preuve et de sécurité du programme de recherche ;
2. rédiger dans `RFC-0026` les textes cibles complets et leurs différences ;
3. réaliser un contre-audit indépendant de `RFC-0026` ;
4. reproduire les preuves puis obtenir une décision explicite du Fondateur
   nommant les versions et empreintes adoptées ;
5. conserver les éditions antérieures ;
6. publier atomiquement les nouvelles éditions et leurs dépendances.

`DEC-000033` autorise la correction de la présente RFC. Elle n'autorise ni
révision constitutionnelle, ni autonomie R3, R4 ou R5.

Cette RFC ne propose pas d'affaiblir :

- la traçabilité ;
- la réversibilité ;
- le droit de refus ;
- la validation scientifique des connaissances ;
- la responsabilité humaine pour R4 et R5 ;
- l'arrêt d'urgence des systèmes physiques.

## 17. Registre et documents impactés

La propagation documentaire suit deux portes distinctes. Aucune source
dépendante ne doit présenter une orientation de recherche comme une
autorisation en vigueur.

### 17.1 Porte A — adoption du programme de recherche

Après une décision explicite adoptant la présente RFC comme programme de
recherche, mais avant toute adoption de `RFC-0026` :

1. mettre à jour `PROJECT_MEMORY.md`, `ROADMAP.md` et `CHANGELOG.md` ;
2. mettre à jour `README.md`, notamment les formulations actives relatives à
   `GSIE-CON-001`, pour distinguer l'état constitutionnel en vigueur de la
   cible de recherche, sans annoncer d'autonomie active ;
3. qualifier les impacts dans `01_DIRECTIVES/ACTIVE/GSIE-DIR-0011.md`,
   `05_SPECIFICATIONS/GEOSYLVA/GEO_001_SPECIFICATION.md`,
   `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md`,
   `GSIE/DOCUMENTATION/CONTRIBUTING_GUIDE.md` et les documentations des
   moteurs qui reprennent l'interdiction absolue ;
4. mettre à jour le registre des sources de vérité uniquement si une nouvelle
   source canonique ou un nouveau processus QMS est créé ;
5. conserver les RFC, décisions et archives historiques sans réécriture de
   leur état d'origine ; toute annotation indique explicitement la source qui
   les supersède.

La Porte A n'autorise aucune modification de la Constitution et aucune
autonomie R3, R4 ou R5.

### 17.2 Porte B — adoption constitutionnelle éventuelle

Uniquement après adoption explicite de `RFC-0026`, avec les textes, versions
et empreintes exacts :

1. publier atomiquement les nouvelles éditions constitutionnelles ;
2. aligner dans le même changement toutes les sources actives inventoriées à
   la Porte A ;
3. mettre à jour `23_QUALITY_MANAGEMENT/SOURCE_OF_TRUTH_REGISTRY.json` si le
   corpus, la précédence ou les propriétaires changent ;
4. archiver ou marquer comme supersédées les anciennes copies actives, sans
   supprimer les RFC, décisions et éditions historiques ;
5. synchroniser à nouveau mémoire, roadmap et changelog avec la décision
   d'adoption et les empreintes publiées.

### 17.3 Preuves de propagation

Avant de franchir chaque porte :

- inventorier les formulations dépendantes avec
  `git grep -n -I -E "ne décide jamais|pilote automatique|diagnostic sans validation humaine" -- "*.md"` ;
- classer chaque résultat comme source active à mettre à jour, référence
  historique à conserver ou archive exclue ;
- joindre la matrice de propagation et justifier toute occurrence active non
  modifiée ;
- exécuter `python3 tools/check_source_of_truth.py` ;
- exécuter `python3 tools/check_governance_consistency.py` ;
- exécuter la CI documentaire complète ;
- vérifier à la Porte A que `git diff -- 00_CONSTITUTION` reste vide.

Un échec de commande, une occurrence active non classée ou une source
dépendante oubliée bloque la porte concernée.

## 18. Critères d'acceptation de la RFC

- le vocabulaire distingue clairement calcul, diagnostic, publication,
  décision et action ;
- la matrice du §6.1 couvre les huit notions du §5 et chaque capacité GSIE
  peut être classée R0 à R5 selon son effet de bout en bout ;
- avant T0, le registre et son schéma versionnés du §6.2 existent, chaque
  capacité activée y apparaît exactement une fois avec un propriétaire, une
  classe, une justification et un statut ;
- avant T0, `python3 tools/check_autonomy_capability_registry.py` réussit et
  bloque les capacités absentes, expirées, dupliquées, non conformes ou sans
  séparation vérifiable entre proposition, contre-revue et approbation ;
- chaque classement identifie le proposant, les contre-relecteurs,
  l'autorité, les preuves, les désaccords et la date de prochaine revue ;
- toute proposition R0 à R2 touchant Ignis ou un système physique possède la
  contre-revue indépendante de sécurité opérationnelle exigée au §6.3 ;
- chaque déclencheur de réexamen produit une nouvelle version avant poursuite
  de l'usage concerné ;
- tout recours conserve la classe provisoire la plus élevée et reçoit un
  arbitrage motivé du Fondateur ;
- avant T0, le processus d'apprentissage et son compte de service n'ont
  aucun droit d'écriture sur les règles, seuils, modèles, configurations ou
  registres actifs ;
- chaque candidat appris reste inactif jusqu'à une validation indépendante
  et une décision humaine formelle ; toute règle ou tout seuil scientifique
  modifié suit en plus une RFC et la validation du comité scientifique ;
- un test d'autorisation prouve qu'un candidat rejeté, incomplet ou non
  validé ne peut pas remplacer la version active ;
- la décision d'adoption fixe T0, T1 et le périmètre exact, avec une durée
  maximale de six mois calendaires ;
- l'absence de renouvellement explicite déclenche le retour A0–A1 à T1 ;
- les interfaces de supervision et correction sont spécifiées ;
- l'explicabilité repose sur des preuves auditables plutôt que sur une
  chaîne de pensée privée ;
- les conditions de passage à A3 sont testables ;
- Ignis, GeoSylva, Forge et GSIE possèdent des exemples de classement ;
- une contre-revue scientifique, métier, sécurité et juridique est
  réalisée ;
- aucune expérimentation R5 ne commence avant le réveil, le contre-audit et
  l'adoption de `RFC-0027`, qui porte l'habilitation nominative, le contrat
  d'arrêt d'urgence et le journal indépendant ; l'adoption de la présente RFC
  n'ouvre aucun droit d'expérimentation R5 ;
- une perte de journalisation bloque les nouvelles actions R5 sans jamais
  bloquer l'arrêt d'urgence ou une action qui réduit le danger ;
- toute modification constitutionnelle finale reçoit une décision propre ;
- la matrice de propagation du §17 couvre et classe toutes les occurrences
  détectées dans les sources suivies ;
- `python3 tools/check_source_of_truth.py` réussit ;
- `python3 tools/check_governance_consistency.py` réussit ;
- la CI documentaire complète réussit ;
- aucun document `Locked` n'est modifié à la Porte A.

## 19. Risques et mesures

| Risque | Mesure |
|---|---|
| « Autonomie » interprétée comme autorisation immédiate | Statut recherche, T0/T1 explicites, aucune reconduction tacite et retour A0–A1 à T1 |
| Mauvaise classification d'une fonction | Matrice normative, registre versionné, séparation proposition/contre-revue/approbation, réexamen au changement d'usage et recours au Fondateur |
| Validation humaine purement formelle | Preuves visibles, responsabilité attribuée, temps de revue suffisant |
| Automatisation dissimulée par l'interface | Statut, niveau et reprise en main toujours visibles |
| Dépendance à un LLM opaque | Moteurs déterministes, preuves externes et interdiction d'autorité unique critique |
| Apprentissage journalisé interprété comme autorisation | Droits séparés, proposition inactive, validation humaine, RFC scientifique et promotion automatique interdite |
| Dérive après déploiement | Surveillance, seuils d'arrêt, versionnement et rollback |
| Habilitation R5 nominale ou périmée | Autorité indépendante, preuves de compétence, habilitation individuelle bornée et révocation technique immédiate |
| Arrêt d'urgence trop lent ou dépendant du système principal | État sûr contractuel, T_stop_max mesurable, canal indépendant et essais du pire cas |
| Perte simultanée du contrôle et de son journal | Enregistreur et observateur indépendants, commandes à effet bloquées, rétention exacte et restauration testée |
| Pression commerciale | R4/R5 et critères scientifiques non contournables |

## 20. Retour arrière

Tant qu'aucune décision n'est adoptée, cette RFC ne change aucune autorité.

Une expérimentation A3 future doit disposer de son propre arrêt et retour
arrière. Son retrait ne doit pas empêcher les modes A0 à A2 ni l'usage manuel.

Toute modification constitutionnelle résultante conserve l'édition
antérieure et peut être supersédée uniquement par une nouvelle RFC.

## 21. Arbitrage du Fondateur déjà recueilli

Le 24 juillet 2026, le Fondateur a validé dans `DEC-000033` l'orientation
suivante :

- la séparation entre refondation multi-domaines et autonomie ;
- le maintien de l'autonomie décisionnelle comme programme de recherche
  encadré ;
- l'absence d'autonomie critique tant que la qualité et la sécurité ne sont
  pas démontrées.

Cet arbitrage autorise la correction et le contre-audit de la présente RFC.
Il ne vaut ni adoption finale, ni modification constitutionnelle, ni
autorisation d'exécution autonome.
