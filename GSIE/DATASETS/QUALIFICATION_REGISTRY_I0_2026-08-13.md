# Qualification Registry I0 — 2026-08-13

| Champ | Valeur |
|---|---|
| **Statut** | Revue technique — SCI-001 scindé, manifeste candidat non appliqué |
| **Périmètre** | 15 fiches I0 externes |
| **Ressources locales** | Exclues ; `E:\Documents` reste la dernière tranche |
| **Effet opérationnel** | Aucun FETCH, aucune copie, aucune promotion |

## 1. Verdict

Le lot I0 n'est pas un ensemble de quinze datasets homogènes. Il contient des
producteurs, des jeux de données, des référentiels et des distributions/API.
Les enregistrer comme quinze `Source` indépendantes créerait des doublons et
rendrait la provenance ambiguë.

La réconciliation retient quatre règles :

1. une organisation ou un service éditorial devient une `Source` ;
2. un corpus versionnable devient un `Dataset`/`DatasetVersion` ;
3. REST, WCS, WFS, WMTS, téléchargement et miroir deviennent des
   `Distribution` distinctes ;
4. une licence de plateforme ne vaut jamais licence de toutes les couches
   qu'elle diffuse.

Le manifeste actif `REGISTRY_MANIFEST.json` n'est pas modifié par cette revue.
Un manifeste candidat strictement `metadata_only` est produit séparément.

## 2. Synthèse des quinze fiches

| ID inventaire | Ressource | Qualification I0 | Décision |
|---|---|---|---|
| `ds-003` | dataIFN | Dataset brut IGN, campagnes annuelles depuis 2005 | Candidat Registry |
| `ds-007` | SAFRAN | Produit climatologique distinct, accès actuel à confirmer | Bloqué |
| `ds-009` | ARPEGE/AROME | Famille de modèles, distributions et millésimes distincts | Bloqué |
| `ds-010` | Observations sol | Produit d'observations distinct ; JSON/CSV documentés | Bloqué |
| `ds-013` | SoilGrids | Dataset v2.0 ; REST suspendu, WCS utilisable par sous-ensemble | Candidat WCS |
| `ds-014` | GBIF | Séparer Species API et données d'occurrences | Candidat Species API |
| `ds-015` | Tela Botanica | Producteur/portail, pas un dataset unique | Bloqué |
| `ds-016` | BDNFF/BDTFX | Référentiel taxonomique versionné, licences à obligations fortes | Bloqué |
| `ds-017` | INPN | Portail/producteur ; séparer TAXREF et autres corpus | Bloqué direct |
| `geopf-plan-ign` | Plan IGN | Représentation cartographique continue, distribution proxy | Proxy seulement |
| `geopf-ortho` | Orthophotos | Collection d'éditions, pas une couche immuable unique | Bloqué par édition |
| `apicarto-cadastre` | API Carto Cadastre | Distribution REST d'une donnée de référence | Candidat metadata |
| `apicarto-admin` | API Carto limites | Distribution REST d'une donnée de référence | Candidat metadata |
| `apicarto-wfs-geoportail` | API Carto WFS | Façade bêta ; la couche appelée doit être qualifiée | Bloqué par couche |
| `geo-api-gouv-communes` | API Géo communes | Service REST administratif, JSON/GeoJSON | Bloqué juridique |

## 3. Fiches qualifiées

### I0-01 — dataIFN (`ds-003`)

- **Source** : IGN — Inventaire forestier national français.
- **Dataset** : données brutes des campagnes annuelles 2005 et suivantes.
- **Distribution** : téléchargement de l'archive complète et de la dernière
  campagne ; dernière mise à jour affichée : 14 octobre 2025.
- **Licence** : Licence Ouverte / Etalab 2.0 ; attribution IGN obligatoire.
- **Couverture** : France ; observations terrain par placette/campagne.
- **Limite spatiale critique** : les coordonnées publiées sont le centre de la
  maille kilométrique la plus proche ; le point réel se trouve à 700 m maximum.
- **Limite statistique critique** : les poids de sondage ne sont pas publiés ;
  GSIE ne doit jamais fabriquer de résultats d'inventaire à partir des données
  brutes. Les résultats statistiques officiels restent ceux de l'IGN.
