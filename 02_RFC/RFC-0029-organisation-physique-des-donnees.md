# RFC-0029 — Organisation physique des données : schémas par domaine et stockage des actifs

| Champ | Valeur |
|---|---|
| **ID** | RFC-0029 |
| **Statut** | Proposée — en attente d'arbitrage du Fondateur |
| **Auteur** | Architecte, sous autorité du Fondateur |
| **Date** | 2026-07-30 |
| **Périmètre** | Base GSIE, stockage objet, tous les moteurs |
| **Nature** | Décision d'architecture |
| **Précédents** | `ADR-001` (héritage par table de classe), `ADR-002` (métamodèle v6.2), `GSIE-CON-005` (traçabilité), `NOMENCLATURE_SOURCES.md`, `DEC-000038` |

## 1. Objet

Le Fondateur pose la question suivante : chaque moteur doit-il disposer de sa
propre base de données — botanique, météo, feu, eau, cartographie — cloisonnée,
partageant la même nomenclature, chacune interrogeable par n'importe quel
moteur ?

La présente RFC répond : **le besoin est fondé, le cloisonnement est nécessaire,
mais il se réalise par des schémas et non par des bases séparées.** Elle décide
en outre où vivent les actifs volumineux — rasters `.tif`, séries
météorologiques — que la version serveur de GSIE recevra en nombre.

## 2. Le diagnostic est exact

Les **93 types enregistrés** vivent aujourd'hui dans le schéma `public`, sans
aucune séparation : la botanique, l'hydrologie, la gouvernance, les données
RGPD, les décisions du forestier, tout au même endroit et indifférencié.

Aucun rôle PostgreSQL ne distingue ce qu'un moteur peut lire de ce qu'il ne
devrait jamais atteindre. Le Climate Engine peut lire `consent` et
`data_subject`. Rien ne l'en empêche au niveau de la base : la protection
repose entièrement sur le RBAC applicatif, c'est-à-dire sur du code.

Cette absence d'organisation est réelle, et personne ne l'avait posée.

## 3. Pourquoi des bases séparées seraient un recul

### 3.1 Trois cent quatorze clés étrangères

`ADR-001` impose l'héritage par table de classe : la clé primaire de chaque
type **est** une clé étrangère vers `resource.id`. Le dénombrement en base est
sans ambiguïté :

```
SELECT count(*) FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'resource';
→ 314
```

PostgreSQL n'a pas de clé étrangère inter-bases. Séparer physiquement convertit
ces 314 contraintes vérifiées par le moteur en conventions surveillées par le
code applicatif — c'est-à-dire par rien de contraignant.

Ce n'est pas une objection théorique. Les défauts corrigés le 29 et le 30
juillet appartiennent tous à cette famille, et c'est PostgreSQL qui les a
arrêtés :

| Défaut | Ce que la clé étrangère a empêché |
|---|---|
| `revision.author_id` sans Agent matérialisé | Une révision attribuée à un auteur inexistant |
| `ResourceDiff` sans ligne racine | Un diff hors du métamodèle |
| Décision citant une recommandation absente | Une trace inexploitable — on sait qu'un forestier a refusé, sans pouvoir dire quoi |

Sans contrainte physique, ces trois écritures auraient réussi. Elles auraient
produit des références **vérifiables en apparence** qui ne renvoient à rien —
précisément la classe de défaut la plus coûteuse à détecter, parce qu'elle ne
provoque aucune erreur.

### 3.2 La corrélation croisée est la raison d'être du système

`StationContexte` agrège des blocs issus de la pédologie, du climat, de la
botanique, de la dynamique forestière, du SIG. Le Correlation Engine et le
Reasoning Engine existent pour établir des liens **entre** ces domaines.

L'exemple donné par le Fondateur pour Ignis — lier l'évapotranspiration à la
réserve utile — est une jointure entre climat et pédologie. En bases séparées,
ce n'est plus une jointure mais une reconstitution applicative : sans plan
d'exécution, sans transaction, sans `ST_Contains` entre les deux jeux.

### 3.3 Une nomenclature non contrainte dérive

Le Fondateur demande « la même base de règles et de nomenclature ». C'est
l'exigence la plus juste de sa proposition, et c'est celle qui condamne le
découpage.

`variables_mesurables_data.py` énonce le problème : sans référentiel commun,
« RUM », « réserve utile » et `reserve_utile_mm` désignent la même grandeur
sans qu'aucun rapprochement soit possible ; une règle est retournée puis échoue
en silence.

