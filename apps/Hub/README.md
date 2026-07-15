# Hub — Centre de Commandement GSIE

> Ce dossier n'est qu'un **pointeur documentaire** — il ne contient pas le
> projet Unreal lui-même. Le projet réel (moteur, `.uproject`, `Content/`,
> dépôt git) vit sur le disque E: pour des raisons de performance (fichiers
> binaires volumineux, DerivedDataCache, compilation de shaders).

## Emplacement réel

| Élément | Chemin |
|---|---|
| Moteur Unreal Engine 5.8 | `E:\GSIE-Centre-Commandement\UE_5.8\` |
| Projet Unreal (`.uproject`) | `E:\GSIE-Centre-Commandement\CentreCommandement\` |
| Dépôt GitHub | [github.com/NeooeN45/Hub](https://github.com/NeooeN45/Hub) (privé) |
| Twinmotion / RealityScan | `E:\GSIE-Centre-Commandement\` |

## Référence documentaire (dans ce dépôt)

- Architecture : `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211, v2.2.0)
- Spécifications : `05_SPECIFICATIONS/HUB/HUB_001_SPECIFICATION.md`,
  `HUB_002_INTERFACE_CONTRACT.md`, `HUB_003_LAYER_SHEETS.md`
- Décision d'adoption : DEC-000010 (Unreal Engine 5.8 + Cesium)

## Pourquoi cette organisation

Convention habituelle du dépôt (`CLAUDE.md` §10) : les apps clientes
(GeoSylva, QGISIA) sont des repos git indépendants physiquement présents
dans `apps/`. Le Hub déroge à cette convention pour la partie binaire —
un projet Unreal génère des dizaines de Go de cache et de fichiers
compilés, mal adaptés à la structure documentaire de `A:\Quintessences`.
Seule cette fiche de référence est versionnée ici ; le code et les assets
vivent dans le dépôt GitHub `NeooeN45/Hub`, cloné sur E:.

> Statut : Phase 4 (GSIE-DIR-0011, code métier autorisé). Projet Unreal
> `CentreCommandement` créé (template Simulation Blank C++ reconstitué
> fidèlement depuis le template officiel Epic), compilation validée
> (`Build.bat CentreCommandementEditor Win64 Development` → Succeeded).
> Voir `CONFIGURATION.md` et `RECHERCHE/` dans le dépôt Hub pour le détail
> des décisions (World Partition écarté, Nanite/Lumen, structure C++) et
> les sources officielles consultées. Prochaine étape : ouvrir l'éditeur
> et suivre la procédure de configuration Cesium documentée.
