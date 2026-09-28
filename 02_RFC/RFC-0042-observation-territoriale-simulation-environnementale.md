# RFC-0042 — Des observations territoriales à la simulation environnementale

| Champ | Valeur |
|---|---|
| **Identifiant** | RFC-0042 |
| **Statut** | Draft — proposition à examiner, non adoptée |
| **Version** | 0.1.0 |
| **Date** | 2026-09-27 |
| **Auteur** | Codex, d'après la vision exprimée par Camille Perraudeau |
| **Décision associée** | DEC-000074 — Draft |
| **Socle examiné** | `d7b400cb15d9f2216f3296d92754a6e67e55a63f` |
| **Continuité** | RFC-0011, RFC-0015, RFC-0029, RFC-0033, RFC-0037 à RFC-0041 |

## 1. Résumé et portée

Quintessences vise une infrastructure d'observation, de connaissance, de
diagnostic et de simulation des territoires réels. Les applications mobiles
alimentent un patrimoine de relevés géolocalisés et datés. GSIE les relie aux
référentiels, études et données extérieures qualifiées pour produire des
rapports, explorer des scénarios et, après validation scientifique, évaluer
des évolutions et des risques. Une application PC de dialogue environnemental
et les Hubs rendent ces capacités accessibles.

Cette RFC précise une trajectoire de réalisation de RFC-0037. Elle ne prouve
ni une capacité prédictive nationale ni un partenariat institutionnel. Elle
ne modifie aucun texte Locked, ne remplace pas le Data Registry et n'adopte
pas les propositions encore Draft, notamment RFC-0040 et RFC-0041.

Les exigences ci-dessous sont des propositions de conception issues de la
demande du Fondateur. Les contrats détaillés, migrations et intégrations
scientifiques restent à instruire et à valider avant leur implémentation.

## 2. Vision fonctionnelle à préserver

1. Chaque application terrain peut produire des observations réelles datées,
   avec un protocole, une localisation et un auteur identifiables.
2. Chaque utilisateur dispose d'un compte Quintessences. L'activation initiale
   nécessite la création d'un compte ou la connexion à un compte existant.
   Le travail hors ligne reste ensuite possible avec cette identité conservée
   localement ; la synchronisation et la restitution vérifient la session et
   les droits serveur. Aucune identité serveur n'est inventée hors connexion.
3. Avant un martelage ou un diagnostic GeoSylva, l'utilisateur choisit une
   unité géographique explicite : cadastre, parcellaire ONF, jeu fourni par
   une DDT, autre référentiel qualifié ou contour GPS déclaré.
4. Une reconnexion synchronise les relevés sans perte silencieuse. Une
   réinstallation suivie d'une connexion doit permettre de récupérer les
   relevés synchronisés, leurs versions et les pièces associées autorisées.
5. GSIE analyse une parcelle, une forêt, un bassin versant ou un territoire
   en conservant la provenance des contributions de plusieurs comptes.
6. Une application PC permet de poser en français des questions sur
   l'environnement à une IA métier d'HorizonOrigin, reliée aux données et
   outils GSIE. Elle produit des explications et des rapports sourcés.
7. Le Hub permet de naviguer dans le temps, de comparer les états et
   scénarios, et de voir les zones observées, extrapolées ou inconnues.
8. Les prévisions sont conservées avant observation du résultat réel ;
   les écarts et retours qualifiés alimentent des améliorations évaluées.

## 3. Ancrage géographique et identité

### 3.1 Ce qui fait référence

L'ancrage repose sur des objets géographiques identifiés, et pas seulement
sur un nom de parcelle, un point GPS ou le propriétaire supposé du terrain.
Un identifiant doit être qualifié par son référentiel, son producteur et sa
version. Deux parcelles cadastrales et ONF qui se recouvrent ne sont pas
automatiquement le même objet. Un jeu fourni par une DDT n'est pas supposé
posséder un identifiant national uniforme : il faut qualifier le jeu réel.

Pour chaque ancrage, le contrat futur devra porter ou référencer :

