# Candidats de ressources - Audit de `E:\Documents` v2.0.0

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-DATA-AUDIT-EDOCUMENTS-001 |
| **Statut** | Draft |
| **Version** | 2.0.0 |
| **Date** | 2026-08-12 |
| **Auteur** | Codex, sous autorité du Fondateur |
| **Portée** | Qualification préliminaire des ressources locales potentiellement utiles à Quintessences |
| **Sources de vérité** | `NOMENCLATURE_SOURCES.md`, RFC-0038, RFC-0039 |

## 1. Résumé

L'exploration initiale repérait de bons fichiers, mais ses compteurs ne
représentaient pas des ressources logiques : les GeoTIFF étaient aussi comptés
comme images et les composants `.shp`, `.dbf`, `.shx`, `.prj` d'un même
shapefile étaient séparés. Le présent audit corrige ce biais, analyse l'ensemble
de `E:\Documents`, replie les sidecars, détecte les doublons exacts et sépare
pertinence, provenance apparente, droits et sensibilité.

Le résultat principal n'est pas « 3 077 datasets disponibles ». Il est :

> 3 077 ressources logiques ont été examinées ; aucune n'est ingérée ni
> qualifiée. Les meilleures ressources constituent des candidats de travail
> pour FieldIntake, GSIE-Bench, le Data Registry et les moteurs domaine.

## 2. Méthode reproductible

L'inventaire est produit par `inventory_edocuments.py`. Il :

1. parcourt `E:\Documents` sans modifier les sources ;
2. exclut les installations logicielles, builds, caches, dépôts `.git` et
   documents personnels manifestement hors périmètre ;
3. distingue documents, tableurs, images, rasters et vecteurs ;
4. regroupe les fichiers associés d'un shapefile en une ressource logique ;
5. extrait un texte borné des PDF, DOCX, ODT, PPTX, XLSX, CSV et fichiers texte ;
6. lit la liste des couches des GeoPackages sans ouvrir leur contenu métier ;
7. calcule SHA-256 sur le fichier principal pertinent jusqu'à 256 Mio ;
8. détecte les doublons exacts par empreinte ;
9. classe la pertinence par thèmes, sans transformer ce classement heuristique
   en décision scientifique ou juridique.

Artefacts produits :

- `inventory_edocuments/manifest.csv` : registre tabulaire complet ;
- `inventory_edocuments/manifest.json` : registre machine-readable ;
- `inventory_edocuments/summary.json` : compteurs et périmètre d'exclusion.

Ces trois artefacts détaillés sont locaux et ignorés par Git : ils contiennent
des chemins de fichiers et des indicateurs de sensibilité qui ne doivent pas
être publiés. Aucun extrait textuel de document n'y est conservé.

Les anciens CSV déposés dans `E:\Documents` ne sont plus la preuve de référence.
Ils restent des fichiers temporaires, non supprimés par cet audit.

## 3. Résultats quantitatifs

### 3.1 Périmètre

| Mesure | Résultat |
|---|---:|
| Fichiers vus dans `E:\Documents` | 41 215 |
| Fichiers restant après exclusions techniques et personnelles | 15 014 |
| Ressources logiques analysées | 3 077 |
| Ressources à pertinence heuristique élevée | 146 |
| Ressources à pertinence heuristique moyenne | 247 |
| Ressources sensibles ou restreintes à confirmer | 489 |
| Groupes de doublons exacts | 143 |
| Ressources appartenant à ces groupes | 414 |
| PDF probablement soumis à OCR | 23 |

Un score élevé signifie uniquement que le contenu touche plusieurs domaines
forestiers. Il ne prouve ni l'exactitude, ni la licence, ni le niveau Gold.

### 3.2 Ressources logiques par catégorie

| Catégorie | Nombre | Remarque |
|---|---:|---|
| Documents | 359 | PDF, DOCX, ODT, PPTX et formats historiques |
| Tableurs et textes structurés | 256 | XLSX, CSV, ODS, TSV |
| Textes | 460 | TXT, Markdown et JSON non géospatial |
| Vecteurs GeoPackage/GeoJSON/KML | 85 | un `.json` ordinaire n'est plus classé comme vecteur |
| Shapefiles logiques | 46 | 148 sidecars repliés dans leur ressource principale |
| Rasters géospatiaux | 195 | exclus du compteur d'images |
| Images ordinaires | 1 676 | cartes rendues, photographies et illustrations |

### 3.3 Limites techniques détectées

