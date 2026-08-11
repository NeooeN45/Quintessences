# Terra — Application pédologie et sols

| Champ | Valeur |
|---|---|
| **Écosystème** | Quintessences |
| **Moteur** | GSIE |
| **Domaine** | Sols / géologie |
| **Statut** | Planifiée (Phase 4) — réservée par GSIE-DIR-0009, activée par DEC-000056 |

## Responsabilités

- Caractérisation des sols (texture, pH, profondeur, drainage,
  réserve utile en eau)
- Classification pédologique (Référentiel Pédologique Français, WRB)
- Cartographie des unités de sol
- Suivi de la qualité des sols

## Moteurs GSIE consommés

Pedology, Knowledge, Climate, Correlation

## Datasets

SoilGrids (ISRIC), RMQS (INRAE), Référentiel Pédologique Français

## Intégration GSIE

Terra est la projection métier pédologie du jumeau numérique
environnemental fédéré GSIE. Elle publie les caractéristiques et
classifications de sol avec leur référentiel source (aucun seuil
n'est inventé — CON-002), et fournit ces données stationnelles aux
autres applications (GeoSylva, Ignis, Hydro, Flora, Artemis, Atlas)
sans produire elle-même de diagnostic.

Voir [GSIE_INTEGRATION.md](GSIE_INTEGRATION.md).

## Voir aussi

- `GSIE/ARCHITECTURE/` — architecture du moteur
- `GSIE/ENGINES/PEDOLOGY_ENGINE/` — moteur consommé
- `GSIE/KNOWLEDGE/` — base de connaissances
- `03_DECISIONS/DEC-000056.md` — décision d'enregistrement
