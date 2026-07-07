# CHANGELOG — GSIE

Format : `## [version] - YYYY-MM-DD`

---

## [RFC-0003 + Review 005-009] - 2026-07-07

### RFC ouvert

- **RFC-0003** — Architecture distribuée GSIE-Net : capture la vision du
  Fondateur sur l'architecture offline-first, multi-couches, distribuée et
  orientée données. Activé en Phase 2. (`02_RFC/RFC-0003.md`)

### Livrables passés en Review

Cinq livrables passent du statut `Draft` au statut `Review` — soumis à la
validation du Fondateur :

- Livrable 005 — `PACT_FOR_AI_AGENTS.md`
- Livrable 006 — `GSIE-DESIGN-PHILOSOPHY.md`
- Livrable 007 — `SCIENTIFIC_CONSTITUTION.md`
- Livrable 008 — `TECHNICAL_CONSTITUTION.md`
- Livrable 009 — `AI_CONSTITUTION.md`

### Mémoire synchronisée

- `PROJECT_MEMORY.md` mis à jour : avancement Review 5/12, RFC-0003 tracé.
- `ROADMAP.md` mis à jour : statuts livrables + RFC-0003 + prochaine étape.

---

## [Conformité] - 2026-07-06

### Audit de l'état réel

- Cartographie complète du dépôt (277 fichiers `.md`) confrontée au ROADMAP et
  à la mémoire. Écarts de traçabilité et de conformité identifiés.

### Conformité des statuts (livrables 005, 006, 010)

- Ajout des champs `Statut : À valider` et `Classification : Loi Fondamentale
  (Immuable)` aux articles `GSIE-CON-005` à `GSIE-CON-010` (en-têtes non
  conformes au cycle de vie).
- Ajout d'en-têtes (édition, version, statut) à `PACT_FOR_AI_AGENTS.md` (005)
  et `GSIE-DESIGN-PHILOSOPHY.md` (006).
- Aucun document `Locked` modifié.

### Traçabilité

- `GSIE-DIR-0004` (GSIE Genesis Directive, ACTIVE) désormais tracée dans
  `PROJECT_MEMORY.md` (racine et `22_`). Elle en était absente.

### RFC

- **RFC-0002** ouvert : « Unification du système d'articles constitutionnels »
  (double système `ARTICLE_0xx` vides / `GSIE-CON-0xx` rédigés). Statut
  *Proposé*, en attente de validation du Fondateur. Aucune suppression exécutée.
- `RFC-0003` à `RFC-0010` : coquilles vides remplacées par des en-têtes
  « Réservé — non ouvert » (traçabilité conservée, aucun RFC supprimé).

### Livrables 011 et 012

- Rédaction des fichiers vides de `17_DOCUMENTATION/` : `WRITING_GUIDELINES.md`,
  `DOCUMENTATION_SYSTEM.md`, `CONTRIBUTING_GUIDE.md`, `ADR_TEMPLATE.md` (Draft).
- `CONTEXT_SNAPSHOT_001.md` : en-tête de réservation ajouté (déclenchement prévu
  à la 10ᵉ Directive — non atteint, snapshot volontairement en attente).

### ROADMAP

- Livrable 010 repointé vers la source réelle (`GSIE-CON-0xx`) avec renvoi au
  RFC-0002.
- Requalification honnête des 14 moteurs (3 fichiers dédiés, 11 README de
  cadrage ; documentation complète = Phase 2).
- Mention des dossiers hors 12 livrables (`18_FINANCING`, `23_QUALITY_MANAGEMENT`)
  et de leur statut de gouvernance à statuer.

### Reste à la main du Fondateur

- Choix d'une option pour RFC-0002 (A / B / C).
- Levée ou confirmation de la réserve sur le `Locked` de `GSIE-CON-000`
  (« LOCKED sous réserve de validation du Fondateur »).
- Rattachement de `18_FINANCING` et `23_QUALITY_MANAGEMENT` aux livrables.