- **Mode proposé** : `metadata_only` dans le candidat ; une future copie exige
  checksum, taille, schéma, citation datée et garde anti-agrégation.
- **Source officielle** : <https://inventaire-forestier.ign.fr/dataIFN/>.

### I0-02 — SAFRAN (`ds-007`)

- **Source** : Météo-France.
- **Nature** : analyse climatique, distincte des prévisions AROME/ARPEGE et du
  produit Météo des forêts.
- **Accès** : à réidentifier sur les nouveaux portails Météo-France.
- **Licence, quota, format, grille, période** : non qualifiés sur une page
  officielle actuelle propre au produit.
- **Mode** : `METADATA_LINK`, `LEGAL_REVIEW_PENDING`.
- **Blocage** : l'entrée globale `meteofrance-portail-api` de SCI-001 affirme
  aujourd'hui une licence identique pour toutes les API ; cette généralisation
  doit être remplacée par une qualification produit par produit.

### I0-03 — ARPEGE/AROME (`ds-009`)

- **Source** : Météo-France.
- **Nature** : deux familles de modèles, plusieurs domaines, résolutions,
  échéances et formats ; elles ne forment pas une version unique.
- **Accès** : portail API et/ou `meteo.data.gouv.fr`, à figer par produit.
- **Mode** : `METADATA_LINK` tant que les distributions exactes, quotas,
  millésimes et licences ne sont pas documentés.
- **Anomalie de code** : l'adapter Météo-France actuellement présent cible
  Météo des forêts ; il ne prouve pas l'intégration ARPEGE/AROME.

### I0-04 — observations au sol (`ds-010`)

- **Source** : Météo-France.
- **Nature** : observations stationnelles ; fichiers unitaires et paquets.
- **Formats documentés** : JSON et CSV dans le descriptif du 15 mars 2025.
- **Grain** : observation ponctuelle ; aucune surface représentative ne doit
  être inventée.
- **Mode** : `METADATA_LINK` jusqu'à qualification de l'API précise, du quota,
  de la licence et de l'historique accessible.

Pour ces trois fiches Météo-France, la migration officielle des données vers
le portail API et `meteo.data.gouv.fr` interdit de figer les anciens liens sans
contrôle : <https://donneespubliques.meteofrance.fr/?id_rubrique=52>.

### I0-05 — SoilGrids (`ds-013`)

- **Source** : ISRIC.
- **Dataset** : SoilGrids v2.0, cartes mondiales de propriétés du sol.
- **Résolution native** : 250 m, soit `62 500 m²` par pixel.
- **Structure** : six profondeurs normalisées et incertitude par quantiles.
- **Licence** : CC BY 4.0.
- **REST** : officiellement suspendu, bêta, sans garantie de disponibilité.
- **WCS** : voie recommandée pour extraire un sous-ensemble ; contrat GSIE déjà
  borné et preuve ponctuelle DEC-000061 déjà réalisée.
- **Mode proposé** : WCS `metadata_only`; aucune réouverture canonique de FETCH.
- **Source officielle** :
  <https://docs.isric.org/globaldata/soilgrids/index.html>.

### I0-06 — GBIF (`ds-014`)

- **Source** : GBIF.
- **Distribution utilisée par le code** : Species API, appariement taxonomique
  et noms vernaculaires dans Checklist Bank.
- **Distribution distincte** : Occurrence API et téléchargements asynchrones.
- **Licence** : les occurrences conservent la licence de chaque dataset
  constitutif (`CC0`, `CC BY` ou `CC BY-NC`) ; aucune licence agrégée ne doit
  être substituée.
- **Mode proposé** : Species API `metadata_only`; occurrences bloquées jusqu'à
  une politique de filtrage des licences et une citation DOI de téléchargement.
- **Sources officielles** : <https://techdocs.gbif.org/en/openapi/v1/species>,
  <https://techdocs.gbif.org/en/openapi/v1/occurrence>,
  <https://www.gbif.org/terms>.

### I0-07 — Tela Botanica (`ds-015`)

- **Nature** : portail et producteur ; ne pas créer un dataset générique
  « flore française ».
- **Découpage requis** : référentiels taxonomiques, bases botaniques,
  observations et cartographies doivent avoir leurs propres versions et droits.
