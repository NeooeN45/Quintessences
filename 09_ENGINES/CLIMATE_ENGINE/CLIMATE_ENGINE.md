# Climate Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Climate Engine |
| **Catégorie** | Moteur domaine (climat) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-002, GSIE-CON-005 |
| **Ordre de développement** | 7 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Gérer les données climatiques historiques et actuelles, calculer les
variables bioclimatiques stationnelles et fournir les projections
climatiques avec leur scénario et leur incertitude.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| Climate Repository | Base de données | Données climatiques historiques stockées |
| Météo-France | Source externe | Données historiques, safran, projections DRIAS |
| DRIAS / IPSL | Source externe | Projections climatiques régionalisées (RCP/SSP) |
| Bundle de mission | Cache local | Données climatiques préchargées (RFC-0003) |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Variables bioclimatiques | Températures, précipitations, déficit hydrique, durée de végétation |
| `CORRELATION_ENGINE` | Données climatiques | Séries pour croisement statistique |
| `SIMULATION_ENGINE` | Projections climatiques | Scénarios long terme pour les projections de peuplement |
| `REASONING_ENGINE` | Variables bioclimatiques | Données pour l'inférence d'adaptation |
| `FOREST_DYNAMICS_ENGINE` | Variables climatiques | Données pour les modèles de croissance |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Base externe | Climate Repository | Stockage des données climatiques |
| Source externe | Météo-France | Données historiques et safran |
| Source externe | DRIAS / IPSL | Projections climatiques régionalisées |
| Aucun moteur | — | Le Climate Engine ne dépend d'aucun autre moteur (source domaine) |

## 5. Contrat d'interface

### Entrée — `ClimateQuery`

```
ClimateQuery = {
  requete_id : UUID
  emprise    : EmpriseGeographique
  periode    : PeriodeTemporelle
  variables  : liste de enum {
    temperature_moyenne, temperature_min, temperature_max,
    precipitations_totales, precipitations_estivales,
    deficit_hydrique, duree_vegetation, gel_jours,
    vent_moyen, vent_max, humidite
  }
  type_donnees : enum { historique, actuelle, projection }
  scenario    : enum { RCP26, RCP45, RCP85, SSP126, SSP245, SSP585 } (si projection)
}

PeriodeTemporelle = {
  debut : ISO 8601 (année)
  fin   : ISO 8601 (année)
}
```

### Sortie — `ClimateData`

```
ClimateData = {
  requete_id  : UUID
  variables   : liste de ClimateVariable
  source      : SourceReference
  date_donnees: ISO 8601
  mode        : enum { en_ligne, hors_ligne, degrade }
}

ClimateVariable = {
  nom         : texte (ex. « deficit_hydrique_estival »)
  valeur      : décimal
  unite       : texte (ex. « mm », « °C », « jours »)
  periode     : PeriodeTemporelle
  scenario    : enum { RCP26, RCP45, RCP85, SSP126, SSP245, SSP585, historique } (optionnel)
  incertitude : IntervalleConfiance (optionnel — obligatoire pour projections)
  source      : SourceReference
}

IntervalleConfiance = {
  minimum : décimal
  maximum : décimal
  niveau  : enum { 80pct, 90pct, 95pct }
}
```

## 6. Garanties

- **Les données climatiques sont datées et qualifiées** — chaque
  variable porte sa source et sa période (principe fondateur).
- **Les projections sont affichées avec leur scénario (RCP/SSP) et leur
  incertitude** — jamais présentées comme certitudes (principe
  fondateur).
- Mode hors-ligne : cache local des données historiques (article T-8).
- Mode dégradé documenté pour les projections temps réel.
- Le moteur ne produit **pas de diagnostic** — il fournit des données
  climatiques (séparation des responsabilités).
- Aucune donnée climatique n'est extrapolée sans justification
  scientifique (`GSIE-CON-002`).

## 7. Cas d'usage

### Cas 1 — Calcul du déficit hydrique estival pour diagnostic de dépérissement

Le Diagnostic Engine demande le déficit hydrique estival pour la
parcelle 27 sur la période 2003–2023. Le Climate Engine retourne :
déficit moyen 180 mm (source : Météo-France Safran, evidence B), avec
une tendance à la hausse sur les 10 dernières années. Ces données
alimentent le diagnostic de dépérissement de la hêtraie.

### Cas 2 — Projection climatique 2050 pour choix d'essence

Le Simulation Engine demande les projections 2041–2070 pour la
parcelle 27 sous scénario RCP 8.5. Le Climate Engine retourne :
température moyenne +2,3 °C (intervalle [+1,8 ; +2,9] à 90 %),
précipitations estivales -15 % (intervalle [-25 % ; -5 %]). Source :
DRIAS 2024. Ces projections permettent d'évaluer l'adaptation future
du hêtre et du chêne sessile à cette station.

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
