# B00 — inventaire initial GeoSylva / serveur

| Champ | Valeur |
|---|---|
| Date | 2026-09-28 |
| État | B00 partiel : contrats inspectés ; environnement complet non qualifié |
| Produit actif | GeoSylva V3.1 après refonte V3.0 |

## Références et synchronisation Git

Le dépôt serveur est `NeooeN45/Quintessences`, base `d7b400c`.
Le dépôt Android est `NeooeN45/GeoSylva`, base distante récupérée `c59ba7c`.
La copie Android de travail inspectée est à `b795b2e` avec de nombreux fichiers
modifiés/non suivis. Elle contient des travaux absents de cette base distante,
dont le client d'analyse. Ces états ne sont pas interchangeables.
La publication documentaire Android part du dépôt distant dans une copie
séparée ; aucun travail local Android n'est écrasé ou déclaré accepté.

## Contrat déjà compatible sur les noms

L'[inventaire calculé](GEOSYLVA_CONTRACT_INVENTORY.json) compare le DTO
`ParcelSyncPayloadDto` au modèle `GeoSylvaParcelPayload` : **29 champs des deux
côtés, aucun nom manquant**. Il fournit les empreintes des fichiers inspectés.
Cela établit la correspondance des noms, pas l'équivalence des types, bornes,
dates ou contraintes de nullabilité. La projection ne contient pas les arbres.

La recherche découvre **38 tables Room locales**. Elles constituent un
inventaire à classer : données utilisateur à restaurer, configuration,
référentiels rechargeables, résultats reproductibles et caches. Ne pas envoyer
indistinctement toute la base Room au serveur. Ne pas prétendre qu'une parcelle
synchronisée implique que les tables liées le sont aussi.

## Écarts prioritaires

1. **Restauration** : matrice objet → API → persistance → export/restauration.
   Inclure forêt/groupe, parcelle, arbres, placettes, relevés, diagnostics,
   campagnes, versions, calculs à conserver et médias selon le périmètre retenu.
2. **Identité territoriale** : réconcilier Place, référence cadastrale/ONF/DDT,
   précision GPS et version de limite ; ne pas confondre auteur et propriétaire
   foncier. L'identité de l'auteur est contrôlée par le serveur.
3. **Analyses** : le client local appelle `/api/v1/geosylva/analyses` ; route
   correspondante non trouvée dans le serveur inspecté. Réconcilier avec
   RFC-0041 et l'orchestration existante avant d'ajouter une API.
4. **Abonnement** : validation Google Play présente côté serveur ; liaison
   achat/compte et cycle des droits non qualifiés. Le Fondateur choisit le
   terrain hors ligne gratuit, synchronisation et analyses avec abonnement ;
   prix et modalités de récupération après expiration non fixés.
5. **Baseline exécutable** : configuration synthétique, démarrage des services,
   migrations et preuve des parcours restent à compléter.

## Prochaine tranche de réalisation

B02/B03 : inventorier d'abord les objets terrain qui doivent survivre à une
réinstallation et les rapprocher du Data Registry. Produire des exemples
synthétiques de deux utilisateurs, deux parcelles et deux campagnes avec
correction. Définir les contrats de restauration avant la migration, puis
implémenter une première tranche complète parcelle + campagne + observations.
Les statistiques multi-échelles suivent au jalon GSIE ; conserver toutes les
versions et sélectionner celles pertinentes pour chaque analyse.

## État des preuves

Le correctif déjà préparé du rejeu `operation_id` a été exercé localement le
2026-09-27 : 20 tests unitaires ciblés, Ruff et mypy réussis. Cette preuve ne
couvre pas PostgreSQL/RLS, appareil Android, CI distante ou historique complet.
La publication GitHub sépare ce correctif des documents de trajectoire.
Référence : [PR #61](https://github.com/NeooeN45/Quintessences/pull/61),
commit `d82f217`, non fusionné au moment de cet inventaire.
Les contrôles documentaires portent sur gouvernance, catalogue des prompts,
JSON et liens ; le registre général des sources de vérité signalait déjà une
revue expirée depuis le 2026-09-14. Ne pas antidater son renouvellement.
