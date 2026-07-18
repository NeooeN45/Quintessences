# RFC-0014 — Garde-fou anti-invention de données + ingestion de la littérature scientifique non structurée

| Champ | Valeur |
|---|---|
| **ID** | RFC-0014 |
| **Statut** | Adopté |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-17 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Impact** | Tous les moteurs GSIE (garde-fou transverse), `GSIE/API/` (module d'extraction), `GSIE/KNOWLEDGE/`, `GSIE/RESEARCH/`, `03_DECISIONS/`, `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md` |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-001 (l'IA assiste, ne décide jamais), GSIE-CON-002 (science), GSIE-CON-005 (traçabilité), GSIE-CON-010 (historique) |
| **Décision liée** | DEC-000025 (à créer) |
| **RFC liées** | RFC-0011 (métamodèle v6.2), RFC-0012 (migration API v6.2), RFC-0013 (ingestion des données géospatiales/tabulaires structurées ONF/CNPF/IGN — **complémentaire, pas redondante**, voir §2.1) |
| **ADR liés** | ADR-001 (racine resource), ADR-002 (Temporal Engine) |

---

## 1. Objet

Cette RFC propose deux choses indissociables :

1. Un **garde-fou architectural transverse**, applicable à *tous* les
   moteurs GSIE (pas seulement l'ingestion) : aucun moteur ne peut
   produire, calculer ou faire circuler une valeur, une corrélation ou
   une recommandation qui ne soit pas traçable jusqu'à une donnée
   réelle, sourcée et vérifiable. Aucune donnée par défaut, interpolée
   silencieusement, ou générée par un LLM sans citation vérifiable
   n'entre dans le graphe de connaissances.
2. Un **pipeline d'ingestion de la littérature scientifique non
   structurée** (guides sylvicoles, guides des stations forestières,
   *Flore forestière française* — Rameau et al., rapports du GIEC,
   enveloppes bioclimatiques par essence, référentiels pédologiques
   narratifs) via extraction assistée par un modèle de langage sous
   contrainte stricte de citation, avec validation humaine obligatoire
   avant tout passage au statut « accepté ».

### 1.1 Ce que cette RFC ne couvre pas

L'ingestion des **datasets géospatiaux et tabulaires structurés**
(BD Forêt v2, IFN, RPF/RPFR, BDAT, LiDAR HD) est déjà couverte par
**RFC-0013**, qui reste l'unique référence pour ce périmètre. Cette
RFC-0014 couvre le complément : les documents **non structurés**
(texte narratif, PDF sans schéma tabulaire exploitable directement),
qui nécessitent une étape d'extraction sémantique qu'un pipeline ETL
classique ne peut pas faire.

## 2. Contexte et motivation

### 2.1 Constat

Le Correlation Engine (livré en Phase 4, session du 2026-07-17)
fonctionne, mais sur un périmètre volontairement réduit : il calcule
des statistiques sur des valeurs fournies directement dans la requête,
faute de moteurs domaine réels pour les alimenter. Sans garde-fou
explicite, rien n'empêche techniquement qu'un futur appelant — humain
ou automatisé — fournisse des valeurs inventées, estimées « à vue de
nez », ou générées par un LLM sans ancrage réel. Le schéma v6.2 est
correctement pensé pour la traçabilité (Assertion + EvidenceAssessment
+ Citation + Source), mais rien ne **force** aujourd'hui son usage à
chaque point d'entrée.

Par ailleurs, la base de connaissances actuelle (`KNOWLEDGE_BASE_SEED.md`)
ne contient qu'un nombre restreint d'assertions d'amorçage. Le
véritable corpus scientifique du domaine (guides sylvicoles, guides
des stations, les 3 tomes de *Flore forestière française*, rapports du
GIEC, enveloppes bioclimatiques, référentiels pédologiques) n'est pas
encore ingéré. Sans lui, Correlation/Reasoning/Diagnostic/
Recommendation n'ont rien de réel à exploiter, quelle que soit la
qualité de leur code.

### 2.2 Le risque spécifique à nommer

Utiliser un LLM (Fable 5 ou tout autre) pour accélérer l'extraction de
connaissance depuis ces sources est utile et souhaité par le
Fondateur — mais un LLM peut halluciner un chiffre, une essence, un
seuil qui semble plausible sans exister dans le texte source. Le
risque n'est pas l'usage du LLM en soi, c'est son usage **sans
contrainte de citation vérifiable et sans validation humaine avant
diffusion**. Cette RFC formalise la limite : le LLM est un
**assistant d'extraction sous supervision**, jamais un **oracle**.

## 3. Architecture proposée

### 3.1 Garde-fou transverse (tous moteurs)

Règle architecturale, à appliquer immédiatement aux moteurs déjà codés
(Correlation) et à tout moteur futur (Reasoning, Diagnostic,
Recommendation, Forest Dynamics, Learning, Simulation) :

> **Aucun moteur ne peut faire circuler une valeur numérique, une
> corrélation ou une conclusion sans un `SourceReference` résolvable
> et un `evidence_level` hérité d'une donnée réelle.** Les valeurs par
> défaut, les interpolations silencieuses et les sorties de LLM non
> citées sont interdites en production. Toute violation est un bug de
> sécurité scientifique, pas une simplification acceptable.

Mise en œuvre concrète :

- Extension de `tools/check_governance_consistency.py` (ou nouveau
  script dédié) : détecter, par analyse statique, les littéraux
  numériques suspects (valeurs par défaut non documentées) dans les
  moteurs de raisonnement — best-effort, pas une garantie totale.
- Revue de code obligatoire (checklist) pour tout nouveau moteur
  Reasoning/Diagnostic/Recommendation avant merge : « chaque donnée
  d'entrée est-elle traçable jusqu'à une Assertion sourcée ou un
  dataset catalogué (RFC-0013) ? »
- Tests contractuels : chaque moteur de raisonnement expose une
  méthode `explain()` ou équivalent qui retourne la chaîne de
  provenance complète d'une conclusion (CON-001 — explicabilité,
  recommandation contournable par le forestier).

