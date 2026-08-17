# Registre des opportunités — GSIE PC

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-REG-PC |
| **Statut** | Draft |
| **Version** | 1.0.0 |
| **Dernier reclassement** | 2026-08-16 |
| **Cible** | Poste de travail, QGIS / QGISIA, traitement LiDAR lourd, exploration et administration de la base, cartographie desktop |
| **Contraintes de la cible** | CPU/GPU local · lots de données volumineux · outils exécutables séparément · pas de contrainte hors-ligne stricte |
| **Registres frères** | GSIE Serveur · Applications mobiles · Hub Unreal Engine · Applications clientes |

---

## 1. Comment lire ce registre

Identifiants `OPP-xxx` stables et uniques dans tous les registres. Classement sur
le seul **intérêt** pour cette cible, de 1 à 5. Le **verrou** décrit ce qui bloque
et ce qu'il faudrait pour le lever — ce n'est pas une pénalité de rang.

**Statuts** : INTÉGRER · BENCHMARKER · SURVEILLER · ÉCARTER.

---

## 2. La particularité juridique de cette cible

C'est le point le plus important de ce registre, et il ne concerne aucun autre.

**Le poste de travail est le seul endroit où le copyleft ne nous coûte presque
rien.** 3DFin, lidR, QGIS et TreeQSM sont en GPL-3.0 ; Metabase, Dekart et
Grafana en AGPL. Utilisés comme **exécutables séparés** — on lance l'outil, il
produit un fichier, on ingère le fichier — ces licences n'imposent rien à notre
code. Le piège est ailleurs : dès qu'on **lie** ce code dans un binaire que l'on
distribue, l'obligation de réciprocité s'applique.

Règle pratique :

| Usage | GPL / AGPL |
|---|---|
| Outil lancé séparément, échange par fichiers ou par base | Sans conséquence |
| Bibliothèque liée dans du code que nous distribuons | **Contaminant** — analyse juridique obligatoire |
| Service web AGPL exposé à des tiers | **Contaminant** — l'AGPL couvre l'usage réseau |

C'est ce qui distingue cette cible de l'embarqué, où la même licence est
rédhibitoire (voir décision D3, registre Applications mobiles).

---

## 3. La règle scientifique qui prime sur toute notation

Elle vient de la méthodologie de l'Inventaire forestier national de l'IGN et
elle est non négociable :

> Un tarif de cubage possède un **domaine de validité défini par son échantillon
> de calibration** — essence, géographie, type de peuplement, définition du
> volume. Les définitions IGN et ONF peuvent différer.

Quintessences refuse donc l'idée d'une formule universelle. Chaque résultat de
cubage ou de biomasse doit pointer vers sa méthode, sa définition du volume,
l'essence, la région, la plage de diamètres et de hauteurs, le peuplement, la
source, la version, l'erreur de calibration et un avertissement hors domaine.

Aucun outil de ce registre ne dispense de cette exigence — plusieurs la rendent
au contraire plus facile à tenir.

---

## 4. Classement au 2026-08-16

