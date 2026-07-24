# RFC-0024 — Programme de recherche pour une autonomie graduée selon le risque

| Champ | Valeur |
|---|---|
| **Statut** | Proposé — programme de recherche, aucune autonomie critique autorisée |
| **Auteur** | Direction technique, sous autorité du Fondateur |
| **Date** | 2026-07-24 |
| **Décision liée** | Aucune — décision à créer après revue |
| **Périmètre** | GSIE, applications, Hub, Ignis, IA et systèmes physiques |
| **Nature** | Révision constitutionnelle et cadre de recherche préparatoire |
| **Snapshot de rédaction** | `77639a07beb2b5445134920b6f89ad3db5805630` |

## 1. Résumé

La présente RFC propose un programme de recherche permettant d'étudier une
autonomie progressive de GSIE sans confondre calcul, recommandation, décision
et action.

Le cadre proposé :

- classe les fonctions selon leur risque ;
- autorise immédiatement les calculs et simulations réversibles ;
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
| **R5** | Sécurité humaine, incendie opérationnel, drone ou système physique | Autorisation humaine qualifiée, arrêt d'urgence et échec sûr obligatoires |

Une fonction est classée selon son impact maximal raisonnablement
prévisible, pas selon son fonctionnement nominal.

En cas de doute entre deux classes, la classe la plus élevée s'applique.

## 7. Régime autorisé pendant les six premiers mois

### 7.1 Autorisé

- traitements de données R0 après validation du pipeline ;
- contrôles de qualité, détection de doublons et mise en quarantaine ;
- calculs et simulations R1 automatiques, journalisés et reproductibles ;
- diagnostics et recommandations R2 présentés comme brouillons explicables ;
- comparaison de scénarios dans le Hub ;
- rejeu historique Ignis sans effet opérationnel ;
- collecte volontaire des corrections et désaccords.

### 7.2 Non autorisé

- promotion automatique d'une connaissance en vérité canonique ;
- publication d'un diagnostic validé sans règle de validation approuvée ;
- décision R3 exécutée en usage réel ;
- toute décision R4 sans validation humaine préalable ;
- toute action R5 sans autorisation humaine explicite ;
- apprentissage modifiant automatiquement une règle scientifique ;
- présentation d'un prototype comme système opérationnel certifié.

## 8. Niveaux de maturité de l'autonomie

| Niveau | Description | Statut initial |
|---|---|---|
| **A0 — Calculateur** | Calcule et simule sans recommander | Autorisé |
| **A1 — Assistant** | Produit analyses, diagnostics brouillons et alternatives | Autorisé sous supervision |
| **A2 — Copilote** | Priorise et recommande, l'humain décide avant effet | Cible des six mois |
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
- Aucun apprentissage en production ne modifie silencieusement une règle,
  un seuil ou un modèle actif.

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

## 16. Révisions constitutionnelles envisagées

Après recherche et contre-audit, une nouvelle édition pourrait concerner :

- `GSIE-CON-001` — remplacer « l'IA ne décide jamais » par une autorité
  humaine, une délégation bornée et des interdictions selon le risque ;
- `AI_CONSTITUTION.md` — réviser le préambule, IA-1, IA-2, IA-3, IA-4,
  IA-5, IA-8, les anti-lois et la déclaration finale ;
- `GSIE-FND-001` — clarifier que l'IA n'est jamais une autorité
  scientifique autonome, même lorsqu'une exécution bornée est autorisée.

Cette RFC ne propose pas d'affaiblir :

- la traçabilité ;
- la réversibilité ;
- le droit de refus ;
- la validation scientifique des connaissances ;
- la responsabilité humaine pour R4 et R5 ;
- l'arrêt d'urgence des systèmes physiques.

## 17. Critères d'acceptation de la RFC

- le vocabulaire distingue clairement calcul, diagnostic, publication,
  décision et action ;
- chaque capacité GSIE peut être classée R0 à R5 ;
- le régime des six mois ne permet aucune décision autonome critique ;
- les interfaces de supervision et correction sont spécifiées ;
- l'explicabilité repose sur des preuves auditables plutôt que sur une
  chaîne de pensée privée ;
- les conditions de passage à A3 sont testables ;
- Ignis, GeoSylva, Forge et GSIE possèdent des exemples de classement ;
- une contre-revue scientifique, métier, sécurité et juridique est
  réalisée ;
- toute modification constitutionnelle finale reçoit une décision propre.

## 18. Risques et mesures

| Risque | Mesure |
|---|---|
| « Autonomie » interprétée comme autorisation immédiate | Statut recherche et régime initial explicite |
| Mauvaise classification d'une fonction | Classe selon impact maximal et escalade en cas de doute |
| Validation humaine purement formelle | Preuves visibles, responsabilité attribuée, temps de revue suffisant |
| Automatisation dissimulée par l'interface | Statut, niveau et reprise en main toujours visibles |
| Dépendance à un LLM opaque | Moteurs déterministes, preuves externes et interdiction d'autorité unique critique |
| Dérive après déploiement | Surveillance, seuils d'arrêt, versionnement et rollback |
| Pression commerciale | R4/R5 et critères scientifiques non contournables |

## 19. Retour arrière

Tant qu'aucune décision n'est adoptée, cette RFC ne change aucune autorité.

Une expérimentation A3 future doit disposer de son propre arrêt et retour
arrière. Son retrait ne doit pas empêcher les modes A0 à A2 ni l'usage manuel.

Toute modification constitutionnelle résultante conserve l'édition
antérieure et peut être supersédée uniquement par une nouvelle RFC.

## 20. Arbitrage du Fondateur déjà recueilli

Le 24 juillet 2026, le Fondateur a validé :

- la séparation entre refondation multi-domaines et autonomie ;
- le maintien de l'autonomie décisionnelle comme programme de recherche
  encadré ;
- l'absence d'autonomie critique tant que la qualité et la sécurité ne sont
  pas démontrées.

Cet arbitrage autorise la rédaction et le contre-audit de la RFC. Il ne vaut
ni adoption finale, ni modification constitutionnelle, ni autorisation
d'exécution autonome.
