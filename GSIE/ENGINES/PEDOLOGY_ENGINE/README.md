# Pedology Engine

Moteur de **données pédologiques**.

## Périmètre

- Gérer les données de sol (texture, pH, profondeur, drainage,
  réserve utile en eau)
- Classer les sols selon les référentiels pédologiques officiels
  (Référentiel Pédologique Français, WRB)
- Fournir les caractéristiques stationnelles liées au sol
- Intégrer les données de la Base de Données des Sols et équivalents

## Principe fondamental

**Toute classification pédologique est sourcée.** Aucun seuil (pH,
texture, drainage) n'est inventé — tout provient du référentiel
cité (CON-002).

## Frontières

- Consomme les données de la `Scientific Database` et du
  `Station Repository`
- Fournit des données pédologiques à `DIAGNOSTIC_ENGINE` et
  `CORRELATION_ENGINE`
- Ne produit pas de diagnostic — fournit des données et des
  classifications

> Statut : *implémentation en cours (Phase 4)* — code livré, voir PEDOLOGY_ENGINE.md et PROJECT_MEMORY.md

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/pedology/router.py`. Périmètre
v1 restreint aux propriétés modélisées par SoilGrids (pH, argile,
sable, limon 0-5cm) — pas de `ProfilSol` ni de `ClassificationSol`
(RPF/WRB), en attente du Référentiel Pédologique Forestier (RFC-0013).

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/pedology/status` | aucune | — | Statut du moteur (`router.py:25`) |
| GET | `/pedology/version` | aucune | — | Version et backend (`router.py:36`) |
| POST | `/pedology/query` | `engine:read` | `30/minute` | Propriétés de sol réelles d'un point (SoilGrids, ISRIC) (`router.py:49`) |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/pedology/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `PedologyQuery` | Entrée de `/pedology/query` | `latitude`, `longitude` (WGS 84), `profondeur` (tranche SoilGrids) |
| `SolCaracteristique` | Une caractéristique de sol | `nom` (ph/argile_pct/sable_pct...), `valeur`, `unite` (bornée par unité), `evidence_level` (B par défaut — plafond SoilGrids, source peer-reviewed unique) |
| `PedologyData` | Sortie de `/pedology/query` | liste de `SolCaracteristique`, `source` |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/pedology/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `PedologyEngineError` | API SoilGrids indisponible ou erreur de décodage | 502 |

### 4. Dépendances

- **Amont** : `Scientific Database`, `Station Repository`.
- **Aval (chaîne principale)** : `DIAGNOSTIC_ENGINE`, `CORRELATION_ENGINE`.
- **Clients API externes** : SoilGrids (ISRIC, `soilgrids_client.py`,
  aucune clé requise ; Poggio et al., 2021, SOIL journal).
- **Persistance** : aucune (moteur sans état, requêtes en direct).
