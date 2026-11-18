# Réconciliation des sources documentées et des sources connectables

**Statut :** contrôle de gouvernance actif
**Date :** 2026-08-30
**Périmètre :** inventaires D1 à D8, registre SCI-001, adapters Data Registry,
handoff Forge et GSIE-Bench.

## Décision

Toutes les sources connues doivent être cataloguées. Toutes les sources
cataloguées ne doivent pas être connectées. La connexion requiert un
identifiant canonique, une fiche de distribution, une qualification juridique
et technique, un chemin d'exécution borné et des tests reproductibles.

Cette séparation protège la base contre les changements d'API, les licences
incomplètes, les jeux non reproductibles et la fuite de données entre
l'entraînement et l'évaluation.

## Ce qui est déjà réalisé

| Famille | Réalisation | Limite conservée |
|---|---|---|
| GBIF | Adapter de résolution d'espèces et surface normalisée | pas d'ingestion globale des occurrences |
| TAXREF | Miroir GBIF déclaré dans SCI-001 et adapter dédié | le service direct INPN ne constitue pas une voie de secours implicite |
| SoilGrids | Client WCS 2.0.1 borné et adapter actif | REST bêta bloqué ; FETCH soumis à décision opérateur |
| Bellifa | Loader local versionné et adapter sans réseau | aucune inférence de statut absent |
| IGN | Cadastre et altitude derrière l'adapter IGN | pas de WFS arbitraire ni d'archivage sans version de couche |
| Météo-France | Météo des forêts derrière un adapter | SAFRAN, ARPEGE/AROME et observations du sol non qualifiés |
| IFN | Handoff Forge versionné, checksum et archivage transactionnel | statut initial découvert ; aucune promotion automatique |

## Inventaire D1 à D8

Les documents de recherche contiennent notamment des sources de taxonomie,
dendrométrie, sols, climat, eau, faune, entomologie, mycologie et pathologie.
Les priorités P0/P1 qui y sont écrites sont des priorités de recherche et non
des autorisations d'accès.

Les groupes à traiter en premier sont :

- BD Forêt, LiDAR HD et BD Ortho pour GIS et Forest Dynamics ;
- DRIAS et les produits climatologiques après qualification de distribution ;
- BDAT, BRGM, RMQS et GIS Sol pour Pedology ;
- OpenObs, BDC-Statuts et les occurrences GBIF pour biodiversité ;
- Hub'Eau, Vigicrues, SANDRE, ADES et BD Topage pour l'hydrologie ;
- DSF, DEPERIS, inventIF, EPPO et Ephytia pour la santé forestière ;
- FongiBase, MycoBank, GlobalFungi et FungalTraits pour la mycologie ;
- Sentinel-1/2, Landsat, MODIS, GEDI et THEIA pour la télédétection.

Ces groupes restent `candidate` tant qu'une fiche ne prouve pas la
distribution exacte, le schéma, le millésime, le quota, la licence et le
protocole de test. Les ressources partenaires ou propriétaires restent
`METADATA_ONLY` ou `PARTNER_GATE`.

## Statuts opérationnels obligatoires

| Statut | Signification | Autorisation |
|---|---|---|
| `ADAPTER_QUERY` | service interrogé par une façade déclarée | requête bornée uniquement |
| `FORGE_HANDOFF` | octets acquis par Forge puis vérifiés par GSIE | archivage manifesté, statut découvert |
| `METADATA_ONLY` | source connue mais non qualifiée | titre, version, lien et citation |
| `EPHEMERAL_TDM` | fouille temporaire autorisée | faits atomiques, destruction de la copie |
| `PARTNER_GATE` | accord nécessaire | aucune copie sans accord |
| `UNWIRED_OPEN_COPY` | licence ouverte mais adapter absent | aucun job tant que l'adapter n'existe pas |
| `BLOCKED` | interdit ou suspendu | aucune ingestion |
| `HISTORICAL` | identité remplacée | réconciliation seulement |

## Travaux restant nécessaires

1. Créer une fiche SCI-001 pour chaque source D1-D8 retenue, sans inventer la
   licence lorsque la preuve manque.
2. Dédupliquer les sources par fournisseur, distribution, millésime et
   checksum, plutôt que par nom commercial.
3. Ajouter un adapter spécialisé par produit ou couche, jamais un connecteur
   générique qui autoriserait des URLs arbitraires.
4. Ajouter les tests de quota, reprise, pagination, cache, checksum,
   provenance et non-régression de schéma.
5. Rejouer un flux Forge → manifeste → archive → validation → promotion
   contrôlée avant toute ouverture de FETCH.
6. Fermer la promotion d'entraînement tant que la suite Open/Silver,
   l'expertise scientifique et l'absence de fuite ne sont pas prouvées.

## Références

- `GSIE/API/src/gsie_api/governance/source_registry.py`
- `GSIE/API/src/gsie_api/governance/source_coverage.py`
- `GSIE/API/src/gsie_api/governance/engine_source_matrix.py`
- `GSIE/API/docs/data/GSIE_DATA_ADAPTER_CONTRACT_PHASE3.md`
- `GSIE/API/docs/data/GSIE_FORGE_ACQUISITION_HANDOFF.md`
- `GSIE/DATASETS/PRIORISATION_INTEGRATION_SOURCES_2026-08-13.md`
- `GSIE/RESEARCH/SOURCES/README.md`
