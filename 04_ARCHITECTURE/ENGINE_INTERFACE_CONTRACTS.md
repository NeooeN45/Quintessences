# Contrats d'interface des 14 moteurs — Matrice d'interactions

| Champ | Valeur |
|---|---|
| **Livrable** | 206 — Contrats d'interface des moteurs |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date de révision** | 2026-07-12 |
| **Lois fondatrices** | GSIE-CON-004, GSIE-CON-005, GSIE-CON-007 |
| **Constitutions liées** | Technique (T-2, T-6) |
| **RFC de référence** | RFC-0003 (GSIE-Net) |
| **Décision d'ouverture** | DEC-000004 |

---

## Matrice d'interactions

Lecture : la ligne **émet** vers la colonne **récepteur**. Une case vide
signifie aucune interaction directe.

| Émetteur \ Récepteur | Evid. | Know. | Correl. | Reas. | Diag. | Recom. | Valid. | GIS | Clim. | Pedol. | Botan. | ForestDyn. | Learn. | Simul. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Evidence** | — | ✅ | | | | | | | | | | | ✅ | |
| **Knowledge** | | — | ✅ | ✅ | | | | | | | | | | |
| **Correlation** | | | — | ✅ | | | | | | | | | ✅ | |
| **Reasoning** | | ✅ | | — | ✅ | | | | | | | | | |
| **Diagnostic** | | | | | — | ✅ | | | | | | | | ✅ |
| **Recommendation** | | | | | | — | ✅ | | | | | | | ✅ |
| **Validation** | | | | | | | — | | | | | | ✅ | |
| **GIS** | | | | | ✅ | | | — | | | | | | ✅ |
| **Climate** | | | | | ✅ | | | | — | | | | | ✅ |
| **Pedology** | | | | | ✅ | | | | | — | | | | ✅ |
| **Botanical** | | | | | ✅ | | | | | | — | | | ✅ |
| **ForestDyn** | | | | | ✅ | | | | | | | — | | ✅ |
| **Learning** | ✅ | ✅ | | | | | | | | | | | — | |
| **Simulation** | | | | | | | ✅ | | | | | | ✅ | — |

Légende : ✅ = flux de données direct entre les deux moteurs.

---

## Détail des flux par moteur

### Evidence Engine (filtre amont)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Connaissance qualifiée | Knowledge Engine | `QualifiedKnowledge` | Connaissance + niveau de preuve + source + version |
| Signaux de réévaluation | Learning Engine | `ReassessmentSignal` | Connaissances dont le niveau de preuve peut évoluer |

### Knowledge Engine (centralisation)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Base de connaissances | Correlation Engine | `KnowledgeQuery` | Réponses aux requêtes de corrélation |
| Base de connaissances | Reasoning Engine | `KnowledgeQuery` | Réponses aux requêtes de raisonnement |

### Correlation Engine (corrélations)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Corrélations détectées | Reasoning Engine | `CorrelationSet` | Ensemble de corrélations multiparamètres |
| Corrélations | Learning Engine | `CorrelationFeedback` | Corrélations à valider/ajuster par apprentissage |

### Reasoning Engine (raisonnement)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Requête de connaissance | Knowledge Engine | `KnowledgeQuery` | Demande de connaissances contextuelles |
| Conclusions raisonnées | Diagnostic Engine | `ReasoningOutput` | Inférences prêtes pour le diagnostic |

### Diagnostic Engine (diagnostic)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Diagnostic | Recommendation Engine | `DiagnosticReport` | État diagnostiqué + problèmes identifiés |
| État courant | Simulation Engine | `SystemState` | État du système pour simulation |

### Recommendation Engine (recommandations)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Recommandations | Validation Engine | `RecommendationSet` | Recommandations contournables + alternatives |
| Scénarios d'intervention | Simulation Engine | `InterventionSpec` | Actions à simuler |

### Validation Engine (validation)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Sorties validées | Utilisateur | `ValidatedOutput` | Recommandations validées + sources + niveau de confiance |
| Écarts détectés | Learning Engine | `ValidationGap` | Écarts entre attendu et observé |

### Moteurs domaine (GIS, Climate, Pedology, Botanical, Forest Dynamics)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Données domaine | Diagnostic Engine | `DomainData` | Données spatiales, climatiques, pédologiques, floristiques, dynamique |
| Données domaine | Simulation Engine | `DomainData` | Conditions aux limites pour les scénarios |

### Learning Engine (apprentissage)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Réévaluation de preuve | Evidence Engine | `ReassessmentRequest` | Mise à jour du niveau de preuve d'une connaissance |
| Mises à jour de connaissances | Knowledge Engine | `KnowledgeUpdate` | Connaissances ajustées par apprentissage |

### Simulation Engine (simulation)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Résultats de simulation | Validation Engine | `SimulationResult` | Projections temporelles + confiance + sources |
| Comparatif de scénarios | Recommendation Engine | `ScenarioComparison` | Scénarios alternatifs comparés |
| Écarts simulation/réalité | Learning Engine | `SimulationGap` | Écarts pour calibration des modèles |

---

## Principes d'interface

1. **Aucun moteur ne connaît les détails internes d'un autre** (GSIE-CON-007).
   Chaque échange passe par un contrat de données explicite.

