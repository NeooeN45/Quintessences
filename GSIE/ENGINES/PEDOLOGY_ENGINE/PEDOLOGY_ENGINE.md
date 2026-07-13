# Pedology Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Pedology Engine |
| **Catégorie** | Moteur domaine (pédologie) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-002, GSIE-CON-005 |
| **Ordre de développement** | 8 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Gérer les données de sol, classer les sols selon les référentiels
pédologiques officiels et fournir les caractéristiques stationnelles
pédologiques (texture, pH, profondeur, drainage, réserve utile en eau)
sans jamais inventer de seuil.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| Scientific Database | Base de données | Données pédologiques stockées |
| Station Repository | Base de données | Données de station (relevés, profils) |
| Base de Données des Sols | Source externe | BD sols nationale, équivalents régionaux |
| Référentiel Pédologique Français | Référentiel | RPF (INRAE) — classifications et seuils |
| WRB | Référentiel | World Reference Base (FAO) — classification internationale |
| Observations terrain | Données utilisateur | Profils de sol, mesures pH, textures relevées |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Caractéristiques pédologiques | Texture, pH, profondeur, drainage, RUM, classification |
| `CORRELATION_ENGINE` | Données pédologiques | Données pour croisement statistique |
| `REASONING_ENGINE` | Caractéristiques pédologiques | Données pour l'inférence d'adaptation |
| `FOREST_DYNAMICS_ENGINE` | Caractéristiques sol | RUM et contraintes pour les modèles de croissance |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Base externe | Scientific Database, Station Repository | Stockage des données pédologiques |
| Référentiel | Référentiel Pédologique Français (INRAE) | Classifications et seuils officiels |
| Référentiel | WRB (FAO) | Classification internationale |
| Aucun moteur | — | Le Pedology Engine ne dépend d'aucun autre moteur (source domaine) |

## 5. Contrat d'interface

### Entrée — `PedologyQuery`

```
PedologyQuery = {
  requete_id : UUID
  station_id : UUID (optionnel)
  emprise    : EmpriseGeographique (optionnel)
  parametres : liste de enum {
    ph, texture, profondeur, drainage, reserve_utile_eau,
    matiere_organique, cailloux, compaction, classification
  }
  referentiel_classification : enum { RPF, WRB } (optionnel)
}
```

### Sortie — `PedologyData`

```
PedologyData = {
  requete_id : UUID
  station_id : UUID (optionnel)
  profil     : ProfilSol (optionnel)
  caracteristiques : liste de SolCaracteristique
  classification : ClassificationSol (optionnel)
  source     : SourceReference
  date_donnees : ISO 8601
}

ProfilSol = {
  horizons   : liste de HorizonSol
  profondeur_totale_cm : décimal
}

HorizonSol = {
  profondeur_min_cm : décimal
  profondeur_max_cm : décimal
  texture     : enum { sableux, sable_limoneux, limoneux, limono_argileux, argileux }
  ph          : décimal
  matiere_organique_pct : décimal (optionnel)
  cailloux_pct : décimal (optionnel)
}

SolCaracteristique = {
  nom         : texte (ex. « reserve_utile_eau »)
  valeur      : décimal
  unite       : texte (ex. « mm », « pH », « % »)
  source      : SourceReference
  evidence_level : enum { A, B, C, D, E, F }
}

ClassificationSol = {
  referentiel : enum { RPF, WRB }
  type_sol    : texte (ex. « Alocrisol », « Luvisol »)
  source      : SourceReference
}
```

## 6. Garanties

- **Toute classification pédologique est sourcée** — aucune
  classification n'est produite sans référence au référentiel cité
  (principe fondateur).
- **Aucun seuil (pH, texture, drainage) n'est inventé** — tout provient
  du référentiel cité (`GSIE-CON-002`).
- Les conflits entre référentiels (RPF vs WRB) sont signalés, jamais
  résolus arbitrairement.
- Le moteur ne produit **pas de diagnostic** — il fournit des données et
  des classifications (séparation des responsabilités).
- Fonctionnement hors-ligne sur données en cache local (article T-8).

## 7. Cas d'usage

### Cas 1 — Classification d'un sol pour choix d'essence

Une station présente un pH 5,2, texture limono-sableuse, profondeur
80 cm, drainage modéré. Le Pedology Engine classe le sol comme
« Alocrisol » (RPF, source : INRAE 2008) / « Acrisol » (WRB, source :
FAO 2014). RUM calculée : 120 mm (source : RPF, formule de calcul de
réserve utile). Ces données sont transmises au Diagnostic Engine pour
évaluer l'adaptation du chêne sessile et du hêtre.

### Cas 2 — Détection d'une contrainte hydrique par RUM faible

Le Pedology Engine fournit une RUM de 60 mm pour une station à sol
superficiel (profondeur 30 cm) sur pente forte. Cette valeur, sourcée
(RPF, INRAE 2008), est transmise au Diagnostic Engine qui l'intègre
comme contrainte pédologique majeure pour le hêtre (RUM minimale
requise : 80 mm selon Rameau et al., 2018).

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
