# CLAUDE.md — GSIE (GeoSylva Intelligence Engine)

> Guide opérationnel pour tout agent IA (Claude Code) travaillant sur ce dépôt.
> Ce fichier ne remplace pas la Constitution — il la sert. En cas de conflit,
> la Constitution (`00_CONSTITUTION/`) prime toujours.

---

## 1. Ce qu'est GSIE (en une phrase)

GSIE est une **fondation scientifique** dont le produit principal est un
**moteur d'intelligence forestière** modulaire, traçable et explicable — **pas
une application**. Les applications ne sont que des clients du moteur.

**Phase actuelle : Phase 1 — Foundation.** Le **produit est la documentation**.
**Aucun développement métier / code applicatif** n'est autorisé tant que les
12 livrables de la Phase 1 ne sont pas validés. Voir `ROADMAP.md`.

---

## 2. Règles non négociables (à lire avant toute action)

1. **La Constitution prime.** Rien de ce que tu produis ne peut contredire
   `00_CONSTITUTION/`. Article fondateur : `GSIE-CON-000` (Primauté).
2. **Ne modifie JAMAIS un document `Locked`** (voir statuts §5). Un `Locked`
   ne change **que** par un RFC dédié dans `02_RFC/`. Ceci inclut :
   `GSIE-FND-001`, `GSIE-FND-002`, `GSIE-CON-000`.
3. **Pas de code métier en Phase 1.** Ne crée aucun moteur exécutable, API,
   SDK ou application. Si on te le demande, signale que la Phase 1 l'interdit
   et propose la documentation correspondante à la place.
4. **Tout en français.** Documentation, commentaires, titres, commits.
5. **La connaissance avant le code ; la science avant l'opinion.** Toute
   affirmation scientifique doit être **sourçable** et **traçable**.
6. **L'IA assiste, ne décide jamais.** Le forestier reste le décideur
   (`GSIE-CON-001`). Les recommandations sont explicables et contournables.
7. **Aucune décision perdue.** Toute décision structurante est tracée
   (voir §4 traçabilité). Mets à jour la mémoire quand tu changes l'état.

---

## 3. Hiérarchie documentaire (le code est toujours le dernier niveau)

```
Vision → Constitution → RFC → Directive → Decision
→ Architecture → Specification → Implementation → Code
```

Ne saute jamais un niveau. Une Architecture ne contredit pas une Décision ;
une Décision ne contredit pas la Constitution.

---

## 4. Arborescence & traçabilité

Dossiers numérotés `00_` à `23_`. Chaque dossier possède un `README.md` qui
définit son objectif, ce qui est autorisé et ce qui est interdit — **lis-le
avant d'ajouter un fichier** dans un dossier.

| Dossier | Rôle |
|---|---|
| `00_CONSTITUTION/` | Principes intangibles, garde-fous (prime sur tout) |
| `01_DIRECTIVES/` | Directives fondatrices (`ACTIVE` / `ARCHIVED`) |
| `02_RFC/` | Propositions d'évolution débattues |
| `03_DECISIONS/` | Décisions tracées et validées |
| `04_ARCHITECTURE/` | Architecture logicielle et scientifique |
| `05_SPECIFICATIONS/` | Exigences fonctionnelles / non fonctionnelles |
| `06_RESEARCH/` | Travaux scientifiques, bibliographie sourcée |
| `07_KNOWLEDGE/` | Base de connaissances structurée |
| `08_DATASETS/` | Jeux de données référencés et sourcés |
| `09_ENGINES/` | 14 moteurs (documentés en Phase 1, non implémentés) |
| `10_ALGORITHMS/` → `16_TOOLS/` | Algorithmes, modèles, apps, API, SDK, tests, outils |
| `17_DOCUMENTATION/` | Documentation officielle et guides contributeurs |
| `18_FINANCING/` → `21_EXPERIMENTS/` | Financement, légal, partenariats, prototypes |
| `22_PROJECT_MEMORY/` | Mémoire détaillée du projet |
| `23_QUALITY_MANAGEMENT/` | Qualité : manuel, politique, KPI, audits, revues |

**Identifiants tracés** (préfixes) :
`GSIE-FND-xxx` (fondateurs), `GSIE-CON-xxx` (articles constitutionnels),
`GSIE-DIR-xxxx` (directives), `RFC-xxxx` (propositions),
`DEC-xxxxxx` (décisions), `GSIE-PROMPT-xxxx` (prompts de pilotage versionnés).