2. **Tous les flux sont tracés** (GSIE-CON-005). Chaque message porte
   un identifiant de source et un horodatage.

3. **Toutes les sorties sont explicables** (GSIE-CON-004). Chaque
   recommandation ou diagnostic cite les moteurs et sources qui l'ont
   produite.

4. **Communication asynchrone par défaut**. Les moteurs domaine
   répondent en temps différé. La chaîne d'intelligence (Evidence →
   Validation) peut être synchrone pour les flux temps réel (Ignis).

5. **Offline-first**. Les moteurs communiquent par messages persistés.
   En cas de coupure réseau, les messages sont mis en file et traités
   à la reconnexion.

---

## Références

- `09_ENGINES/*/` — documentation détaillée de chaque moteur
- `04_ARCHITECTURE/ENGINE_COMMUNICATION_PROTOCOL.md` — protocole d'échange
- `04_ARCHITECTURE/GSIE_DATA_FLOW.md` — flux de données global
- `04_ARCHITECTURE/ENGINE_DEVELOPMENT_ORDER.md` — ordre de développement

---

## Types communs

Les types suivants sont partagés par plusieurs moteurs. Ils sont définis
ici une seule fois et référencés par les contrats de chaque moteur.

### Types primitifs

```
UUID            : identifiant unique (UUID v7 — ordonné temporellement)
ISO 8601       : horodatage UTC (précision milliseconde)
texte          : chaîne de caractères UTF-8
entier         : nombre entier
decimal        : nombre décimal (float64)
booleen        : vrai | faux
map            : dictionnaire clé-valeur
liste          : liste ordonnée
```

### `SourceReference`

Référence de source — présent dans tout message portant une connaissance
(GSIE-CON-005, S-1).

```
SourceReference = {
  type_source       : enum { peer_reviewed, referentiel_officiel, expert_identifie, observation_terrain }
  auteur            : texte (ou organisme)
  date_publication  : ISO 8601 (optionnel)
  reference         : texte (DOI, URL, citation, code référentiel)
  version_source    : texte (optionnel)
}
```

### `EvidenceLevel`

Niveau de preuve scientifique (S-2).

```
EvidenceLevel = enum {
  A,  // méta-analyse / consensus fort
  B,  // établi (peer-reviewed, reproductible)
  C,  // probable (peer-reviewed, domaine partiel)
  D,  // expert identifié, non publié
  E,  // observation terrain non publiée
  F   // incertain / contesté
}
```

### `ConfidenceLevel`

Niveau de confiance d'une conclusion, recommandation ou projection.

```
ConfidenceLevel = decimal (0.0 à 1.0)
```

### `EmpriseGeographique`

Zone géographique d'étude ou d'application.

```
EmpriseGeographique = {
  type        : enum { point, polygone, parcelle }
  geometrie   : structure GeoJSON (optionnel)
  parcelle_id : texte (optionnel)
}
```

### `PeriodeTemporelle`

Période temporelle pour les requêtes climatiques ou de corrélation.

```
PeriodeTemporelle = {
  debut : ISO 8601 (année)
  fin   : ISO 8601 (année)
}
```

### `IntervalleConfiance`

Intervalle de confiance pour les projections et incertitudes.

```
IntervalleConfiance = {
  minimum : decimal
  maximum : decimal
  niveau  : enum { 80pct, 90pct, 95pct }
}
```

### `IntervalleValeur`

Intervalle de valeurs pour les optima autécologiques.

```
IntervalleValeur = {
  minimum : decimal
  maximum : decimal
  unite   : texte
}
```

---

## Schémas de données formels par moteur

Les schémas ci-dessous consolident les contrats d'interface définis dans
chaque document moteur (`09_ENGINES/*/ENGINE.md` §5). Ils sont la
**source de vérité unique** pour l'implémentation (Phase 4).

### Evidence Engine

#### Entrée — `RawKnowledgeSubmission`

```
RawKnowledgeSubmission = {
  soumission_id    : UUID
  type_contenu     : enum { publication, referentiel, expert, observation }
  contenu          : structure libre (texte, tableau, mesure, image)
  source_candidate : SourceReference
  date_soumission  : ISO 8601
  soumetteur       : texte (utilisateur ou pipeline automatique)
}
```

#### Sortie — `QualifiedKnowledge`

```
QualifiedKnowledge = {
  connaissance_id    : UUID
  contenu_normalise  : structure (dépend du type de connaissance)
  evidence_level     : EvidenceLevel
  source             : SourceReference
  version            : entier (commence à 1)
  date_qualification : ISO 8601
  conflits           : liste de ConflitBibliographique (optionnel)
  statut             : enum { accepte, quarantine, refuse }
}

ConflitBibliographique = {
  source_a    : SourceReference
  source_b    : SourceReference
  description : texte
}
```

#### Sortie — `ReassessmentSignal` (vers Learning Engine)

```
ReassessmentSignal = {
  signal_id          : UUID
  connaissance_id    : UUID
  raison             : texte (ex. « nouvelle publication contradictoire »)
  evidence_actuel    : EvidenceLevel
  evidence_propose   : EvidenceLevel
  source_nouvelle    : SourceReference (optionnel)
  date_signal        : ISO 8601
}
```

### Knowledge Engine

#### Entrée — `QualifiedKnowledge` (depuis Evidence Engine)

