# Corpus sylvicole scientifique de Quintessences / GeoSylva

**Addendum stratégique au plan directeur — version du 18 juillet 2026**
**Périmètre :** GeoSylva, Encyclopédie Quintessences, Evidence Engine, Knowledge Engine, Botanical Engine, Forest Dynamics Engine, Diagnostic Engine et Recommendation Engine.

**Origine :** addendum externe fourni par le Fondateur, versé tel quel dans `GSIE/RESEARCH/` pour référence. N'a pas encore été audité par un agent GSIE (constitution-audit) ni transformé en RFC/décision — le document propose lui-même (§12) des demandes de partenariat CNPF/ONF à formaliser avant toute ingestion massive.

## 1. Décision stratégique

La documentation sylvicole actuellement prévue est insuffisante pour revendiquer une application professionnelle d'aide à la décision.

Le manque ne se résume pas à « ajouter davantage de PDF dans un RAG ». Il faut construire un **système de connaissances sylvicoles scientifiques** capable de représenter simultanément :

- l'autécologie des essences ;
- les stations forestières et leurs clés de détermination ;
- les classes de fertilité et indices de station ;
- les itinéraires sylvicoles selon l'essence, la station, le traitement et l'objectif ;
- les modèles de croissance et de production ;
- le climat actuel et futur, avec scénarios et incertitudes ;
- les risques sanitaires, climatiques et biotiques ;
- la biodiversité et les limites des indicateurs indirects ;
- les provenances et matériels forestiers de reproduction ;
- les règles régionales applicables aux forêts privées et publiques ;
- la provenance exacte, la version, le domaine de validité et le niveau de preuve de chaque assertion.

Le dispositif cible doit comporter quatre couches distinctes :

1. **Sources brutes immuables** : documents, données et modèles conservés avec version, empreinte et droits.
2. **Connaissances structurées et validées** : objets scientifiques exploitables par la machine.
3. **Moteur déterministe de règles et de calcul** : compatibilités, exclusions, indices, prescriptions et contrôles.
4. **RAG + LLM** : recherche, synthèse et explication, sans pouvoir inventer une règle ni prendre la décision finale.

Le LLM ne doit donc jamais être la vérité métier. Il est l'interface linguistique d'un système de preuves.

## 2. Pourquoi le référentiel actuel n'est pas encore professionnel

Le plan directeur indique déjà 95+ essences, un diagnostic stationnel, un RAG local envisagé et 18 sources externes. Il reconnaît cependant que certaines inférences sont heuristiques, que l'indice de station doit être corrigé, que les domaines de validité ne sont pas représentés et que les packs hors ligne sont encore simulés.

Une fiche d'essence comportant quelques attributs généraux ne constitue pas une autécologie exploitable. De même :

- une essence peut être compatible climatiquement mais inadaptée au sol ;
- une station peut être favorable aujourd'hui mais risquée à l'horizon 2070 ;
- une classe de fertilité n'a de sens qu'avec son essence, sa courbe, son âge de référence et sa zone de calibration ;
- un itinéraire national général peut être incompatible avec un SRGS, une DRA/SRA ou une règle MFR locale ;
- une recommandation valable en futaie régulière peut être incohérente en futaie irrégulière ;
- un indicateur de potentiel, comme l'IBP, ne remplace pas un inventaire réel de biodiversité ;
- ARCHI et DEPERIS décrivent un état ou une trajectoire sanitaire, mais n'établissent pas à eux seuls la cause du dépérissement.

Conséquence : les données heuristiques existantes doivent être marquées **indicatives et non validées**, jusqu'à leur remplacement ou validation documentaire.

## 3. Carte des corpus de référence

Les statuts ci-dessous sont des décisions d'ingestion prudentes, pas un avis juridique. Chaque document et chaque jeu de données doit conserver sa propre licence.