| Problème | Nombre | Conséquence |
|---|---:|---|
| GeoPackage illisible | 1 | quarantaine technique ; aucune ingestion |
| PDF/ODT avec erreur de parsing | 6 | revue manuelle ou réparation de copie |
| DOCX non reconnu comme package | 2 | fichier possiblement renommé ou corrompu |
| PDF probablement image/scanné | 23 | OCR contrôlé requis avant recherche textuelle |
| Ressources > 256 Mio | variable | checksum explicitement différé, jamais supposé |

Le GeoPackage en erreur est :
`E:\Documents\Projet fête de la forêt DFCI\Carte DFCI\TD DFCI\ANCIEN PROJET\Zip terrain\data\data GP1.gpkg`.

## 4. Portefeuilles prioritaires

### 4.1 Diagnostics stationnels et collecte terrain - priorité P0

| Ressource | Empreinte SHA-256 | Usage proposé | Statut prudent |
|---|---|---|---|
| `E:\Documents\bts\Fiche Diagnostic Forestier Plus fiche térrain vierge.docx` | `6235bc9b...0c0f3` | Prototype de schéma et d'interface FieldIntake | À refondre et sourcer |
| `E:\Documents\bts\FICHE DE DIAGNOSTIC STATIONNEL camille (Version Intégrée et Approfon.pdf` | `f4aa24eb...b966b` | Cas de contradictions et de qualité GSIE-Bench | Pas Gold ; relecture nécessaire |
| `E:\Documents\bts\bio\Diagnostic stationnel Camille Perraudeau.docx` | `226bfd0c...41372` | Candidat de scénario stationnel | Droits et références à reconstruire |
| `E:\Documents\bts\EIL Carto\Diagnostic_stationnel_Longeyroux_Placette_EIL.docx` | `7bdbfe21...7186e` | Scénario territorial lié à des placettes SIG | À lier aux sources et mesures |
| `E:\Documents\bts\Référentiel Par Défaut + Fiche Terrain A4 — Gradients Autoécologiques.docx` | `d90ac1ed...7141` | Vocabulaire candidat pour formulaires adaptatifs | Seuils à qualifier un par un |
| Relevés ODT `PSG tutoré\Documents\Relever terrain\` | voir manifeste | Cas réels de peuplements et variantes de saisie | Données potentiellement sensibles |

Ces fichiers ne doivent pas être transformés directement en vérité terrain. Ils
servent à construire le schéma de collecte, la liste des contrôles et des cas de
test, puis à faire qualifier chaque annotation.

### 4.2 Dendrométrie, inventaire et sylviculture - priorité P0

| Ressource | Empreinte SHA-256 | Valeur potentielle |
|---|---|---|
| `...\Amélioration des peuplement\Tableur comparatif placettes.xlsx` | `059d9d75...70863` | Comparaison de placettes et vérification de calculs |
| `...\PSG\Documents relatif au psg\Données inv 489 points2.xlsx` | `d7f14bed...053b3` | Jeu d'inventaire volumineux pour tests de cohérence |
| `...\PSG\Documents relatif au psg\Description_pplmnts2026.xlsx` | `a6cce246...ddc1` | Description structurée des peuplements |
| `...\PSG tutoré\Documents\données terrain.xlsx` | `9fe12dcd...ea0` | Petit jeu terrain pour prototype FieldIntake |
| `...\Parcelle forêt Domanial de la Vergne\Analyse de parcelle forestière.docx` | `ff2b4f33...1756` | Diagnostic sylvicole à relier aux guides et données |

Usages recommandés : tests de formules, contrôles d'unités, détection de valeurs
impossibles, comparaison entre inventaire intégral et échantillonnage, puis
baselines non-IA. Les tarifs de cubage, facteurs de forme et conventions de
surface terrière doivent être versionnés séparément.

### 4.3 Guides et références institutionnelles - priorité P1

Les guides ONF sur les hêtraies, chênaies, sapinières et itinéraires sylvicoles,
le SRGS Limousin, les documents CNPF/CRPF, FCBA, OFB/ONCFS et les rapports
forêt-gibier forment une bibliothèque de référence très riche.

Routage autorisé à ce stade :

```text
document local
    -> fiche RESEARCH avec référence bibliographique
    -> statut citation_only ou licence à clarifier
    -> extraction de règles interdite sans qualification
    -> KNOWLEDGE seulement après source précise, domaine de validité et revue