| Information | Rôle |
|---|---|
| Ressource GSIE et référence d'origine | Identité stable et traçabilité |
| Producteur, jeu, millésime et version | Identifier le référentiel retenu |
| Géométrie, système de coordonnées, empreinte | Rejouer les opérations spatiales |
| Date de validité et date d'enregistrement | Distinguer terrain et connaissance disponible |
| Méthode, précision et qualité | Décrire les limites de la localisation |
| Relations et justification | Recouvrement, inclusion, équivalence proposée, succession |
| Droits d'utilisation | Consultation, conservation, agrégation, redistribution |

Un contour GPS conserve son statut de relevé et sa précision. Il ne devient
pas silencieusement une limite cadastrale. Le référentiel retenu pour une
mission est explicite ; les désaccords entre géométries restent visibles.
Les divisions, fusions et corrections de parcelles créent des successions
versionnées plutôt qu'un remplacement destructif.

### 3.2 Compte, territoire et contribution

Le compte est l'identité d'accès ; l'auteur est la provenance ; la parcelle
est l'ancrage territorial. Un compte ne prouve pas la propriété foncière.
Plusieurs comptes peuvent contribuer sur le même territoire sans fusion
automatique de leurs observations ni accès réciproque à leurs données.

Réutiliser les concepts canoniques `Place`, `Agent`, `Observation`,
`TemporalContext`, `Revision`, `Snapshot`, `Rights` et `Consent` avant
d'ajouter un type. La liaison entre identifiant mobile et ressource GSIE
reste celle à formaliser avec RFC-0041. Une table de synchronisation privée
ne devient pas par simple copie un catalogue scientifique partagé.

## 4. Temps, historique et synchronisation

### 4.1 Séparer les événements et les corrections

Un martelage daté est une opération métier. Deux martelages sont deux
événements ; la correction du même relevé en crée une nouvelle version.
La date de terrain, la date d'envoi et la date de réception serveur sont
distinctes. L'horloge du téléphone ne suffit pas à arbitrer un conflit.

L'analyse « état à T » sélectionne les versions pertinentes et disponibles
selon une politique annoncée. L'analyse d'évolution compare les événements
et états successifs. Pour rejouer une prévision historique, la date de
disponibilité des données interdit d'utiliser une correction ou une étude
publiée après l'émission initiale de cette prévision.

Exemple : une forêt contient A, relevée par U1, et B, relevée par U2.
Le bilan utilise A-v1 et B-v2 si ce sont les états admissibles pour sa
période. B-v1 demeure consultable pour l'évolution ; B-v1 et B-v2 ne sont
pas deux surfaces à additionner. Si leurs dates diffèrent, le rapport
affiche cette hétérogénéité au lieu de prétendre à un inventaire simultané.

### 4.2 Contrat de synchronisation à construire

- Journal des opérations et des révisions persisté, restitution des anciennes
  versions et pièces, avec protocole de restauration documenté.
- Rejeu d'une opération identique sans nouvel effet ; collision de contenu
  signalée, jamais acquittée comme une sauvegarde réussie.
- Conflits de terminaux conservés et arbitrés explicitement ; aucune règle
  implicite « le dernier téléphone gagne ».
- Pagination cohérente d'un instantané ou journal avec curseur : une liste
  triée par date mutable avec `OFFSET` ne garantit pas une restauration
  complète pendant des écritures concurrentes.
- Suppression logique, droits de conservation et pièces associées traités
  ensemble ; les obligations de conservation/effacement sont instruites
  séparément, sans promettre une rétention illimitée des données personnelles.
- Reprise après coupure et test sur un client vierge avec réseau interrompu,
  doublons, ordre inversé et modifications concurrentes.

Le correctif de collision d'identifiant fourni avec cette proposition ne
livre pas ce journal ni le protocole complet de restauration.

## 5. De la parcelle au territoire

Le périmètre affiché, le périmètre étudié et le domaine nécessaire au calcul
peuvent différer. Une analyse hydrologique peut nécessiter l'amont d'une
parcelle ; un contour administratif ne constitue pas une frontière physique.
Chaque exécution doit déclarer ces emprises et ses conditions aux limites.

