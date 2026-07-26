# RFC-0027 — Exigences opérationnelles des capacités R5

| Champ | Valeur |
|---|---|
| **ID** | RFC-0027 |
| **Statut** | Brouillon dormant — aucune capacité R5 n'existe |
| **Auteur** | Direction technique, sous autorité du Fondateur |
| **Date** | 2026-07-25 |
| **Décision liée** | `DEC-000033` — aucune autonomie R3, R4 ou R5 autorisée |
| **RFC d'origine** | `RFC-0024` §6.4, §12.1, §15.1, §15.2, §15.3 |
| **Périmètre** | Habilitation humaine, arrêt d'urgence et journal des capacités R5 |
| **Nature** | Spécification opérationnelle conditionnelle |

## 1. Objet

La présente RFC rassemble les exigences opérationnelles applicables aux
capacités de classe **R5** — sécurité humaine, incendie opérationnel, drone ou
système physique — telles que définies par `RFC-0024` §6.

Ces exigences ont été rédigées dans `RFC-0024` puis extraites sans
modification de contenu. Le motif est documenté au §2.

## 2. Pourquoi une RFC distincte

`RFC-0024` porte un programme de recherche sur l'autonomie graduée. Son
adoption conditionne un régime expérimental limité aux classes R0 à R2.

Les exigences R5 décrivent des systèmes qui n'existent pas : aucun drone,
aucun actionneur, aucun banc physique n'est déployé ni prévu avant la
validation de la simulation historique d'Ignis. Les maintenir dans `RFC-0024`
produisait trois effets indésirables :

1. elles représentaient près d'un cinquième du texte à contre-auditer à
   chaque cycle, sans qu'aucune ne soit applicable ;
2. elles portaient des constats bloquants — fusion des rôles d'habilitation
   et de sécurité, définition du « mécanisme équivalent » au chaînage
   cryptographique — qui retardaient l'adoption d'un régime R0–R2 sans rapport
   avec eux ;
3. elles laissaient croire qu'un cadre R5 opérationnel existait, alors
   qu'aucune compétence en sécurité fonctionnelle n'est identifiée au plan de
   réalisation.

La séparation ne les affaiblit pas. Elle les rend exigibles au moment où une
capacité R5 est réellement envisagée, et cesse de bloquer ce qui ne les
concerne pas.

## 3. Condition de réveil

La présente RFC reste **dormante**. Elle ne peut être portée au statut
`Proposé` que si l'ensemble des conditions suivantes est réuni :

1. une capacité R5 candidate est identifiée, décrite et classée conformément
   à `RFC-0024` §6.3 ;
2. une autorité de sécurité R5 humaine et qualifiée est nommée par décision
   du Fondateur ;
3. les compétences en sécurité fonctionnelle et en conformité juridique
   nécessaires aux revues sont identifiées et disponibles ;
4. `RFC-0024` a été adoptée ;
5. un contre-audit indépendant a porté sur le texte réveillé.

Tant que ces conditions ne sont pas réunies, **aucune capacité R5 ne peut être
expérimentée, activée ni déployée**, conformément à `RFC-0024` §7.2 et à
`DEC-000033`.

## 4. Constats ouverts sur ce texte

Le contre-audit n°2 du 2026-07-25 a relevé sur ces sections :

| ID | Gravité | Objet |
|---|---|---|
| `D-A10-04` | P1 | La fusion des rôles d'habilitation R5 et de sécurité R5 est autorisée sous une condition intestable |
| `D-A10-07` | P2 | « Mécanisme équivalent » au chaînage cryptographique n'est pas défini |

Ces constats doivent être traités avant tout réveil. Ils ne bloquent plus
l'adoption de `RFC-0024`.

## 5. Exigences reprises de RFC-0024

Le texte des sections suivantes est repris sans modification. La numérotation
d'origine est conservée entre parenthèses pour préserver la traçabilité des
constats et des citations d'audit.

## 5.1 Habilitation humaine R5 (ex-`RFC-0024` §6.4)

La présente RFC ne crée aucune habilitation R5 et n'autorise aucun test,
usage ou déploiement R5.

Avant toute future expérimentation R5, une décision distincte du Fondateur
désigne une **autorité d'habilitation R5** humaine, nommée et compétente pour
le domaine concerné. Cette autorité est indépendante de l'implémentation de
la capacité et de son objectif de livraison.

La même décision désigne une **autorité de sécurité R5** responsable de
l'analyse des dangers et de l'approbation des paramètres de sécurité. Elle
peut être la même personne que l'autorité d'habilitation uniquement si ses
compétences et son indépendance sont démontrées. Elle ne peut être ni
l'implémenteur de la capacité, ni son opérateur, ni la personne responsable
de son délai de livraison.