Voir §Evidence Engine. Le Knowledge Engine reçoit les connaissances au
statut `accepte`.

#### Requête — `KnowledgeQuery`

```
KnowledgeQuery = {
  requete_id   : UUID
  type         : enum { par_concept, par_relation, par_domaine, par_essence, par_station }
  filtres      : map (clé-valeur selon le type)
  evidence_min : EvidenceLevel (optionnel — filtre par niveau minimum)
}
```

#### Sortie — `KnowledgeQueryResult`

```
KnowledgeQueryResult = {
  requete_id    : UUID
  connaissances : liste de KnowledgeObject
  total         : entier
  version_graph : texte (version du graphe au moment de la requête)
}

KnowledgeObject = {
  connaissance_id   : UUID
  type              : enum { concept, relation, regle, seuil, modele, classification }
  contenu           : structure typée selon `type`
  evidence_level    : EvidenceLevel
  source            : SourceReference
  version           : entier
  date_integration  : ISO 8601
  historique        : liste de VersionEntry
  domaines_validite : liste de DomaineValidite (optionnel)
}

VersionEntry = {
  version       : entier
  date          : ISO 8601
  justification : texte
  rfc_reference : texte (optionnel)
}

DomaineValidite = {
  parametre : texte (ex. « pH », « altitude », « climat »)
  minimum   : decimal (optionnel)
  maximum   : decimal (optionnel)
  unite     : texte (optionnel)
}
```

### Correlation Engine

#### Entrée — `CorrelationRequest`

```
CorrelationRequest = {
  requete_id            : UUID
  domaine               : enum { stationnel, climatique, sylvicole, sanitaire, global }
  parametres            : liste de ParametreCorrelation
  zone_etude            : EmpriseGeographique (optionnel)
  periode               : PeriodeTemporelle (optionnel)
  seuil_significativite : decimal (optionnel, défaut 0.05)
}

ParametreCorrelation = {
  source_moteur : enum { GIS, CLIMATE, PEDOLOGY, BOTANICAL, FOREST_DYNAMICS, TERRAIN }
  variable      : texte (ex. « pH », « precipitations_estivales », « altitude »)
  unite         : texte
}
```

#### Sortie — `CorrelationMatrix` (= `CorrelationSet`)

```
CorrelationMatrix = {
  matrice_id         : UUID
  requete_origine    : UUID
  correlations       : liste de Correlation
  date_calcul        : ISO 8601
  sources_utilisees  : liste de SourceReference
}

Correlation = {
  variable_a         : ParametreCorrelation
  variable_b         : ParametreCorrelation
  coefficient        : decimal (-1.0 à 1.0)
  p_valeur           : decimal
  type_relation      : enum { positive, negative, non_significative }
  n_observations     : entier
  domaine_validite   : texte (ex. « France méditerranéenne, sols acides »)
  source             : SourceReference
  evidence_level     : EvidenceLevel
  confidence         : ConfidenceLevel
}
```

#### Sortie — `CorrelationFeedback` (vers Learning Engine)

```
CorrelationFeedback = {
  feedback_id      : UUID
  matrice_origine  : UUID
  correlations     : liste de Correlation
  date_feedback    : ISO 8601
}
```

### Reasoning Engine

#### Entrée — `ReasoningRequest`

```
ReasoningRequest = {
  requete_id     : UUID
  station_id     : UUID (optionnel)
  contexte       : StationContexte
  question       : texte (ex. « quelles essences sont adaptées ? »)
  profondeur_max : entier (limite de profondeur de la chaîne d'inférence)
}

StationContexte = {
  geographie   : GeoData (pente, exposition, altitude, coordonnees)
  climat       : ClimateData (temperatures, precipitations, deficit)
  pedologie    : PedologyData (pH, texture, profondeur, drainage, RUM)
  botanique    : BotanicalData (essences presentes, vegetation)
  peuplement   : DynamicsProjection (age, densite, croissance)
  correlations : liste de Correlation (issues du Correlation Engine)
}
```

#### Sortie — `InferenceResult` (= `ReasoningOutput`)

```
InferenceResult = {
  resultat_id     : UUID
  requete_origine : UUID
  conclusions     : liste de Conclusion
  contradictions  : liste de ContradictionDetectee (optionnel)
  date_inference  : ISO 8601
}

Conclusion = {
  conclusion_id           : UUID
  enonce                  : texte (ex. « le hêtre est adapté à cette station »)
  niveau_confiance        : ConfidenceLevel
  chaine_inference        : liste de EtapeInference
  sources_utilisees       : liste de SourceReference
  connaissances_utilisees : liste de UUID (KnowledgeObject)
  moteurs_solicites       : liste de texte
}

EtapeInference = {
  ordre             : entier (1, 2, 3…)
  regle_appliquee   : texte (description de la règle)
  source_regle      : SourceReference
  premisses         : liste de texte (faits ou conclusions antérieurs)
  conclusion_locale : texte
}

ContradictionDetectee = {
  conclusion_a : UUID
  conclusion_b : UUID
  description  : texte
}
```

### Diagnostic Engine

#### Entrée — `DiagnosticRequest`