| Rang | ID | Opportunité | Intérêt | Verrou actuel | Pour le lever | Statut |
|---:|---|---|:-:|---|---|---|
| 1 | OPP-003 | **3DFin + lidR** — dendrométrie LiDAR | 5 | GPL-3.0 (voir §2) ; qualité dépendante de l'acquisition, sous-bois et occlusions | Usage en outils séparés ; benchmark matériel sur nos nuages | INTÉGRER |
| 2 | OPP-048 | **DBeaver Community** — exploration du schéma | 5 | Aucun | Adoption directe pour les 116 tables ; DEC à tracer | INTÉGRER |
| 3 | OPP-049 | **SchemaSpy** — documentation ERD auto-générée | 5 | Aucun (LGPL, génération statique) | Génération en intégration continue sur le schéma courant | INTÉGRER |
| 4 | OPP-044 | **allodb + allometric** — référentiels d'équations allométriques | 5 | **Droits à examiner équation par équation** ; ne remplacent pas les tarifs français | Import contrôlé dans le registre avec source, unités et domaine de validité | BENCHMARKER |
| 5 | OPP-045 | **Capsis** (CIRAD) — modèles de croissance français | 5 | Licence, paramètres, essences et zone à examiner modèle par modèle | Prise de contact avec les auteurs ; examen individuel, pas global | BENCHMARKER |
| 6 | OPP-041 | **DeepForest** — détection de houppiers sur RGB aérien, MIT | 4 | Le projet avertit lui-même qu'un modèle générique ne convient pas à tout capteur | Fine-tuning local — donc corpus annoté, même verrou que la perception drone | BENCHMARKER |
| 6bis | OPP-039 | **TreeLearn** — segmentation individuelle LiDAR, MIT — **supérieure à SegmentAnyTree/ForAINet/TLS2Trees sur Wytham Woods** | 5 | CUDA/spconv ; domaine d'apprentissage différent du nôtre | Benchmark sur forêts françaises — priorité relevée par la preuve de performance | BENCHMARKER |
| 8 | OPP-054 | **DuckDB Spatial** — analytique locale sur fichiers | 4 | Aucun ; complète la base, ne la remplace pas | Usage exploratoire sur GeoParquet/COPC | INTÉGRER |
| 9 | OPP-055 | **CoSIA / OCS GE (IGN)** — couverture et occupation du sol par IA | 4 | Conditions de réutilisation et millésimes à qualifier | Vérifier licences et fraîcheur avant tout usage dérivé | BENCHMARKER |
| 10 | OPP-051 | **Apache Superset** — BI avancée, Apache-2.0 | 4 | Déploiement Docker à monter | Docker Compose cohérent avec l'existant ; test RLS | BENCHMARKER |
| 11 | OPP-056 | **geocontext MCP** — accès outillé à la Géoplateforme IGN | 4 | Dépendance à un service tiers | Évaluer en usage assistant, jamais en source de vérité | BENCHMARKER |
| 12 | OPP-052 | **Kepler.gl + Dekart** — cartographie web sur PostGIS | 3 | Dekart en AGPLv3 (voir §2) ; déploiement à monter | Self-hosted en Docker ; ne pas lier au code distribué | BENCHMARKER |
| 13 | OPP-046 | **medfate** — bilan hydrique et résilience méditerranéenne | 3 | Calibration régionale absente | Zone pilote méditerranéenne avant tout usage | SURVEILLER |
| 14 | OPP-040 | **ForAINet** — segmentation panoptique LiDAR aérien, BSD-3 | 3 | Dépôt peu industrialisé ; DBH difficile depuis l'aérien | Pilote recherche, pas production | SURVEILLER |
| 15 | OPP-050 | **Metabase** — BI self-service pour non-techniciens | 3 | AGPL (voir §2) ; recouvre partiellement Superset | Trancher Metabase *ou* Superset, pas les deux | SURVEILLER |
| 16 | OPP-042 | **Detectree2** — polygones de couronnes, MIT | 3 | Modèles orientés forêts denses et tropicales | Réévaluer si un besoin d'annotation de couronnes émerge | SURVEILLER |
| 17 | OPP-053 | **deck.gl · MapLibre GL JS 5 · Protomaps/PMTiles** | 3 | Aucun ; briques d'intégration | À mobiliser quand une interface carto le justifiera | SURVEILLER |
| 18 | OPP-043 | **TreeQSM · TLS2trees** — reconstruction et segmentation TLS | 2 | TreeQSM en MATLAB ; maintenance lente ; arbres isolés | Conserver comme baselines de comparaison, pas comme chaîne | SURVEILLER |
| 19 | OPP-057 | **GéoLLM (IGN)** — interrogation naturelle des données IGN | 2 | Maturité et conditions d'accès non qualifiées | Veille ; comparer à notre propre chaîne RAG | SURVEILLER |
| 20 | OPP-047 | **iLand · LANDIS-II** — dynamique forestière à l'échelle du paysage | 3 | Calcul lourd — foyer réel côté serveur/HPC | *Renvoi croisé : registre GSIE Serveur.* Attendre le vertical slice forestier | SURVEILLER |