---

## [Outillage] - 2026-07-03

### Configuration Claude Code

- Initialisation du dépôt git + `.gitignore`
- `CLAUDE.md` racine (gouvernance opérationnelle pour les agents IA)
- `.claude/` : `settings.json`, hook `guard-locked` (protection des `Locked`),
  6 commandes métier, 3 sous-agents, skill projet `gsie-governance`
- Skills : installation vendorisée et épinglée de `mermaid` (MIT, commit
  `8ab1815`, provenance tracée) ; création de la skill `skill-management`
- `.claude/SKILLS_GSIE.md` : sélection des meilleures skills (internes,
  officielles et communautaires) par phase

---

## [0.0.1] - 2026-07-01

### Fondation

- Création de l'arborescence officielle (22 dossiers numérotés)
- Création de la Constitution : 6 documents transverses + 100 articles
  vides
- Création des RFC-0001 à RFC-0010 (RFC-0001 rédigée)
- Création des décisions DEC-000001 et DEC-000002
- Création de la Directive fondatrice GSIE-DIR-0001
- Création de la mémoire du projet (6 fichiers dans 22_PROJECT_MEMORY)
- Création des README de chaque dossier
- Création des fichiers racine : README, PROJECT_MEMORY, CHANGELOG,
  ROADMAP

### Décisions

- DEC-000001 : GSIE est une Fondation scientifique
- DEC-000002 : Phase 1 — Fondation, aucun développement métier

## [0.0.2] - 2026-07-01

### Documents fondateurs de la Constitution

- Création de `CONSTITUTIONAL_PREAMBLE.md` — autorité, portée,
  classification des lois (Immuables / Évolutives) et hiérarchie
  documentaire
- Création de `PHILOSOPHICAL_PREAMBLE.md` — vision, valeurs et
  convictions fondatrices
- Création de `ARTICLE_000.md` — Primauté de la Constitution (Loi
  Immutable, ADOPTÉ)

### Évolutions de RFC

- RFC-0001 : passage de BROUILLON à ADOPTÉ
- RFC-0001 : ajout des 4 décisions fondatrices
  - D1 : distinction Préambule constitutionnel / Préambule philosophique
  - D2 : introduction de l'Article 000 « Primauté de la Constitution »
  - D3 : classification des lois (Immuables et Évolutives)
  - D4 : hiérarchie documentaire officielle (Vision → Code)

### Mémoire du projet

- Mise à jour de `PROJECT_MEMORY.md` et `DECISION_HISTORY.md` avec les
  décisions fondatrices de RFC-0001

## [0.0.3] - 2026-07-01

### Lancement officiel Phase 1 Foundation (GSIE-DIR-0003)

- Création de la Directive `GSIE-DIR-0003` (ACTIVE)
- Définition des **12 livrables obligatoires** de la Phase 1
- La **documentation devient le produit principal** de la phase
- Aucun développement métier avant validation des 12 livrables

### Fichiers créés

- `17_DOCUMENTATION/CONTRIBUTING_GUIDE.md` (vide — livrable 011)
- `17_DOCUMENTATION/DOCUMENTATION_SYSTEM.md` (vide — livrable 011)
- `17_DOCUMENTATION/ADR_TEMPLATE.md` (vide — livrable 011)
- `17_DOCUMENTATION/WRITING_GUIDELINES.md` (vide — livrable 011)
- `22_PROJECT_MEMORY/CONTEXT_SNAPSHOT_001.md` (vide — livrable 012)

### Fichiers mis à jour

- `ROADMAP.md` — ajout de la Foundation Roadmap (12 livrables + statuts)
- `PROJECT_MEMORY.md` — entrée sur la documentation comme produit principal
- `22_PROJECT_MEMORY/PROJECT_MEMORY.md` — avancement des 12 livrables
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — 3 nouvelles décisions DIR-0003
- `22_PROJECT_MEMORY/VISION_HISTORY.md` — Vision V1.1
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée Phase 1 Foundation