```
DiagnosticRequest = {
  requete_id      : UUID
  station_id      : UUID
  peuplement_id   : UUID (optionnel)
  conclusions     : liste de Conclusion (issues du Reasoning Engine)
  contexte        : StationContexte
  type_diagnostic : enum { stationnel, sylvicole, sanitaire, global }
}
```

#### Sortie — `Diagnostic` (= `DiagnosticReport`)

```
Diagnostic = {
  diagnostic_id     : UUID
  requete_origine   : UUID
  station_id        : UUID
  type_diagnostic   : enum { stationnel, sylvicole, sanitaire, global }
  etat_global       : enum { sain, vigueur_reduite, deperissement, critique }
  contraintes       : liste de ElementDiagnostic
  atouts            : liste de ElementDiagnostic
  risques           : liste de RisqueDiagnostic
  confiance         : ConfidenceLevel
  incertitudes      : liste de texte
  conclusions_source: liste de UUID (Conclusion du Reasoning Engine)
  date_diagnostic   : ISO 8601
}

ElementDiagnostic = {
  description    : texte (ex. « sol acide, pH 5,2 »)
  domaine        : enum { pedologique, climatique, topographique, botanique, sylvicole }
  evidence_level : EvidenceLevel
  source         : SourceReference
}

RisqueDiagnostic = {
  description    : texte (ex. « risque de dépérissement lié au déficit hydrique »)
  probabilite    : enum { faible, modere, eleve, tres_eleve }
  horizon        : texte (ex. « 5 ans », « 20 ans »)
  domaine        : enum { climatique, sanitaire, sylvicole }
  evidence_level : EvidenceLevel
  source         : SourceReference
}
```

### Recommendation Engine

#### Entrée — `RecommendationRequest`

```
RecommendationRequest = {
  requete_id            : UUID
  diagnostic_id         : UUID
  objectif_forestier    : enum { production, protection, biodiversite, mixte, reboisement }
  contraintes_forestier : liste de texte (préférences du forestier, optionnel)
  alternatives_demandees: booleen (défaut : vrai)
}
```

#### Sortie — `RecommendationSet`

```
RecommendationSet = {
  ensemble_id        : UUID
  requete_origine    : UUID
  diagnostic_source  : UUID
  recommandations    : liste de Recommendation
  date_generation    : ISO 8601
}

Recommendation = {
  recommandation_id    : UUID
  type_action          : enum { plantation, eclaircie, coupe_rase, regeneration, protection, intervention_sanitaire, attente_surveillance }
  description          : texte (ex. « planter du chêne sessile, densité 1100 t/ha »)
  essence_concernee    : texte (optionnel)
  parametres           : map (clé-valeur : densité, période, surface, etc.)
  justification        : JustificationRecommandation
  alternatives         : liste de Recommendation (optionnel)
  niveau_confiance     : ConfidenceLevel
  scenario_projection  : UUID (référence vers Simulation Engine, optionnel)
  contournable         : booleen (toujours vrai — GSIE-CON-001)
}

JustificationRecommandation = {
  diagnostic_ref            : UUID
  connaissances_utilisees   : liste de UUID (KnowledgeObject)
  regles_appliquees         : liste de texte
  sources                   : liste de SourceReference
  facteurs_limitants        : liste de texte
  moteurs_solicites         : liste de texte
}
```

#### Retour forestier — `ForestierDecision`

```
ForestierDecision = {
  recommandation_id        : UUID
  decision                 : enum { accepte, refuse, modifie, demande_alternative }
  justification_forestier  : texte (optionnel)
  modifications            : map (optionnel — paramètres modifiés)
  date_decision            : ISO 8601
}
```

### Validation Engine

#### Entrée — `ValidationRequest`

```
ValidationRequest = {
  requete_id              : UUID
  type_sortie             : enum { diagnostic, recommandation, ensemble_complet }
  contenu                 : Diagnostic ou RecommendationSet
  chaines_inference       : liste de Conclusion (optionnel)
  connaissances_utilisees : liste de UUID (KnowledgeObject)
}
```

#### Sortie — `ValidationResult` (= `ValidatedOutput`)

```
ValidationResult = {
  validation_id   : UUID
  requete_origine : UUID
  statut          : enum { valide, bloque, partiellement_valide }
  controles       : liste de ControleResultat
  causes_blocage  : liste de CauseBlocage (si statut = bloque)
  date_validation : ISO 8601
}

ControleResultat = {
  nom_controle : texte
  resultat     : enum { conforme, non_conforme, non_applicable }
  details      : texte
}

CauseBlocage = {
  type_cause        : enum {
    sans_niveau_preuve,
    sans_source,
    sans_chaine_inference,
    hors_domaine_validite,
    connaissance_obsolete,
    contradiction_non_signalee,
    recommandation_non_contournable,
    explicabilite_insuffisante
  }
  element_concerne : UUID
  description      : texte
}
```

#### Sortie — `ValidationGap` (vers Learning Engine)

```
ValidationGap = {
  gap_id          : UUID
  validation_id   : UUID
  type_ecart      : enum { connaissance_obsolete, hors_domaine, contradiction, explicabilite_insuffisante }
  element_concerne: UUID
  description     : texte
  date_detection  : ISO 8601
}
```

### GIS Engine

#### Entrée — `GeoQuery`