Un vocabulaire ne vaut que s'il est **contraint**, par une clé étrangère. En
bases séparées, il redevient une convention. Et une convention non contrainte
dérive sans bruit : c'est exactement ce qui s'est produit avec les six colonnes
portant `doc=` au lieu de `comment=`, dont les descriptions n'existaient que
côté Python et qu'aucune lecture du schéma ne montrait.

## 4. Décision

### 4.1 Une base, des schémas par domaine

Le cloisonnement se fait par **schémas PostgreSQL**. Les clés étrangères les
traversent ; les droits s'y appliquent ; chaque domaine modélise ce qu'il doit.

| Schéma | Contenu | Justification |
|---|---|---|
| `gsie_noyau` | `resource`, `source`, `citation`, `assertion`, `evidence_assessment`, `place`, `scale_context`, `revision`, `resource_diff`, vocabulaire | Tout référence ce noyau. Il porte la traçabilité et la nomenclature |
| `gsie_botanique` | Taxons, autécologie, gradients trophique et hydrique, clés de détermination | Flore forestière, référentiels taxonomiques |
| `gsie_climat` | Stations, normales, indices, scénarios | Météo-France, DRIAS |
| `gsie_pedologie` | Sols, horizons, réserve utile | RRP, INRAE |
| `gsie_hydro` | Bassins versants, masses d'eau, débits, piézométrie | Ignis, Hydro |
| `gsie_feu` | Historique d'incendies, indices de danger, combustibles | Ignis |
| `gsie_foret` | Peuplements, itinéraires, règles sylvicoles, dynamique | GeoSylva |
| `gsie_gouvernance` | Décisions, recommandations, validations, apprentissage | Chaîne de raisonnement |
| `gsie_rgpd` | `consent`, `data_subject`, `sensitivity_classification`, `access_policy` | **Isolement le plus strict** — voir §4.2 |

Le graphe AGE (`gsie_knowledge_graph`) et `ag_catalog` restent inchangés.

### 4.2 Des rôles PostgreSQL par moteur

Chaque moteur reçoit un rôle qui possède `USAGE` sur son schéma et sur
`gsie_noyau`, et rien d'autre. Le schéma `gsie_rgpd` n'est accessible qu'au
rôle `gsie_rgpd_manager`.

La protection cesse ainsi de reposer sur le seul RBAC applicatif. Les deux se
cumulent : le code refuse par métier, la base refuse par droit. Un défaut du
premier — comme la fuite RGPD par filtre de type vide, corrigée le 29 juillet —
ne suffit plus à exposer la donnée.

Le RLS déjà en place (`20260727_0004_rls_tables_sensibles`) est conservé.

### 4.3 Les octets sortent, la référence reste

C'est l'invariant central de cette RFC, et il vaut pour tous les actifs
volumineux à venir.

> **Le noyau conserve la référence, l'extérieur conserve les octets.**

Aucun raster, aucune série temporelle n'entre en table relationnelle. Mais
aucun n'existe non plus sans sa ligne dans le noyau. Le métamodèle le prévoit
déjà, et — comme pour la persistance des décisions — cette capacité n'est pas
branchée :

| Type existant | Champs déjà exigés | Rôle |
|---|---|---|
| `source` | `title`, `subtype`, `source_nature` | Qui publie |
| `distribution` | `access_method`, `licence` | Comment on y accède, sous quel droit |
| `data_asset` | `checksum`, `archived_at`, `format`, `size_bytes` | L'octet exact, daté |
| `scale_context` | `grain_m2` | La résolution native |
| `rights_statement` | `licence`, `usage_rights` | Ce qu'on a le droit d'en faire |

Un `.tif` versé dans le stockage objet est donc décrit par un `data_asset`
portant son empreinte et sa date d'archivage, rattaché à une `distribution`
portant sa licence, elle-même rattachée à une `source`. Sa résolution native
vit dans `scale_context.grain_m2`.

Conséquence directe : une carte affichée dans GeoSylva peut toujours dire d'où
elle vient, sous quelle licence, à quelle résolution, et si l'octet servi est
bien celui qui a été archivé. Sans cette chaîne, une donnée disparue ne dira
jamais rétrospectivement sous quelle licence elle était publiée
(`NOMENCLATURE_SOURCES.md` §1).