```

Le fait qu'un PDF ait été fourni pendant un BTS ou soit accessible localement
n'accorde aucun droit de copie, redistribution, annotation ou entraînement IA.

### 4.4 Données géospatiales et scénarios territoriaux - priorité P1

| Ensemble | Preuve technique | Usage proposé | Risque principal |
|---|---|---|---|
| `CCF Celles sur Plaine.gpkg` | 7 couches, EPSG:2154, SHA-256 `4695a77a...bd90a` | scénario inventaire + cadastre + placettes | données cadastrales/restreintes |
| `Placette.gpkg` | 1 couche, EPSG:3857, doublon exact | test de déduplication et reprojection | CRS inadapté aux calculs de surface |
| couches Longeyroux | placettes et centres en EPSG:2154 | scénario stationnel spatial | provenance de chaque couche |
| `chantier_ecole_osm.geojson` | SHA-256 `e3e23ce7...ffab2` | test OSM/terrain | ODbL et attribution à confirmer |
| projets DFCI | GeoPackages de 19 à 21 couches, rasters MNT/MNS/MNH | futur benchmark Ignis/DFCI | licences, données sensibles, versions multiples |
| `MNH_hauteur_objets.tif` | 39,8 Mio, SHA-256 `b31a9239...31ade` | contrôle de dérivation MNS-MNT | recette et alignement à reconstruire |
| MNT France 25 m COG | environ 1,3 Gio, checksum différé | contexte national | licence, coût et grain natif |

Les grands GeoPackages DFCI montrent aussi des incohérences de CRS internes
(`EPSG:2154` et identifiants locaux `EPSG:100000`). Ils doivent être ouverts en
quarantaine, couche par couche, avec contrôle géométrique avant tout usage.

### 4.5 Santé forestière, biodiversité et équilibre forêt-gibier - priorité P2

Le corpus contient des fiches pathogènes, bilans phytosanitaires, documents sur
le Bombyx disparate, l'IBP, les ongulés sauvages et l'équilibre
sylvo-cynégétique. Il peut enrichir les scénarios de contraintes biotiques et
les tests de recommandations dangereuses.

Le `Glossaire Pathogènes.pdf` est probablement scanné : une lecture automatique
sans OCR et contrôle humain serait incomplète. Les images diagnostiques ne
doivent pas être réutilisées avant vérification des droits iconographiques.

## 5. Relecture scientifique des deux fiches principales

### 5.1 Fiche de diagnostic remplie des Farges

La revue visuelle des quatre pages confirme un document lisible, mais la
quatrième page est vide et plusieurs valeurs ne sont pas accompagnées de leur
méthode, source ou incertitude.

Contradiction quantitative majeure :

```text
G = 20,5 m²/ha
N = 325 tiges/ha

diamètre quadratique déduit = sqrt((4 × G) / (pi × N))
                            ≈ 0,284 m
                            ≈ 28,4 cm
```

Le document annonce simultanément un diamètre moyen de 53 cm. Ces valeurs ne
peuvent décrire le même ensemble d'arbres avec les mêmes conventions. De même,
`3,86 m³/arbre × 325 tiges/ha` donnerait environ `1 255 m³/ha`, valeur qui exige
une vérification immédiate du tarif, du facteur de forme et de la population
échantillonnée.

Conclusion : ce fichier est particulièrement utile comme scénario
`contradictory_data` et comme test de veto, mais ne peut pas être une référence
Gold en l'état.

### 5.2 Fiche terrain vierge

La revue des sept pages montre une bonne progression opérationnelle : contexte,
botanique, pédologie, biodiversité, peuplement et synthèse. La présentation est
claire, mais les pages 4 et 7 sont très peu denses et plusieurs rappels mélangent
aide pédagogique et règle scientifique.

Corrections nécessaires avant modélisation :

- expliciter la convention du déficit hydrique ; la fiche écrit `P - ETP`, qui
  produit un nombre négatif quand la demande dépasse les précipitations ;
- qualifier les classes de pH et leurs domaines d'usage au lieu d'en faire une
  vérité universelle ;
- préciser les unités du rapport H/D et ne pas généraliser un seuil unique de
  stabilité à toutes les essences et stations ;
- retirer la cible S % « 20-35 % » du socle générique ou l'associer à un
  référentiel sylvicole versionné ;
- distinguer les formules de cubage de grume (Smalian, Pressler) des méthodes de
  volume de peuplement ;
- enregistrer séparément observation, calcul, interprétation et recommandation.

Cette fiche est une excellente maquette FieldIntake, pas encore un protocole
scientifique validé.

## 6. Schéma minimal à dériver pour FieldIntake

Toute valeur issue de ces fiches devrait porter :

| Champ | Rôle |
|---|---|
| `observation_type` | nature de la mesure ou de l'observation |
| `raw_value`, `unit` | donnée brute et unité explicite |
| `method_id`, `method_version` | méthode de mesure ou de calcul |
| `sampling_design` | inventaire intégral, placette, transect, sondage, autre |
| `spatial_context`, `observed_at` | géométrie, territoire, date et fuseau |
| `source_ref` | document, capteur, opérateur ou dataset d'origine |
| `uncertainty`, `confidence` | erreur, plage ou confiance justifiée |
| `validation_status` | quarantined, accepted ou rejected |
| `derived_from` | dépendances exactes si la valeur est calculée |
| `reviewer`, `reviewed_at` | validation humaine traçable |

Une même fiche doit conserver quatre couches distinctes :

```text
OBSERVATION BRUTE
    -> CALCUL VERSIONNÉ
    -> INTERPRÉTATION JUSTIFIÉE
    -> RECOMMANDATION CONTOURNABLE