L'agrégation porte sur les observations autorisées après qualification des
dates, méthodes, unités, géométries et doublons. Les grandeurs extensives
et intensives ont des règles distinctes : une moyenne de moyennes ou une
addition de surfaces recouvrantes n'est pas une règle générique acceptable.
La méthode, ses pondérations et sa source sont à qualifier par indicateur.

Chaque rapport conserve un manifeste des entrées et versions retenues,
la période, la couverture, les exclusions, les modèles, paramètres et
versions exécutés, ainsi que les limites de validité. Une zone non relevée
reste inconnue ; une donnée périmée ne devient pas une mesure actuelle.
Les observations contradictoires sont conservées et signalées.

Le filtrage des droits intervient avant recherche, calcul et restitution,
y compris dans les index vectoriels, caches, traces et rapports dérivés.
La synchronisation pour sauvegarde ne vaut pas autorisation de mutualisation,
d'entraînement ou de transfert vers un fournisseur de modèle externe.

## 6. Application PC et IA environnementale d'HorizonOrigin

La cible produit est une application PC dédiée au dialogue environnemental,
utilisant le compte Quintessences. Elle permet de sélectionner un territoire,
une période et les données autorisées, puis de demander un diagnostic,
une comparaison, une explication ou un scénario. Elle partage le socle GSIE
avec GeoSylva et le Hub ; elle ne crée pas une nouvelle base faisant autorité.

Le produit et sa spécialisation sont maîtrisés par HorizonOrigin : outils,
connaissances qualifiées, politiques, évaluations et expérience utilisateur.
Le choix entre modèle existant, adaptation et entraînement propre reste une
décision ultérieure fondée sur des preuves de qualité, droits et coût.
« IA maison » n'implique pas un entraînement généraliste à partir de zéro.

Flux cible : intention → périmètre et droits → recherche de preuves →
plan borné → appels d'outils GSIE → contrôles → réponse et rapport.
Le système peut clarifier une demande ambiguë et décliner les demandes hors
du domaine environnemental. Chaque conclusion renvoie aux observations ou
documents utilisés, avec versions et dates ; les calculs renvoient à leur
exécution reproductible. L'absence de preuve déclenche une réponse limitée
ou une demande de relevé, jamais un résultat fabriqué.

Les documents récupérés sont des données non fiables du point de vue des
instructions : ils ne peuvent changer les outils autorisés, les droits ni
les règles d'exécution. L'agent utilise des interfaces typées, des limites
de coût/temps et des droits bornés. Les outils statistiques et physiques
produisent les valeurs ; le modèle de langage organise et explique.
La première tranche conversationnelle proposée fonctionne en lecture seule.

## 7. Simulation et apprentissage à long terme

La cible « simulateur de monde » signifie une représentation des territoires
réels, avec des résolutions annoncées et adaptées aux phénomènes. Elle ne
promet pas la connaissance exacte de tout état ni la date certaine d'une
catastrophe. Les scénarios restent séparés des observations canoniques.

Un premier cas scientifique proposé est le suivi du stress hydrique d'un
territoire pilote : relief, propriétés des sols, forçages météorologiques,
disponibilité en eau et réponse des peuplements. La sélection des méthodes,
leurs paramètres, unités, domaines de validité et conditions aux limites
exige une qualification scientifique avant calcul opérationnel.

Les contrats de couplage devront expliciter variables échangées, maillages,
pas de temps, unités, conservation des grandeurs, incertitudes et règles
d'arrêt. Le changement d'échelle ne crée pas une précision supplémentaire.
Les modèles feu, maladies ou autres risques seront qualifiés séparément.

La progression se mesure en comparant des prévisions figées aux observations
ultérieures. Prévoir une séparation des territoires et des périodes entre
apprentissage, calibration et évaluation ; conserver les baselines simples,
la calibration des probabilités, les fausses alertes, événements manqués et
délais d'anticipation. Les seuils d'acceptation seront fixés avec les experts
selon le phénomène et l'usage, avant consultation des résultats d'évaluation.

Un avis utilisateur, une correction d'observation et un résultat réellement
mesuré ont des statuts distincts. Les retours sont qualifiés avant emploi.
Les mises à jour passent par des candidats versionnés, une évaluation et une
promotion contrôlée avec retour arrière. Respecter RFC-0039 et les limites
de RFC-0040 ; aucun apprentissage automatique non validé de la chaîne de
décision n'est autorisé par ce texte.