---

## 5. Fiches — les cinq premiers

### OPP-003 · 3DFin + lidR — la chaîne LiDAR de référence
3DFin segmente les arbres et produit position, diamètre et hauteur depuis TLS/MLS,
avec des interfaces autonome, CloudCompare, QGIS et Python — très proche du
besoin GeoSylva. lidR traite LAS/LAZ, les modèles de canopée et les catalogues
massifs par tuiles, avec une littérature abondante.
**Les deux sont en GPL-3.0**, ce qui est sans conséquence ici (§2) et le serait
totalement sur mobile.
**Réserve honnête :** la qualité dépend d'abord de l'acquisition. Sous-bois et
occlusions dégradent le résultat davantage que le choix de l'algorithme, et les
paramètres de lidR influencent fortement la sortie. Un benchmark sur nos propres
nuages est un préalable, pas une formalité.

### OPP-048 · DBeaver Community — 116 tables à comprendre
Polyvalent, ERD visuel, import/export multi-format, extensions PostgreSQL.
L'alternative pgAdmin reste possible ; DataGrip n'a d'intérêt qu'avec une licence
JetBrains déjà présente.

### OPP-049 · SchemaSpy — la documentation qui ne vieillit pas
Génère une documentation HTML statique du schéma. Sa valeur n'est pas l'outil
mais l'automatisation : une documentation de schéma écrite à la main est fausse
au bout d'une migration.

### OPP-044 · allodb + allometric — utiles, et dangereux si mal employés
Des centaines d'équations de biomasse structurées, avec sélection pondérée par
taxonomie, climat et site. **Elles ne remplacent pas les tarifs français** et
leur domaine de validité (§3). Leur bon usage est l'import contrôlé dans le
registre de modèles, chaque équation portant sa source, ses unités et son
domaine — jamais l'application directe.

### OPP-045 · Capsis — la plateforme française qu'on ne peut pas prendre en bloc
Plateforme CIRAD de modèles de croissance et de sylviculture. L'erreur serait de
l'adopter globalement : chaque modèle a ses paramètres, sa licence, ses essences
et sa zone. L'examen se fait modèle par modèle, idéalement en collaboration avec
les auteurs.

---

## 5bis. Enrichissement — recherche web du 2026-08-16

**TreeLearn dépasse SegmentAnyTree, ForAINet et TLS2Trees sur benchmark, pas
seulement sur le papier.** Évalué sur le jeu Wytham Woods, TreeLearn (OPP-039,
actuellement rang 6) surpasse les trois autres méthodes de segmentation
individuelle listées dans ce registre. C'est une donnée neuve : au moment de la
rédaction du registre, TreeLearn n'était noté que 4/5 avec un domaine
d'apprentissage jugé incertain. **Reclassement mérité** — voir journal §9.

**Un besoin de standardisation confirme notre §3.** Une publication ISPRS de
2026 sur le *benchmarking* de la segmentation TLS observe que les nouvelles
méthodes sont testées sur des données et des protocoles différents, rendant la
comparaison difficile — établir un banc et un protocole standardisés est
identifié comme la clé pour un progrès cohérent du domaine. C'est exactement la
règle du domaine de validité posée en §3 de ce registre, vue cette fois depuis la
littérature scientifique plutôt que depuis l'IGN.

**ForestFormer3D** (arXiv:2506.16991) — nouveau candidat non répertorié : cadre
unifié de segmentation de nuages de points LiDAR forestiers de bout en bout.
Non encore qualifié pour ce registre ; à évaluer lors du prochain cycle de veille
aux côtés de TreeLearn et SegmentAnyTreeV2.

