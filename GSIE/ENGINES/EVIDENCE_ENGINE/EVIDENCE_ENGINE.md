# Evidence Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Evidence Engine |
| **Catégorie** | Chaîne d'intelligence (filtre amont) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-002, GSIE-CON-005, GSIE-CON-010 |
| **Ordre de développement** | 2 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Évaluer la qualité scientifique de chaque connaissance avant son
intégration dans GSIE et lui attribuer un niveau de preuve sourcé et
traçable.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| Sources externes — publications | Donnée brute | Articles scientifiques peer-reviewed, méta-analyses |
| Sources externes — référentiels | Donnée brute | Référentiel Pédologique Français, WRB, BDNFF, IGN, Météo-France |
| Sources externes — experts | Donnée brute | Connaissances d'experts identifiés (niveau « expert ») |
| Sources externes — observations terrain | Donnée brute | Relevés de terrain, inventaires, photos |
| `GSIE/DATASETS/` | Métadonnées | Jeux de données référencés et sourcés |
| `GSIE/RESEARCH/` | Métadonnées | Bibliographie sourcée |
| Pipeline d'import | Donnée brute | Données brutes en attente de qualification |

L'Evidence Engine est le **point d'entrée amont** du système : il ne
consomme la sortie d'aucun autre moteur.

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `KNOWLEDGE_ENGINE` | Connaissance qualifiée | Connaissances dotées d'un niveau de preuve, d'une source et d'un identifiant de version |
| `LEARNING_ENGINE` | Signaux | Connaissances dont le niveau de preuve est susceptible d'évolution (réévaluation) |
| Journal d'audit | Trace | Historique des évaluations, conflits détectés, décisions de qualification |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Bases externes | `GSIE/DATASETS/`, `GSIE/RESEARCH/` | Sources de métadonnées et bibliographie |
| Aucun moteur | — | L'Evidence Engine ne dépend d'aucun autre moteur (amont de la chaîne) |

## 5. Contrat d'interface

### Entrée — `RawKnowledgeSubmission`

```
RawKnowledgeSubmission = {
  soumission_id     : UUID
  type_contenu      : enum { publication, referentiel, expert, observation }
  contenu           : structure libre (texte, tableau, mesure, image)
  source_candidate  : SourceReference
  date_soumission   : ISO 8601
  soumetteur        : Identifiant (utilisateur ou pipeline automatique)
}

SourceReference = {
  type_source   : enum { peer_reviewed, referentiel_officiel, expert_identifie, observation_terrain }
  auteur        : texte ou organisme
  date_publication : ISO 8601 (optionnel)
  reference     : texte (DOI, URL, citation, code référentiel)
  version_source : texte (optionnel)
}
```

### Sortie — `QualifiedKnowledge`

```
QualifiedKnowledge = {
  connaissance_id   : UUID
  contenu_normalise : structure (dépend du type de connaissance)
  evidence_level    : enum { A, B, C, D, E, F }
    // A = méta-analyse / consensus fort
    // B = établi (peer-reviewed, reproductible)
    // C = probable (peer-reviewed, domaine partiel)
    // D = expert identifié, non publié
    // E = observation terrain non publiée
    // F = incertain / contesté
  source            : SourceReference
  version           : entier (commence à 1)
  date_qualification: ISO 8601
  conflits          : liste de ConflitBibliographique (optionnel)
  statut            : enum { accepte, quarantine, refuse }
}

ConflitBibliographique = {
  source_a : SourceReference
  source_b : SourceReference
  description : texte
}
```

## 6. Garanties

- **Aucune connaissance n'entre dans le système sans niveau de preuve**
  (principe fondateur, `GSIE_CORE_BLUEPRINT.md`).
- Toute connaissance qualifiée porte une source identifiable et
  vérifiable (`GSIE-CON-002`).
- L'historique des évaluations est conservé — une réévaluation
  n'écrase jamais l'ancienne (`GSIE-CON-010`).
- Les conflits bibliographiques sont signalés, jamais résolus
  arbitrairement (`GSIE-CON-002`).
- Les connaissances sans source sont mises en quarantaine, jamais
  intégrées silencieusement (`GSIE-CON-005`).
- Fonctionnement hors-ligne complet (article T-8) — l'évaluation se
  fait sur les données déjà importées.

## 7. Cas d'usage

### Cas 1 — Import d'une publication sur l'autécologie du chêne sessile