### 4.4 Deux stockages hors base, et seulement deux

**Stockage objet compatible S3** pour les rasters, tuiles, archives et pièces
jointes. `object_storage.py` existe déjà, avec `LocalStorage` pour le
développement et `S3Storage` à implémenter. Le confinement des clés y a été
renforcé et couvert le 30 juillet.

**Séries temporelles** pour les observations météorologiques et hydrologiques :
tables partitionnées par période dans `gsie_climat` et `gsie_hydro`.

La ligne de partage n'est pas le domaine, c'est **la nature de la donnée** :

| Nature | Où | Pourquoi |
|---|---|---|
| Connaissance — une affirmation sourcée, qu'un moteur infère | Base, schéma de domaine | Doit porter source, niveau de preuve, citation ; doit être jointe |
| Observation — un relevé horodaté, volumineux, refetchable | Tables partitionnées | Volume, cycle de vie propre ; n'est pas inférée directement |
| Octet — raster, archive, document | Stockage objet | N'est pas une ligne relationnelle |

**La Flore forestière relève de la première catégorie.** Les gradients trophique
et hydrique, les tolérances, les exigences en lumière sont des affirmations
scientifiques : chacune doit porter sa source et son niveau de preuve. Les
sortir du noyau les couperait de `source`, `citation` et `assertion` — elles
deviendraient consultables mais **non inférables**, ce qui ôte l'essentiel de
leur valeur. C'est le contenu qui a le plus besoin d'être dans le graphe.

## 5. Ce qui ne change pas

- `ADR-001` et `ADR-002` restent intacts : mêmes types, mêmes clés, même
  héritage. Un schéma est un espace de noms, pas un modèle différent.
- `CON-010` : aucune suppression physique, révisions inchangées.
- Le code applicatif : SQLAlchemy porte le schéma dans `__table_args__`, les
  requêtes ne changent pas.
- Le RBAC applicatif reste en place — il se double d'une protection en base, il
  ne s'y substitue pas.

## 6. Conséquences

**Migration lourde.** Déplacer 93 tables entre schémas est une opération
`ALTER TABLE … SET SCHEMA` par table, avec mise à jour de tous les modèles.
Faisable, mais d'autant plus coûteuse que la base grossit — **à faire tôt**.

**Le contrôle de dérive strict devient l'instrument de sûreté.** Il compare le
registre SQLAlchemy à la base ; il détectera toute table restée dans `public`
ou tout modèle dont le schéma déclaré ne correspond pas. Il a déjà rattrapé
trois erreurs de ce genre.

**Rôles à créer et à distribuer** : autant que de moteurs, plus le rôle RGPD.
Leur gestion opérationnelle relève du déploiement, pas de cette RFC.

## 7. Critères d'acceptation

1. Aucune table applicative ne subsiste dans `public`.
2. Toute clé étrangère vers `gsie_noyau` est vérifiée et fonctionnelle après
   migration — le compte de 314 est conservé ou expliqué.
3. Un rôle de moteur ne peut pas lire une table d'un schéma qui ne lui est pas
   accordé — vérifié par test d'intégration, pas par revue.
4. Le rôle d'un moteur non-RGPD se voit refuser `SELECT` sur `gsie_rgpd`.
5. Tout `data_asset` enregistré porte `checksum` et `archived_at` non nuls.
6. Un raster servi à un client est rattachable à sa `source`, sa `licence` et
   son `grain_m2` par une seule requête.
7. Le contrôle de dérive passe sans tolérance.

## 8. Périmètre du premier lot

Élargir d'un coup serait risqué. Ordre proposé :

1. Créer `gsie_noyau` et y déplacer les tables de traçabilité — c'est le socle
   dont tout dépend.
2. Créer `gsie_rgpd` et l'isoler par rôle. **Priorité la plus haute** : c'est
   le seul schéma dont l'absence de cloisonnement porte un risque réglementaire.
3. Créer les schémas de domaine, un par un, en commençant par celui qui a le
   moins de dépendances croisées.
4. Brancher `data_asset` et `distribution` sur le stockage objet, avec
   `S3Storage`.
5. Partitionner les séries temporelles quand le premier volume réel arrive.

## 9. Contre-audit — ce que font les institutions comparables

Trois enseignements tirés de la pratique établie, sur demande du Fondateur.
Deux confirment la décision, un la **corrige**.