**Superset sur PostGIS — aucune donnée chiffrée trouvée.** La recherche ne
confirme ni n'infirme la tenue de charge sur nos 116 tables et plusieurs millions
de lignes après ingestion Treekipedia/GBIF. Superset gère nativement le pétaoctet
en théorie, mais la performance réelle dépend entièrement du réglage de la base
sous-jacente — **le test sur notre propre volume (§Prochaines étapes de la
source archivée) reste un préalable non contournable**, pas une formalité.

---

## 6. Écartées — motifs durs uniquement

| ID | Opportunité | Motif |
|---|---|---|
| OPP-116 | Tableau, Power BI, Sigma Computing, Basedash | Propriétaires, SaaS ou coût sans rapport avec la valeur apportée (jusqu'à 75-200 k$/an pour Tableau) |
| OPP-117 | CARTO, Felt, Foursquare Studio | SaaS non auto-hébergeables — incompatibles avec la souveraineté des données du projet |
| OPP-118 | Navicat, TablePlus, Mako, QueryPlane | Aucune valeur ajoutée face à DBeaver, ou SaaS |
| OPP-119 | Redash, Lightdash, Evidence | Recouverts par Superset ; Lightdash suppose dbt, non adopté |
| OPP-120 | Mapeo | Cartographie offline orientée terrain communautaire — hors besoin |
| OPP-121 | Formule de cubage universelle | Contredit la règle §3. Définitif. |

---

## 7. Ce qui bloque plusieurs lignes à la fois

**Le corpus annoté, encore.** OPP-041 (DeepForest) attend un fine-tuning local,
donc des houppiers annotés sur nos images. C'est le même verrou que la perception
drone et que le pack essences embarqué. Trois registres, un seul effort de
données.

**Le choix Metabase ou Superset.** OPP-050 et OPP-051 se recouvrent largement.
Les maintenir tous deux coûterait deux déploiements pour une fonction. Superset
est mieux placé — Apache-2.0 contre AGPL, SQL Lab, davantage de connecteurs —
mais Metabase reste supérieur pour un forestier non technicien. **À trancher, pas
à cumuler.**

---

## 8. Sources absorbées

| Document d'origine | Apport |
|---|---|
| `ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18` (§5) | Outils de mesure 3D, allométrie, règle du domaine de validité, chaîne GeoSylva |
| `VEILLE_OUTILS_VISUALISATION_DB_2026-07-31` | BI, cartographie, explorateurs SQL, stack recommandée, conditions d'adoption |
| `IGN_IA_STRATEGY` | CoSIA, OCS GE, GéoLLM, geocontext MCP, datasets IGN |
| `ETUDE_DATA_PLATFORM_EMERGENTE_2026-08-09` (§3.4) | DuckDB Spatial en analytique locale |
| `LIDAR_HD_SPECIFICATIONS` | Spécifications d'acquisition — cadre des benchmarks LiDAR |

---

## 9. Journal des reclassements

| Date | Mouvement | Motif |
|---|---|---|
| 2026-08-16 | Création — 20 opportunités actives, 6 écartées | Consolidation par cible d'exécution |
| 2026-08-16 | OPP-050 (Metabase) rétrogradée derrière OPP-051 (Superset) | Recouvrement fonctionnel ; Apache-2.0 préférable à AGPL |
| 2026-08-16 | OPP-047 (iLand, LANDIS-II) conservée avec renvoi serveur | Le foyer d'exécution réel est le calcul lourd, pas le poste |
| 2026-08-16 | OPP-039 (TreeLearn) remontée de rang 6 vers rang 3 | Benchmark Wytham Woods : supérieure à SegmentAnyTree, ForAINet, TLS2Trees — donnée absente lors de la première rédaction |

---

## 10. Historique

| Version | Date | Auteur | Modification |
|---|---|---|---|
| 1.0.0 | 2026-08-16 | Claude | Création — registre par cible d'exécution |
