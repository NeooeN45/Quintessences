# PROJECT_MEMORY — Vue courante du projet Quintessences

| Champ | Valeur |
|---|---|
| **Écosystème** | Quintessences |
| **Moteur** | GSIE (General System Intelligence Engine) |
| **Phase** | 2 — Architecture |
| **Directive courante** | GSIE-DIR-0003 |
| **Dernière mise à jour** | 2026-07-12 |

---

## État

**Quintessences** est un écosystème d'applications environnementales
fondé sur le moteur **GSIE** (General System Intelligence Engine).
Spécialisations : GeoSylva (forêt), GSIE-FEU (incendie), futures à venir.

Le projet est en **Phase 2 : Architecture**, lancée officiellement par
**DEC-000004** le 2026-07-12. La Phase 1 (Foundation) est **clôturée** —
les 12 livrables sont Validated (9/12) ou Locked (3/12).

La Phase 2 autorise l'architecture détaillée des moteurs, les
spécifications techniques, les RFC d'architecture et le banc de
simulation GSIE-FEU (hors dépôt). Le code métier dans le dépôt
 reste interdit jusqu'en Phase 4.

### Avancement des livrables

- **Validated** : 9 / 12 (001, 005, 006, 007, 008, 009, 010, 011, 012)
- **Locked** : 3 / 12 (002 — Préambule Constitutionnel, 003 — Préambule Philosophique, 004 — Article 000)
- **Draft** : 0 / 12

### Articles constitutionnels rédigés