### 9.1 Le mapping RGPD doit être séparé des données pseudonymisées

C'est la correction, et elle porte sur le premier lot.

L'article 32 du RGPD ne demande pas seulement d'isoler les données
personnelles. Il exige que le **mécanisme de réversion** — la table de
correspondance entre pseudonyme et identité — soit conservé séparément des
données pseudonymisées elles-mêmes, sous contrôle d'accès distinct. Les
lignes directrices 01/2025 de l'EDPB le formulent en trois temps :
transformer la donnée, stocker la correspondance à part, restreindre l'accès.

Le §4.1 prévoyait un unique schéma `gsie_rgpd`. C'est insuffisant : un rôle
capable de lire ce schéma reconstituerait les identités. Deux schémas sont
nécessaires :

| Schéma | Contenu | Accès |
|---|---|---|
| `gsie_rgpd` | Données pseudonymisées, `consent`, `sensitivity_classification`, `access_policy` | Rôle `gsie_rgpd_manager` |
| `gsie_rgpd_identites` | `data_subject` et toute table de correspondance pseudonyme → identité | Rôle **distinct**, jamais accordé à un moteur |

Le bénéfice est concret : une compromission du premier schéma ne livre pas les
identités. Un seul schéma aurait donné l'apparence de la conformité sans sa
propriété principale.

### 9.2 Le catalogue séparé de la donnée — confirmé par INRAE

INRAE distribue ses données via **Data INRAE**, un entrepôt fondé sur
Dataverse, et **Geodata INRAE** pour le géographique. Le catalogue de
métadonnées y est distinct du stockage des jeux eux-mêmes, chaque jeu portant
un identifiant pérenne.

C'est exactement l'invariant du §4.3 — le noyau conserve la référence,
l'extérieur conserve les octets. La convergence est rassurante : ce n'est pas
une invention locale.

Second point convergent : Data INRAE a introduit en 2024 l'usage de
**vocabulaires contrôlés** pour ses mots-clés. GSIE a pris la même direction
avec `variables_mesurables_data.py`, et le §3.3 en fait l'argument central
contre le découpage en bases. Une institution de cette taille arrive à la même
conclusion sur la nécessité d'un vocabulaire contraint.

### 9.3 STAC et COG — la norme du domaine, que GSIE n'utilise pas encore

Le monde géospatial a une réponse établie au problème que pose la version
serveur : **STAC** (SpatioTemporal Asset Catalog), aujourd'hui norme OGC, pour
cataloguer les actifs, et **COG** (Cloud Optimized GeoTIFF) pour les stocker.

Un COG se lit **partiellement en HTTP** : un client peut obtenir la fenêtre qui
l'intéresse sans télécharger le fichier entier. Pour GeoSylva, sur un
téléphone en forêt, la différence n'est pas cosmétique.

L'inventaire de `data_asset` révèle un manque réel : il porte `format`,
`size_bytes`, `checksum`, `archived_at`, `original_uri` — mais **aucune emprise
spatiale ni temporelle**. La question que GeoSylva posera en premier — « quels
rasters couvrent cette station ? » — n'a donc pas de réponse par requête.

Trois orientations en découlent, à trancher par le Fondateur :

1. **Adopter COG comme format d'archivage** des rasters. Coût nul à
   l'ingestion, gain permanent à la lecture.
2. **Doter `data_asset` d'une emprise** — géométrie et intervalle temporel —
   ou le rattacher explicitement à `place` et à un contexte temporel. Sans
   cela, le catalogue n'est pas interrogeable spatialement.
3. **Aligner le vocabulaire sur STAC** là où il se recouvre, pour qu'un actif
   GSIE soit exportable en STAC Item sans traduction. L'interopérabilité que
   `GSIE-CON-005` vise s'arrête sinon aux frontières du projet.

Ces trois points sont des **ajouts**, pas des corrections : rien de ce qui
précède n'est invalidé.

### 9.4 Le raster out-db résout le trou d'emprise — mécanisme retenu

PostGIS distingue deux modes de stockage raster, et la pratique établie tranche
nettement pour les volumes que la version serveur recevra.

| Mode | Ce que la base contient | Conséquence |
|---|---|---|
| **in-db** | Le flux d'octets complet | 2 To de rasters font une base de 2 To — souvent davantage, la compression interne étant moins bonne que celle du format source |
| **out-db** | Un pointeur : **emprise, métadonnées et URI** | 2 To de rasters font quelques mégaoctets de table |