## 8. État constaté sur le code de départ

Cette matrice est une inspection de source au commit indiqué, pas un audit
de production ni une validation scientifique. Les dépôts externes GeoSylva
et Forge ne sont pas audités dans cette tranche.

| Brique | Preuve dans le dépôt | Écart vers la cible |
|---|---|---|
| Vision multi-domaines | RFC-0037 ; `GSIE/ARCHITECTURE/GSIE_ENVIRONMENTAL_DIGITAL_TWIN_PLATFORM.md` | Décliner collecte, restauration et parcours PC en preuves de bout en bout |
| Synchronisation privée | `GSIE/API/src/gsie_api/sync/geosylva.py`, `repository.py`, `infrastructure/models/sync.py` | Une ligne courante par compte/client, compteur de version ; pas d'archive de tous les relevés dans ce chemin |
| Ancrage parcellaire | `GSIE/API/src/gsie_api/sync/schemas.py` | Champs cadastraux optionnels ; liaison canonique, ONF/DDT/GPS et sélection obligatoire non démontrées |
| Ingestion terrain | `GSIE/API/src/gsie_api/data/field_intake.py`, `field_intake_station.py` | Réutiliser la qualification ; ne pas assimiler une copie privée à une donnée acceptée |
| Registre et acquisition | `GSIE/API/src/gsie_api/data/manifest_application.py`, `fetch_policy.py` | Qualifier chaque source et les droits ; aucune collecte Internet sans bornes |
| Orchestration | `GSIE/API/src/gsie_api/engines/orchestration/service.py`, `hydration.py` | Façade GeoSylva et identité stationnelle encore proposées dans RFC-0041 |
| Simulation | `GSIE/API/src/gsie_api/engines/simulation/engine.py` | Projection simplifiée à taux constant configuré, sans mortalité ni couplage climatique ; aucune preuve de prévision territoriale |
| Conversation PC | `GSIE/API/README.md` et RFC-0037 | Parcours PC authentifié, citations et contrôles de bout en bout à spécifier et démontrer |
| Évaluation | RFC-0039 ; `GSIE/TESTS/GSIE_BENCH/` et `GSIE/API/src/gsie_api/benchmark/runner.py` | Étendre les cas à la restauration, aux rapports et aux prévisions spatiales/temporelles |

La simulation actuelle emploie une croissance composée alors que plusieurs
commentaires la nomment linéaire. Ce constat appelle un chantier scientifique
distinct ; il ne faut pas changer une formule sans en instruire la méthode.

## 9. Trajectoire de réalisation et portes de sortie

| Lot | Travail et dépendances | Preuve avant passage au lot suivant |
|---|---|---|
| L0 — État vérifiable | Matrice de capacités, défaut de rejeu, vocabulaire commun ; présent cadrage | Diff revu, tests du correctif, documentation cohérente ; aucune capacité scientifique surdéclarée |
| L1 — Terrain durable | Référentiel/version + liaison RFC-0041 + journal de relevés + restauration ; contrats et migrations à valider | Client vierge retrouve tous les relevés/versions/pièces autorisés ; coupures, collisions, concurrence et frontières de comptes testées |
| L2 — Rapport territorial | Préparation serveur RFC-0041, données acceptées, agrégation datée, manifeste d'analyse | Cas A/U1 et B/U2 : résultat recalculable, pas de doublon, refus des données non autorisées, visibilité des lacunes |
| L3 — Dialogue PC | Réutiliser L2, outils bornés, sources documentaires qualifiées, compte et périmètre | Questions métier de référence ; citations résolvables ; demandes hors domaine et injections documentaires maîtrisées |
| L4 — Pilote scientifique | Processus eau/sol/peuplement sélectionnés et couplés, données indépendantes de validation | Résultats comparés à une baseline et aux observations ; incertitudes et domaine de validité publiés |
| L5 — Prévision et extension | Prévisions figées, retours qualifiés, territoires et risques supplémentaires | Évaluation prospective, dérive suivie, versions reproductibles, retour arrière démontré |