```
GeoQuery = {
  requete_id        : UUID
  type              : enum { station, parcelle, zone, itineraire }
  emprise           : EmpriseGeographique
  couches_demandees : liste de enum { mnt, pente, exposition, altitude, hydrographie, cadastre, orthophoto, sol }
  resolution        : texte (optionnel — ex. « 5m », « 25m »)
}
```

#### Sortie — `GeoData` (= `DomainData`)

```
GeoData = {
  requete_id   : UUID
  station_id   : UUID (optionnel)
  couches      : liste de GeoLayer
  source       : SourceReference
  date_donnees : ISO 8601
  mode         : enum { en_ligne, hors_ligne, degrade }
}

GeoLayer = {
  nom        : enum { mnt, pente, exposition, altitude, hydrographie, cadastre, orthophoto }
  type       : enum { raster, vecteur, mesure }
  valeurs    : structure selon type (grille, géométries, valeur ponctuelle)
  unite      : texte (ex. « degrés », « mètres », « % »)
  resolution : texte (optionnel)
  source     : SourceReference
  date_maj   : ISO 8601
}

StationCharacteristics = {
  station_id                  : UUID
  altitude_m                  : decimal
  pente_degres                : decimal
  exposition_degres           : decimal (0–360)
  hydrographie_proximite_m    : decimal (optionnel)
  coordonnees                 : { latitude : decimal, longitude : decimal } (WGS 84)
  source                      : SourceReference
}
```

### Climate Engine

#### Entrée — `ClimateQuery`

```
ClimateQuery = {
  requete_id  : UUID
  emprise     : EmpriseGeographique
  periode     : PeriodeTemporelle
  variables   : liste de enum {
    temperature_moyenne, temperature_min, temperature_max,
    precipitations_totales, precipitations_estivales,
    deficit_hydrique, duree_vegetation, gel_jours,
    vent_moyen, vent_max, humidite
  }
  type_donnees: enum { historique, actuelle, projection }
  scenario    : enum { RCP26, RCP45, RCP85, SSP126, SSP245, SSP585 } (si projection)
}
```

#### Sortie — `ClimateData` (= `DomainData`)

```
ClimateData = {
  requete_id   : UUID
  variables    : liste de ClimateVariable
  source       : SourceReference
  date_donnees : ISO 8601
  mode         : enum { en_ligne, hors_ligne, degrade }
}

ClimateVariable = {
  nom         : texte (ex. « deficit_hydrique_estival »)
  valeur      : decimal
  unite       : texte (ex. « mm », « °C », « jours »)
  periode     : PeriodeTemporelle
  scenario    : enum { RCP26, RCP45, RCP85, SSP126, SSP245, SSP585, historique } (optionnel)
  incertitude : IntervalleConfiance (optionnel — obligatoire pour projections)
  source      : SourceReference
}
```

### Pedology Engine

#### Entrée — `PedologyQuery`

```
PedologyQuery = {
  requete_id                  : UUID
  station_id                  : UUID (optionnel)
  emprise                     : EmpriseGeographique (optionnel)
  parametres                  : liste de enum {
    ph, texture, profondeur, drainage, reserve_utile_eau,
    matiere_organique, cailloux, compaction, classification
  }
  referentiel_classification  : enum { RPF, WRB } (optionnel)
}
```

#### Sortie — `PedologyData` (= `DomainData`)

```
PedologyData = {
  requete_id        : UUID
  station_id        : UUID (optionnel)
  profil            : ProfilSol (optionnel)
  caracteristiques  : liste de SolCaracteristique
  classification    : ClassificationSol (optionnel)
  source            : SourceReference
  date_donnees      : ISO 8601
}

ProfilSol = {
  horizons              : liste de HorizonSol
  profondeur_totale_cm  : decimal
}

HorizonSol = {
  profondeur_min_cm      : decimal
  profondeur_max_cm      : decimal
  texture                : enum { sableux, sable_limoneux, limoneux, limono_argileux, argileux }
  ph                     : decimal
  matiere_organique_pct  : decimal (optionnel)
  cailloux_pct           : decimal (optionnel)
}

SolCaracteristique = {
  nom           : texte (ex. « reserve_utile_eau »)
  valeur        : decimal
  unite         : texte (ex. « mm », « pH », « % »)
  source        : SourceReference
  evidence_level: EvidenceLevel
}

ClassificationSol = {
  referentiel : enum { RPF, WRB }
  type_sol    : texte (ex. « Alocrisol », « Luvisol »)
  source      : SourceReference
}
```

### Botanical Engine

#### Entrée — `BotanicalQuery`

```
BotanicalQuery = {
  requete_id  : UUID
  type        : enum { par_essence, par_taxon, par_station, identification }
  essence     : texte (nom scientifique ou vernaculaire, optionnel)
  station_id  : UUID (optionnel)
  parametres  : liste de enum {
    taxonomie, nomenclature, autecologie, synonymes, exigences, optimum, amplitude
  }
}
```

#### Sortie — `BotanicalData` (= `DomainData`)