Le mode out-db est celui qui répond au §9.3 : **l'emprise est en base**, donc
`ST_Intersects` fonctionne, tandis que les octets restent dans le stockage
objet. « Quels rasters couvrent cette station ? » redevient une requête
spatiale ordinaire.

Le mécanisme se complète de lui-même : GDAL lit un raster distant par
**requêtes HTTP à plage d'octets**, et sur un format à tuilage interne — donc
sur un COG — obtient une fenêtre carrée en quelques requêtes seulement. Le
choix du COG au §9.3 et celui du out-db ici ne sont pas deux décisions, mais
une seule.

**Décision** : rasters en out-db, octets en stockage objet au format COG,
emprise et métadonnées en base. L'ordre de grandeur justifie à lui seul
l'écart — une base non spatiale dite « grande » pèse une vingtaine de
gigaoctets, là où le raster se compte en téraoctets, avec les conséquences
correspondantes sur la sauvegarde et la réplication.

### 9.5 Séries temporelles — hypertables ou partitionnement natif

Le §9 laissait la question ouverte. Le contre-audit permet de la poser
correctement, sans la trancher : elle dépend d'un arbitrage que le Fondateur
seul peut rendre.

| | Partitionnement natif | TimescaleDB |
|---|---|---|
| Ingestion | Comparable | Comparable |
| Requêtes agrégées | Ordinaires | Nettement plus rapides sur de gros volumes |
| Gestion des partitions | **Manuelle** — les créer d'avance, sans trou, et continuer à mesure que le temps passe | Automatique (`create_hypertable`) |
| Compression en colonnes | Non | Oui |
| Agrégats continus | À faire soi-même | Natifs |
| Dépendance | Aucune | Une extension à installer et suivre |

Les **agrégats continus** méritent attention : une normale climatique, une
moyenne mensuelle dérivée d'observations journalières, c'est exactement ce que
le Climate Engine calculera en boucle. Les entretenir à la main est faisable,
mais c'est du code à écrire et à surveiller.

**Réserve à vérifier avant toute décision** : la compression et les agrégats
continus relèvent, sauf erreur, de la *Timescale License* et non d'Apache 2.0.
Pour un projet qui enregistre `licence`, `usage_rights` et
`ai_training_allowed` sur chacune de ses sources, adopter une dépendance sans
en connaître les termes serait incohérent avec sa propre exigence. À établir
avant l'arbitrage, pas après.

**Recommandation prudente** : commencer en partitionnement natif, qui n'engage
rien, et ne basculer que si le volume réel le justifie — le §8 prévoit déjà de
partitionner « quand le premier volume réel arrive ». Le schéma des tables ne
change pas entre les deux options : le report ne coûte rien.

### 9.6 Vocabulaires — SKOS et Darwin Core

Le §3.3 pose que le vocabulaire doit être contraint. Reste à savoir **selon
quel modèle**, si l'on veut que la connaissance GSIE soit échangeable.

**SKOS** (*Simple Knowledge Organization System*) est une recommandation du W3C
et le modèle standard d'interopérabilité des vocabulaires — import, export,
partage, alignement — y compris pour des vocabulaires qui ne sont pas publiés
sur le web. C'est le cadre dans lequel exprimer `variables_mesurables` et le
vocabulaire des grandeurs.

**Darwin Core** (TDWG) est le standard d'échange des données de biodiversité,
et c'est le format que publie GBIF — dont GSIE consomme déjà l'API, aux côtés
de TAXREF. Aligner la partie taxonomique de `gsie_botanique` sur Darwin Core
n'est donc pas un ajout gratuit : c'est se conformer à ce que la source publie
déjà. Sa documentation type d'ailleurs les valeurs contrôlées en
`skos:Concept`, ce qui referme le cercle entre les deux standards.

Enfin, le métamodèle emploie déjà `agent` et `activity`, qui viennent de
**PROV-O** (W3C). L'alignement sur les standards n'est donc pas une direction
nouvelle : c'est la direction déjà prise, qu'il s'agit de tenir sur les
vocabulaires comme elle l'est sur la provenance.

**Orientation proposée** : exprimer les vocabulaires GSIE en SKOS, aligner la
taxonomie sur Darwin Core, et conserver l'alignement PROV existant. Aucune
migration lourde n'en découle — il s'agit de nommer et de structurer, pas de
déplacer.