### 3.2 Pipeline d'ingestion de la littérature non structurée

```
Document source (PDF/texte — Guide sylvicole, Flore forestière
française, rapport GIEC, enveloppe bioclimatique, etc.)
  → Découpage en passages citables (page, section, paragraphe)
  → Extraction assistée par LLM scientifique (RAG sur le texte réel
    fourni, PAS sur la mémoire du modèle — le LLM ne doit jamais
    répondre depuis sa connaissance générale du sujet)
  → Chaque fait extrait DOIT porter : citation exacte (page/section),
    texte source verbatim court, proposition de evidence_level
  → Statut initial systématique : « quarantine » (jamais « accepte »
    automatiquement, quel que soit le score de confiance du LLM)
  → Validation humaine (Fondateur ou expert forestier désigné) :
    vérifie la citation contre le document source réel
  → Passage à « accepte » uniquement après validation humaine
  → Ingestion dans Knowledge Engine (Assertion + EvidenceAssessment +
    Citation + Source, schéma v6.2 déjà en place)
```

Points de rejet automatique (avant même la validation humaine) :

- Absence de citation exacte (page/section) → rejet, pas de fallback
- Le passage cité, une fois relu automatiquement dans le document
  source, ne contient pas les termes clés de l'extraction → rejet
- Confiance du LLM sur sa propre extraction en dessous d'un seuil
  configurable → passage direct en quarantaine renforcée (double
  validation humaine requise)

### 3.3 Rôle explicite de l'IA (LLM) dans ce pipeline

- **Autorisé** : extraire un fait d'un texte fourni, en citant sa
  source exacte ; proposer une structuration `KnowledgeIngestRequest` ;
  signaler ses propres doutes.
- **Interdit** : compléter un chiffre manquant depuis sa connaissance
  générale ; fusionner deux sources sans le signaler explicitement ;
  s'auto-valider (passer un statut à « accepte ») ; produire une
  correction ou une extrapolation de plusieurs sources en une seule
  citée artificiellement.

Cette distinction reprend et opérationnalise CON-001 (« l'IA assiste,
ne décide jamais ») pour le cas spécifique de l'extraction de
connaissance scientifique.

### 3.4 Feuille de route de maturité par moteur

