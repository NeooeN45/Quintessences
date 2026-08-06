# Flora — Application végétation

| Champ | Valeur |
|---|---|
| **Écosystème** | Quintessences |
| **Moteur** | GSIE |
| **Domaine** | Végétation |
| **Statut** | Planifiée (Phase 4) |

## Responsabilités

- Flore
- Taxonomie
- Cartographie végétale
- Phénologie

## Moteurs GSIE consommés

Botanical, Knowledge, GIS, Climate

## Datasets

GBIF, Tela Botanica, BDNFF, INPN

## Intégration GSIE

Flora est la projection métier végétation du jumeau numérique fédéré GSIE.
Elle échange avec GeoSylva, Ignis, Hydro et Artemis par des ressources GSIE
versionnées, en conservant la provenance des observations et la séparation
entre état réel, prévision et simulation.

Voir [GSIE_INTEGRATION.md](GSIE_INTEGRATION.md).

## Voir aussi

- `GSIE/ARCHITECTURE/` — architecture du moteur
- `GSIE/KNOWLEDGE/` — base de connaissances