## 10. Trois régimes de données, et une règle qui les départage

Le §4.4 distinguait connaissance, observation et octet. Cette partition est
insuffisante dès lors que GSIE consommera des flux WMS, WMTS, WFS, des API
cartographiques tierces et des catalogues distants. Il faut distinguer selon
**qui détient l'octet**.

| Régime | Exemple | GSIE détient | Reproductible dans dix ans |
|---|---|---|---|
| **Possédée** | COG archivé, jeu importé | L'octet, avec `checksum` et `archived_at` | **Oui** |
| **Référencée** | Couche WMS, tuiles WMTS, API tierce | Rien — seulement un contrat d'accès | **Non** |
| **Dérivée** | NDVI calculé, ré-échantillonnage, mosaïque | L'octet produit, et la méthode | Oui, **si** la provenance est écrite |

### 10.1 La règle

> **Ce qui fonde un diagnostic doit être archivé, jamais seulement référencé.**

Une couche WMS peut changer de contenu, de projection ou disparaître sans
préavis, et sans que son URL change. Un diagnostic rendu en 2026 qui citerait
une tuile WMS ne serait pas revérifiable en 2029 : la référence resterait
valide en apparence et ne prouverait plus rien.

C'est exactement la classe de défaut corrigée les 29 et 30 juillet — une
recommandation citant un diagnostic jamais lu, un taux arbitraire circulant
sous une citation `ADR-009`. Une source consultable n'est pas une source
vérifiable.

**Conséquence opérationnelle** : les services distants sont légitimes pour
**afficher**, jamais pour **inférer**. Dès qu'une donnée distante entre dans une
chaîne de raisonnement, elle est d'abord archivée en actif possédé, avec son
empreinte et sa date. Le coût est modeste — une tuile pèse quelques centaines
de kilooctets — et il achète la reproductibilité, que `GSIE-CON-005` exige.

Cette règle mérite d'être **encodée**, pas seulement écrite : le moteur
d'évidence doit refuser un `evidence_level` supérieur à `F` pour une assertion
dont la seule source est une `distribution` en accès `ogc_wms`, `ogc_wmts` ou
`api_rest` sans actif archivé correspondant.

### 10.2 Le métamodèle l'anticipait déjà

`AccessMethod` porte onze valeurs, dont **`ogc_wms`, `ogc_wfs`, `ogc_wmts`,
`ogc_wcs` et `stac_api`**. La distinction entre accès distant et fichier
téléchargé (`file_download`, `file_import`) est donc déjà exprimable.

C'est la troisième fois dans cette session qu'une capacité conçue se révèle
non branchée — après les types `decision`/`recommendation` et le couple
`data_asset`/`distribution`. Le métamodèle v6.2 est plus riche que le code qui
l'emploie.

Pour les données **dérivées**, `activity` (PROV-O) existe également, avec
`started_at`, `ended_at` et `agent_id`. Un NDVI calculé depuis une scène
Sentinel doit produire une `activity` reliant l'actif d'entrée à l'actif de
sortie. Sans elle, un indice ne dit ni de quoi ni comment il a été tiré — et
redevient un nombre sans origine.

### 10.3 Vecteurs

Les vecteurs — parcelles, bassins versants, zonages, périmètres de protection —
sont des lignes PostGIS ordinaires dans leur schéma de domaine. Aucun
traitement particulier : c'est le cas nominal de PostGIS, et le volume reste
modeste face aux rasters.

Seule exigence : leur `place` doit porter la géométrie et le
`scale_context.grain_m2` doit dire à quelle échelle le tracé fait sens. Un
périmètre saisi au 1:100 000 employé pour une décision à la parcelle est une
erreur silencieuse — le grain la rend visible.

### 10.4 Indexation — un constat corrigé après vérification

**Rectification.** Une version antérieure de cette RFC annonçait « 2 index
GiST sur 118 tables » comme un manque structurel. Le contre-audit établit que
c'est **faux** : la base ne porte que **deux colonnes géométriques**,
`place.geometry` (Lambert-93) et `place.geom_4326`, et **les deux sont
indexées en GiST**. La couverture est donc complète, pas déficiente.

Le constat réel est différent, et plus lourd : sur 118 tables et 703 index
B-tree, **le modèle spatial se réduit à deux colonnes d'une seule table**.
Pour un système qui va recevoir des téraoctets de raster, des vecteurs sur
toute la France et des emprises d'actifs, la géométrie n'est pas
sous-indexée — elle est **quasi absente**.

