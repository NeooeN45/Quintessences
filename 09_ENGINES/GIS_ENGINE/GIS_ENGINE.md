# GIS Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | GIS Engine |
| **Catégorie** | Moteur domaine (géospatial) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-005, GSIE-CON-007 |
| **Ordre de développement** | 6 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Gérer, calculer et fournir les données géospatiales de référence
(parcelles, relief, hydrographie) et les caractéristiques stationnelles
dérivées (pente, exposition, altitude), avec traçabilité de la source
et de la date de mise à jour.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| Spatial Database | Base de données | Données géospatiales stockées (parcelles, MNT, hydrographie) |
| IGN | Source externe | BD Ortho, BD Topo, MNT, cadastre, données forestières IGN |
| Cadastre | Source externe | Limites parcellaires, propriété |
| Bundle de mission | Cache local | Données préchargées pour fonctionnement hors-ligne (RFC-0003) |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Caractéristiques stationnelles | Pente, exposition, altitude, distance, hydrographie |
| `CORRELATION_ENGINE` | Données géospatiales | Couches pour croisement statistique |
| `REASONING_ENGINE` | Caractéristiques stationnelles | Données géographiques pour l'inférence |
| `SIMULATION_ENGINE` | Emprise et terrain | MNT et limites pour les projections spatialisées |
| Utilisateur (via interface) | Cartes | Couches cartographiques pour visualisation terrain |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Base externe | Spatial Database | Stockage des données géospatiales |
| Source externe | IGN | Données officielles (BD Ortho, BD Topo, MNT) |
| Source externe | Cadastre | Limites parcellaires |
| Aucun moteur | — | Le GIS Engine ne dépend d'aucun autre moteur (source domaine) |

## 5. Contrat d'interface

### Entrée — `GeoQuery`

```
GeoQuery = {
  requete_id : UUID
  type       : enum { station, parcelle, zone, itineraire }
  emprise    : EmpriseGeographique
  couches_demandees : liste de enum { mnt, pente, exposition, altitude, hydrographie, cadastre, orthophoto, sol }
  resolution : texte (optionnel — ex. « 5m », « 25m »)
}
```

### Sortie — `GeoData`

```
GeoData = {
  requete_id   : UUID
  station_id   : UUID (optionnel)
  couches      : liste de GeoLayer
  source       : SourceReference
  date_donnees : ISO 8601 (date de mise à jour des données)
  mode         : enum { en_ligne, hors_ligne, degrade }
}

GeoLayer = {
  nom       : enum { mnt, pente, exposition, altitude, hydrographie, cadastre, orthophoto }
  type      : enum { raster, vecteur, mesure }
  valeurs   : structure selon type (grille, géométries, valeur ponctuelle)
  unite     : texte (ex. « degrés », « mètres », « % »)
  resolution: texte (optionnel)
  source    : SourceReference
  date_maj  : ISO 8601
}

StationCharacteristics = {
  station_id  : UUID
  altitude_m  : décimal
  pente_degres: décimal
  exposition_degres : décimal (0–360)
  hydrographie_proximite_m : décimal (optionnel)
  coordonnees : { latitude, longitude } (WGS 84)
  source      : SourceReference
}
```

## 6. Garanties

- **Toute donnée géospatiale est sourcée et datée** — chaque couche
  porte son origine (IGN, cadastre) et sa date de mise à jour (principe
  fondateur).
- Mode hors-ligne : cache local des données de référence (article T-8,
  RFC-0003 bundle de mission).
- Mode dégradé documenté lorsque les données temps réel sont
  indisponibles.
- Le moteur ne produit **pas de diagnostic** — il fournit des données
  et des caractéristiques (séparation des responsabilités).
- Les coordonnées sont en WGS 84 (standard interoperable).

## 7. Cas d'usage

### Cas 1 — Calcul des caractéristiques stationnelles pour une parcelle

Le forestier sélectionne la parcelle 27 sur l'application. Le GIS
Engine interroge le MNT en cache local (IGN, 2024) et calcule : altitude
moyenne 420 m, pente moyenne 18°, exposition dominante sud-ouest (225°),
distance au cours d'eau le plus proche : 150 m. Ces caractéristiques
sont transmises au Diagnostic Engine et au Reasoning Engine.

### Cas 2 — Visualisation cartographique hors-ligne en terrain isolé

Le forestier est en terrain sans réseau. Le GIS Engine fournit les
couches cartographiques (orthophoto IGN, limites parcellaires, MNT)
depuis le cache local du bundle de mission. L'application affiche la
carte, la position GPS du forestier et les arbres inventoriés. Les
modifications sont stockées localement et synchronisées au retour
(RFC-0003, synchronisation orientée données).

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