```
BotanicalData = {
  requete_id   : UUID
  especes      : liste de EspeceData
  source       : SourceReference
  date_donnees : ISO 8601
}

EspeceData = {
  taxon_id            : UUID
  nom_scientifique    : texte
  nom_vernaculaire    : texte
  synonymes           : liste de texte
  famille             : texte
  autecologie         : Autecologie (optionnel)
  taxonomie_version   : texte (version du référentiel)
  source              : SourceReference
}

Autecologie = {
  optimum_ph            : IntervalleValeur (optionnel)
  optimum_altitude      : IntervalleValeur (optionnel)
  optimum_precipitations: IntervalleValeur (optionnel)
  tolerance_gel         : decimal (°C, optionnel)
  tolerance_ombre       : enum { tres_forte, forte, moderee, faible, tres_faible }
  exigence_eau          : enum { hygrophyte, mesophyte, xerophyte }
  exigence_sol          : texte (optionnel)
  source                : SourceReference
  evidence_level        : EvidenceLevel
}
```

### Forest Dynamics Engine

#### Entrée — `DynamicsRequest`

```
DynamicsRequest = {
  requete_id      : UUID
  peuplement_id   : UUID
  etat_initial    : PeuplementState
  horizon_annees  : entier (ex. 10, 30, 50)
  scenario_climat : texte (optionnel — ex. « RCP85 »)
  perturbations   : liste de Perturbation (optionnel)
}

PeuplementState = {
  essence_principale       : texte
  age_moyen                : decimal (années)
  densite_t_ha             : decimal
  diametre_moyen_cm        : decimal
  hauteur_moyenne_m        : decimal
  surface_terriere_m2_ha   : decimal
  structure                : enum { reguliere, irreguliere, melange, taillis }
  source_inventaire        : SourceReference
}

Perturbation = {
  type      : enum { tempete, secheresse, ravageur, incendie, coupe }
  annee     : entier
  intensite : enum { faible, modere, fort, tres_fort }
}
```

#### Sortie — `DynamicsProjection` (= `DomainData`)

```
DynamicsProjection = {
  projection_id            : UUID
  requete_origine          : UUID
  trajectoires             : liste de TrajectoireCroissance
  perturbations_modelisees : liste de Perturbation (optionnel)
  source_modele            : SourceReference
  date_projection          : ISO 8601
}

TrajectoireCroissance = {
  essence        : texte
  points         : liste de PointTrajectoire
  modele         : texte (ex. « ONF-FFN », « INRAE-MARGINAL »)
  source         : SourceReference
  evidence_level : EvidenceLevel
}

PointTrajectoire = {
  annee                      : entier
  diametre_cm                : decimal
  hauteur_m                  : decimal
  volume_m3_ha               : decimal
  accroissement_annuel_m3_ha : decimal
  incertitude                : IntervalleConfiance (optionnel)
}
```

### Learning Engine

#### Entrée — `LearningSignal`

```
LearningSignal = {
  signal_id   : UUID
  type        : enum { retour_forestier, sortie_bloquee, pattern_emergent, observation_terrain }
  contenu     : structure selon type
  date_signal : ISO 8601
}

RetourForestier = {
  recommandation_id        : UUID
  decision                 : enum { accepte, refuse, modifie, demande_alternative }
  justification_forestier  : texte (optionnel)
  contexte_station         : UUID
}

PatternEmergent = {
  description  : texte
  correlations : liste de Correlation
  confiance    : ConfidenceLevel
}
```

#### Sortie — `LearningOutput`

```
LearningOutput = {
  output_id                 : UUID
  type                      : enum { proposition_revision, calibration_modele, pattern_confirme }
  description               : texte
  justification             : liste de texte (chaîne d'apprentissage)
  donnees_source            : liste de SourceReference
  confidence                : ConfidenceLevel
  connaissances_concernees  : liste de UUID (KnowledgeObject)
  date_output               : ISO 8601
  statut                    : enum { propose, en_validation, valide, rejete }
}
```

#### Sortie — `ReassessmentRequest` (vers Evidence Engine)

```
ReassessmentRequest = {
  request_id         : UUID
  connaissance_id    : UUID
  evidence_actuel    : EvidenceLevel
  evidence_propose   : EvidenceLevel
  justification      : texte
  sources_nouvelles  : liste de SourceReference
  date_request       : ISO 8601
}
```

#### Sortie — `KnowledgeUpdate` (vers Knowledge Engine)

```
KnowledgeUpdate = {
  update_id          : UUID
  connaissance_id    : UUID
  type_update        : enum { revision_niveau, calibration_parametre, nouveau_domaine_validite }
  ancienne_version   : entier
  nouvelle_valeur    : structure (dépend du type)
  justification      : texte
  sources            : liste de SourceReference
  date_update        : ISO 8601
  statut             : enum { propose, en_validation, valide, rejete }
}
```

### Simulation Engine

#### Entrée — `ScenarioSimulation`

```
ScenarioSimulation = {
  scenario_id       : UUID
  source_diagnostic : UUID (DiagnosticRef)
  intervention      : InterventionSpec
  horizon           : texte (Duration — ex. « 5 ans », « 10 ans », « 30 ans »)
  climate_scenario  : texte (ClimateScenarioRef — ex. « RCP45 », « RCP85 », « courant »)
  parameters        : map (paramètres de simulation ajustables)
}

InterventionSpec = {
  type        : enum { plantation, eclaircie, coupe_rase, regeneration, protection, lutte_feu }
  parametres  : map (clé-valeur : densité, période, surface, intensité, etc.)
}
```

#### Sortie — `SimulationResult`