Ce n'est pas un défaut à corriger mais une construction à faire, et elle
viendra avec les schémas de domaine. La stratégie d'indexation doit donc être
posée **avant** l'ingestion, pendant que la base est vide :

| Donnée | Index | Pourquoi |
|---|---|---|
| Géométries (`place`, emprises out-db) | **GiST** | Requête spatiale — indispensable |
| Séries temporelles partitionnées | **BRIN** sur l'horodatage | Données naturellement ordonnées par le temps : index minuscule, très efficace |
| Recherche par identifiant, jointures | B-tree | Cas ordinaire |
| Attributs JSONB interrogés | GIN | `contenu`, qualificateurs |

Le BRIN mérite d'être souligné : sur une table d'observations insérées dans
l'ordre chronologique, il occupe une fraction d'un B-tree pour un résultat
équivalent. À 175 millions de lignes par an, la différence n'est pas théorique.

### 10.6 Vérifications empiriques du contre-audit

Les affirmations qui portent cette RFC ont été **testées**, pas seulement
énoncées. Trois éprouvées sur la base réelle, une corrigée, deux à établir.

| Affirmation | Verdict |
|---|---|
| Une clé étrangère fonctionne **entre schémas** | **Prouvé** — l'insertion d'un orphelin est refusée : `violates foreign key constraint` |
| `ON DELETE CASCADE` traverse les schémas | **Prouvé** — 0 enfant restant après suppression du parent |
| Un rôle sans droit ne peut pas lire un schéma RGPD | **Prouvé** — `ERROR: permission denied for schema` |
| « 2 index GiST = manque structurel » | **Faux, corrigé** — voir §10.4 |
| `postgis_raster` disponible | **Disponible en 3.4.3, non installé** — l'out-db exige donc d'activer l'extension |
| `timescaledb` disponible | **Absent de l'image** — l'adopter suppose de changer l'image Docker, coût à ajouter à l'arbitrage du §9.5 |

Les deux premières lignes sont l'argument central du §3.1 : le cloisonnement
par schémas conserve l'intégrité référentielle. Ce n'était pas une opinion
d'architecte, c'est désormais un fait vérifié sur cette base.

La troisième valide le premier lot du §8 : l'isolement RGPD tient par la base,
et non par le seul code applicatif.

La quatrième est une erreur de ma part, trouvée en vérifiant ce que j'avais
écrit. Elle est conservée dans le texte plutôt que réécrite en silence — une
RFC qui efface ses corrections apprend moins qu'une RFC qui les montre.

### 10.5 Mise en cache des services distants

Redis est déjà en place — il sert le cache de `/ready` et le registre des
jetons. Les réponses des services distants doivent y transiter, avec une durée
de vie propre à chaque source.

Deux motifs déjà présents dans le code sont à généraliser : `ResilientHttpClient`
pour la résilience — un JSON malformé d'une API tierce ne doit jamais faire
tomber un moteur, garde déjà éprouvée par six mutations — et le refus de
laisser un secret ou une trace brute entrer dans un champ persisté, garde du
worker d'outbox.

## 11. Audit de l'inventaire réel — quatre natures non couvertes

Question du Fondateur : les sources déjà compilées seront-elles toutes prises
en charge avec la bonne logique ?

`SOURCES_DONNEES_EXHAUSTIVES.md` compte **2 349 lignes**. Confrontées aux trois
régimes du §10 et au cadre de preuve, **quatre natures n'ont aujourd'hui aucune
place correcte**.

### 11.1 Le constat

`SourceType` ne porte que quatre valeurs : `peer_reviewed`,
`referentiel_officiel`, `expert_identifie`, `observation_terrain`.

| Nature présente à l'inventaire | Exemples | Type qu'on serait contraint de lui donner |
|---|---|---|
| **Donnée synthétique** | GCS-Cinéma (Unreal/Niagara), Gazebo, Isaac Sim | `observation_terrain` |
| **Sortie de modèle** | Détection YOLO fumée/flamme, segmentation ML | `observation_terrain` |
| **Flux capteur temps réel** | Drone RGB/LWIR (< 100 ms), Meshtastic | `observation_terrain` |
| **Capteur citoyen / communautaire** | sensor.community, Blitzortung | `observation_terrain` |