Dans un contexte soumis à une chaîne de commandement, une autorisation
réglementaire ou une compétence légale particulière, l'autorité compétente
de l'organisme concerné demeure souveraine. Une décision interne de
Quintessences ou du Fondateur ne s'y substitue jamais.

L'autorité d'habilitation vérifie les compétences et délivre une
habilitation individuelle. Le registre conserve au minimum :

- l'identité de la personne et son moyen d'authentification individuel ;
- le rôle, les formations, qualifications, expériences et évaluations
  pratiques vérifiées ;
- le système, la capacité, les actions, le territoire et le contexte
  couverts ;
- les limites, interdictions, conditions de supervision et modes dégradés ;
- la réussite d'un exercice d'arrêt d'urgence, d'échec sûr et de reprise
  manuelle sur la version concernée ;
- l'autorité émettrice, les preuves examinées et les éventuelles réserves ;
- un début et une fin de validité, pour une durée maximale de douze mois et
  jamais au-delà de la validité des qualifications requises ;
- les conditions de suspension, de retrait et de renouvellement.

Une habilitation de groupe, un compte partagé ou une autorisation implicite
liée au poste occupé sont interdits. Une expérimentation impliquant un effet
physique comporte au minimum un opérateur habilité et un superviseur de
sécurité distinct, tous deux capables de déclencher l'arrêt d'urgence.

L'habilitation est immédiatement suspendue lorsque :

- sa date de fin ou une qualification requise expire ;
- la personne change de rôle, de capacité, de version ou de contexte
  au-delà du périmètre autorisé ;
- un exercice obligatoire échoue ou n'est pas réalisé à l'échéance ;
- un incident, presque-incident ou écart de procédure met en doute la
  compétence ou les limites de l'habilitation ;
- le moyen d'authentification est perdu, partagé ou compromis ;
- l'autorité d'habilitation, l'autorité opérationnelle compétente ou le
  Fondateur ordonne la suspension.

La suspension révoque immédiatement les droits techniques correspondants,
préserve les journaux et interdit toute nouvelle action R5. La réactivation
des droits n'est jamais automatique : elle exige l'analyse de la cause, les
actions correctives, une nouvelle vérification des compétences et une décision
versionnée de l'autorité d'habilitation.

L'autorité d'habilitation tient un registre des habilitations actives,
expirées, suspendues et révoquées. Chaque action R5 référence l'habilitation
exacte qui l'a autorisée.

## 5.2 Contrat d'arrêt d'urgence R5 (ex-`RFC-0024` §12.1)

Chaque capacité R5 possède, avant tout test, un contrat d'interface
versionné définissant :

- l'état sûr attendu et les dangers qu'un arrêt brutal pourrait lui-même
  créer ;
- la commande d'arrêt, ses canaux et les personnes autorisées à l'actionner ;
- une valeur numérique et une unité pour le délai maximal
  **T_stop_max** ;
- le point de départ de la mesure, au déclenchement physique ou électronique
  de la commande, et son point de fin, lors de la confirmation indépendante
  de l'état sûr ;
- les étapes et délais intermédiaires si l'état sûr exige un arrêt
  contrôlé ;
- les scénarios d'essai, responsabilités, instruments de mesure et preuves
  à conserver.

L'autorité de sécurité R5 désignée au §6.4 approuve T_stop_max à partir de
l'analyse des dangers. Une moyenne, un percentile ou un objectif non contraignant ne
remplace pas ce maximum. L'absence de valeur exacte bloque le test et
l'activation.

Le mécanisme d'arrêt :

- est indépendant du modèle, de l'application principale et du chemin
  normal de commande ;
- dispose d'un canal local et, lorsqu'un effet physique existe, d'un moyen
  matériel indépendant adapté au danger ;
- reste opérant en cas de panne du processus principal, de perte du réseau,
  de saturation, d'indisponibilité du journal ou de défaillance partielle de
  l'alimentation ;
- a priorité sur toute commande d'action et n'exige aucune confirmation
  secondaire après son déclenchement ;
- fournit une confirmation d'état sûr observée indépendamment du composant
  commandé ;
- adopte un arrêt contrôlé plutôt qu'une coupure brutale lorsque l'analyse
  démontre qu'une coupure immédiate augmenterait le danger.

L'arrêt est testé :

1. avant chaque session ou campagne d'expérimentation R5 ;
2. après toute modification matérielle, logicielle, réseau ou de
   configuration ;
3. au moins tous les trente jours pour un service R5 maintenu en
   disponibilité continue ;