### Décisions

- DIR-0003-D1 : La documentation devient le cœur du projet
- DIR-0003-D2 : 12 livrables obligatoires, produits dans l'ordre
- DIR-0003-D3 : Aucun développement métier avant validation des 12 livrables

## [0.0.4] - 2026-07-01

### Verrouillage officiel des préambules fondateurs

- Rangement de `GSIE-FND-001.md` (Préambule Philosophique) dans
  `00_CONSTITUTION/` — LOCKED, v1.0, Première Édition
- Rangement de `GSIE-FND-002.md` (Préambule Constitutionnel) dans
  `00_CONSTITUTION/` — LOCKED, v1.0, Première Édition
- Suppression des drafts `PHILOSOPHICAL_PREAMBLE.md` et
  `CONSTITUTIONAL_PREAMBLE.md` (remplacés par les éditions officielles)
- Suppression de `PREAMBLE.md` (vide, hérité de l'ancienne structure)

### Avancement des livrables

- Livrable 002 (Préambule Constitutionnel) : Draft → **Locked**
- Livrable 003 (Préambule Philosophique) : Draft → **Locked**
- Total : 2 Validated, 2 Locked, 8 Draft

### Fichiers mis à jour

- `ROADMAP.md` — statuts 002 et 003 → Locked, avancement global
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — références et
  avancement
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — entrées FND-001, FND-002
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée verrouillage
- `02_RFC/RFC-0001.md` — références aux nouveaux noms de fichiers

## [0.0.5] - 2026-07-01

### Articles constitutionnels officiels

- Rangement de `GSIE-CON-000.md` dans `00_CONSTITUTION/` — La Primauté
  de la Constitution (LOCKED, Loi Fondamentale Immuable, v1.0)
- Rangement de `GSIE-CON-003.md` — La Connaissance avant le Code
  (Draft, à valider)
- Rangement de `GSIE-CON-004.md` — Toute décision doit être explicable
  (Draft, à valider)
- Rangement de `GSIE-CON-005.md` — Toute connaissance doit être
  traçable (Draft, à valider)
- Suppression du draft `ARTICLE_000.md` (remplacé par l'édition
  officielle `GSIE-CON-000.md`)

### Avancement des livrables

- Livrable 004 (Article 000) : Validated → **Locked** (édition officielle)
- Livrable 010 (Articles 001-100) : 3 articles rédigés (003, 004, 005)
  en attente de validation
- Total : 1 Validated, 3 Locked, 8 Draft

### Fichiers mis à jour

- `ROADMAP.md` — livrable 004 → Locked, tableau des articles rédigés
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — références et
  avancement
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — entrées CON-000, 003, 004, 005
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée articles officiels

## [0.0.6] - 2026-07-01

### Articles constitutionnels supplémentaires

- Rangement de `GSIE-CON-006.md` — La Documentation fait partie du
  Produit (Draft)
- Rangement de `GSIE-CON-007.md` — La Modularité est obligatoire (Draft)
- Rangement de `GSIE-CON-008.md` — Le Projet appartient à sa Vision
  (Draft)
- Rangement de `GSIE-CON-009.md` — GSIE est un patrimoine scientifique
  vivant (Draft)
- Rangement de `GSIE-CON-010.md` — Toute connaissance doit pouvoir
  évoluer sans perdre son historique (Draft)

### Documents transverses (livrables 005 et 006)

- Rangement de `PACT_FOR_AI_AGENTS.md` dans `00_CONSTITUTION/` — Pacte
  des Agents IA (a remplacé le fichier vide — livrable 005)
- Rangement de `GSIE-DESIGN-PHILOSOPHY.md` dans `00_CONSTITUTION/` —
  Design Philosophy (a remplacé le `DESIGN_PHILOSOPHY.md` vide —
  livrable 006)

### Documents méthodologiques

- Rangement de `ARCHITECTURE_PRINCIPLES.md` dans `04_ARCHITECTURE/`
- Rangement de `RESEARCH_METHOD.md` dans `06_RESEARCH/`
- Rangement de `KNOWLEDGE_METHOD.md` dans `07_KNOWLEDGE/`

### Avancement des livrables

- Livrable 005 (Pacte IA) : rédigé, à valider
- Livrable 006 (Design Philosophy) : rédigé, à valider
- Livrable 010 (Articles) : 9 articles rédigés (000, 003 à 010)
- Total : 1 Validated, 3 Locked, 8 Draft (dont 2 rédigés à valider)

### Fichiers mis à jour

- `ROADMAP.md` — statuts 005/006, tableau des articles (9 rédigés),
  documents transverses et méthodologiques
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — articles, documents,
  avancement, prochaine étape
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — 11 nouvelles entrées
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée second lot

## [0.0.7] - 2026-07-01

### Documents d'architecture

- Rangement de `GSIE_MASTER_ARCHITECTURE.md` dans `04_ARCHITECTURE/` —
  architecture globale en couches
- Rangement de `GSIE_CORE_BLUEPRINT.md` dans `04_ARCHITECTURE/` —
  blueprint du cœur système (chaîne de moteurs)
- Rangement de `GSIE_DATA_FLOW.md` dans `04_ARCHITECTURE/` — flux
  officiel des données

### Moteurs documentés

- Recréation de `09_ENGINES/KNOWLEDGE_ENGINE/` — README + définition
  (`KNOWLEDGE_ENGINE.md`)
- Recréation de `09_ENGINES/CORRELATION_ENGINE/` — README + définition
  (`CORRELATION_ENGINE.md`)
- Création de `09_ENGINES/EVIDENCE_ENGINE/` — nouveau moteur, README +
  définition (`EVIDENCE_ENGINE.md`)

### Fichiers mis à jour

- `ROADMAP.md` — documents d'architecture et moteurs documentés
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — nouvelles sections
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée architecture et moteurs

## [0.0.8] - 2026-07-02

### Genesis Directive (GSIE-DIR-0004)

- Création de la Directive `GSIE-DIR-0004` (ACTIVE, Priorité ABSOLUE,
  Classification FONDATION) dans `01_DIRECTIVES/ACTIVE/`
- Formalisation de l'identité, du rôle de l'agent, de la méthode de
  travail, des qualités prioritaires, des interdictions et de la
  philosophie modulaire
- Liste officielle des **14 moteurs GSIE**
- Liste officielle des **9 bases spécialisées**
- Décision : conservation de l'arborescence existante (22 dossiers),
  la directive s'intègre sans restructurer

### Articles constitutionnels manquants

- Création de `GSIE-CON-001.md` — Le forestier reste le décideur
  (Draft, Loi Fondamentale Immuable). Toute sortie est contournable,
  explicable, non-contraignante. Interdiction de décision automatique.
- Création de `GSIE-CON-002.md` — La science avant tout (Draft, Loi
  Fondamentale Immuable). Aucune connaissance sans source, niveau de
  preuve, traçabilité et révisabilité.

La Constitution compte désormais **11 articles** (CON-000 à CON-010),
tous rédigés.

### Nouveaux moteurs documentés

- Création de `09_ENGINES/FOREST_DYNAMICS_ENGINE/` — dynamique des
  peuplements (nouveau, DIR-0004)
- Création de `09_ENGINES/LEARNING_ENGINE/` — apprentissage (nouveau,
  DIR-0004, subordonné à CON-001 et CON-004)
- Création de `09_ENGINES/SIMULATION_ENGINE/` — simulation de
  scénarios (nouveau, DIR-0004)

`09_ENGINES/` contient désormais **6 moteurs documentés** sur 14.

### Analyse d'architecture

- 7 points de friction identifiés (contradiction Evidence Engine,
  pipeline linéaire, constitutions vides, absence de contrat
  d'interface, stratégie hors-ligne, README racine non aligné)
- Recommandation : ne pas verrouiller les documents d'architecture
  tant que les contradictions ne sont pas résolues

### Fichiers mis à jour

- `ROADMAP.md` — articles 001 et 002, 3 nouveaux moteurs
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — articles et
  moteurs
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — section 2026-07-02,
  6 nouvelles décisions
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée Genesis Directive

### Décisions

- DIR-0004-D1 : Genesis Directive officielle
- DIR-0004-D2 : Liste officielle des 14 moteurs GSIE
- DIR-0004-D3 : Liste officielle des 9 bases spécialisées
- DIR-0004-D4 : Conservation de l'arborescence existante
- CON-001 : Le forestier reste le décideur
- CON-002 : La science avant tout

## [0.0.9] - 2026-07-02

### Constitutions sectorielles (livrables 007, 008, 009)

- Rédaction de `SCIENTIFIC_CONSTITUTION.md` — 7 articles : sources
  acceptées (5 catégories), 6 niveaux de preuve (A-F), conflits
  bibliographiques, révision par RFC, incertitude explicite, 10
  domaines, patrimoine versionné
- Rédaction de `TECHNICAL_CONSTITUTION.md` — 10 articles : modularité,
  couplage faible, subordination code→connaissance, anti-duplication,
  tests obligatoires, versionnement, gestion d'erreurs, **hors-ligne
  (T-8)**, sécurité, dépendances
- Rédaction de `AI_CONSTITUTION.md` — 8 articles : rôle assistant,
  explicabilité, anti-boîte noire, apprentissage encadré, désaccord
  humain, biais affichés, agents IA soumis aux règles, pas de décision
  automatique

### Résolution de la contradiction Evidence Engine (ARCH-D1)

- `GSIE_DATA_FLOW.md` corrigé : Evidence Engine repositionné **avant**
  Knowledge Graph
- `GSIE_CORE_BLUEPRINT.md` corrigé : Evidence Engine repositionné
  **avant** Knowledge Engine
- Cohérence rétablie entre les 3 documents (Data Flow, Core Blueprint,
  README Evidence Engine)

### 14/14 moteurs documentés (ARCH-D2)

Création des 8 moteurs restants avec README (périmètre, principe,
frontières, position) :
- `REASONING_ENGINE/` — raisonnement sur connaissances
- `DIAGNOSTIC_ENGINE/` — diagnostics stationnels
- `RECOMMENDATION_ENGINE/` — recommandations contournables
- `VALIDATION_ENGINE/` — validation des sorties
- `GIS_ENGINE/` — données géospatiales
- `CLIMATE_ENGINE/` — données climatiques
- `PEDOLOGY_ENGINE/` — données pédologiques
- `BOTANICAL_ENGINE/` — flore et taxonomie

### README racine mis à jour

- Section « État du projet » reflète l'état réel (11 articles, 3
  constitutions sectorielles, 14 moteurs)
- Ajout section « Moteurs GSIE » : tableau des 14 moteurs + chaîne
  principale
- Ajout section « Bases spécialisées » : tableau des 9 bases

### Fichiers mis à jour

- `README.md` — sections moteurs et bases, état du projet
- `ROADMAP.md` — 14 moteurs, livrables 007-009 rédigés
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — constitutions,
  14 moteurs, architecture corrigée
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — 5 nouvelles décisions
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée constitutions +
  résolution Evidence Engine + 14 moteurs

### Décisions

- SCI-CON : Constitution Scientifique (livrable 007)
- TECH-CON : Constitution Technique (livrable 008)
- AI-CON : Constitution IA (livrable 009)
- ARCH-D1 : Evidence Engine repositionné en amont de Knowledge Engine
- ARCH-D2 : 14/14 moteurs officiels documentés