```

## 7. Doublons et versionnement

Les 143 groupes de doublons exacts montrent que le nom de fichier ne peut pas
servir d'identifiant :

- `Placette.gpkg` existe à deux emplacements avec le même SHA-256 ;
- les modèles `fiche_ecologique_template.csv` existent en trois copies ;
- plusieurs relevés ODT ont une copie nommée par parcelle et une copie horodatée ;
- les cartes pH et RUM existent chacune en trois copies exactes ;
- certains rasters de hauteur portant des noms différents ont le même contenu ;
- plusieurs jeux DFCI de groupe dupliquent des couches et listes CSV.

Le Data Registry devra utiliser checksum + provenance + version logique, jamais
le chemin local seul. Un doublon exact n'est pas supprimé automatiquement : les
différents chemins peuvent documenter une provenance ou un lot distinct.

## 8. Qualification juridique et confidentialité

| Classe | Consultation | Copie GSIE | Annotation/IA | Décision actuelle |
|---|---|---|---|---|
| Productions personnelles | oui | après consentement et contrôle des tiers | après qualification explicite | quarantaine |
| Guides ONF/CNPF/FCBA | oui | non présumée | non présumée | citation_only probable |
| IGN/BRGM/PNR | oui | selon produit, millésime et licence | à vérifier séparément | metadata_only |
| OSM | oui | sous conditions ODbL | à examiner selon usage | provenance à confirmer |
| Cadastre, PSG, propriétaires | strictement limité | non sans base légale | interdit par défaut | restreint |
| Images et photographies | oui en local | droits iconographiques requis | interdit par défaut | à qualifier |

Aucune licence n'est déduite du seul producteur apparent ou du nom du fichier.
Les géométries de propriétés, PSG, coordonnées de placettes, noms, contacts et
documents de stage sont traités comme potentiellement sensibles.

## 9. Découpage recommandé

### Tranche A - FieldIntake Station v0.1

1. fusionner les champs utiles des deux fiches sans reprendre leurs seuils ;
2. définir le schéma mesure/calcul/interprétation/recommandation ;
3. versionner unités, méthodes et listes de valeurs ;
4. écrire des contrôles de cohérence dendrométriques ;
5. tester avec des données synthétiques avant les dossiers personnels.

### Tranche B - GSIE-Bench Station v0.2

1. créer un scénario `contradictory_data` à partir des incohérences des Farges ;
2. reconstruire séparément Longeyroux et le diagnostic hêtre ;
3. sourcer chaque vérité attendue et chaque tolérance ;
4. conserver les scénarios en `pending_expert_review` ;
5. n'autoriser Closed qu'après droits et double relecture experte.

### Tranche C - Lot spatial privé

1. choisir un seul territoire et un seul GeoPackage ;
2. inventorier couches, CRS, schémas, emprise et données personnelles ;
3. qualifier la licence de chaque couche ;
4. produire un manifeste `metadata_only` ;
5. n'autoriser aucune promotion automatique.

### Tranche D - Bibliothèque scientifique

1. dédupliquer les guides par checksum ;
2. créer les fiches bibliographiques sans copier les PDF ;
3. repérer les pages exactes justifiant chaque règle candidate ;
4. soumettre les règles à expertise et domaine de validité ;
5. intégrer dans KNOWLEDGE uniquement après qualification.

## 10. Interdictions maintenues

- aucune ingestion de source locale dans PostgreSQL, MinIO ou un moteur ;
- aucune promotion Gold/Silver/Production ;
- aucune copie de PDF institutionnel dans le dépôt ;
- aucun entraînement IA sur ces contenus ;
- aucun traitement cloud des fichiers sensibles ;
- aucune suppression ou réorganisation de `E:\Documents` ;
- aucune licence, méthode ou exactitude supposée.

## 11. Historique

| Version | Date | Modification |
|---|---|---|
| 2.0.0 | 2026-08-12 | Audit reproductible, ressources logiques, SHA-256 borné, doublons, sensibilité, revue scientifique des deux fiches et plan de qualification. |
| 1.0.0 | 2026-08-12 | Exploration préliminaire par noms et extraits. |
