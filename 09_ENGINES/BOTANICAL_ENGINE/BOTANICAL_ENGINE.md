# Botanical Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Botanical Engine |
| **Catégorie** | Moteur domaine (botanique) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-005, GSIE-CON-010 |
| **Ordre de développement** | 9 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Gérer la taxonomie, la nomenclature et l'autécologie des espèces
forestières, en assurant le versionnement des évolutions taxonomiques et
la fourniture des données d'identification et d'exigences écologiques.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| Species Repository | Base de données | Données d'espèces stockées (taxonomie, autécologie) |
| Ontology | Base de données | Ontologie taxonomique et relations nomenclaturales |
| Tela Botanica | Source externe | Référentiel nomenclatural français |
| GBIF | Source externe | Global Biodiversity Information Facility |
| BDNFF | Source externe | Base de Données Nomenclaturale de la Flore de France |
| Observations terrain | Données utilisateur | Relevés floristiques, identifications |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Données botaniques | Autécologie des essences présentes et candidates |
| `CORRELATION_ENGINE` | Données botaniques | Présence/absence d'essences pour croisement |
| `RECOMMENDATION_ENGINE` | Données botaniques | Exigences et optimums d'essences candidates |
| `REASONING_ENGINE` | Données botaniques | Autécologie pour l'inférence d'adaptation |
| Utilisateur (via interface) | Identification | Aide à la détermination, clés d'identification |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Base externe | Species Repository | Stockage des données d'espèces |
| Base externe | Ontology (via `KNOWLEDGE_ENGINE`) | Structure taxonomique |
| Source externe | Tela Botanica, GBIF, BDNFF | Référentiels nomenclaturaux officiels |
| Aucun moteur | — | Le Botanical Engine ne dépend d'aucun autre moteur (source domaine) |

## 5. Contrat d'interface

### Entrée — `BotanicalQuery`

```
BotanicalQuery = {
  requete_id : UUID
  type       : enum { par_essence, par_taxon, par_station, identification }
  essence    : texte (nom scientifique ou vernaculaire, optionnel)
  station_id : UUID (optionnel)
  parametres : liste de enum {
    taxonomie, nomenclature, autecologie, synonymes, exigences, optimum, amplitude
  }
}
```

### Sortie — `BotanicalData`

```
BotanicalData = {
  requete_id : UUID
  especes    : liste de EspeceData
  source     : SourceReference
  date_donnees : ISO 8601
}

EspeceData = {
  taxon_id        : UUID
  nom_scientifique : texte
  nom_vernaculaire : texte
  synonymes       : liste de texte
  famille         : texte
  autecologie     : Autecologie (optionnel)
  taxonomie_version : texte (version du référentiel)
  source          : SourceReference
}

Autecologie = {
  optimum_ph       : IntervalleValeur (optionnel)
  optimum_altitude : IntervalleValeur (optionnel)
  optimum_precipitations : IntervalleValeur (optionnel)
  tolerance_gel    : décimal (°C, optionnel)
  tolerance_ombre  : enum { tres_forte, forte, moderee, faible, tres_faible }
  exigence_eau     : enum { hygrophyte, mesophyte, xerophyte }
  exigence_sol     : texte (optionnel)
  source           : SourceReference
  evidence_level   : enum { A, B, C, D, E, F }
}

IntervalleValeur = {
  minimum : décimal
  maximum : décimal
  unite   : texte
}
```

## 6. Garanties

- **Toute donnée botanique est sourcée et versionnée** — chaque taxon
  porte son référentiel d'origine (Tela Botanica, GBIF, BDNFF) et la
  version du référentiel (principe fondateur).
- **Les évolutions taxonomiques sont tracées** — un taxon peut changer
  de nom, mais l'historique est conservé (`GSIE-CON-010`).
- Les synonymes sont gérés — une recherche par ancien nom renvoie le
  taxon courant.
- Le moteur ne produit **pas de diagnostic** — il fournit des données
  taxonomiques et autécologiques (séparation des responsabilités).
- Fonctionnement hors-ligne sur données en cache local (article T-8).
- Les données autécologiques portent leur niveau de preuve
  (`GSIE-CON-005`).

## 7. Cas d'usage

### Cas 1 — Fourniture de l'autécologie du chêne sessile pour recommandation

Le Recommendation Engine demande l'autécologie du chêne sessile
(*Quercus petraea*). Le Botanical Engine retourne : optimum pH 4,5–6,0
(evidence B, source : Rameau et al., 2018), optimum altitude 0–1400 m
(evidence B), tolérance gel -22 °C (evidence C), exigence eau :
mésophyte (evidence B). Le synonyme *Quercus sessiliflora* est
référencé. Ces données alimentent la recommandation de reboisement.

### Cas 2 — Évolution taxonomique d'une espèce

En 2028, le GBIF révise la classification d'une espèce : *Sorbus aria*
devient *Aria edulis*. Le Botanical Engine archive l'ancienne
classification (version 1, *Sorbus aria*, source GBIF 2024) et crée la
nouvelle (version 2, *Aria edulis*, source GBIF 2028). Les recherches
par *Sorbus aria* continuent de fonctionner via le système de
synonymes. Les recommandations passées restent explicables avec le
nom utilisé à l'époque (`GSIE-CON-010`).

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
