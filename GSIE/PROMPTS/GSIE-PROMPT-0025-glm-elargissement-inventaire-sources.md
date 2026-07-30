# GSIE-PROMPT-0025 — Élargissement de l'inventaire des sources de données

| Champ | Valeur |
|---|---|
| Statut | À LANCER |
| Agent cible | GLM 5.2 |
| Environnement | Devin |
| Dépôt | Quintessences |
| Branche | `feat/inventaire-sources-elargi` |
| Fichiers possédés | `GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md`, `GSIE/DATASETS/DATASET_CATALOG.md` |
| Fichiers interdits | tout `GSIE/API/src/**` — **aucun code**, ce prompt est documentaire |
| Précédents | `NOMENCLATURE_SOURCES.md`, `RFC-0029`, `DEC-000038`, `ADR-009` |
| Orchestrateur | Architecte |
| Relecteur | Architecte puis Fondateur |

## Constat

`SOURCES_DONNEES_EXHAUSTIVES.md` recense **179 sources distinctes** sur
2 349 lignes. Le travail est sérieux et bien structuré.

Il est aussi **insuffisant pour ce qui vient**. L'audit du 30 juillet
(`RFC-0029` §11) a établi deux choses :

1. Quatre natures de données présentes dans le projet — synthétique, sortie de
   modèle, capteur instrumenté, capteur participatif — n'ont aucun type de
   source correct, et tomberaient toutes dans `observation_terrain`.
2. L'inventaire est **mince sur les services distants** (WMS, WMTS, WFS, WCS,
   STAC) alors que `AccessMethod` les prévoit depuis l'origine.

À quoi s'ajoutent des angles morts géographiques et thématiques listés au §3.

**Objectif : porter l'inventaire à un état qui tienne pour cinq ans**, en
qualité de description autant qu'en nombre.

## 1. Règle absolue — ne rien inventer

`ADR-009` interdit au système d'inventer. Cette interdiction vaut pour toi.

**Un agent qui liste des sources hallucine des URL.** C'est le mode d'échec
attendu de cette tâche, et il est particulièrement coûteux ici : une source
fausse dans l'inventaire sera découverte des mois plus tard, au moment de
l'ingestion, quand personne ne saura plus d'où elle venait.

Par conséquent :

- **Chaque URL doit être vérifiée** par un accès réel avant d'être écrite.
- Une source dont tu ne peux pas vérifier l'URL, la licence ou le producteur
  va dans une section séparée **`À VÉRIFIER`**, avec le motif exact du doute.
- **Ne complète jamais un champ par analogie.** Une licence inconnue s'écrit
  `licence: inconnue — à établir`, jamais « probablement Etalab ».
- Mieux vaut 300 sources vérifiées que 800 dont 200 sont fausses. Le nombre
  n'est pas le critère de réussite ; la vérifiabilité l'est.

Le compte rendu final devra indiquer **combien d'URL ont été effectivement
testées**, et combien ont échoué.

## 2. Format obligatoire de chaque entrée

`NOMENCLATURE_SOURCES.md` fixe ce qu'une source doit porter. Chaque entrée
nouvelle respecte ce format, sans exception :

| Champ | Obligatoire | Note |
|---|---|---|
| `nom` | oui | Nom officiel du producteur |
| `producteur` | oui | Organisme, avec son pays |
| `url` | oui | **Vérifiée**, pas déduite |
| `access_method` | oui | Une des onze valeurs de `AccessMethod` — voir §4 |
| `licence` | oui | Nom exact, ou `inconnue — à établir` |
| `ai_training_allowed` | oui | `False` par défaut. Autoriser est un acte |
| `grain_m2` | si spatial | Résolution native en m². `50 cm` → `0.25` |
| `emprise` | si spatial | France métropolitaine, DOM, Europe, mondial |
| `etendue_temporelle` | si temporel | Début — fin, ou « continu » |
| `frequence_mise_a_jour` | oui | Quotidienne, annuelle, ponctuelle… |
| `format` | oui | GeoTIFF, COG, NetCDF, Shapefile, GeoPackage, CSV, JSON… |
| `volume_estime` | oui | Ordre de grandeur, avec l'unité |
| `type_source` | oui | Voir §5 — **quatre valeurs nouvelles** |
| `moteur_destinataire` | oui | Quel(s) moteur(s) GSIE la consommeraient |
| `regime` | oui | `possedee`, `referencee`, `derivee` — voir `RFC-0029` §10 |