Les quatre tombent dans la même case, et c'est la plus grave qu'on puisse
choisir : **une flamme rendue sous Unreal Engine deviendrait indiscernable
d'une observation de terrain.**

### 11.2 Pourquoi c'est constitutionnel, pas cosmétique

Une image de synthèse entrant dans une chaîne d'inférence sous l'étiquette
`observation_terrain` produirait un diagnostic dont la chaîne est complète, les
sources citées, le niveau de preuve affiché — et dont le fait fondateur n'a
jamais existé. C'est la forme la plus aboutie du défaut corrigé les 29 et 30
juillet : une référence vérifiable en apparence.

Le cas de la sortie de modèle est pire encore. `GSIE-CON-001` pose que l'IA
assiste et ne décide jamais. Une détection YOLO est une **inférence machine**,
pas une observation. L'admettre comme observation ferait entrer une décision
machine dans la chaîne par la porte des faits — en contournant l'article, sans
le contredire explicitement.

Les données d'entraînement posent une question voisine : Pyro-SDIS, FLAME,
D-Fire servent à **entraîner un détecteur**, jamais à affirmer un fait sur une
forêt. Rien aujourd'hui n'empêche de citer un jeu d'entraînement comme source
d'une assertion.

### 11.3 Ce que la RFC propose

**Étendre `SourceType`** de quatre valeurs :

| Valeur | Ce qu'elle désigne | Plancher de preuve imposé |
|---|---|---|
| `donnee_synthetique` | Rendu simulé, jeu généré | **Interdite en fondement d'inférence** |
| `sortie_de_modele` | Prédiction, détection, segmentation | `E` au mieux — et jamais sans l'`activity` qui la produit |
| `capteur_instrumente` | Capteur calibré, chaîne de mesure connue | `D` par défaut, `C` si étalonnage documenté |
| `capteur_participatif` | Capteur citoyen, réseau communautaire | `F` — observation isolée non recoupée |

**Interdire l'usage d'un jeu d'entraînement comme source d'assertion**, par un
qualificatif porté sur la source. La distinction est de nature, pas de degré :
un corpus d'entraînement décrit ce qu'un modèle doit reconnaître, il n'affirme
rien sur un peuplement.

**Exiger l'`activity` PROV pour toute sortie de modèle** : quel modèle, quelle
version, sur quelle entrée. Sans elle, une détection est un nombre sans
origine — et `activity` existe déjà (§10.2).

### 11.4 Le flux temps réel est un quatrième régime

Le §10 en distingue trois selon qui détient l'octet. Un flux drone à moins de
100 ms n'entre dans aucun : il est consommé au bord, et n'existe pas comme
objet stable.

La règle du §10.1 s'y applique néanmoins, et la tranche : **ce qui fonde une
décision doit être archivé**. Un flux peut déclencher une alerte en temps réel
— c'est son intérêt — mais l'instant qui fonde un diagnostic doit être figé en
actif possédé, avec son empreinte et son horodatage. Le reste du flux peut
être écarté.

Autrement dit : le temps réel sert à **alerter**, l'archive sert à **prouver**.

### 11.5 Réponse à la question posée

**Non**, l'inventaire n'est pas intégralement couvert par la logique actuelle.
Les sources documentaires, référentielles et satellitaires le sont ; les
quatre natures ci-dessus ne le sont pas, et la case par défaut qu'elles
prendraient est la plus dommageable possible.

Ce n'est pas un défaut de l'inventaire — il est bon, et c'est lui qui a permis
de trouver le manque. C'est le cadre de preuve qui a été conçu pour de la
connaissance scientifique, avant qu'Ignis n'amène des capteurs, des drones et
de la simulation.

## 12. Ce que cette RFC ne tranche pas

- **Le choix du stockage objet** (MinIO auto-hébergé, S3, Scaleway) : décision
  d'exploitation, dépendante de l'hébergement et de la souveraineté des données.
- **L'usage de TimescaleDB** pour les séries : le partitionnement natif de
  PostgreSQL peut suffire, et ajouter une extension a un coût d'exploitation.
  À décider au vu du premier volume réel.
- **La réplication et la sauvegarde**, qui relèvent de l'exploitation.
- **Le découpage en microservices** : cette RFC ne porte que sur les données.
  Séparer les processus est une question distincte, et les arguments ci-dessus
  ne s'y appliquent pas.