```
SimulationResult = {
  scenario_id   : UUID
  projections   : liste de TimedProjection
  confidence    : ConfidenceLevel
  sources       : liste de SourceReference
  assumptions   : liste de texte (hypothèses simplificatrices)
  alternatives  : liste de SimulationResult (scénarios alternatifs comparés)
}

TimedProjection = {
  timestamp     : ISO 8601
  state         : texte (SystemState — état du système à cet instant)
  key_indicators: map (biomasse, risque feu, biodiversité, etc.)
}
```

#### Sortie — `ScenarioComparison` (vers Recommendation Engine)

```
ScenarioComparison = {
  comparison_id  : UUID
  scenarios      : liste de SimulationResult
  critere_tri    : texte (ex. « biomasse_maximale », « risque_minimal »)
  date_comparison: ISO 8601
}
```

#### Sortie — `SimulationGap` (vers Learning Engine)

```
SimulationGap = {
  gap_id          : UUID
  scenario_id     : UUID
  projection_id   : UUID
  ecart_type      : enum { surestimation, sous_estimation, direction_incorrecte }
  valeur_projete  : decimal
  valeur_observe  : decimal
  date_detection  : ISO 8601
}
```

---

## Garanties de service

Chaque interaction entre moteurs respecte des garanties explicites. Le
mode (synchrone/asynchrone/event-driven) est défini par le contrat du
moteur destinataire (voir `ENGINE_COMMUNICATION_PROTOCOL.md` §2).

### Garanties par type d'interaction

| Interaction | Mode | Latence cible | Retry | Timeout | Idempotent |
|---|---|---|---|---|---|
| Evidence → Knowledge (qualification) | Async | < 5 s | 3 × backoff | 30 s | Oui |
| Knowledge → Correlation/Reasoning (query) | Sync | < 500 ms | 1 | 5 s | Oui |
| Correlation → Reasoning (matrix) | Async | < 10 s | 3 × backoff | 60 s | Oui |
| Reasoning → Diagnostic (inference) | Sync | < 2 s | 1 | 10 s | Oui |
| Diagnostic → Recommendation | Sync | < 1 s | 1 | 5 s | Oui |
| Recommendation → Validation | Sync | < 500 ms | 1 | 5 s | Oui |
| Domaine (GIS/Climate/…) → Diagnostic | Async | < 5 s | 3 × backoff | 30 s | Oui |
| Domaine → Simulation | Async | < 5 s | 3 × backoff | 30 s | Oui |
| Simulation → Validation | Async | < 60 s | 2 × backoff | 300 s | Oui |
| Learning → Knowledge/Evidence | Async | < 10 s | 3 × backoff | 60 s | Oui |
| Event-driven (tous) | Pub/Sub | — | — | — | Oui |

### Règles transverses

- **Toutes les opérations sont idempotentes** (déduplication par
  `message_id` — voir `ENGINE_COMMUNICATION_PROTOCOL.md` §4.6).
- **Circuit breaker** sur chaque moteur (§4.5 du protocole) : 5 erreurs
  consécutives → ouverture, 30 s → semi-ouvert.
- **Offline-first** : les interactions async/event-driven transitent
  par la file locale persistante (SQLite) en cas de coupure réseau.

---

## Gestion des erreurs

La gestion des erreurs est définie dans
`ENGINE_COMMUNICATION_PROTOCOL.md` §4. Cette section consolide les
codes d'erreur spécifiques aux contrats d'interface.

### Structure d'erreur

Voir `ENGINE_COMMUNICATION_PROTOCOL.md` §4.2 — `EngineError`.

### Codes d'erreur par moteur

| Code | Moteur | Catégorie | Retryable | Description |
|---|---|---|---|---|
| `EVIDENCE_INVALID_SOURCE` | Evidence | validation | Non | Source non identifiable ou non vérifiable |
| `EVIDENCE_QUARANTINE` | Evidence | internal | Non | Connaissance en quarantaine (conflit non résolu) |
| `KNOWLEDGE_NOT_FOUND` | Knowledge | not_found | Non | Aucune connaissance ne correspond à la requête |
| `KNOWLEDGE_GRAPH_CORRUPTED` | Knowledge | internal | Oui | Graphe de connaissances corrompu |
| `CORRELATION_INSUFFICIENT_DATA` | Correlation | validation | Non | Pas assez d'observations pour calculer une corrélation |
| `REASONING_NO_APPLICABLE_RULE` | Reasoning | validation | Non | Aucune règle ne s'applique au contexte |
| `REASONING_CONTRADICTION` | Reasoning | internal | Non | Contradiction détectée (transmise, pas une erreur fatale) |
| `DIAGNOSTIC_INCOMPLETE_CONTEXT` | Diagnostic | validation | Non | Contexte stationnel incomplet |
| `RECOMMENDATION_NO_VALID_OPTION` | Recommendation | not_found | Non | Aucune recommandation valide pour le diagnostic |
| `VALIDATION_BLOCKED` | Validation | validation | Non | Sortie bloquée par le moteur de validation |
| `GIS_LAYER_UNAVAILABLE` | GIS | not_found | Oui | Couche demandée non disponible (cache ou serveur) |
| `CLIMATE_PROJECTION_UNAVAILABLE` | Climate | not_found | Oui | Projection non disponible pour ce scénario/période |
| `PEDOLOGY_PROFILE_MISSING` | Pedology | not_found | Non | Profil pédologique non disponible pour cette station |
| `BOTANICAL_TAXON_NOT_FOUND` | Botanical | not_found | Non | Taxon non trouvé dans le référentiel |
| `FOREST_DYNAMICS_MODEL_UNAVAILABLE` | ForestDyn | not_found | Non | Modèle de croissance non disponible pour cette essence |
| `LEARNING_INSUFFICIENT_DATA` | Learning | validation | Non | Pas assez de données pour l'apprentissage |
| `SIMULATION_TIMEOUT` | Simulation | timeout | Oui | Simulation dépassée par le timeout |
| `SIMULATION_INVALID_SCENARIO` | Simulation | validation | Non | Scénario de simulation invalide |
| `CONTRACT_VERSION_MISMATCH` | Tous | contract | Non | Version de contrat incompatible (voir §Versioning) |