Une publication peer-reviewed (Rameau et al., 2018) décrit l'optimum
écologique du chêne sessile sur sols acides à pH 4,5–6,0. L'Evidence
Engine évalue la source : type `peer_reviewed`, reproductible, consensus
modéré → `evidence_level = B`. La connaissance est acceptée et transmise
au Knowledge Engine. Aucune autre source ne contredit ce range pour
cette essence → aucun conflit.

### Cas 2 — Détection d'un conflit sur le seuil de vulnérabilité au gel

Deux publications donnent des seuils différents de vulnérabilité au gel
pour le sapin pectiné : -20 °C (source A, 2015) et -15 °C (source B,
2023, provenances du Sud). L'Evidence Engine qualifie les deux
connaissances (niveaux B et C respectivement), crée un
`ConflitBibliographique` référençant les deux sources, et transmet les
deux au Knowledge Engine. Aucune moyenne arbitraire n'est calculée.

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, à titre de **pistes pour la Phase 4** (implémentation
future), des cadres méthodologiques et outils existants pertinents pour la
responsabilité de l'Evidence Engine : évaluer la qualité scientifique d'une
connaissance et lui attribuer un niveau de preuve sourcé et traçable. Aucun
de ces éléments ne constitue une prescription d'implémentation — ils
documentent l'état de l'art pour nourrir une future spécification
(`05_SPECIFICATIONS/`) et une architecture technique détaillée.

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **GRADE** (Grading of Recommendations, Assessment, Development and Evaluation) | Grille de référence pour opérationnaliser l'échelle `evidence_level` (A–F) sur les publications peer-reviewed | Cadre de gradation le plus établi et le plus documenté au monde pour passer d'un corpus de preuves à un niveau de confiance explicite, en évaluant systématiquement le risque de biais, la cohérence, le caractère direct de la preuve et sa précision. Une transposition de ses cinq domaines d'évaluation au contexte forestier/écologique donnerait une base auditable au lieu d'une notation ad hoc. |
| **CEE Guidelines and Standards for Evidence Synthesis in Environmental Management** (Collaboration for Environmental Evidence) | Grille de lecture critique spécifique aux sciences de l'environnement, en amont ou en complément de GRADE | Contrairement à GRADE (né en médecine clinique), ce référentiel est conçu pour les données écologiques et de gestion environnementale — le domaine exact des sources traitées par ce moteur (autécologie, sylviculture, pédologie). La CEE édite aussi un outil de critical appraisal (risque de biais) directement applicable aux publications reçues en entrée. |
| **GRADE-CERQual** | Évaluation de la confiance pour les connaissances qualitatives : dires d'experts (niveau D) et observations de terrain non publiées (niveau E) | GRADE seul est conçu pour des preuves quantitatives (essais, méta-analyses) ; CERQual couvre spécifiquement les données qualitatives via quatre composantes (limites méthodologiques, cohérence, adéquation des données, pertinence). C'est la piste la plus directement transposable pour justifier, de façon tracée, les niveaux D/E de l'enum `evidence_level` plutôt que de les fixer arbitrairement. |
| **ASReview** (Active learning for Systematic Reviews) | Triage semi-automatisé du flux entrant de publications avant qualification humaine | Outil open source utilisant l'apprentissage actif pour prioriser les documents les plus pertinents dans un corpus de littérature, réduisant le temps de tri manuel tout en conservant une décision humaine finale — cohérent avec l'article constitutionnel « l'IA assiste, ne décide jamais » (`GSIE-CON-001`). Pertinent pour le volume croissant de publications forestières/écologiques entrant par le pipeline d'import. |
| **Rayyan** | Alternative ou complément à ASReview pour le screening collaboratif titres/résumés | Application web/mobile dédiée à l'accélération du tri initial de la littérature par semi-automatisation, avec traçabilité des décisions de chaque relecteur — utile si la qualification de connaissances nécessite un tri collaboratif multi-experts avant passage à l'Evidence Engine proprement dit. |
| **Vérification de citations scientifiques par NLI/LLM avec ancrage documentaire** (paradigme SciFact/FEVER) | Vérifier qu'un fait extrait automatiquement d'une publication est réellement soutenu par le texte source, avant attribution d'un `evidence_level`, si une extraction assistée par LLM est envisagée | Les grands modèles de langage peuvent fabriquer des citations ou déformer le contenu d'une source. Le paradigme « claim verification » ancre chaque affirmation extraite dans un passage précis du document source (label Supports/Refutes/NotEnoughInfo), ce qui correspond exactement à l'exigence constitutionnelle de traçabilité (`GSIE-CON-005`) et réduit le risque qu'une connaissance non vérifiée soit qualifiée par erreur. |
| **Retraction Watch Database (accessible via l'API Crossref)** | Filtre de fiabilité de la source en amont de la qualification : détecter si une publication candidate a été rétractée ou corrigée | Base de référence recensant les rétractations académiques toutes disciplines confondues, désormais interrogeable via l'API Crossref pour tout DOI. Une vérification systématique contre cette base avant attribution d'un niveau de preuve éviterait qu'une publication rétractée soit qualifiée `evidence_level B` ou `C` sans signalement. |

### Discussion — pistes d'articulation pour une future spécification

- **Gradation** : une future spécification pourrait s'appuyer sur GRADE comme
  socle méthodologique pour les sources `peer_reviewed`, complété par
  GRADE-CERQual pour les sources `expert_identifie` et `observation_terrain`,
  plutôt que de définir l'échelle A–F de façon interne et non comparable à un
  standard reconnu.
- **Triage amont** : ASReview et Rayyan répondent tous deux au même besoin
  (réduire le volume de littérature à examiner manuellement) mais avec des
  logiques différentes (apprentissage actif vs. screening collaboratif) ; le
  choix entre les deux relève d'une analyse Phase 4 selon le volume et la
  gouvernance humaine souhaitée sur le pipeline d'import.
- **Extraction automatisée et détection d'hallucination** : si l'Evidence
  Engine intègre à terme une extraction de faits assistée par LLM depuis les
  publications sources, le risque d'hallucination de citations documenté dans
  la littérature récente impose un mécanisme de vérification ancré dans le
  texte source avant toute qualification.
- **Fiabilité de source et biais de publication** : au-delà de la détection de
  rétractations, les méthodes classiques de détection de biais de publication
  (funnel plot, test d'Egger) restent la référence en méta-analyse pour
  signaler qu'un ensemble de sources concordantes peut refléter un biais de
  publication plutôt qu'un consensus réel ; cette dimension mériterait d'être
  reprise dans le champ `conflits` de `QualifiedKnowledge` lors d'une future
  itération de la spécification.

Ces pistes restent à instruire, comparer et arbitrer lors de la
spécification détaillée de la Phase 4 ; aucune ne doit être lue comme un
choix d'implémentation déjà validé.

### Sources

- Guyatt, G.H., Oxman, A.D., Vist, G.E., Kunz, R., Falck-Ytter, Y., Alonso-Coello, P., Schünemann, H.J. (GRADE Working Group), « GRADE: an emerging consensus on rating quality of evidence and strength of recommendations », *BMJ*, 336, 2008, p. 924-926. https://pmc.ncbi.nlm.nih.gov/articles/PMC2335261/
- Collaboration for Environmental Evidence (CEE), « Guidelines and Standards for Evidence Synthesis in Environmental Management ». https://environmentalevidence.org/ ; outil associé : https://environmentalevidence.org/cee-critical-appraisal-tool/
- Lewin, S., Booth, A., Glenton, C. et al. (2018), « Applying GRADE-CERQual to qualitative evidence synthesis findings: introduction to the series », *Implementation Science*, 13(Suppl 1), 2. https://link.springer.com/article/10.1186/s13012-017-0688-3 ; ressource : https://www.cerqual.org/
- Dicks, L.V., Walsh, J.C., Sutherland, W.J. (2014), « Organising evidence for environmental management decisions: a '4S' hierarchy », *Trends in Ecology & Evolution*. https://www.sciencedirect.com/science/article/pii/S0169534714001992
- van de Schoot, R., de Bruin, J., Schram, R. et al. (2021), « An open source machine learning framework for efficient and transparent systematic reviews », *Nature Machine Intelligence*, 3, p. 125-133. Outil : ASReview, https://asreview.nl/ ; code : https://github.com/asreview/asreview
- Ouzzani, M., Hammady, H., Fedorowicz, Z., Elmagarmid, A. (2016), « Rayyan—a web and mobile app for systematic reviews », *Systematic Reviews*, 5, 210. https://link.springer.com/article/10.1186/s13643-016-0384-4
- Wadden, D., Lin, S., Lo, K. et al. (2020), « Fact or Fiction: Verifying Scientific Claims », *Proceedings of EMNLP 2020* (dataset SciFact). https://aclanthology.org/2020.emnlp-main.609/
- Crossref, « Retraction Watch retractions now in the Crossref API ». https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
