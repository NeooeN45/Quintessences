# Aeris — Application météo et climat

| Champ | Valeur |
|---|---|
| **Écosystème** | Quintessences |
| **Moteur** | GSIE |
| **Domaine** | Atmosphère / météo |
| **Statut** | Planifiée (Phase 4) — réservée par GSIE-DIR-0009, activée par DEC-000056 |

## Responsabilités

- Prévisions et observations météorologiques
- Variables bioclimatiques (températures, précipitations, déficit
  hydrique, durée de végétation)
- Alertes météo (gel, sécheresse, tempête)
- Projections climatiques (scénarios RCP/SSP)

## Moteurs GSIE consommés

Climate, Knowledge, Correlation, Diagnostic

## Datasets

Météo-France (SYNOP), Copernicus Climate Change Service (C3S)

## Intégration GSIE

Aeris est la projection métier météo/climat du jumeau numérique
environnemental fédéré GSIE. Elle publie les observations et
prévisions météorologiques ainsi que les variables bioclimatiques
avec leur provenance, leur date et — pour les projections — leur
scénario et leur incertitude. Elle alimente les autres applications
(GeoSylva, Ignis, Hydro, Flora, Artemis, Terra) en données
climatiques datées sans se substituer à leurs propres diagnostics.

Voir [GSIE_INTEGRATION.md](GSIE_INTEGRATION.md).

## Voir aussi

- `GSIE/ARCHITECTURE/` — architecture du moteur
- `GSIE/ENGINES/CLIMATE_ENGINE/` — moteur consommé
- `GSIE/KNOWLEDGE/` — base de connaissances
- `03_DECISIONS/DEC-000056.md` — décision d'enregistrement