Une entrée à laquelle il manque un champ obligatoire n'est pas une entrée :
elle va dans `À VÉRIFIER`.

## 3. Angles morts identifiés — à couvrir en priorité

Ces manques ont été relevés par l'Architecte. Ils ne sont pas exhaustifs :
c'est le point de départ, pas le périmètre.

### 3.1 Géographique

L'inventaire est presque entièrement métropolitain.

- **Outre-mer** : Guyane (forêt amazonienne française, ONF Guyane), La Réunion,
  Martinique, Guadeloupe, Mayotte, Nouvelle-Calédonie. Ce sont des forêts
  majeures, à écologie radicalement différente.
- **Transfrontalier** : Suisse (WSL, NFI suisse), Allemagne (Thünen,
  Bundeswaldinventur), Belgique, Espagne (MITECO, IFN espagnol), Italie
  (INFC), Luxembourg. Un massif ne s'arrête pas à la frontière.

### 3.2 Thématique

- **Archives historiques** — carte de Cassini, carte d'État-Major, **photos
  aériennes IGN depuis 1919**. La dynamique forestière sur un siècle n'a pas
  d'autre source. Probablement l'angle mort le plus riche.
- **Réglementaire et zonages** — Natura 2000, ZNIEFF, réserves biologiques,
  PPRIF, servitudes, arrêtés de protection de biotope, forêts de protection.
- **Foncier et filière** — cadastre, propriété forestière, documents de
  gestion durable, filière bois, dessertes.
- **Sols** — RMQS, GlobalSoilMap, BDAT, cartes pédologiques départementales.
- **Génétique et matériel forestier** — vergers à graines, régions de
  provenance, arrêtés MFR.
- **Phytosanitaire** — DSF, EPPO, réseaux d'observation des ravageurs.
- **Biodiversité** — INPN, OFB, Atlas de la biodiversité, données
  naturalistes associatives.
- **Sylvopastoralisme, agroforesterie, haies** — BD Haies, dispositifs
  agroforestiers.

### 3.3 Modes d'accès

L'inventaire décrit surtout des téléchargements. Or les services distants sont
ce qu'un client consommera au quotidien :

- **Géoservices IGN** — WMS, WMTS, WFS, et leur catalogue complet de couches.
- **Copernicus** — services WMS/WMTS, API, catalogues STAC.
- **Sentinel Hub, PEPS, CDSE** — accès aux scènes Sentinel.
- **Catalogues STAC** publics — Element84, Microsoft Planetary Computer,
  Copernicus.
- **API météo** — Météo-France (portail public), OpenData, ECMWF, DRIAS.
- **Hydro** — Hub'Eau (plusieurs API), Sandre, BanqueHydro.

Pour chacun : la couche ou le point d'entrée **exact**, pas le portail
d'accueil. « Géoportail » n'est pas une source ; « IGN WMTS, couche
ORTHOIMAGERY.ORTHOPHOTOS » en est une.

## 4. `AccessMethod` — les onze valeurs à employer

`api_rest`, `api_graphql`, `ogc_wms`, `ogc_wfs`, `ogc_wmts`, `ogc_wcs`,
`stac_api`, `file_download`, `file_import`, `publication_text`,
`knowledge_extraction`.

N'en invente aucune. Si une source n'entre dans aucune, signale-le en compte
rendu — c'est une information utile, pas un échec.

## 5. `type_source` — quatre valeurs nouvelles, proposées par `RFC-0029` §11.3

Les quatre valeurs actuelles (`peer_reviewed`, `referentiel_officiel`,
`expert_identifie`, `observation_terrain`) ne couvrent pas tout. Emploie
également, en les signalant comme proposées :

