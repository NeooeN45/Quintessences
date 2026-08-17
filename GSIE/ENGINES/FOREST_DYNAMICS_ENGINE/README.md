# Forest Dynamics Engine

Moteur de **dynamique des peuplements forestiers**.

## Périmètre

- Modélisation de la croissance et de l'évolution des peuplements
- Simulation de la dynamique forestière sur le long terme
- Intégration des modèles de production et de régénération
- Prise en compte des perturbations (tempêtes, sécheresses, ravageurs)

## Frontières

- Consomme les données de `KNOWLEDGE_ENGINE` et `CORRELATION_ENGINE`
- Fournit des projections à `SIMULATION_ENGINE` et
  `RECOMMENDATION_ENGINE`
- Ne produit pas de recommandation directe

> État d’implémentation : une API v1 est présente dans
> `GSIE/API/src/gsie_api/engines/forest_dynamics/`. Elle couvre le
> calcul dendrométrique décrit ci-dessous et ne simule pas encore la
> dynamique forestière à long terme.

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/forest_dynamics/router.py`.
Périmètre v1 restreint au calcul dendrométrique géométrique (surface
terrière) — pas de projection de croissance (`TrajectoireCroissance`),
faute de coefficients empiriques sourcés et vérifiés (ONF-FFN/CAPSIS
ou calibration IFN, ADR-009).

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/forest-dynamics/status` | aucune | — | Statut du moteur |
| GET | `/forest-dynamics/version` | aucune | — | Version et backend |
| POST | `/forest-dynamics/dendrometrics` | `engine:read` | `60/minute` | Calcule la surface terrière (G = π/4 × D² × N) d'un peuplement mesuré |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/forest_dynamics/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `PeuplementState` | État mesuré d'un peuplement | `essence_principale`, `age_moyen`, `densite_t_ha`, `diametre_moyen_cm`, `structure` (`StructurePeuplement`) |
| `DendrometricRequest` | Entrée de `/forest-dynamics/dendrometrics` | `peuplement_id`, `etat_initial` (`PeuplementState`), `station_observation_id` (référence traçabilité seule, RFC-0016 tranche 2/10) |
| `DendrometricResult` | Sortie | surface terrière calculée, source du calcul |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/forest_dynamics/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `ForestDynamicsEngineError` | Données de peuplement invalides pour le calcul géométrique | non exposée directement (router sans bloc `try/except`, remonte en 500 si non capturée en amont) |

### 4. Dépendances

- **Amont (chaîne principale)** : `KNOWLEDGE_ENGINE`, `CORRELATION_ENGINE`.
- **Aval** : `SIMULATION_ENGINE`, `RECOMMENDATION_ENGINE`.
- **Clients API externes** : aucun.
- **Persistance** : aucune — moteur sans état, fonction pure de son
  entrée (aucune session DB requise, `station_observation_id` transmis
  en aller-retour sans résolution).