| Moteur | État (2026-07-17) | Niveau de complexité requis | Priorité |
|---|---|---|---|
| Evidence | Codé, 67 tests Rust | Suffisant | — |
| Knowledge | Codé, Postgres, versionné | Suffisant (manque le volume de vraies connaissances, voir §3.2) | P0 (ingestion) |
| Correlation | Codé v1 réduite | Suffisant en attendant les moteurs domaine | — |
| GIS | Placeholder | Doit consommer RFC-0013 (BD Forêt, LiDAR HD) — pas de données simulées | P0 |
| Climate | Inexistant | DRIAS 2020, Météo-France — jamais de valeurs climatiques inventées | P1 |
| Pedology | Inexistant | RPF/RPFR (RFC-0013) + BDAT — jamais d'estimation de pH/texture sans source | P1 |
| Botanical | Inexistant | GBIF/INPN TAXREF + *Flore forestière française* (ce RFC, §3.2) | P0 |
| Forest Dynamics | Inexistant | IFN (RFC-0013) + guides sylvicoles (ce RFC, §3.2) | P1 |
| Reasoning | Inexistant | Chaîne d'inférence explicable, chaque prémisse tracée (§3.1) | P2 |
| Diagnostic | Inexistant | Idem Reasoning — aucune classification sans corrélations sourcées réelles | P2 |
| Recommendation | Inexistant | Le plus sensible : jamais de décision, uniquement des options tracées et contournables (CON-001) | P2 |
| Validation | Inexistant | Vérifie la cohérence inter-moteurs, pas de logique métier propre | P2 |
| Learning | Inexistant | Ne promeut JAMAIS un pattern statistique en connaissance validée sans repasser par Evidence Engine (§3.1) | P3 |
| Simulation | Inexistant | Modèles paramétrés par des connaissances sourcées uniquement, jamais de constantes ad hoc | P3 |

### 3.5 Intégrations complémentaires à RFC-0013

RFC-0013 couvre BD Forêt v2, IFN, RPF/RPFR, BDAT, LiDAR HD, catalogues
stations CNPF. Cette RFC ajoute au périmètre d'intégration réelle :

| Source | Domaine | Usage |
|---|---|---|
| GBIF, INPN TAXREF | Botanique, taxonomie | Référentiel taxonomique validé pour Botanical Engine |
| DRIAS 2020 | Climat | Projections climatiques (RCP/SSP) pour Climate Engine et scénarios (déjà prévu dans `scenario_subtype`, migration 0002) |
| GIEC/IPCC (rapports) | Climat, contexte scientifique global | Justification scientifique des scénarios, pas de données locales chiffrées directement exploitables — usage qualitatif/contextuel uniquement, à ne pas confondre avec DRIAS pour les chiffres |
| *Flore forestière française* (Rameau et al., 3 tomes) | Autécologie | Corpus déjà partiellement cité dans `KNOWLEDGE_BASE_SEED.md` — à ingérer intégralement via §3.2 |
| Guides sylvicoles et guides des stations (CNPF/IDF) | Sylviculture | Sous réserve de vérification des droits d'usage (point légal, pas technique — à trancher par le Fondateur avant ingestion) |

Catalogue exhaustif des ~179 sources par moteur, avec méthodes d'accès
concrètes (endpoints API, auth, formats) : voir
`GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md` — référence de premier
plan pour prioriser les intégrations §3.4/§3.5, complémentaire à
`DATASET_CATALOG.md` (DS-001 à DS-029) et à RFC-0013.

### 3.6 Pilote réalisé (2026-07-17)

Premier document pilote testé de bout en bout : *Lettre du DSF n°61*
(Département Santé des Forêts, septembre 2024, PDF public
`agriculture.gouv.fr`, identifié via `SOURCES_DONNEES_EXHAUSTIVES.md`
§10.13). Résultat : 8 faits réels extraits (page 3, biologie d'Epinotia
subsequana et données de piégeage 2022), tous vérifiés (citation
retrouvée mot pour mot dans le texte source), tous en statut
« quarantine » — aucun jamais accepté automatiquement. Implémentation :
`Forge/src/dataset_forge/documents/extraction.py` (`KnowledgeExtractor`).

Enseignements du pilote, à retenir pour la suite de l'implémentation :
- Les modèles de raisonnement (ex. `nemotron-3-nano`) peuvent épuiser
  leur budget de tokens en chaîne de pensée avant de produire la
  réponse finale — préférer un modèle direct (`deepseek-v4-flash`) pour
  ce type de tâche d'extraction structurée.
