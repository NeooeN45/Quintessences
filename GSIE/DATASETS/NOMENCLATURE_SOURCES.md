# Nomenclature d'enregistrement des sources GSIE

| Champ | Valeur |
|---|---|
| **Statut** | Validée — arbitrages du Fondateur consignés au §8 |
| **Auteur** | Architecte |
| **Date** | 2026-07-28 |
| **Portée** | Toute source de données entrant dans GSIE |
| **Précédents** | `DEC-000038` (domaine de validité), `ADR-009` (garde-fou anti-invention), `GSIE-CON-005` |

## 1. Pourquoi

`SOURCES_DONNEES_EXHAUSTIVES.md` recense environ **179 sources**. Elles sont
décrites en prose : la résolution y figure sous les formes « Polygones 500 m²
min », « 50 cm rasters, ~10 pts/m² », « Placettes 20 m rayon », « Station /
parcelle ». Lisible par un humain, inexploitable par un moteur.

Aucune de ces sources n'est enregistrée comme resource. Le jour où elles le
seront, les métadonnées devront être reconstituées — et une source disparue ne
dira jamais rétrospectivement sous quelle licence elle était publiée.

**Le champ vide n'est pas neutre, il est irrécupérable.** Même raisonnement
que le domaine de validité des règles (`DEC-000038`).

## 2. Ce que la porte de validation exige déjà

Contrairement à ce qu'on pourrait croire, l'essentiel est déjà obligatoire :

| Type | Champs déjà exigés |
|---|---|
| `distribution` | `access_method`, `licence` |
| `data_asset` | `checksum`, `archived_at`, `format`, `size_bytes` |
| `rights_statement` | `licence`, `usage_rights` |
| `source` | `title`, `subtype`, `source_nature` |

Et les valeurs par défaut sont prudentes, ce qui est le bon réglage :
`ai_training_allowed` vaut **False**, `attribution_required` vaut **True**.
Autoriser est un acte ; l'oubli refuse.

**Le seul trou réel est `scale_context.grain_m2`**, facultatif aujourd'hui.

## 3. Les trois régimes d'accès

Le choix n'est pas « quelle source » mais **quel régime**. Il se déclare, il
ne se devine pas.

| Régime | Quand | `access_method` | Copie ? |
|---|---|---|---|
| **Proxy** | affichage, exploration | `ogc_wms`, `ogc_wmts`, `api_rest` | non |
| **Référence prouvée** | source stable et pérenne | `stac_api`, `ogc_wfs`, `api_rest` | non, mais `checksum` daté |
| **Copie** | la donnée entre dans une conclusion | `file_download`, `file_import` | oui, `data_asset` complet |

**Règle non négociable, dérivée de `CON-010`** :

> Toute donnée qui entre dans une conclusion citable doit être **archivée**,
> ou **prouvée inchangée** par un `checksum` daté.

Un flux WMS interrogé à la volée ne permet ni l'un ni l'autre : la carte
d'aujourd'hui n'est pas celle d'hier, et rien ne le signale. Le régime
**proxy est donc interdit** comme fondement d'une conclusion.

## 4. Le grain : comment le déclarer

`grain_m2` est la **surface réellement observée** par une unité de la source.
Il est exprimé en mètres carrés, toujours, quelle que soit la nature de la
donnée. C'est ce qui rend deux sources comparables.

| Nature de la source | Règle | Exemple |
|---|---|---|
| Raster | côté² | 50 cm → `0.25` ; 1,3 km → `1690000` |
| Polygones | surface minimale cartographiée | BD Forêt, 500 m² min → `500` |
| Placettes | surface de la placette | IFN, rayon 20 m → `1257` |
| Points / stations | surface représentative **déclarée par la source** | jamais devinée |
| Documentaire | **sans objet** — pas de `scale_context` | Rameau 2008 |

Deux interdits :

1. **Ne jamais déclarer un grain plus fin que celui de la source.** Interpoler
   AROME de 1,3 km vers 100 m ne crée pas d'information : la carte est plus
   lisse, pas plus informée. Le grain reste `1690000`.
2. **Ne jamais deviner le grain d'une source ponctuelle.** Si la source ne
   déclare pas de surface représentative, `grain_m2` reste vide et la source
   n'est pas utilisable comme couche spatiale — seulement comme observation
   localisée.

Quand une donnée est rééchantillonnée, `grain_m2` conserve **la résolution
native**, et la résolution de sortie appartient au produit dérivé, pas à la
source.

## 5. Licence et droits

`rights_statement` porte quatre champs, tous décisifs :

| Champ | Question à laquelle il répond |
|---|---|
| `licence` | sous quel régime la donnée est publiée |
| `usage_rights` | `open` / `restricted` / `private` |
| `attribution_required` | doit-on citer le producteur |
| `ai_training_allowed` | **a-t-on le droit d'entraîner un modèle dessus** |

Le dernier n'est pas théorique. « Je peux consulter » n'implique jamais « je
peux entraîner ». Il vaut `False` par défaut : une source dont on n'a pas
vérifié ce point ne sert pas à l'apprentissage.

### Le cas « accord à formaliser »

L'inventaire porte aujourd'hui des mentions telles que « Accord ONF (à
formaliser) » (DS-005) ou « Accord SOERE » (DS-006).

