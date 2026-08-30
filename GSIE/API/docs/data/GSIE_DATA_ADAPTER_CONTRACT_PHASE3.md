# CONTRAT DES ADAPTERS DATA REGISTRY — PHASE 3 [GSIE-DATA-ADAPTER-0001] [1.2.0]

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-DATA-ADAPTER-0001 |
| **Statut** | Draft |
| **Version** | 1.3.0 |
| **Date** | 2026-08-30 |
| **Auteur** | Codex — sous contrôle du Fondateur |
| **Décision de rattachement** | RFC-0038 v1.2.0 / DEC-000059 — Validated |

## 1. Résumé

La tranche Phase 3 stabilise l’interface commune des fournisseurs externes,
le registre lazy de plugins et les façades fournisseurs. Les façades IGN,
SoilGrids WCS, GBIF, TAXREF et Météo-France délèguent aux clients résilients
existants ; l’Indigénat Bellifa délègue au dataset local versionné. Aucun
appel réseau n’est effectué à leur construction. Leur activation reste une
décision explicite du bootstrap, après allowlist et configuration opérateur.

## 2. Contexte

Le Data Registry est maintenant disponible en lecture. Les clients fournisseurs
historiques restent réutilisables derrière leurs façades, tandis que Bellifa
est lu localement et SoilGrids passe par son client WCS dédié ; tous sont
désormais accessibles par des façades compatibles avec le contrat commun. Un
adapter doit devenir l’unique façade autorisée pour la découverte, la santé,
la requête, le fetch et la normalisation d’un fournisseur. Le resolver n’est
pas une responsabilité de l’adapter.

## 3. Contenu principal

### 3.1 Descripteur et capacités

Chaque plugin déclare une clé stable, un nom, une version, ses domaines GSIE,
ses capacités et, lorsqu’il ouvre un endpoint, un hôte explicitement autorisé.
Les capacités sont : `discovery`, `metadata`, `health`, `query`, `fetch` et
`normalize`. La capacité `health` est obligatoire. Une opération non déclarée
échoue avec le code stable `ADAPTER_CAPABILITY_UNSUPPORTED`.

### 3.2 Contrats d’échange

Les objets immuables du contrat bornent :

- le `trace_id`, le délai et la taille maximale de fetch via `AdapterContext` ;
- les emprises WGS84, curseurs et limites de découverte ;
- les candidats découverts (`external_id`, version, domaine, licence et
  distribution) ;
- les résultats de requête et leurs curseurs ;
- les paramètres fournisseur structurés de `AdapterFetchRequest.parameters`,
  séparés de l’URL distribuée et soumis à la validation propre de chaque
  adapter ;
- les flux de fetch, jamais chargés entièrement en mémoire par le contrat ;
- les rapports de santé avec statut, horodatage, latence et statut HTTP.

Les URLs de fournisseur refusent les schémas locaux, les identifiants, les
query/fragment et les hôtes hors allowlist. La résolution DNS et le blocage
des IP privées restent assurés au moment de l’appel par
`ResilientHttpClient`.

### 3.3 Registre de plugins

`AdapterPluginRegistry` enregistre une factory sans l’instancier. La création
est lazy, mise en cache par clé et vérifie que le descripteur renvoyé par la
factory est identique à celui enregistré. Les doublons, factories défaillantes
et descripteurs incohérents produisent des codes d’erreur stables. Le registre
permet une sélection descriptive par domaine ou capacité ; il ne choisit pas
une source et ne contourne aucune licence.

### 3.4 Façades livrées et limites de cette tranche

Les six façades suivantes sont disponibles et enregistrées par le bootstrap
standard :

- `GBIFAdapter` : rapprochement d’espèce et nom vernaculaire ;
- `IGNAdapter` : parcelle cadastrale et altitude RGE ALTI, avec deux hôtes
  IGN explicitement allowlistés ;