> Note : les articles constitutionnels ont pour identifiant `GSIE-CON-0xx`
> mais peuvent être portés par des fichiers `ARTICLE_0xx.md`. Vérifie
> toujours l'en-tête du fichier pour l'identifiant et le statut réels.

---

## 5. Cycle de vie d'un document (statuts)

| Statut | Signification | Peux-tu l'éditer librement ? |
|---|---|---|
| `Draft` | Créé, contenu en cours | Oui |
| `Review` | Rédigé, en attente de validation du fondateur | Oui, avec prudence |
| `Validated` | Validé par le fondateur | Non sans raison tracée |
| `Locked` | Verrouillé | **Non — uniquement via RFC** |

Un livrable ne passe en `Review` que si le précédent est au minimum en
`Review` (ordre imposé, `ROADMAP.md`).

---

## 6. Flux de travail attendu de l'agent

1. **Comprendre avant d'agir.** Lis le `README.md` du dossier concerné, puis
   les documents parents dans la hiérarchie (§3).
2. **Respecter le statut** du document cible (§5) avant toute modification.
3. **Rédiger** en français, factuel, sourcé, sans jargon inutile.
4. **Tracer.** Si tu prends/actes une décision structurante, crée/mets à jour
   l'entrée correspondante (`03_DECISIONS/`, `22_PROJECT_MEMORY/`).
5. **Synchroniser la mémoire.** Après un changement d'état du projet, mets à
   jour `PROJECT_MEMORY.md`, `ROADMAP.md` et `CHANGELOG.md` si pertinent.
6. **Ne pas élargir le périmètre.** En cas de doute (nouveau code, doc
   verrouillée, contradiction constitutionnelle), **arrête-toi et signale-le**
   plutôt que de contourner une règle.

---

## 7. Fichiers racine de référence

| Fichier | Rôle | Quand le consulter |
|---|---|---|
| `README.md` | Présentation, moteurs, bases, gouvernance | Vue d'ensemble |
| `PROJECT_MEMORY.md` | État courant, livrables, décisions actives | Avant toute tâche |
| `ROADMAP.md` | 12 livrables Phase 1 + phases suivantes | Pour situer une tâche |
| `CHANGELOG.md` | Journal des évolutions | Après un changement |

---

## 7bis. Skills & outillage Claude Code

- Skill projet **`gsie-governance`** (`.claude/skills/`) : auto-déclenchée dès
  qu'on touche un document GSIE ; impose la gouvernance. Prioritaire.
- Commandes : `/rfc`, `/decision`, `/article`, `/engine-doc`, `/sync-memory`,
  `/constitution-audit`. Sous-agents : `constitution-guardian`, `doc-redactor`,
  `memory-keeper`.
- Sélection des meilleures skills externes par phase : voir
  `.claude/SKILLS_GSIE.md`. En Phase 1, aucune skill ne doit produire de code métier.

## 8. Style & conventions

- **Markdown** propre : titres hiérarchisés, tables pour les listes de faits,
  blocs de code pour les schémas de flux.
- **Ton** : sobre, scientifique, sans emphase commerciale.
- **Références de fichiers** : chemins relatifs depuis la racine du dépôt.
- **Pas de dépendances externes non sourcées** dans la doc scientifique.
- **Sources** : toute donnée écologique/pédologique/climatique doit citer sa
  source (`06_RESEARCH/`, `08_DATASETS/`).

---

## 9. Les 14 moteurs (documentés, non implémentés en Phase 1)

Chaîne principale :

```
Evidence → Knowledge → Correlation → Reasoning → Diagnostic
→ Recommendation → Validation → Utilisateur
```

Moteurs domaine (alimentent le raisonnement) : GIS, Climate, Pedology,
Botanical, Forest Dynamics. Moteurs transverses : Learning, Simulation.
Chaque moteur = **une responsabilité unique**, documenté dans
`09_ENGINES/<NOM>_ENGINE/`.

---

## 10. Rappel final

> GSIE — la connaissance est le véritable produit. Le code n'est qu'un moyen.
> En cas de doute entre « avancer vite » et « respecter la gouvernance »,
> **choisis toujours la gouvernance.**