- **Mode** : `METADATA_LINK` jusqu'au choix d'un produit précis.

### I0-08 — BDNFF/BDTFX (`ds-016`)

- **Source** : Tela Botanica et partenaires scientifiques selon la version.
- **Nature** : référentiel nomenclatural/taxonomique des trachéophytes.
- **Droits annoncés** : base sous ODbL 1.0 et données contenues sous CC BY-SA
  2.0 ; attribution et partage à l'identique doivent être qualifiés pour les
  dérivés GSIE et les packs hors ligne.
- **Mode** : `METADATA_LINK`; pas d'entraînement IA ni de redistribution par
  défaut.
- **Source officielle** :
  <https://www.tela-botanica.org/ressources/donnees/telechargements/>.

### I0-09 — INPN/TAXREF (`ds-017`)

- **Source** : PatriNat/MNHN/OFB pour le portail INPN.
- **Découpage requis** : TAXREF, statuts, espaces protégés et observations sont
  des datasets distincts.
- **TAXREF** : référentiel intégral diffusé en archive texte versionnée ; le
  miroir GBIF déjà déclaré dans SCI-001 reste le chemin candidat tant que la
  disponibilité directe n'est pas requalifiée.
- **Mode** : accès INPN direct bloqué ; `taxref-via-gbif` seulement dans le
  manifeste candidat.
- **Référence** :
  <https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo>.

### I0-10 — Plan IGN (`geopf-plan-ign`)

- **Source** : IGN/Géoplateforme.
- **Nature** : représentation cartographique multi-échelles mise à jour en
  continu, disponible en WMS/WMTS/TMS.
- **Régime** : proxy de visualisation ; impropre comme preuve immuable d'une
  conclusion sans millésime ni archive.
- **Licence** : à lire dans les métadonnées de la ressource/layer, pas dans les
  seules CGU de la plateforme.
- **Source officielle** :
  <https://cartes.gouv.fr/aide/fr/partenaires/ign/representations-cartographiques-souveraines/plan-ign/>.

### I0-11 — orthophotos nationales (`geopf-ortho`)

- **Source** : IGN/Géoplateforme.
- **Nature** : collection `ORTHOIMAGERY.ORTHOPHOTOS` diffusée en WMS-Raster et
  WMTS, avec éditions territoriales successives.
- **Découpage requis** : une `DatasetVersion` par édition/millésime utile ; le
  service continu reste une distribution proxy.
- **Licence, emprise, résolution et date** : à extraire des métadonnées de
  chaque édition avant usage analytique.
- **Mode** : proxy seulement dans l'état courant.

### I0-12 — API Carto Cadastre (`apicarto-cadastre`)

- **Source** : IGN, API Carto.
- **Distribution** : REST, module Cadastre, réponses géographiques JSON/GeoJSON.
- **Disponibilité de service annoncée** : 99,5 % par mois pour API Carto.
- **Licence** : la licence du jeu cadastral servi doit être liée explicitement
  à la distribution ; les CGU de la plateforme ne suffisent pas.
- **Mode proposé** : `metadata_only`; candidat de réconciliation avec
  `ign-apicarto-geopf`.

### I0-13 — API Carto limites administratives (`apicarto-admin`)

- **Source** : IGN, API Carto.
- **Distribution** : REST, module Limites administratives.
- **Découpage** : dataset administratif versionné distinct du service API.
- **Mode proposé** : `metadata_only`; version de la donnée sous-jacente à
  capturer avant toute conclusion.

### I0-14 — API Carto WFS-Géoportail (`apicarto-wfs-geoportail`)

- **Source** : IGN, API Carto.
- **Nature** : façade REST vers des couches WFS, indiquée comme bêta.
- **Risque** : la source, la licence, la résolution et le schéma changent selon
  la couche demandée ; une fiche générique ne peut autoriser aucun FETCH.
- **Mode** : bloqué jusqu'à création d'une distribution par couche allowlistée.

Documentation officielle commune aux trois fiches :
<https://geoservices.ign.fr/documentation/services/api-et-services-ogc/api-carto-rest>.
Les CGU rappellent que la licence est celle choisie par le fournisseur de la
donnée et se lit dans ses métadonnées : <https://cartes.gouv.fr/cgu/?lang=fr>.

