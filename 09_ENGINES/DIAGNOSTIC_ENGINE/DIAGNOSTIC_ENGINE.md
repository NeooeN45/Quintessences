# Diagnostic Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Diagnostic Engine |
| **Catégorie** | Chaîne d'intelligence (analyse stationnelle) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-001, GSIE-CON-004 |
| **Ordre de développement** | 11 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Synthétiser les conclusions du Reasoning Engine et les données
multi-domaines en un diagnostic cohérent de l'état d'une station ou
d'un peuplement, identifiant les contraintes, atouts et risques — sans
prescrire d'action.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `REASONING_ENGINE` | Conclusions inférées | Déductions logiques avec chaîne d'inférence |
| `GIS_ENGINE` | Données géospatiales | Pente, exposition, altitude, hydrographie |
| `CLIMATE_ENGINE` | Données climatiques | Variables bioclimatiques, projections |
| `PEDOLOGY_ENGINE` | Données pédologiques | Caractéristiques et classifications du sol |
| `BOTANICAL_ENGINE` | Données botaniques | Végétation présente, autécologie |
| `FOREST_DYNAMICS_ENGINE` | Données de peuplement | Croissance, régénération, perturbations |
| `KNOWLEDGE_ENGINE` | Référentiels | Référentiels stationnels et sylvicoles |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `RECOMMENDATION_ENGINE` | Diagnostic | État de la station, contraintes, atouts, risques, confiance |
| `VALIDATION_ENGINE` | Diagnostic | Pour contrôle de cohérence avant présentation |
| `SIMULATION_ENGINE` | Diagnostic | État initial pour les projections de scénarios |
| Utilisateur (via interface) | Rapport de diagnostic | Présentation de l'analyse au forestier |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `REASONING_ENGINE` | Conclusions inférées (obligatoire) |
| Moteur | `GIS_ENGINE` | Données géospatiales stationnelles |
| Moteur | `CLIMATE_ENGINE` | Données bioclimatiques |
| Moteur | `PEDOLOGY_ENGINE` | Données pédologiques |
| Moteur | `BOTANICAL_ENGINE` | Données botaniques |
| Moteur | `FOREST_DYNAMICS_ENGINE` | Données de peuplement |
| Moteur | `KNOWLEDGE_ENGINE` | Référentiels stationnels |

## 5. Contrat d'interface

### Entrée — `DiagnosticRequest`

```
DiagnosticRequest = {
  requete_id  : UUID
  station_id  : UUID
  peuplement_id : UUID (optionnel)
  conclusions : liste de Conclusion (issues du Reasoning Engine)
  contexte    : StationContexte (voir REASONING_ENGINE.md §5)
  type_diagnostic : enum { stationnel, sylvicole, sanitaire, global }
}
```

### Sortie — `Diagnostic`

```
Diagnostic = {
  diagnostic_id   : UUID
  requete_origine : UUID
  station_id      : UUID
  type_diagnostic : enum { stationnel, sylvicole, sanitaire, global }
  etat_global     : enum { sain, vigueur_reduite, depérissement, critique }
  contraintes     : liste de ElementDiagnostic
  atouts          : liste de ElementDiagnostic
  risques         : liste de RisqueDiagnostic
  confiance       : décimal (0,0 à 1,0)
  incertitudes    : liste de texte
  conclusions_source : liste de UUID (Conclusion du Reasoning Engine)
  date_diagnostic : ISO 8601
}

ElementDiagnostic = {
  description    : texte (ex. « sol acide, pH 5,2 »)
  domaine        : enum { pedologique, climatique, topographique, botanique, sylvicole }
  evidence_level : enum { A, B, C, D, E, F }
  source         : SourceReference
}

RisqueDiagnostic = {
  description    : texte (ex. « risque de dépérissement lié au déficit hydrique »)
  probabilite    : enum { faible, modere, eleve, tres_eleve }
  horizon        : texte (ex. « 5 ans », « 20 ans »)
  domaine        : enum { climatique, sanitaire, sylvicole }
  evidence_level : enum { A, B, C, D, E, F }
  source         : SourceReference
}
```

## 6. Garanties

- **Un diagnostic est une analyse, pas une décision** — il décrit l'état
  et les risques, il ne prescrit pas l'action (principe fondateur).
- Toute contrainte, atout ou risque est sourcé avec son niveau de
  preuve (`GSIE-CON-002`, `GSIE-CON-005`).
- La confiance et les incertitudes du diagnostic sont explicitement
  documentées (`GSIE-CON-004`).
- Le forestier reste le décideur — le diagnostic est contournable
  (`GSIE-CON-001`).
- Les contradictions entre domaines (ex. sol favorable mais climat
  défavorable) sont mises en évidence, jamais masquées.
- Fonctionnement hors-ligne complet (article T-8).

## 7. Cas d'usage

### Cas 1 — Diagnostic de dépérissement d'une hêtraie de plaine

Une hêtraie à 250 m d'altitude présente 30 % de mortalité. Le
Diagnostic Engine synthétise : contrainte climatique (déficit hydrique
estival croissant, evidence B), contrainte stationnelle (sol superficiel,
RUM faible, evidence B), atout (pH favorable 6,2, evidence B). État
global : « dépérissement ». Risque : « aggravation du dépérissement à
horizon 10 ans, probabilité élevée ». Confiance : 0,75. Le diagnostic
est transmis au Recommendation Engine sans prescrire d'action.

### Cas 2 — Diagnostic de station pour choix d'essence après coupe rase

Après une coupe rase sur une station à pente 15 %, altitude 400 m, sol
limoneux profond, pH 5,8, précipitations 900 mm. Le Diagnostic Engine
produit : atouts (sol profond, RUM élevée, pH modérément acide),
contraintes (pente, exposition nord), risques (érosion post-coupe,
probabilité modérée). État global : « sain ». Le diagnostic est transmis
au Recommendation Engine qui proposera des essences adaptées.

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