---

## Versioning des contrats

Le versioning des contrats suit **SemVer** (Semantic Versioning) adapté
aux contrats d'interface. Voir `ENGINE_COMMUNICATION_PROTOCOL.md` §5
pour le détail complet.

### Règles

| Changement | Type de version | Compatibilité |
|---|---|---|
| Ajout d'un champ optionnel | Patch (1.0.0 → 1.0.1) | Rétrocompatible |
| Ajout d'une nouvelle opération | Minor (1.0.1 → 1.1.0) | Rétrocompatible |
| Suppression ou renommage d'un champ | Major (1.1.0 → 2.0.0) | **Cassante** — migration requise |

### Version courante des contrats

| Moteur | Version contrat | Statut |
|---|---|---|
| Evidence Engine | 1.0.0 | Draft |
| Knowledge Engine | 1.0.0 | Draft |
| Correlation Engine | 1.0.0 | Draft |
| Reasoning Engine | 1.0.0 | Draft |
| Diagnostic Engine | 1.0.0 | Draft |
| Recommendation Engine | 1.0.0 | Draft |
| Validation Engine | 1.0.0 | Draft |
| GIS Engine | 1.0.0 | Draft |
| Climate Engine | 1.0.0 | Draft |
| Pedology Engine | 1.0.0 | Draft |
| Botanical Engine | 1.0.0 | Draft |
| Forest Dynamics Engine | 1.0.0 | Draft |
| Learning Engine | 1.0.0 | Draft |
| Simulation Engine | 1.0.0 | Draft |

> Toutes les versions sont 1.0.0 en Phase 2 (Architecture). Les
> évolutions de contrat seront tracées dans ce tableau lors de
> l'implémentation (Phase 4).

---

## Tests d'interface

Chaque moteur doit valider son respect des contrats d'interface avant
publication. Les tests d'interface sont de trois types :

### 1. Tests de conformité de schéma

Vérifient que les messages produits et consommés respectent les
schémas formels définis ci-dessus.

- **Validation à la sérialisation** : chaque message sérialisé est
  validé contre son schéma (Pydantic côté Python, serde côté Rust) ;
- **Validation à la désérialisation** : chaque message reçu est
  validé avant traitement ;
- **Tests de champs obligatoires** : les champs non optionnels
  déclenchent une erreur s'ils sont absents ;
- **Tests de types** : les types déclarés sont respectés (UUID, ISO
  8601, enum, decimal, etc.).

### 2. Tests de contrat (behavioral)

Vérifient que le moteur respecte les garanties déclarées.

- **Test d'idempotence** : un même `message_id` envoyé deux fois
  produit le même résultat ;
- **Test de timeout** : le moteur répond dans le temps déclaré ou
  renvoie `timeout` ;
- **Test de mode dégradé** : le moteur fonctionne hors-ligne avec
  les données en cache local ;
- **Test de circuit breaker** : le moteur ouvre le circuit après 5
  erreurs consécutives.

### 3. Tests d'intégration inter-moteurs

Vérifient que les flux entre moteurs respectent la matrice
d'interactions.

- **Test de flux principal** : Evidence → Knowledge → Correlation →
  Reasoning → Diagnostic → Recommendation → Validation ;
- **Test de flux domaine** : GIS/Climate/Pedology/Botanical/ForestDyn
  → Diagnostic ;
- **Test de flux transverse** : Learning → Knowledge/Evidence,
  Simulation → Validation/Recommendation/Learning ;
- **Test de bout en bout** : une requête utilisateur complète
  produit une sortie validée avec chaîne de trace intacte.

### Outils de test

| Outil | Rôle | Côté |
|---|---|---|
| Pydantic | Validation de schéma | Python |
| serde | Validation de schéma | Rust |
| pytest | Tests unitaires et d'intégration | Python |
| `contract_test` (à implémenter) | Tests de conformité de contrat | Commun |

> Les tests d'interface seront implémentés en Phase 4
> (Implémentation). En Phase 2, les schémas formels ci-dessus
> servent de spécification pour leur rédaction.

---

## Historique

| Date | Événement |
|---|---|
| 2026-07-12 | Création — matrice d'interactions + détail des flux |
| 2026-07-12 | Audit Phase 2 — en-tête complété, types communs, schémas formels des 14 moteurs, garanties de service, codes d'erreur, versioning, tests d'interface |