| Valeur | Ce qu'elle désigne |
|---|---|
| `donnee_synthetique` | Rendu simulé, jeu généré (Unreal, Gazebo, Isaac Sim) |
| `sortie_de_modele` | Prédiction, détection, segmentation produite par un modèle |
| `capteur_instrumente` | Capteur calibré, chaîne de mesure connue |
| `capteur_participatif` | Capteur citoyen, réseau communautaire |

**Point d'attention majeur.** Un jeu de données d'entraînement — Pyro-SDIS,
FLAME, D-Fire — n'est **pas** une source d'assertion. Il décrit ce qu'un
modèle doit reconnaître ; il n'affirme rien sur un peuplement. Marque-les
`usage: entrainement_uniquement`, et ne les mélange pas aux sources de
connaissance.

## 6. Organisation en sous-agents

Le volume justifie une répartition. Un sous-agent par domaine, travaillant en
parallèle, chacun produisant un fichier partiel qui sera fusionné :

| Sous-agent | Périmètre |
|---|---|
| A | Forestier, dendrométrie, gestion, filière |
| B | Climat, météo, projections |
| C | Sols, géologie, hydrologie |
| D | Biodiversité, taxonomie, phytosanitaire |
| E | Télédétection, satellite, catalogues STAC |
| F | Incendie, risques, DFCI |
| G | Réglementaire, zonages, foncier |
| H | Archives historiques et cartographie ancienne |
| I | Outre-mer et transfrontalier |

**Chaque sous-agent applique le §1 intégralement.** Un sous-agent qui rend des
URL non vérifiées fait échouer la tâche entière : la fusion ne peut pas
rattraper une invention.

**Contrainte de fusion** : un même producteur peut apparaître chez plusieurs
sous-agents (l'IGN produit du forestier, du réglementaire et de l'historique).
Dédoublonne par URL exacte, pas par nom.

## 7. Ce que tu ne dois pas faire

- **Aucun code.** Ce prompt est documentaire. Ne touche à rien sous
  `GSIE/API/src/`.
- **Ne modifie pas** `NOMENCLATURE_SOURCES.md` ni `RFC-0029` — ce sont des
  documents d'arbitrage, tu en es le lecteur, pas l'auteur.
- **Ne supprime aucune entrée existante.** Si tu penses qu'une source listée
  est erronée ou morte, signale-la en compte rendu sous
  `SIGNALEMENTS — entrées existantes douteuses`, avec la preuve. Le Fondateur
  tranche.
- **N'estime pas un volume par analogie.** Un ordre de grandeur inconnu
  s'écrit `volume: inconnu`.

## 8. Critères d'acceptation

1. Chaque entrée nouvelle porte **tous** les champs obligatoires du §2.
2. **Chaque URL a été testée**, et le compte rendu dit combien l'ont été et
   combien ont échoué.
3. Les entrées non vérifiables sont dans `À VÉRIFIER`, avec le motif.
4. Les neuf domaines du §6 sont couverts, ou l'absence est justifiée.
5. Les modes d'accès distants (§3.3) sont représentés par des couches ou
   points d'entrée **exacts**, jamais par un portail.
6. Les jeux d'entraînement IA sont séparés et marqués
   `usage: entrainement_uniquement`.
7. Aucun doublon d'URL.
8. Le comptage du §7 de `SOURCES_DONNEES_EXHAUSTIVES.md` est mis à jour, en
   distinguant vérifié et à vérifier.

## 9. Compte rendu attendu

Court et factuel. Quatre points :

1. **Combien de sources ajoutées**, par domaine.
2. **Combien d'URL testées, combien en échec.** Ce chiffre est le plus
   important du compte rendu.
3. **Ce que tu n'as pas trouvé** — un domaine où tu as cherché sans résultat
   est une information précieuse : elle évite qu'un autre recommence.
4. **Signalements** — entrées existantes douteuses, modes d'accès hors des
   onze valeurs, natures de données hors des huit `type_source`.

Ne rédige pas de synthèse valorisante. Si une partie du travail est
incomplète, dis-le : une lacune signalée coûte moins cher qu'une lacune
découverte à l'ingestion.