**Une source dont la licence n'est pas formalisée ne s'ingère pas.** Elle peut
être recensée, étudiée, citée dans un document — mais elle n'entre pas dans la
base tant que le régime d'usage n'est pas écrit. Le moment où l'on copie une
donnée puis où on la re-sert par son propre service, **on redistribue** : ce
n'est plus de la consultation.

Aucune valeur d'énumération n'est ajoutée pour cet état (§8.2) : la
distinction se lit à la présence ou à l'absence de licence renseignée. Porter
dans l'inventaire l'interlocuteur et la date de la demande suffit.

## 6. Fiche minimale d'une source

Aucune source n'entre sans ces champs. Ils sont tous existants.

```
source                title, subtype, source_nature
dataset               title, description
dataset_version       version, release_date
distribution          access_method, licence, rights_statement_id
rights_statement      licence, usage_rights,
                      attribution_required, ai_training_allowed
scale_context         level, grain_m2            ← si donnée spatiale
data_asset            format, size_bytes, checksum,
                      original_uri, archived_at  ← si copie
```

### Exemple complet — DS-002, LiDAR HD

```
source            title          « LiDAR HD »
                  subtype        dataset
                  source_nature  data_provider
dataset_version   version        « 2024 »
distribution      access_method  file_download
                  licence        « Licence Ouverte 2.0 »
rights_statement  usage_rights   open
                  attribution_required  true      (IGN doit être cité)
                  ai_training_allowed   true      (Licence Ouverte le permet)
scale_context     level          landscape
                  grain_m2       0.25             (rasters 50 cm)
data_asset        checksum       <sha256>
                  archived_at    2026-07-28T...
```

Le nuage de points brut (~10 pts/m²) est une **distribution distincte** du
même `dataset_version`, avec son propre `grain_m2`. Une source qui livre
plusieurs produits de résolutions différentes se déclare en plusieurs
distributions, jamais en une moyenne.

## 7. Ordre d'enregistrement des 179 sources

Ne pas tout enregistrer d'un coup. Priorité par usage réel :

1. **Les sources déjà consommées par le code** — AROME, GBIF/TAXREF,
   SoilGrids, IGN, Météo-France. Elles sont utilisées sans être déclarées :
   c'est la dette la plus urgente.
2. **Les sources de la chaîne pilote** (`DEC-000038` : chêne sessile, réserve
   utile, un territoire).
3. **Les sources à licence ouverte non encore consommées** — Sentinel, LiDAR
   HD, BD Forêt.
4. **Les sources sous accord à formaliser** — après formalisation seulement.

## 8. Arbitrages du Fondateur (2026-07-28)

### 8.1 Le grain est exigé quand la source est spatiale — mais le lien manque

**Retenu** : `grain_m2` devient obligatoire dès qu'un `scale_context` décrit
une source de données spatiale, et reste facultatif pour les contextes
d'échelle sémantiques (une question posée « à l'échelle du peuplement » n'a pas
de grain).

**Obstacle structurel constaté à l'implémentation** : aucun `dataset`,
`distribution` ni `data_asset` ne référence `scale_context`. Quinze tables le
font — `question`, `decision`, `correlation`, `scenario`, `sampling_event`… —
mais **pas la chaîne des jeux de données**.

Autrement dit, `scale_context.grain_m2` décrit aujourd'hui *le grain
d'observation d'un objet de connaissance*, pas *la résolution native d'une
source*. La seconde n'a donc **aucun emplacement** dans le métamodèle.

La règle ne peut pas être appliquée sans trancher d'abord :

| Voie | Effet |
|---|---|
| Ajouter `scale_context_id` à `distribution` | réutilise un concept existant, cohérent avec le métamodèle ; migration |
| Ajouter `native_grain_m2` à `distribution` | plus direct, mais duplique une notion déjà modélisée |
| Statu quo | la résolution native reste en prose, inexploitable par un moteur |

**Recommandation** : la première. `scale_context` porte déjà `level`,
`extent_m2` (couverture) et `grain_m2` (résolution) — exactement ce qu'une
distribution doit déclarer. Dupliquer le nombre ailleurs créerait deux sources
de vérité, faute que `DEC-000038` a précisément écartée pour les règles.

C'est une modification de contrat : elle relève d'une décision tracée, non de
la présente nomenclature.

### 8.2 Pas de valeur d'énumération pour la licence non formalisée

**Retenu** : aucun `licence_a_formaliser` dans `usage_rights`. La distinction
se lit à la présence ou à l'absence de licence renseignée, ce qui suffit
aujourd'hui et pourra évoluer si l'usage le démontre.

La règle opérationnelle est inchangée : **licence absente, pas d'ingestion.**

### 8.3 Le droit d'entraînement reste à approfondir

**Non tranché.** `ai_training_allowed` vaut `False` par défaut, ce qui est le
réglage prudent : en l'absence de vérification, la source ne sert pas à
l'apprentissage.

Reste à établir **qui vérifie, sur quels critères, et avec quelle trace** qu'une
licence autorise l'entraînement. Une licence ouverte n'emporte pas
automatiquement ce droit, et l'engagement est juridique, pas technique. À
instruire avec `19_LEGAL/`.