### I0-15 — API Géo communes (`geo-api-gouv-communes`)

- **Source** : service public `geo.api.gouv.fr`; opérateur juridique et licence
  de redistribution à consigner avant copie.
- **Distribution** : REST `/communes` et `/communes/{code}`, formats JSON ou
  GeoJSON ; géométries centre, contour, mairie ou emprise.
- **Couverture** : communes françaises et relations administratives.
- **Mode** : `METADATA_LINK`; usage en requête possible après qualification du
  contrat de service, mais aucune archive/offline par défaut.
- **Source officielle** :
  <https://geo.api.gouv.fr/decoupage-administratif/communes>.

## 4. Écarts du manifeste actif

| Entrée active | Écart | Correction future |
|---|---|---|
| `gbif-occurrences` | L'adapter actuel utilise Species API, pas Occurrence API | Renommer/scinder |
| `soilgrids-properties` | Distribution déclarée REST/JSON alors que REST est suspendu | Déclarer WCS séparément |
| `meteofrance-services` | Plusieurs produits sont agrégés sous une même licence supposée | Une fiche par produit/API |
| `ign-apicarto` | Cadastre, altitude et autres couches sont confondus | Une distribution par module/couche |

Ces écarts ne sont pas corrigés silencieusement : changer les identités déjà
persistées nécessite une migration/reconciliation dédiée et des tests de rejeu.

## 5. Manifeste candidat

`REGISTRY_MANIFEST_I0_CANDIDATE_2026-08-13.json` contient uniquement des
entrées compatibles avec le contrat actuel et le registre SCI-001 :

- données brutes IFN ;
- Species API GBIF ;
- SoilGrids WCS ;
- API Carto Cadastre ;
- API Carto Limites administratives.

Toutes restent `discovered`, `metadata_only` et `offline_pack=false`. SAFRAN,
AROME/ARPEGE, observations Météo-France, Tela/BDTFX, INPN direct, Plan IGN,
orthophotos, WFS générique et API Géo restent hors manifeste candidat tant que
leurs contrats précis ne sont pas qualifiés.

## 6. Porte de sortie I0

Le prochain passage peut être autorisé seulement après :

1. correction versionnée de SCI-001 pour séparer les produits agrégés ;
2. stratégie de migration des quatre entrées déjà persistées ;
3. test de validation et `dry-run` du manifeste candidat ;
4. QualityAssessment complet par distribution ;
5. décision opérateur source par source.

Cette qualification n'autorise aucune application du manifeste candidat.

## 7. Contrôles reproduits

```text
Lecture JSON                     OK — 5 entrées
Validation DatasetManifest      OK — SCHEMA_OK 5
Génération manifest_preview     OK — PREVIEW_OK 5
Opérations                      metadata_only uniquement
Statuts                         discovered uniquement
Packs hors ligne                aucun
Tests du contrat de manifeste   12 passed
git diff --check                propre sur les fichiers suivis modifiés
```

La campagne pytest isolée avec la configuration globale de couverture a bien
exécuté les 12 tests avec succès, mais a retourné un code non nul parce qu'une
seule suite ne peut atteindre le seuil de couverture global de 97,1 %. La
relance fonctionnelle explicite avec `--no-cov` est verte ; aucun seuil du
projet n'a été abaissé ni modifié.

## 8. Réconciliation SCI-001

DEC-000068 applique la scission dans le registre déclaratif. Les quatre
identités actives trop agrégées sont désormais marquées historiques et sont
refusées par la porte d'ingestion. Les nouvelles identités sont utilisées par
le manifeste candidat et la qualification FETCH canonique de SoilGrids cible
désormais `soilgrids-wcs` tout en restant fermée.

La base active demeure inchangée. Le plan de migration est décrit dans
`MIGRATION_IDENTITES_REGISTRY_I0_2026-08-13.md`.

La campagne élargie de cette scission compte 51 tests ciblés passants ; Ruff et
mypy strict sont propres.

La comparaison statique des adapters confirme `gbif-species-api` et
`meteofrance-meteo-forets` pour les opérations effectivement codées. Elle ne
permet pas de migrer les occurrences GBIF, les distributions IGN ou le
DataAsset WCS SoilGrids sans traces et qualification de contenu.