| Domaine | Source officielle | Apport | Statut d'intégration recommandé |
|---|---|---|---|
| Autécologie et climat | [ClimEssences — ONF/CNPF](https://climessences.fr/) | Fiches espèces selon 37 critères, sources et fiabilité ; compatibilités climatiques IKS ; exports cartographiques | **Référence et lien profond au départ. Autorisation écrite nécessaire** avant copie massive, indexation RAG ou redistribution hors ligne ; les CGU protègent textes, logiciels et algorithmes. |
| Diagnostic sylvo-climatique | [BioClimSol — CNPF](https://www.cnpf.fr/decouvrez-bioclimsol) | Croisement BIO–CLIM–SOL, vulnérabilité de parcelle, essences et interventions | **Partenariat ou module sous licence**, pas de scraping ni de clone. L'utilisation exige une [licence certifiante](https://www.cnpf.fr/nos-actions-nos-outils/outils-et-techniques/bioclimsol). |
| Itinéraires nationaux | [96 fiches CNPF pour 20 essences ou groupes](https://www.cnpf.fr/gestion-durable-des-forets/mise-en-oeuvre/fiches-itineraires-techniques-par-essence) | Taillis, futaies régulières/irrégulières, conversions, travaux et coupes | Corpus d'amorçage, mais général : chaque règle doit être filtrée par territoire et SRGS. **Autorisation CNPF requise** pour réutilisation/redistribution au-delà des usages permis. |
| Guides régionaux privés | [Publications régionales CNPF](https://www.cnpf.fr/se-former-s-informer/nos-publications/publications-regionales) | Essences, stations, diagnostics, sylviculture, travaux, sanitaire et réglementation locale | Registre exhaustif par délégation et territoire ; demander droits de structuration, indexation et diffusion. |
| Stations forestières | [CNPF — stations forestières](https://www.cnpf.fr/nos-actions-nos-outils/outils-et-techniques/les-stations-forestieres) | Clés terrain, topographie, sol, flore, potentialités et préconisations | Source locale prioritaire. Ne jamais appliquer un guide hors de sa zone et de son climat de validité. |
| Sylviculture publique | [Collection ONF — 51 guides et mémentos](https://www.onf.fr/onf/recherche-pour-les-tags-et-les-collections?collection=Guides+de+sylviculture) | Règles par essence/groupe, contexte biogéographique, fertilité, peuplement et objectif | Inventorier document par document. Les documents publics/officiels et les contenus éditoriaux n'ont pas nécessairement le même régime de réutilisation ; qualification juridique obligatoire. |
| Cadre privé | SRGS de chaque région CNPF | Méthodes et itinéraires admis pour les documents de gestion durable des forêts privées | **Couche réglementaire versionnée**, prioritaire sur un conseil général. Conserver région, date d'effet et texte remplacé. |
| Cadre public | [DRA et SRA](https://agriculture.gouv.fr/politique-forestiere-les-schemas-regionaux-damenagement-sra) | Objectifs et stratégie de gestion durable des forêts domaniales et des collectivités | Couche réglementaire distincte du SRGS, versionnée par territoire et type de propriété. |
| Données phytoécologiques | [SILVAE / EcoPlant / Digitalis](https://silvae.agroparistech.fr/) | Relevés géolocalisés, facteurs écologiques et couches SIG issues du laboratoire SILVA | **Ingestion prioritaire** lorsque la fiche confirme la Licence Ouverte ; conserver résolution, méthode, limites et citation de chaque couche. |
| Inventaire national | [Données brutes IGN de l'inventaire forestier](https://www.data.gouv.fr/datasets/donnees-brutes-de-l-inventaire-forestier) | Environ 6 000 placettes et 60 000 arbres mesurés par an, données éco-floristiques | **Licence Ouverte**. Utiliser pour analyses, contrôles et calibration ; les positions publiques sont arrondies au kilomètre. |
| Taxonomie | [TAXREF v18 et référentiels associés](https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353) | Identifiants taxonomiques, noms valides et synonymes | Référentiel canonique des taxons français ; contrôler la licence du paquet avant redistribution. |
| Habitats | [HABREF](https://www.patrinat.fr/fr/referentiel-habitats-habref-6184) | Typologies, hiérarchies, versions et correspondances d'habitats | Référentiel canonique des habitats ; conserver version et typologie d'origine. |
| Sols | [DoneSol — INRAE/GIS Sol](https://info-et-sols.val-de-loire.hub.inrae.fr/ressources/systemes-d-information/si-sol/donesol) | Études pédologiques, UCS/UTS, profils, horizons et analyses physico-chimiques | Accès et droits à contractualiser ; ne pas confondre donnée ponctuelle, unité cartographique et prédiction. |
| Provenances | [Registre national et régions de provenance MFR](https://agriculture.gouv.fr/fournisseurs-especes-reglementees-provenances-et-materiels-de-base-forestiers) | Sources de graines/plants, régions de provenance, matériels de base | Couche indispensable : une recommandation d'essence sans provenance est incomplète. |
| Éligibilité régionale | [Arrêtés régionaux MFR](https://agriculture.gouv.fr/materiels-forestiers-de-reproduction-arretes-regionaux-relatifs-aux-aides-de-letat-a) | Essences, provenances, densités et normes éligibles aux aides | Données réglementaires à mise à jour rapide, avec date d'effet et expiration. La Nouvelle-Aquitaine dispose notamment d'un arrêté du 6 mars 2026. |
| Santé des arbres | [ARCHI — CNPF](https://www.cnpf.fr/nos-actions-nos-outils/outils-et-techniques/archi) | Diagnostic visuel de dépérissement et potentiel de résilience par architecture | Protocole guidé, avec compétence/formation et essence prises en compte. **Ne diagnostique pas la cause.** |
| Santé des peuplements | [DEPERIS — ministère de l'Agriculture](https://agriculture.gouv.fr/la-methode-deperis-comment-quantifier-et-mesurer-letat-de-sante-dune-foret-et-son-evolution) | Quantification et suivi de l'état du houppier, toutes essences | Protocole déterministe et formulaire terrain. **Quantifie sans expliquer la cause.** |
| Surveillance sanitaire | [Département de la santé des forêts](https://agriculture.gouv.fr/les-actions-du-departement-de-la-sante-des-forets) | Observations, bioagresseurs, suivis et bilans régionaux | Veille versionnée ; séparer observation, signalement, risque et diagnostic confirmé. |
| Biodiversité potentielle | [IBP — CNPF/INRAE](https://www.cnpf.fr/nos-actions-nos-outils/outils-et-techniques/ibp-indice-de-biodiversite-potentielle) | Potentiel d'accueil, 10 facteurs, recommandations de gestion | Implémenter la version, le domaine d'application et le protocole exact. **Ne pas présenter comme inventaire réel de biodiversité.** |
| Suivis à long terme | [RENECOFOR — ONF](https://www.onf.fr/renecofor) | Placettes permanentes, arbres, sols, atmosphère et flore | Source de validation et de tendance ; protocole, fréquence et conditions d'accès doivent accompagner les données. |
| Croissance et dynamique | [Capsis — modèles](https://capsis.cirad.fr/capsis/models) | Modèles de croissance, dynamique, mortalité, sécheresse et scénarios | Registre de modèles. Vérifier séparément code, données, licence, domaine de calibration et accès ; seule une partie est distribuée librement. |
| Génétique forestière | [EUFORGEN — guides techniques](https://www.euforgen.org/publications/technical-guidelines) | Conservation et usage des ressources génétiques de plus de 40 espèces | Complément aux MFR et à l'autécologie ; vérifier la licence de chaque publication. |
| Autécologie européenne | [European Atlas of Forest Tree Species — JRC](https://forest.jrc.ec.europa.eu/en/european-atlas/) | Distribution, habitat, usages, menaces et préférences climatiques | Source européenne secondaire de contrôle et d'enrichissement, avec version/DOI. |
| Données forestières ouvertes | [Open Data ONF](https://www.onf.fr/onf/%2B/35%3A%3Aopendata-onf.html) | Contours, parcelles publiques, aménagements et catalogues thématiques | Ingérer uniquement les jeux explicitement ouverts, selon leur licence propre. |

### Lecture juridique essentielle

- Les [mentions légales de ClimEssences](https://climessences.fr/mentions-legales) interdisent en principe la copie, la modification et la distribution sans autorisation écrite, hors usages personnels/privés/non commerciaux prévus.
- Les [mentions légales du CNPF](https://www.cnpf.fr/mentions-legales) formulent une restriction comparable pour les contenus du site.
- Les [mentions légales ONF](https://www.onf.fr/onf/%2B/21c%3A%3Amentions-legales.html) distinguent informations/documents publics et autres contenus protégés. Cette distinction doit être faite document par document.
- La présence d'un bouton « télécharger » ou « exporter » n'accorde pas automatiquement le droit d'intégrer le contenu dans un produit commercial, un index vectoriel ou un pack hors ligne redistribué.

## 4. Ontologie scientifique minimale

Le métamodèle universel de Quintessences peut rester la racine, mais il lui faut des profils forestiers explicites.

### 4.1 Taxon

Champs minimaux :

- identifiant TAXREF et, si utile, EPPO/GBIF ;
- nom scientifique accepté, auteur et rang ;
- synonymes historiques ;
- noms vernaculaires par langue/région ;
- statut indigène, introduit ou cultivé, avec territoire ;
- validité temporelle de la taxonomie.

### 4.2 AutecologyProfile

Pour chaque essence, stocker des observations sourcées et non une simple note globale :

- optimum et limites thermiques ;
- besoin hydrique, sensibilité à la sécheresse et à l'engorgement ;
- continentalité, gel précoce/tardif, chaleur extrême ;
- bilan hydrique et saison critique ;
- niveau trophique, pH, saturation en bases, calcaire actif ;
- texture, compaction, drainage, profondeur, réserve utile ;
- lumière, compétition et dynamique de succession ;
- enracinement, sensibilité au vent, neige et incendie ;
- altitude, exposition et topographie ;
- agents biotiques et pathologies majeures ;
- comportement juvénile/adulte et régénération ;
- plasticité, provenance et variabilité génétique ;
- valeur, unité, saison, stade de vie, territoire, méthode, incertitude et source précise.

Les valeurs contradictoires restent visibles dans un `ConflictRecord`. Elles ne doivent pas être moyennées automatiquement.

### 4.3 StationType et StationObservation

`StationType` décrit une unité conceptuelle issue d'un guide ; `StationObservation` décrit ce qui est réellement observé sur une parcelle.

Champs clés :

- guide, version, zone et polygone de validité ;
- SER/GRECO/région naturelle ;
- topographie, exposition et confinement ;
- substrat, sol, horizons, humus et hydromorphie ;
- flore indicatrice et groupes écologiques ;
- réserve utile mesurée ou estimée, avec méthode ;
- contraintes, potentialités et incertitude de détermination ;
- clé suivie, réponses saisies et embranchement obtenu ;
- compatibilités proposées par le guide, séparées des observations.

### 4.4 SiteIndexModel et FertilityClass

Une classe de fertilité ne doit **jamais** être stockée comme une valeur universelle `1`, `2` ou `3`.

Le mémento ONF du [pin d'Alep](https://www.onf.fr/outils/ressources/127da569-d109-4abb-b533-379feaa78da7/%2B%2Bversions%2B%2B/1/%2B%2Bparas%2B%2B/3/%2B%2Bass%2B%2B/1/%2B%2Bi18n%2B%2Bdata%3Afr?_=1740574301.730001&download=1) définit par exemple la fertilité à partir de la hauteur dominante des 100 plus grosses tiges par hectare à 50 ans : classe 1 au-dessus de 14 m, classe 2 entre 10 et 14 m, classe 3 sous 10 m, avec une convention d'âge précisée. D'autres guides emploient d'autres âges, courbes et conventions.

Objet minimal :

```text
FertilityClass
  id: ONF.PINUS_HALEPENSIS.HDOM50_AGE_STUMP.C1
  species_id: TAXREF:...
  model_id: ...
  variable: dominant_height
  dominant_definition: 100_largest_stems_per_ha
  reference_age_years: 50
  age_convention: age_at_stump
  lower_bound_m: 14
  lower_inclusive: false
  calibration_region: ...
  valid_stand_types: ...
  extrapolation_policy: forbidden | warning | modelled
  source_document_id: ...
  source_page_table: ...
  uncertainty: ...
```

`SiteIndexModel` doit en plus conserver équation ou table, paramètres, méthode d'ajustement, échantillon de calibration, domaine d'âge/hauteur, erreur, publication et règles d'interpolation/extrapolation.

### 4.5 SilviculturalSystem, SilviculturalRule et Intervention

`SilviculturalSystem` : futaie régulière, futaie irrégulière, taillis, taillis sous futaie, mélange, conversion, transformation, libre évolution, etc.

`SilviculturalRule` doit contenir :

- contexte requis : essence, mélange, station, fertilité, structure, âge/hauteur, propriété, région et objectif ;
- déclencheur observable ;
- action proposée : dépressage, éclaircie, désignation, régénération, enrichissement, coupe sanitaire, travaux ;
- intensité et variables cibles : N/ha, G/ha, diamètre, hauteur, espacement, prélèvement ;
- périodicité, rotation et critères de passage ;
- contraintes et veto ;
- résultats attendus et risques ;
- niveau de preuve ;
- source exacte, page/table/figure ;
- dates d'effet, révision et remplacement ;
- validateur humain.

Une règle extraite par LLM reste `DRAFT`. Elle ne peut devenir `APPROVED` qu'après revue humaine et tests.

### 4.6 ProvenanceMaterial

Une proposition de plantation doit relier :

- essence ;
- région de provenance et matériel de base ;
- catégorie réglementaire ;
- zone d'utilisation ;
- admissibilité aux aides ;
- densité/norme des plants ;
- version de l'arrêté ;
- disponibilité réelle, si connue ;
- recommandation génétique et risque de maladaptation.

### 4.7 DiagnosticProtocol et HealthRisk

Le protocole doit préciser : critères, saison, essence, compétence attendue, matériel, échelle, répétabilité, seuils, version et limites.

Les résultats doivent distinguer :

- symptôme observé ;
- note calculée ;
- syndrome ou état ;
- agent causal suspecté ;
- agent confirmé ;
- niveau de confiance ;
- action de surveillance ;
- conseil sylvicole.

### 4.8 EvidenceStatement et ConflictRecord

Toute assertion exploitable doit porter au minimum :

- identifiant stable ;
- formulation atomique ;
- source, auteur/organisme et version ;
- page, tableau, figure ou enregistrement ;
- territoire, échelle et période ;
- type de preuve : mesure, expérimentation, modèle, synthèse, expertise, réglementation ;
- grade de preuve et incertitude ;
- date d'extraction, extracteur, relecteur et date de validation ;
- statut : `DRAFT`, `REVIEWED`, `APPROVED`, `DEPRECATED`, `REJECTED` ;
- relations de contradiction, confirmation ou remplacement.

## 5. Chaîne de décision professionnelle

Le résultat ne doit pas être « l'IA recommande le Douglas ». La chaîne correcte est :

1. **Observations terrain** : localisation, peuplement, sol, topographie, flore, sanitaire et qualité des mesures.
2. **Diagnostic stationnel** : clé locale, unité possible, alternatives et incertitude.
3. **Filtre réglementaire** : SRGS ou DRA/SRA, zonages, Natura 2000, MFR et restrictions locales.
4. **Compatibilité autécologique** : eau, nutrition, sol, climat, risques et provenance.
5. **Analyse climatique** : période de référence, horizon, scénario, modèle et dispersion.
6. **Fertilité/croissance** : indice de station et modèle dans son domaine valide.
7. **Options sylvicoles** : plusieurs itinéraires compatibles, jamais une réponse unique forcée.
8. **Effets croisés** : production, biodiversité, carbone, eau, risque incendie, sanitaire et économie.
9. **Recommandation explicable** : hypothèses, alternatives rejetées, incertitudes et observations manquantes.
10. **Décision humaine** : validation, modification ou rejet par le professionnel.

Le moteur de règles réalise les filtres, calculs, seuils et veto. Le LLM explique le chemin, cite les preuves et aide à interroger le dossier.

## 6. Contrat de sortie : le passeport de décision

Chaque diagnostic ou scénario doit produire un passeport lisible et exportable contenant :

- observations mesurées, avec qualité et protocole ;
- résultats calculés de façon déterministe ;
- résultats de modèles, séparés des mesures ;
- recommandations issues de documents ou d'experts ;
- textes réglementaires applicables ;
- sources exactes, version, pages et liens ;
- scénario climatique, période et résolution ;
- domaine de validité et extrapolations ;
- désaccords entre sources ;
- données absentes susceptibles de changer la conclusion ;
- alternatives et raisons de leur rejet ;
- date de calcul, versions des moteurs et du pack ;
- identité/statut du validateur humain.

L'interface doit afficher visuellement cinq catégories différentes : **observé**, **calculé**, **modélisé**, **documenté/recommandé**, **incertain**.

## 7. Pipeline d'acquisition et de validation

### Étape A — Registre des sources et des droits

Créer `ScientificSourceRegistry` avec : organisme, propriétaire, URL, identifiant, version, date, territoire, fréquence de mise à jour, licence, usage commercial, droit d'indexation, droit de créer des dérivés, droit de redistribution hors ligne, attribution, contact et empreinte SHA-256.

Statuts juridiques proposés :

- `OPEN_CONFIRMED` ;
- `PUBLIC_DOCUMENT_REUSE_CONFIRMED` ;
- `PERMISSION_REQUIRED` ;
- `LICENSED_PARTNER` ;
- `METADATA_ONLY` ;
- `DO_NOT_INGEST` ;
- `LEGAL_REVIEW_PENDING`.

### Étape B — Conservation brute

- instantané immuable ;
- fichier original et métadonnées ;
- empreinte, date de récupération et URL ;
- version du droit applicable ;
- aucun écrasement : une nouvelle édition crée une nouvelle ressource.

### Étape C — Extraction assistée

- extraction texte/OCR conservant la pagination ;
- détection des titres, tableaux, figures, unités et notes ;
- formules converties en représentation vérifiable, pas seulement en prose ;
- tables conservées comme tables ;
- chaque segment relié à la page et à la zone d'origine ;
- LLM autorisé à créer des **candidats**, jamais à les approuver.

### Étape D — Normalisation

- unités SI et unité originale ;
- taxons reliés à TAXREF ;
- territoires reliés aux SER/GRECO et limites administratives ;
- dates, scénarios climatiques et conventions d'âge explicites ;
- noms de traitements et variables dendrométriques contrôlés ;
- aucune valeur absente transformée en zéro.

### Étape E — Validation scientifique

- revue par un curateur de données ;
- revue métier par un forestier compétent ;
- arbitrage des conflits, sans suppression de la divergence ;
- jeu de cas de référence par essence, station et région ;
- statut et signature de validation ;
- relecture périodique ou déclenchée par une nouvelle version source.

### Étape F — Publication

- PostgreSQL/PostGIS comme vérité canonique de Quintessences ;
- objets et documents dans un stockage immuable ;
- projections de recherche et Zvec entièrement régénérables ;
- SQLite/Room comme vérité locale du pack mobile ;
- index vectoriel dérivé, jamais seul détenteur de la connaissance.

## 8. RAG scientifique : exigences minimales

Le RAG doit rechercher d'abord par métadonnées structurées, puis par similarité sémantique.

Filtres obligatoires :

- taxon et synonymes ;
- territoire/SER/GRECO ;
- guide de station et version ;
- propriété privée, domaniale ou collectivité ;
- traitement sylvicole ;
- classe de fertilité nommée ;
- scénario et horizon climatiques ;
- date d'effet réglementaire ;
- niveau de preuve ;
- statut de validation ;
- droits autorisant l'usage demandé.

Règles de réponse :

- citation de page/table pour chaque conseil concret ;
- abstention si aucune preuve approuvée ne couvre le contexte ;
- signalement des contradictions ;
- interdiction de convertir une corrélation en causalité ;
- interdiction de compléter silencieusement une donnée manquante ;
- priorité aux règles approuvées sur le texte généré ;
- aucune prescription automatique fondée uniquement sur des embeddings.

## 9. Packs scientifiques hors ligne

Un pack doit être territorial et versionné, par exemple :

```text
fr-na-ser-g12-sylviculture-2026.3
```

Contenu :

- taxons et synonymes utiles ;
- stations et clés autorisées ;
- autécologie structurée des essences ciblées ;
- règles sylvicoles approuvées ;
- courbes/indices de fertilité et modèles autorisés ;
- réglementation et MFR en vigueur ;
- protocoles de terrain ;
- cartes et couches ouvertes ;
- index lexical et vectoriel ;
- citations et métadonnées, même lorsque le document complet ne peut pas être distribué.

Manifeste :

- version, territoire, dépendances et taille ;
- contenu et licences ;
- date de création, `valid_from`, `review_after` et `supersedes` ;
- empreinte de chaque fichier ;
- signature cryptographique ;
- version minimale de l'application ;
- procédure de reprise, vérification, rollback et suppression.

Les documents protégés non autorisés ne doivent pas être cachés dans le pack. Le pack peut conserver leur métadonnée, une citation courte autorisée et un lien, mais pas leur texte intégral ni un index permettant de le reconstruire.

## 10. Programme pilote recommandé : Nouvelle-Aquitaine

La bonne stratégie n'est pas de prétendre couvrir immédiatement 149 essences et toute la France. Le premier corpus validé doit couvrir un territoire réel et un ensemble limité d'essences majeures.

### Périmètre proposé

- Nouvelle-Aquitaine, avec découpage SER/GRECO ;
- 12 à 20 essences choisies avec un forestier référent ;
- priorité aux chênes sessile, pédonculé et pubescent, châtaignier, hêtre, pin maritime, Douglas, pin sylvestre, pin laricio, peupliers et essences d'accompagnement locales ;
- guides de stations couvrant les zones pilotes ;
- SRGS Nouvelle-Aquitaine ;
- arrêté MFR Nouvelle-Aquitaine du 6 mars 2026 ;
- guides ONF/CNPF pertinents pour les chênes du Sud-Ouest et le pin maritime ;
- données IGN, SILVAE et DSF pertinentes ;
- trois horizons : actuel, milieu de siècle, fin de siècle, avec scénarios explicités.

### Livrable pilote

- 100 % des assertions utilisées en production reliées à une source précise ;
- 100 % des classes de fertilité contextualisées ;
- 100 % des règles avec domaine de validité et statut de validation ;
- au moins 50 cas « or » validés par des professionnels ;
- tests de non-régression à chaque nouvelle version ;
- un pack hors ligne signé ;
- une interface qui sait répondre « données insuffisantes ».

## 11. Backlog à ajouter au MASTER_PLAN

| ID | Priorité | Action | Critère d'acceptation |
|---|---:|---|---|
| SCI-001 | P0 | Créer le registre des sources, licences et droits | Aucun document n'entre en RAG ou pack sans statut juridique explicite. |
| SCI-002 | P0 | Marquer toutes les données autécologiques actuelles selon leur preuve | Toute valeur est `APPROVED`, `INDICATIVE` ou `UNKNOWN`; aucune heuristique n'est présentée comme certitude. |
| SCI-003 | P0 | Installer TAXREF comme taxonomie canonique | Tous les taxons et synonymes sont résolus par identifiant stable. |
| SCI-004 | P0 | Implémenter `EvidenceStatement`, citations fines et conflits | Toute assertion professionnelle retourne source, page, version, territoire et niveau de preuve. |
| SCI-005 | P0 | Refaire l'indice de station et les classes de fertilité | Aucun entier de classe sans modèle, essence, âge, convention et région. |
| SCI-006 | P0 | Séparer observations, calculs, modèles et recommandations dans l'UI | Le passeport de décision affiche les cinq catégories et les incertitudes. |
| SCI-007 | P0 | Ouvrir les négociations CNPF/ONF | Réponse écrite sur indexation, dérivés, commercial, offline, mises à jour et attribution. |
| SCI-008 | P1 | Implémenter le schéma forestier spécialisé | Autécologie, stations, fertilité, règles, modèles, MFR et protocoles sont requêtables. |
| SCI-009 | P1 | Construire le moteur déterministe de règles | Les prescriptions reposent sur règles approuvées, filtres et veto, pas sur génération libre. |
| SCI-010 | P1 | Constituer le pilote Nouvelle-Aquitaine | 12–20 essences, guides locaux, SRGS/MFR, 50 cas or et validation professionnelle. |
| SCI-011 | P1 | Industrialiser l'extraction PDF/table/formule | Chaque candidat conserve page/zone et passe par revue avant publication. |
| SCI-012 | P1 | Déployer le RAG hybride filtré | Métadonnées + lexical + vectoriel ; abstention et citations obligatoires. |
| SCI-013 | P1 | Produire les packs scientifiques signés | Installation, checksum, reprise, version, expiration et rollback testés hors réseau. |
| SCI-014 | P1 | Versionner SRGS, DRA/SRA et MFR | Une règle remplacée reste historisée ; l'application avertit si le pack est périmé. |
| SCI-015 | P1 | Ajouter ARCHI/DEPERIS/IBP avec leurs limites | L'UI ne transforme jamais état, potentiel ou symptôme en causalité/certitude. |
| SCI-016 | P2 | Intégrer les modèles Capsis sélectionnés | Licence, domaine, validation, erreur et reproductibilité documentés par modèle. |
| SCI-017 | P2 | Étendre à trois régions et 40–60 essences | Même niveau de preuve et mêmes tests que le pilote. |
| SCI-018 | P3 | Couverture nationale et partenariats institutionnels | Corpus national maintenu par flux de mise à jour et comité scientifique. |

Ces actions renforcent directement les éléments existants `D-03`, `D-35`, `F-08`, `F-11` et `F-12`. `AutecologyExpansion` ne doit pas être simplement restauré avec des valeurs anciennes : son modèle de données doit d'abord être aligné sur ce référentiel scientifique.

## 12. Demande de partenariat à adresser au CNPF et à l'ONF

Questions à faire confirmer par écrit :

1. Existe-t-il une API ou un export machine lisible des fiches, critères, sources et versions ?
2. Quintessences peut-il indexer les contenus dans un RAG, y compris pour un usage commercial ?
3. Peut-il dériver des règles structurées, seuils et profils autécologiques ?
4. Peut-il distribuer ces dérivés et/ou extraits dans des packs chiffrés hors ligne ?
5. Quelles citations, mentions, logos et liens sont obligatoires ?
6. Quelles données doivent rester accessibles uniquement via leur service ?
7. Existe-t-il un flux de mises à jour et des identifiants de version stables ?
8. Une intégration officielle de BioClimSol ou ClimEssences est-elle envisageable ?
9. Quel protocole de validation scientifique et quelle responsabilité contractuelle sont requis ?
10. Un partenariat pilote en Nouvelle-Aquitaine peut-il associer un comité d'experts et des cas terrain ?

## 13. Lignes rouges

- Ne pas aspirer ClimEssences, BioClimSol ou les publications CNPF/ONF puis les redistribuer sans autorisation.
- Ne pas présenter BioClimSol comme un algorithme ouvert à reproduire.
- Ne pas laisser un LLM calculer ou inventer seul une prescription sylvicole.
- Ne pas créer une « classe de fertilité 1 » universelle.
- Ne pas confondre compatibilité climatique, adaptation stationnelle et recommandation finale.
- Ne pas confondre carte modélisée et observation terrain.
- Ne pas confondre IBP et biodiversité réellement inventoriée.
- Ne pas confondre ARCHI/DEPERIS et diagnostic causal.
- Ne pas cacher les conflits entre sources derrière une moyenne ou un score unique.
- Ne pas proposer une essence de plantation sans provenance/MFR et version réglementaire.
- Ne pas conserver une réglementation hors ligne sans date de révision et avertissement de péremption.
- Ne pas publier une règle professionnelle sans page source, domaine de validité, validateur et tests.

## 14. Conclusion

Cette extension n'est pas une fonctionnalité secondaire. Elle matérialise directement les principes de Quintessences : **science avant opinion, connaissance avant code, traçabilité et explicabilité**.

Le véritable avantage concurrentiel ne sera pas le nombre de PDF, le nombre d'essences affichées ou la présence d'un LLM. Ce sera la capacité à répondre :

> « Cette recommandation provient de quelle preuve, pour quelle station, quelle essence, quelle fertilité, quel climat, quel territoire, quelle réglementation, avec quelle incertitude, et qui l'a validée ? »

Si GeoSylva répond correctement à cette question, y compris hors ligne, l'application peut devenir un outil professionnel crédible. Sinon, elle reste un assistant riche mais indicatif.
