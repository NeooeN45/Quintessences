# RFC-0016 — Schéma forestier spécialisé et chaîne de décision professionnelle

| Champ | Valeur |
|---|---|
| **ID** | RFC-0016 |
| **Statut** | Adopté |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-18 |
| **Auteur** | Camille Perraudeau (Fondateur) — proposition rédigée à partir de l'addendum externe versé en `GSIE/RESEARCH/CORPUS_SYLVICOLE_SCIENTIFIQUE_QUINTESSENCES_2026-07-18.md` |
| **Impact** | Botanical Engine, Forest Dynamics Engine, futurs Diagnostic/Recommendation Engines, métamodèle v6.2 (nouvelles tables satellite), GeoSylva (packs offline territoriaux), `03_DECISIONS/`, `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md` |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-001 (l'IA assiste, ne décide jamais), GSIE-CON-002 (science), GSIE-CON-005 (traçabilité) |
| **Décision liée** | DEC-000027 (Validated) |
| **RFC liées** | RFC-0013 (ingestion données structurées ONF/CNPF), RFC-0014 (garde-fou anti-invention + pipeline documentaire), RFC-0015 (Environmental Model Fabric — registre de modèles, dont cette RFC est un cas d'application forestier spécifique) |
| **ADR liés** | ADR-007 (garde-fou transverse anti-invention) — cette RFC en est une application directe au domaine sylvicole |

---

## 1. Objet

RFC-0014 a posé le garde-fou anti-invention des données. RFC-0015 a
généralisé ce garde-fou aux modèles scientifiques (registre,
domaine de validité, licences). Cette RFC applique les deux au domaine
**sylvicole** spécifiquement, en formalisant :

1. une **ontologie forestière spécialisée** (§4 du corpus source) —
   `Taxon`, `AutecologyProfile`, `StationType`/`StationObservation`,
   `SiteIndexModel`/`FertilityClass`, `SilviculturalSystem`/
   `SilviculturalRule`/`Intervention`, `ProvenanceMaterial`,
   `DiagnosticProtocol`/`HealthRisk`, `EvidenceStatement`/`ConflictRecord` ;
2. une **chaîne de décision professionnelle en 10 étapes** (§5), du
   relevé terrain à la validation humaine finale ;
3. un **passeport de décision** (§6) distinguant explicitement cinq
   catégories : observé, calculé, modélisé, documenté/recommandé,
   incertain ;
4. un **principe non négociable** : une classe de fertilité n'est
   jamais universelle — elle n'a de sens qu'accompagnée de son
   essence, son modèle, son âge de référence, sa région de
   calibration et sa source.

### 1.1 Ce que cette RFC ne couvre pas

- Le registre des sources et licences (SCI-001) — déjà implémenté
  (`gsie_api.governance.source_registry`, hors RFC dédiée, cohérent
  avec RFC-0015 §3.4).
- TAXREF comme taxonomie canonique (SCI-003) — déjà implémenté
  (`BotanicalEngine.resolve_taxref`).
- Les démarches de partenariat CNPF/ONF (corpus source §12) — action
  documentaire séparée, hors périmètre technique de cette RFC.
- Le choix technique du moteur de règles déterministe (SCI-009) —
  cette RFC pose le schéma de données qu'il consommera, pas son
  implémentation.

## 2. Contexte et motivation

### 2.1 Constat

Le Botanical Engine actuel (Phase 4) résout la taxonomie (GBIF,
TAXREF) et l'indigénat par sylvoécorégion (dataset Bellifa et al.
2026). Il ne modélise pas encore l'autécologie complète, les stations
forestières, les classes de fertilité, les itinéraires sylvicoles, ni
les protocoles sanitaires. Sans ce schéma, aucune recommandation
sylvicole ne peut être tracée jusqu'à sa preuve — exactement le risque
que RFC-0014 a nommé pour les données individuelles, ici décliné pour
le domaine métier central de GeoSylva.

L'exemple documenté par le corpus source est concret : le mémento ONF
du pin d'Alep définit une classe de fertilité par la hauteur dominante
des 100 plus grosses tiges par hectare à 50 ans (classe 1 au-dessus de
14 m). D'autres guides utilisent d'autres âges, courbes et
conventions pour la même notion de « fertilité ». Stocker une classe
de fertilité comme un entier nu (`1`, `2`, `3`) sans ces métadonnées
rendrait toute comparaison inter-essences ou inter-guides fausse par
construction.

### 2.2 Le risque spécifique à nommer

Sans ce schéma, une future intégration du moteur de règles
déterministe (SCI-009) ou d'un Diagnostic/Recommendation Engine
risquerait de mélanger des observations de nature différente
(mesure de terrain, sortie de modèle, règle documentée, simulation) et
de présenter une estimation comme une certitude. Le corpus source
nomme ce risque précisément : « la recommandation ne doit pas être
"l'IA recommande le Douglas", mais une chaîne de 10 étapes traçable ».

## 3. Architecture proposée

### 3.1 Entités du schéma forestier spécialisé (§4 du corpus source)

Nouvelles tables satellite du métamodèle v6.2 (cohérentes avec le
pattern déjà en place : `resource` racine + satellite typée) :

| Entité | Rôle | Champs clés |
|---|---|---|
| `AutecologyProfile` | Observations sourcées par essence (une par variable, jamais une note globale) | valeur, unité, saison, stade de vie, territoire, méthode, incertitude, source |
| `StationType` | Unité conceptuelle issue d'un guide de station | guide, version, zone/polygone de validité, SER/GRECO |
| `StationObservation` | Ce qui est réellement observé sur une parcelle | clé suivie, réponses saisies, embranchement obtenu, incertitude de détermination |
| `SiteIndexModel` | Modèle de fertilité (équation/table, domaine, erreur) | méthode d'ajustement, échantillon de calibration, domaine d'âge/hauteur |
| `FertilityClass` | Classe de fertilité contextualisée — **jamais un entier nu** | species_id, model_id, variable, âge de référence, convention d'âge, bornes, région de calibration, source, page |
| `SilviculturalSystem` | Futaie régulière/irrégulière, taillis, conversion, etc. | — |
| `SilviculturalRule` | Règle d'intervention sylvicole | contexte requis, déclencheur, action, intensité, niveau de preuve, statut `DRAFT`/`APPROVED`, validateur humain |
| `ProvenanceMaterial` | Provenance/MFR pour une proposition de plantation | région de provenance, matériel de base, admissibilité aux aides, version de l'arrêté |
| `DiagnosticProtocol` / `HealthRisk` | Protocoles sanitaires (ARCHI, DEPERIS, IBP) | critères, seuils, version, limites — distingue symptôme observé / agent causal suspecté / agent confirmé |
| `EvidenceStatement` / `ConflictRecord` | Assertion atomique sourcée + désaccords explicites entre sources | source, page/table, territoire, grade de preuve, statut `DRAFT`→`APPROVED` |

Règle transverse (reprise et spécialisée d'ADR-007) :

> **Une `FertilityClass` sans `species_id`, `model_id`, âge de
> référence, convention d'âge et région de calibration est un bug de
> sécurité scientifique, pas une simplification acceptable.**

### 3.2 Statuts de validation (repris de RFC-0014 §3.2, appliqués ici)

Toute `SilviculturalRule` ou `EvidenceStatement` extraite par LLM
reste `DRAFT`. Le passage à `APPROVED` exige une validation humaine
(curateur de données + forestier compétent, corpus source §7 étape E)
— jamais une auto-validation par le pipeline d'extraction.

### 3.3 Chaîne de décision professionnelle (§5 du corpus source)

```
1. Observations terrain (peuplement, sol, topographie, flore, sanitaire)
2. Diagnostic stationnel (clé locale, alternatives, incertitude)
3. Filtre réglementaire (SRGS, DRA/SRA, MFR, zonages)
4. Compatibilité autécologique (eau, sol, climat, risques, provenance)
5. Analyse climatique (période, horizon, scénario, dispersion)
6. Fertilité/croissance (indice de station dans son domaine valide)
7. Options sylvicoles (plusieurs itinéraires, jamais une réponse forcée)
8. Effets croisés (production, biodiversité, carbone, eau, risque, économie)
9. Recommandation explicable (hypothèses, alternatives rejetées, incertitudes)
10. Décision humaine (validation, modification ou rejet par le professionnel)
```

Le moteur de règles déterministe (SCI-009, hors périmètre technique de
cette RFC) réalise les étapes 3 à 8. Le LLM (RFC-0015 §3.1,
orchestrateur non autoritaire) explique le chemin à l'étape 9 et cite
les preuves — il ne décide jamais à l'étape 10.

### 3.4 Passeport de décision (§6 du corpus source)

Chaque diagnostic ou scénario produit un objet exportable distinguant
visuellement cinq catégories, reprenant le principe déjà posé pour
AROME (RFC-0015 §3.2 : observation/estimation/simulation/
recommandation) et l'étendant à cinq catégories sylvicoles :

- **observé** (mesure de terrain, protocole et qualité associés) ;
- **calculé** (résultat déterministe, ex. surface terrière § Forest
  Dynamics Engine déjà en place) ;
- **modélisé** (sortie de `SiteIndexModel` ou de modèle de croissance,
  séparée des mesures) ;
- **documenté/recommandé** (règle sylvicole sourcée, page/table
  précises) ;
- **incertain** (désaccord entre sources, donnée manquante
  susceptible de changer la conclusion).

## 4. Programme pilote proposé : Nouvelle-Aquitaine (§10 du corpus source)

Cohérent avec le principe de progression par vertical slices déjà
posé en RFC-0015 §3.7 : pas de couverture nationale immédiate.

- Nouvelle-Aquitaine, découpage SER/GRECO ;
- 12 à 20 essences (chênes sessile/pédonculé/pubescent, châtaignier,
  hêtre, pin maritime, Douglas, pin sylvestre, pin laricio, peupliers) ;
- guides de stations locaux, SRGS Nouvelle-Aquitaine, arrêté MFR du
  6 mars 2026 ;
- trois horizons climatiques (actuel, milieu de siècle, fin de siècle) ;
- livrable : 100 % des assertions sourcées, 100 % des classes de
  fertilité contextualisées, au moins 50 cas « or » validés par des
  professionnels, un pack hors ligne signé.

Ce périmètre ne dépend d'aucune source bloquée par le registre SCI-001
(ClimEssences, BioClimSol) — il s'appuie sur des sources déjà
`OPEN_CONFIRMED` (IFN, TAXREF, IGN) ou sur des guides CNPF/ONF à
qualifier document par document (`LEGAL_REVIEW_PENDING`, non
bloquants pour démarrer le schéma lui-même).

## 5. Plan d'implémentation

### Phase A — schéma de données (P0)

1. Modéliser les 10 entités (§3.1) comme tables satellite v6.2 ;
2. Étendre le registre de modèles (RFC-0015 §3.3) pour couvrir
   `SiteIndexModel` comme cas concret de `ModelRegistry` ;
3. Porte de validation : aucune `FertilityClass` sans les 5 champs
   obligatoires (§3.1) — extension de
   `tools/check_governance_consistency.py`.

### Phase B — intégration Botanical/Forest Dynamics (P1)

4. `AutecologyProfile` alimenté par extraction documentaire sourcée
   (RFC-0014 §3.2), jamais par heuristique ;
5. `StationObservation` comme extension du Forest Dynamics Engine
   (déjà limité à la surface terrière géométrique — RFC-0013) ;
6. Passeport de décision (§3.4) exposé par l'API, cinq catégories
   visuellement distinctes.

### Phase C — pilote Nouvelle-Aquitaine (P1-P2)

7. Constitution du corpus 12-20 essences (§4) ;
8. 50 cas « or » validés par un forestier référent ;
9. Premier pack offline signé (RFC-0015 §3.6) territorial.

## 6. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| Sur-ingénierie du schéma avant tout cas d'usage réel | Temps perdu sans validation terrain | Phase C (pilote Nouvelle-Aquitaine) doit suivre immédiatement Phase A, pas être repoussée |
| Confusion entre observation, modèle et règle documentée dans l'UI | Recommandation présentée à tort comme une certitude | Passeport de décision (§3.4) obligatoire, cinq catégories non fusionnables |
| Classes de fertilité incomparables silencieusement mélangées | Recommandation incohérente entre deux guides | Porte de validation Phase A (5 champs obligatoires) avant tout `FertilityClass` |
| Blocage sur les sources CNPF/ONF non qualifiées juridiquement | Ralentit le pilote | Le schéma et le pilote ne dépendent pas de ClimEssences/BioClimSol (sources déjà `OPEN_CONFIRMED` suffisent pour démarrer) |

## 7. Alternatives considérées

### 7.1 Étendre `EspeceData` existant avec des champs autécologiques libres

**Rejetée** — un dictionnaire libre ne peut pas porter le domaine de
validité (essence/modèle/âge/région) exigé pour chaque classe de
fertilité ; reproduirait exactement le défaut nommé en §2.1.

### 7.2 Couverture nationale immédiate (149 essences, toute la France)

**Rejetée** — même raisonnement que RFC-0015 §3.7 : aucune preuve de
validité terrain à cette échelle sans passer d'abord par un pilote
mesurable. Le corpus source le nomme explicitement (§10).

### 7.3 Laisser le LLM déduire les classes de fertilité par similarité sémantique

**Rejetée** — contredit RFC-0015 §3.1 (LLM orchestrateur non
autoritaire) et le principe non négociable §3.1 de cette RFC.

## 8. Conséquences

### 8.1 Positives

- Cadre unique pour toute donnée sylvicole future (autécologie,
  stations, fertilité, itinéraires, sanitaire, provenances) ;
- Élimine structurellement le risque de classe de fertilité
  universelle déjà identifié comme faille par le corpus source ;
- Chemin concret et mesurable (pilote Nouvelle-Aquitaine) plutôt
  qu'une ambition non bornée.

### 8.2 Négatives

- Complexité de schéma supplémentaire (10 nouvelles entités) ;
- Ralentit l'ingestion de nouvelles connaissances sylvicoles tant que
  la validation humaine (Phase E du pipeline RFC-0014) n'a pas
  statué — choix assumé, pas un défaut.

## 9. Décision requise

**Décision** : Valider cette RFC et autoriser l'implémentation du
schéma forestier spécialisé (§5, Phase A), en commençant par les
entités `FertilityClass`/`SiteIndexModel` (le cas le plus documenté et
le plus risqué en cas d'invention silencieuse), puis la constitution
du pilote Nouvelle-Aquitaine (Phase C).

**Décideur** : Camille Perraudeau (Fondateur)

## 10. Références

- `GSIE/RESEARCH/CORPUS_SYLVICOLE_SCIENTIFIQUE_QUINTESSENCES_2026-07-18.md` — source de cette RFC
- `02_RFC/RFC-0015-environmental-model-fabric.md` — registre de modèles, dont `SiteIndexModel` est un cas d'application
- `02_RFC/RFC-0014-gouvernance-scientifique-anti-invention.md` — statuts `DRAFT`/`APPROVED`, pipeline d'extraction
- `02_RFC/RFC-0013-ingestion-donnees-onf-cnpf.md` — Forest Dynamics Engine, périmètre actuel (surface terrière géométrique)
- `GSIE/API/src/gsie_api/governance/source_registry.py` — SCI-001, déjà implémenté
- `GSIE/API/src/gsie_api/engines/botanical/taxref_client.py` — SCI-003, déjà implémenté
- `GSIE/ENGINES/BOTANICAL_ENGINE/BOTANICAL_ENGINE.md`, `GSIE/ENGINES/FOREST_DYNAMICS_ENGINE/FOREST_DYNAMICS_ENGINE.md`

## 11. Historique

| Date | Modification | Auteur |
|---|---|---|
| 2026-07-18 | Création — RFC-0016 Draft | Camille Perraudeau |
| 2026-07-18 | Validation Fondateur — Adopté (DEC-000027 Validated) | Camille Perraudeau |