- `SoilGridsAdapter` : emprise, propriété, profondeur et quantile via WCS
  2.0.1 `maps.isric.org/mapserv`, avec allowlist des couvertures et flux
  GeoTIFF borné ; le registre de qualification garde FETCH fermé par défaut ;
- `TaxrefAdapter` : résolution TAXREF via le miroir GBIF explicitement déclaré
  dans SCI-001 ;
- `IndigenatBellifaAdapter` : lecture exacte du TSV Bellifa versionné, sans
  appel réseau ni statut complété par inférence ;
- `MeteoFranceAdapter` : niveau de danger de feux de forêt par département.

Chaque façade délègue à un client résilient ou au loader local versionné,
renvoie `unknown` en mode offline pour le contrôle de santé, convertit les
erreurs fournisseur en statuts `DatasetHealth` stables et n’invente aucune
valeur absente. Les ports
simulés des tests ne sont pas des connexions de production : ils vérifient la
validation et la normalisation sans réseau. Le bootstrap, les jobs périodiques,
le cache partagé, le resolver, les fetchs volumineux et la migration des
consommateurs restent hors périmètre. Aucun accès fournisseur ne doit être
ajouté directement à une application cliente.

### 3.5 Vérification

Les tests unitaires couvrent le descripteur, la sécurité URL, les bornes de
requête, la création lazy, le cache, les doublons, les factories incohérentes,
le refus explicite des capacités absentes et les six façades avec des clients
simulés. Ruff et mypy strict passent sur le contrat, les façades et leurs
tests ; aucun appel fournisseur n’est réalisé.

## 4. Sources et références

- `02_RFC/RFC-0038-data-registry-gsie.md` — séquencement Registry → adapters → resolver ;
- `03_DECISIONS/DEC-000059.md` — adoption du Data Registry ;
- `GSIE/API/src/gsie_api/data/adapters.py` — contrat et registre ;
- `GSIE/API/src/gsie_api/data/gbif_adapter.py` — façade GBIF ;
- `GSIE/API/src/gsie_api/data/ign_adapter.py` — façade IGN ;
- `GSIE/API/src/gsie_api/data/soilgrids_adapter.py` — façade SoilGrids WCS ;
- `GSIE/API/src/gsie_api/data/soilgrids_wcs_client.py` — client WCS et flux borné ;
- `GSIE/API/src/gsie_api/data/taxref_adapter.py` — façade TAXREF ;
- `GSIE/API/src/gsie_api/data/indigenat_adapter.py` — façade Indigénat Bellifa ;
- `GSIE/API/src/gsie_api/data/meteofrance_adapter.py` — façade Météo-France ;
- `GSIE/API/src/gsie_api/shared/http_client.py` — résilience HTTP et protection SSRF ;
- `GSIE/API/src/gsie_api/engines/gis/ign_client.py` — client IGN à encapsuler ;
- `GSIE/API/src/gsie_api/engines/botanical/gbif_client.py` — client GBIF à encapsuler ;
- `GSIE/API/src/gsie_api/engines/pedology/soilgrids_client.py` — client SoilGrids historique conservé hors du Data Registry ; il ne doit plus servir de cible d’adapter ni réintroduire le REST bêta ;
- `GSIE/API/tests/unit/test_data_registry_adapters.py` — tests de contrat.

## 5. Historique des modifications

| Version | Date | Modification |
|---|---|---|
| 1.0.0 | 2026-08-10 | Création du contrat commun et du registre lazy Phase 3. |
| 1.1.0 | 2026-08-10 | Ajout de la façade GBIF non activée par défaut et de ses tests simulés. |
| 1.2.0 | 2026-08-10 | Ajout des façades IGN, SoilGrids et Météo-France, de leurs ports simulés et de la vérification hors réseau. |
| 1.3.0 | 2026-08-30 | Branchement Registry de TAXREF et Bellifa ; remplacement de la façade SoilGrids REST par WCS 2.0.1 et ajout du fetch structuré borné. |