Ces lots sont des portes de capacité, pas des promesses de calendrier.
La documentation de L3 peut avancer pendant L1, mais une démonstration de
dialogue n'atteste pas la livraison de L2 ni la validité de L4.

Avant dimensionnement national, mesurer volumes par relevé et par zone,
pièces/raster, taux de synchronisation, croissance de l'historique, latence,
coût par rapport/simulation, coût de stockage et restauration. Extrapoler
depuis des mesures et un budget explicites ; éviter un achat GPU préalable.
Les compétences nécessaires couvrent SIG et données, mobile/serveur, qualité,
sécurité, foresterie, hydrologie et validation scientifique. Les partenariats
IGN, ONF, INRAE, Météo-France ou autres restent des pistes, non des accords.

## 10. NVIDIA : candidats à évaluer, pas dépendances adoptées

| Candidat | Usage à examiner | Condition de choix |
|---|---|---|
| NeMo Agent Toolkit | Orchestration instrumentée et évaluation d'agents | Gain mesuré sur les parcours L2/L3 ; compatibilité avec les contrats GSIE |
| NeMo Retriever | Extraction et recherche dans les documents scientifiques | Qualité des citations, versions, droits et coût sur le corpus réel |
| NIM et modèles adaptés | Inférence hébergée ou maîtrisée | Comparaison qualité/confidentialité/coût, licences et réversibilité |
| cuGraph | Accélération de certains calculs de relations | Graphe utile démontré et gain réel par rapport à la référence CPU |
| PhysicsNeMo | Modèles scientifiques combinant données et physique | Méthode de référence validée et erreur du modèle accéléré mesurée |
| Earth-2 | Pistes de prévision météo et d'assimilation d'observations | Compatibilité géographique, résolution, forçages et évaluation locale |

PhysicsNeMo et Earth-2 sont des outils à qualifier, pas des modèles forestiers
validés pour GSIE. NeMo Retriever Library n'est pas couverte globalement par
NVIDIA AI Enterprise selon sa documentation ; vérifier séparément le support
des composants. Aucun modèle, compte fournisseur ou transfert de relevé réel
n'est activé par cette proposition.

## 11. Sources et références

- Demande du Fondateur, conversation du 2026-09-27 : collecte multi-applications,
  parcellaire de référence, comptes, historique, simulation et dialogue PC.
- [Architecture fédérée existante](../GSIE/ARCHITECTURE/GSIE_ENVIRONMENTAL_DIGITAL_TWIN_PLATFORM.md).
- [RFC-0037](RFC-0037-gsie-environmental-digital-twin-platform.md),
  [RFC-0038](RFC-0038-data-registry-gsie.md),
  [RFC-0039](RFC-0039-gsie-bench-v0-1.md),
  [RFC-0040](RFC-0040-controle-qualite-modeles-perception.md),
  [RFC-0041](RFC-0041-contrat-facade-geosylva-identite-stationnelle.md).
- [NeMo Agent Toolkit](https://docs.nvidia.com/nemo/agent-toolkit/latest/),
  [NeMo Retriever](https://docs.nvidia.com/nemo/retriever/latest/extraction/overview/),
  [NIM](https://docs.nvidia.com/nvidia-nim-document-center/index.html),
  [cuGraph](https://docs.nvidia.com/cugraph/26.10/) : sources officielles
  consultées le 2026-09-27 ; figer versions et licences avant expérimentation.
- [PhysicsNeMo](https://docs.nvidia.com/physicsnemo/latest/overview.html) et
  [Earth-2 et assimilation](https://developer.nvidia.com/blog/turn-your-latest-observations-into-timely-weather-decisions-with-nvidia-earth-2) :
  documentation et présentation NVIDIA consultées le 2026-09-27 ; les gains
  annoncés sur leurs exemples ne sont pas extrapolés au territoire français.

## 12. Historique

| Date | Version | Modification |
|---|---|---|
| 2026-09-27 | 0.1.0 | Cible explicitée, écarts repérés dans le code et lots vérifiables ; ajout du dialogue PC et des référentiels multiples |