4. sous charge maximale et avec panne du processus principal, perte réseau,
   saturation du stockage, perte d'un capteur et défaillance d'alimentation
   prévues par l'analyse de danger.

Chaque essai mesure le pire délai observé et démontre qu'il reste inférieur
ou égal à T_stop_max. Un échec, une mesure absente ou une confirmation
d'état sûr ambiguë suspend immédiatement la capacité.

## 5.3 Journal R5 indépendant et inaltérable en exploitation (ex-`RFC-0024` §15.1)

Le journal R5 est produit par un enregistreur distinct du composant qu'il
surveille. Le contrôleur ne doit pouvoir ni modifier ni supprimer ses
preuves.

L'enregistreur possède une identité de sécurité, un processus, un stockage
et un domaine de défaillance séparés du chemin principal de commande. Il
peut être local pour garantir le fonctionnement hors ligne, mais il reste
indépendant du composant et synchronise ultérieurement ses preuves sans
réécrire l'historique.

Le journal est :

- en écriture seule par ajout pendant l'exploitation ;
- chaîné cryptographiquement ou protégé par un mécanisme équivalent rendant
  toute altération détectable ;
- horodaté en UTC et par une horloge monotone, avec numéros de séquence ;
- attribué à des identités individuelles ou techniques authentifiées ;
- répliqué ou ancré dans un second domaine de défaillance ;
- chiffré et soumis à des droits d'accès limités.

Il enregistre au minimum :

- l'identifiant et la version de la capacité, du modèle, des règles, des
  données et de la configuration ;
- les entrées déterminantes, sorties, incertitudes et contrôles appliqués ;
- l'identité, l'habilitation et l'autorisation humaines ;
- chaque commande, accusé de réception, changement d'état et effet observé ;
- les délégations, refus, corrections et reprises manuelles ;
- les déclenchements d'arrêt, délais mesurés et confirmations d'état sûr ;
- les erreurs, pertes de communication, modes dégradés et changements de
  santé du journal lui-même.

Un journal interne au composant peut compléter ces preuves, mais ne les
remplace jamais.

## 5.4 Disponibilité et échec sûr de la journalisation (ex-`RFC-0024` §15.2)

Un observateur indépendant contrôle la santé de l'enregistreur et du flux de
preuves. Le contrat d'interface fixe une valeur numérique
**T_log_detect_max** pour le délai maximal de détection d'une perte de
journalisation.

Tant que le journal indépendant n'a pas confirmé sa disponibilité :

- aucune nouvelle commande R5 produisant un effet ne peut être acceptée ;
- la capacité rejoint l'état sûr dans les limites de T_stop_max ;
- l'arrêt d'urgence et les commandes qui réduisent le danger restent
  prioritaires et ne sont jamais bloqués par l'absence de journal ;
- la défaillance est inscrite dans un journal de santé secondaire dès que
  celui-ci est disponible.

L'absence de T_log_detect_max, l'incapacité de l'observateur à provoquer
l'échec sûr ou une dépendance commune non maîtrisée entre contrôleur et
enregistreur bloque toute expérimentation R5.

## 5.5 Rétention et restauration (ex-`RFC-0024` §15.3)

Le contrat de chaque capacité R5 fixe une durée exacte **D_retention**, avec
une unité, un événement de départ, la destination des archives, les
responsables d'accès et la procédure de destruction. Une formulation comme
« selon les besoins » ou l'absence de durée bloque l'autorisation.

D_retention est approuvée par les responsables sécurité et juridique selon
les risques, les obligations applicables et la minimisation des données.
Toute enquête, contestation, procédure ou conservation légale suspend la
destruction des preuves concernées.

Une restauration complète est testée :

- avant la première expérimentation ;
- au moins une fois par trimestre tant que la capacité est active ;
- après toute migration de stockage, modification du format, perte de
  journal ou incident R5.

Le test doit reconstruire la chronologie, vérifier les séquences, empreintes,
signatures ou ancrages, retrouver les décisions et habilitations, et rejouer
les preuves nécessaires à l'analyse. Son résultat est lui-même conservé dans
un domaine indépendant.

## 6. Retour arrière

Le retrait de la présente RFC ne modifie aucune autorité. Les exigences
qu'elle porte restent celles auxquelles toute capacité R5 devra satisfaire ;
leur absence n'autorise rien.

## 7. Interdictions

La présente RFC n'autorise ni expérimentation, ni activation, ni déploiement
d'une capacité R5, ni modification d'un document `Locked`, ni dérogation aux
interdictions de `RFC-0024` §4 et §7.2.