- Certains PDF administratifs ont un encodage de police cassé (accents
  perdus) — n'invalide pas la garantie anti-invention (la citation est
  vérifiée contre le même texte, corrompu des deux côtés), mais un
  fallback OCR sera nécessaire pour une exploitation humaine propre en
  production.

**Deuxième pilote (2026-07-17)** : *Guide de sylviculture dynamique
(feuillus)* (CNPF Grand Est, accès libre, `grandest.cnpf.fr`). Résultat :
10 faits extraits sur 3 pages (techniques de détourage, seuils de
régénération par îlot, règles d'espacement) — **8 vérifiés
(quarantine), 2 correctement rejetés** (citation non retrouvée
verbatim) : le garde-fou fonctionne aussi en rejet, pas seulement en
acceptation. Confirme la généralisation du pipeline à un type de
document différent (guide technique vs. lettre de bilan sanitaire).

**Troisième pilote (2026-07-18)** : premier essai du chemin « clean
room » (19_LEGAL/STRATEGIE_ACCES_SOURCES_PROTEGEES_2026-07-18.md) pour
alimenter `AutecologyProfile` (RFC-0016) sans dépendre de ClimEssences/
BioClimSol. Recherche via `MultiSourceDocumentSearcher` (HAL/OpenAlex,
déjà connectés) sur l'autécologie du chêne sessile → article réel
identifié : Parelle J., Brendel O., Jolivet Y. (2007), « Intra- and
interspecific diversity in the response to waterlogging of two
co-occurring white oak species (Quercus robur and Q. petraea) »,
*Annals of Forest Science* (hal-02653679, INRAE, PDF en accès libre).
Résultat : **29 faits vérifiés (quarantine) sur 31 extraits, 2
correctement rejetés**, couvrant tolérance à la sécheresse, préférence
de sol (acide/drainé pour *Q. petraea* vs alluvial/fertile pour *Q.
robur*), et réponses physiologiques à l'engorgement racinaire —
premières données `AutecologyProfile` réelles et sourcées pour
l'essence pilote, obtenues sans recopier ClimEssences/BioClimSol.

Bug réel trouvé et corrigé pendant ce pilote : `_verify_citation`
rejetait à tort des citations verbatim correctes à cause des césures
de fin de ligne introduites par l'extraction PDF d'un texte justifié
(« ecological re-\nquirements » au lieu de « ecological requirements »)
— corrigé dans `Forge/src/dataset_forge/documents/extraction.py`
(`_normalize` recolle désormais les césures avant comparaison, sans
assouplir l'exigence de correspondance exacte par ailleurs).

Conforme à la stratégie juridique (mode `TDM_EPHEMERAL`, article
L122-5-3 CPI) : le PDF source a été détruit immédiatement après
extraction — seuls les faits atomiques cités sont conservés
(`GSIE/KNOWLEDGE/pilotes_extraction/parelle_2007_quercus_waterlogging_facts.json`),
jamais le texte intégral de l'article. Source enregistrée dans le
registre (`hal-depot-auteur`, SCI-001) avec ce mode explicite.

## 4. Plan d'implémentation

### Phase 1 — garde-fou (immédiat, avant tout nouveau moteur de raisonnement)

1. Formaliser la règle §3.1 en ADR dédié — fait, voir
   `GSIE/ARCHITECTURE/ADR-007-garde-fou-anti-invention.md` (Accepté)
2. Étendre le checker de gouvernance avec une détection best-effort
   des valeurs numériques non sourcées dans les moteurs
3. Ajouter la checklist de revue de code aux contributions de moteurs
   Reasoning/Diagnostic/Recommendation

### Phase 2 — pipeline d'extraction documentaire (P0)

4. Module `gsie_api.extraction` : découpage en passages citables,
   appel LLM sous contrainte RAG, structuration `KnowledgeIngestRequest`
5. Interface de validation humaine (au minimum : endpoint API + script
   CLI, une UI complète peut attendre)
6. Ingestion pilote sur un document unique (à choisir avec le
   Fondateur — *Flore forestière française* tome 1 est un candidat
   naturel, déjà partiellement cité)

### Phase 3 — montée en charge (P1-P2)

7. Ingestion des guides sylvicoles/stations (sous réserve §3.5)
8. Ingestion des rapports GIEC pertinents (contexte climatique)
9. Intégration GBIF/INPN, DRIAS

## 5. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| LLM extrait un fait plausible mais absent du texte source | Fausse connaissance validée | Citation exacte obligatoire + relecture automatique du passage cité + validation humaine (§3.2) |
| Volume de validation humaine trop important (goulot d'étranglement) | Ingestion trop lente | Prioriser par moteur (P0 : Botanical/Forest Dynamics), accepter un rythme lent plutôt qu'un contrôle relâché |
| Droits d'usage des guides CNPF/IDF non clarifiés | Blocage légal | Vérification préalable par le Fondateur avant toute ingestion (point explicitement hors périmètre technique) |
| Garde-fou §3.1 non appliqué de façon cohérente (oubli humain) | Régression silencieuse vers données inventées | Automatiser autant que possible (checker, tests contractuels `explain()`) plutôt que compter sur la seule discipline |

## 6. Alternatives considérées

### 6.1 Laisser chaque moteur inventer des valeurs de test/défaut librement

**Rejetée** — c'est précisément le risque que le Fondateur a demandé
d'éliminer. Contredit CON-002 (science) et CON-005 (traçabilité).

### 6.2 Utiliser le LLM comme oracle direct (poser la question, faire confiance à la réponse)

**Rejetée** — aucune garantie de citation vérifiable, risque
d'hallucination non détectable a posteriori. Le LLM reste un
assistant d'extraction sous contrainte, jamais une source en soi.

### 6.3 Ingestion manuelle intégrale sans assistance LLM

**Rejetée pour le volume visé** — les 3 tomes de *Flore forestière
française* et les rapports du GIEC représentent un volume que
l'extraction manuelle pure rendrait irréaliste. L'assistance LLM sous
contrainte de citation est un compromis raisonnable entre rigueur et
faisabilité.

## 7. Conséquences

### 7.1 Positives

- Garantie structurelle (pas seulement documentaire) qu'aucune donnée
  inventée n'entre dans le graphe de connaissances
- Chemin concret pour ingérer le vrai corpus scientifique du domaine
- Cadre clair et réutilisable pour tout usage futur d'un LLM dans GSIE

### 7.2 Négatives

- Ralentit l'ingestion (validation humaine systématique) — c'est un
  choix assumé, pas un défaut à corriger
- Complexité supplémentaire (module d'extraction + interface de
  validation)

## 8. Décision requise

**Décision** : Valider cette RFC et autoriser l'implémentation du
garde-fou transverse (§3.1, immédiat) et du module d'extraction
documentaire (§3.2, Phase 2), en commençant par un document pilote à
désigner par le Fondateur.

**Décideur** : Camille Perraudeau (Fondateur)

## 9. Références

- `GSIE/KNOWLEDGE/KNOWLEDGE_BASE_SEED.md` — amorçage actuel, citations
  *Flore forestière française* déjà présentes
- `02_RFC/RFC-0013-ingestion-donnees-onf-cnpf.md` — pipeline
  complémentaire pour les données structurées
- `00_CONSTITUTION/GSIE-CON-001.md` — l'IA assiste, ne décide jamais
- `00_CONSTITUTION/GSIE-CON-002.md` — science
- `00_CONSTITUTION/GSIE-CON-005.md` — traçabilité
- `GSIE/ENGINES/CORRELATION_ENGINE/CORRELATION_ENGINE.md` — garanties
  déjà posées (§6 : sourcé, pas de causalité non justifiée)
- `GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md` — catalogue exhaustif
  (~179 sources) avec méthodes d'accès concrètes par source, utilisé
  pour identifier le document pilote §3.6

## 10. Historique

| Date | Modification | Auteur |
|---|---|---|
| 2026-07-17 | Création — RFC-0014 Draft | Camille Perraudeau |
| 2026-07-17 | Validation Fondateur — Adopté (DEC-000025 Validated) | Camille Perraudeau |
| 2026-07-17 | Pilote réalisé (§3.6) + lien vers SOURCES_DONNEES_EXHAUSTIVES.md | Camille Perraudeau |