- `GSIE-CON-000.md` — La Primauté de la Constitution (Locked, Loi Fondamentale Immuable)
- `GSIE-CON-001.md` — Le forestier reste le décideur (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-002.md` — La science avant tout (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-003.md` — La Connaissance avant le Code (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-004.md` — Toute décision doit être explicable (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-005.md` — Toute connaissance doit être traçable (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-006.md` — La Documentation fait partie du Produit (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-007.md` — La Modularité est obligatoire (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-008.md` — Le Projet appartient à sa Vision (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-009.md` — GSIE est un patrimoine scientifique vivant (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-010.md` — Toute connaissance doit pouvoir évoluer sans perdre son historique (Validated, Loi Fondamentale Immuable)

### Documents transverses et méthodologiques rédigés

- `PACT_FOR_AI_AGENTS.md` — Pacte des Agents IA (livrable 005, Validated)
- `GSIE-DESIGN-PHILOSOPHY.md` — Design Philosophy (livrable 006, Validated)
- `SCIENTIFIC_CONSTITUTION.md` — Constitution Scientifique (livrable 007, Validated)
- `TECHNICAL_CONSTITUTION.md` — Constitution Technique (livrable 008, Validated)
- `AI_CONSTITUTION.md` — Constitution IA (livrable 009, Validated)
- `04_ARCHITECTURE/ARCHITECTURE_PRINCIPLES.md` — Architecture Principles
- `06_RESEARCH/RESEARCH_METHOD.md` — GSIE Research Method
- `07_KNOWLEDGE/KNOWLEDGE_METHOD.md` — GSIE Knowledge Method

### Documents d'architecture rédigés

- `04_ARCHITECTURE/GSIE_MASTER_ARCHITECTURE.md` — Architecture globale
- `04_ARCHITECTURE/GSIE_CORE_BLUEPRINT.md` — Blueprint du cœur système (Evidence Engine repositionné en amont)
- `04_ARCHITECTURE/GSIE_DATA_FLOW.md` — Flux de données officiel (Evidence Engine repositionné en amont)

### Branche GSIE-FEU (RFC-0004)

- `22_PROJECT_MEMORY/GSIE-FEU.md` — Registre d'idées vivant (60+ idées, 9
  sections : perception, jumeau numérique, vol drone, communications, GCS,
  données, stratégie, modèles IA, veille concurrentielle). Version 0.7.x.
- `22_PROJECT_MEMORY/GSIE-FEU/` — Livrables du Jalon 0 (comparatifs sourcés).

### Moteurs amorcés (14/14 — profondeur à qualifier)

> 3 moteurs ont un fichier dédié (EVIDENCE, KNOWLEDGE, CORRELATION) ; 11 n'ont
> qu'un README de cadrage. Documentation complète = Phase 2. Détail : `ROADMAP.md`.

- `09_ENGINES/EVIDENCE_ENGINE/` — Evidence Engine (filtre amont)
- `09_ENGINES/KNOWLEDGE_ENGINE/` — Knowledge Engine
- `09_ENGINES/CORRELATION_ENGINE/` — Correlation Engine
- `09_ENGINES/REASONING_ENGINE/` — Reasoning Engine
- `09_ENGINES/DIAGNOSTIC_ENGINE/` — Diagnostic Engine
- `09_ENGINES/RECOMMENDATION_ENGINE/` — Recommendation Engine
- `09_ENGINES/VALIDATION_ENGINE/` — Validation Engine
- `09_ENGINES/GIS_ENGINE/` — GIS Engine
- `09_ENGINES/CLIMATE_ENGINE/` — Climate Engine
- `09_ENGINES/PEDOLOGY_ENGINE/` — Pedology Engine
- `09_ENGINES/BOTANICAL_ENGINE/` — Botanical Engine
- `09_ENGINES/FOREST_DYNAMICS_ENGINE/` — Forest Dynamics Engine
- `09_ENGINES/LEARNING_ENGINE/` — Learning Engine
- `09_ENGINES/SIMULATION_ENGINE/` — Simulation Engine

## RFC ouverts

- **RFC-0003** — Architecture distribuée GSIE-Net (Proposé — 2026-07-07) :
  capture la vision fondateur sur l'architecture offline-first, distribuée,
  multi-couches et orientée données. Activé en Phase 2.
- **RFC-0004** — GSIE-FEU : Système autonome de surveillance et d'analyse
  des incendies (**ADOPTÉ** — 2026-07-12, DEC-000003) : nouvelle branche
  fonctionnelle dédiée au risque incendie, positionnée comme application
  cliente de GSIE. Registre d'idées dans `22_PROJECT_MEMORY/GSIE-FEU.md` ;
  livrables Jalon 0 dans `22_PROJECT_MEMORY/GSIE-FEU/`. Aucun développement
  métier en Phase 1. Voir `02_RFC/RFC-0004.md`.

---

## Décisions actives

- **DEC-000001** — GSIE est une Fondation scientifique
- **DEC-000002** — Phase 1 : Fondation, aucun développement métier
- **RFC-0001-D1** — Distinction Préambule constitutionnel / philosophique
- **RFC-0001-D2** — Article 000 « Primauté de la Constitution »
- **RFC-0001-D3** — Classification des lois (Immuables / Évolutives)
- **RFC-0001-D4** — Hiérarchie documentaire officielle (Vision → Code)
- **DIR-0003-D1** — La documentation devient le cœur du projet
- **DIR-0003-D2** — 12 livrables obligatoires, produits dans l'ordre
- **DIR-0003-D3** — Aucun développement métier avant validation des 12 livrables
- **DEC-000003** — Adoption RFC-0004 : branche fonctionnelle GSIE-FEU (application cliente)
- **DEC-000004** — Entrée en Phase 2 : Architecture (Phase 1 clôturée)
- **DEC-000005** — Amendement DEC-000003/000004 : archivage du code du banc GSIE-FEU (Jalon 0)
- **DEC-000006** — Restructuration identité : Quintessences (écosystème) > GSIE (moteur) > GeoSylva (app forestière)

## Documents structurants

- **GSIE-DIR-0001** — Directive fondatrice (ACTIVE)
- **GSIE-DIR-0003** — Lancement officiel Phase 1 Foundation (ACTIVE)
- **GSIE-DIR-0004** — GSIE Genesis Directive (ACTIVE)
- **RFC-0001** — Méthodologie de rédaction de la Constitution (ADOPTÉ)
- **RFC-0002** — Unification du système d'articles constitutionnels (Proposé, en attente de validation du Fondateur)
- **RFC-0003** — Architecture distribuée GSIE-Net (Proposé)
- **RFC-0004** — Branche fonctionnelle GSIE-FEU (ADOPTÉ — DEC-000003)
- **RFC-0005 à RFC-0010** — Réservés, non ouverts

## Documents fondateurs de la Constitution

- `GSIE-FND-002.md` — Préambule Constitutionnel (Locked — livrable 002)
- `GSIE-FND-001.md` — Préambule Philosophique (Locked — livrable 003)
- `GSIE-CON-000.md` — La Primauté de la Constitution (Locked — livrable 004)

## Vision courante

**Quintessences** = écosystème d'intelligence environnementale (marque
umbrella). **GSIE** = General System Intelligence Engine, le moteur
spécialisable par domaine. **GeoSylva** = app forestière (première
spécialisation). La connaissance est le véritable produit.

**Durant la Phase 1**, la documentation est le produit principal. Le
code viendra en son temps, subordonné aux fondations.

## Prochaine étape

**Phase 1 CLÔTURÉE** — tous les livrables sont Validated (9/12) ou
Locked (3/12). Le projet peut entrer en Phase 2 (Architecture) après
décision du Fondateur (DEC à tracer).

> La mémoire détaillée vit dans `22_PROJECT_MEMORY/`.
> La roadmap complète des 12 livrables vit dans `ROADMAP.md`.
