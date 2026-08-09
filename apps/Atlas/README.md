# Atlas — Application cartographie et SIG

| Champ | Valeur |
|---|---|
| **Écosystème** | Quintessences |
| **Moteur** | GSIE |
| **Domaine** | Cartographie globale |
| **Statut** | Planifiée (Phase 4) — réservée par GSIE-DIR-0009, activée par DEC-000056 |

## Responsabilités

- Cartographie interactive multi-couches
- Analyse spatiale (relief, pente, exposition, distance)
- Catalogue et gestion des couches géospatiales
- Export et partage de cartes

## Moteurs GSIE consommés

GIS, Knowledge, Correlation

## Datasets

IGN (BD Topo, BD Ortho, RGE ALTI), Cadastre, OpenStreetMap

## Intégration GSIE

Atlas est la projection métier cartographie/SIG du jumeau numérique
environnemental fédéré GSIE. Elle publie et sert les couches
géospatiales de référence avec leur origine et leur date de mise à
jour, et fournit les services d'analyse spatiale communs aux autres
applications (GeoSylva, Ignis, Hydro, Flora, Artemis, Terra) sans
dupliquer leurs bases internes.

Voir [GSIE_INTEGRATION.md](GSIE_INTEGRATION.md).

## Voir aussi

- `GSIE/ARCHITECTURE/` — architecture du moteur
- `GSIE/ENGINES/GIS_ENGINE/` — moteur consommé
- `GSIE/KNOWLEDGE/` — base de connaissances
- `03_DECISIONS/DEC-000056.md` — décision d'enregistrement
