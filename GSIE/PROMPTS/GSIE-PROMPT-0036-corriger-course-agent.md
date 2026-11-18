# GSIE-PROMPT-0036 — Corriger la course de création d'Agent

| Champ | Valeur |
|---|---|
| Statut | EN_REVUE |
| Agent cible | Codex |
| Environnement | Codex Cloud |
| Dépôt | NeooeN45/Quintessences |
| Branche | `fix/agent-identite-concurrente-2026-11-18` |
| Commit de départ | `47be2044e1af9082a47dc1ad2d673fd16080f592` |
| Date | 2026-11-18 |
| Orchestrateur | Codex |
| Relecteur | Agent indépendant, puis Fondateur |
| Priorité | P1 |

## Mission

Rendre sûre la création de l'Agent dans `RecommendationEngine._agent` lorsque
plusieurs analyses écrivent simultanément. Publier le correctif et ses preuves
dans une demande de fusion dédiée. L'inventaire des 40 branches distantes et
des références locales a trouvé `0035` comme dernier identifiant attribué.

## Pourquoi maintenant

La réconciliation de la PR nº 74 est intégrée à `main`. Le bilan du 16 novembre
rapporte 2 erreurs sur 96 analyses concurrentes (`23505`,
`ix_resource_gsie_id`). Les 96 succès du prototype ne couvrent pas les deux
incohérences révélées par les sondes d'identité du §7.2.

## Documents obligatoires

1. `AGENTS.md`, `PROJECT_MEMORY.md`, `ROADMAP.md` et `GSIE/API/AGENTS.md`.
2. `GSIE/API/README.md` et `GSIE/ENGINES/RECOMMENDATION_ENGINE/README.md`.
3. Le [bilan de la PR nº 74, §7.2](../../23_QUALITY_MANAGEMENT/AUDITS/LEVEE_BLOCAGES_PR74_2026-11-16.md#72-course-ix_resource_gsie_id).
4. `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`,
   `GSIE/PROMPTS/TEMPLATE_TASK.md` et `GSIE/PROMPTS/REGISTER.md`.
5. Le moteur de recommandation, les modèles `ResourceModel` et `AgentModel`,
   les fixtures de concurrence et les workflows GitHub applicables.

## Périmètre autorisé

- `GSIE/API/src/gsie_api/engines/recommendation/engine.py` pour la création
  d'Agent et les erreurs associées.
- `GSIE/API/tests/integration/` pour `harnais_f.py`, le plan de campagne,
  le point d'entrée pytest, les sondes d'identité et la mesure de verrouillage.
- `GSIE/API/tests/unit/` pour les tests ciblés de ce comportement.
- `GSIE/API/tests/mutation/harnais.py` et `.github/workflows/ci.yml` pour la
  mutation et le raccordement nécessaire à la CI existante.
- Le présent prompt, son registre, le rapport de preuve et la traçabilité
  locale de ce changement dans `PROJECT_MEMORY.md`, `ROADMAP.md` et
  `CHANGELOG.md`.

## Non-objectifs

- Modifier la génération des recommandations ou les règles scientifiques.
- Modifier les contrats d'identité ou imposer l'immuabilité du nom de l'Agent.
- Reprendre les autres chantiers de la PR nº 74 ou déployer le serveur.

## Interdictions

- Aucun document `Locked` modifié et aucune donnée réelle touchée.
- Aucun secret ni donnée personnelle dans les preuves.
- Aucune nouvelle tentative automatique, aucun test affaibli et aucun échec
  supprimé d'un bilan.
- Aucun push sur `main`, aucune fusion, aucune réécriture d'historique distant.
- Aucune publication hors de la branche dédiée, de sa demande de fusion et de
  la référence de sauvegarde distante datée.

## Conditions d'arrêt

- Dépôt ou base de départ incompatibles avec la mission, ou changements locaux
  inconnus dans la zone à modifier.
- Campagne ne pouvant être exécutée qu'en modifiant une base existante,
  production ou contenant des données réelles.
- Correctif nécessitant une migration destructive ou un élargissement de
  périmètre.

Le travail indépendant reste autorisé si une preuve ne peut être exécutée.
Le rapport distingue les preuves du 16 novembre des nouvelles mesures et
qualifie la provenance du harnais versionné si les originaux sont indisponibles.

## Méthode attendue

1. Vérifier `main`, préparer le harnais et son plan borné. Exécuter l'analyse
   concurrente sur PostgreSQL avec les moteurs réels, des transactions et
   sessions indépendantes et une barrière juste avant l'insertion racine.
2. Exécuter les tests de régression avant toute modification du moteur et
   conserver leur échec. Relever analyses, succès, échecs et SQLSTATE sur la
   campagne initiale. Les deux sondes d'identité doivent pouvoir échouer
   indépendamment de la fréquence de la course.
3. Insérer la ligne racine avec `ON CONFLICT DO NOTHING` sans cible. Effectuer
   une nouvelle lecture du tuple UUID, type `agent` et `gsie_id` attendu avant
   l'insertion de l'enfant. Vérifier le type de l'enfant après son insertion.
   Signaler explicitement une incohérence sans mettre à jour ni aliaser
   l'identité existante.
4. Mesurer, avec des transactions PostgreSQL indépendantes et une durée
   bornée, si un changement concurrent reste possible avant le commit. Justifier
   le verrou retenu ou son absence, puis vérifier le comportement des lectures
   concurrentes de l'Agent déjà présent.
5. Garder chaque sonde en test, enregistrer la mutation correspondante dans
   le harnais existant et vérifier sa détection.
6. Relancer la même campagne sur une base de test initialement équivalente.
   Vérifier la persistance et l'unicité après les commits, puis lire le diff
   complet.
7. Créer la demande de fusion distincte et relever les résultats CI par job
   sur le hash publié. Pousser une sauvegarde distante datée et vérifier que
   chaque référence publiée pointe au hash attendu.

## Validations obligatoires

Depuis la racine du dépôt :

```text
python3 tools/check_ai_prompts.py
python3 tools/check_governance_consistency.py
python3 tools/check_source_of_truth.py
python3 tools/check_build_consistency.py
git diff --check
```

Depuis `GSIE/API`, avec le verrou de dépendances du dépôt :

```text
uv run ruff check src tests
uv run mypy src/gsie_api
uv run pytest tests/unit -q --no-cov
uv run pytest tests/integration -q
uv run python tests/mutation/harnais.py
```

Consigner les commandes ciblées du test rouge, des campagnes avant et après et
de la mesure SQL, avec les codes de sortie et les limites d'environnement.
Relever les résultats réels des jobs de la CI GitHub, y compris les jobs ignorés
ou bloqués, ainsi que leur SHA.

## Critères d'acceptation

- Un tiers peut reproduire la preuve à partir du plan et des tests versionnés.
- Une preuve rouge sur la base de départ précède la modification du moteur.
- Le scénario historique de 96 analyses par variante est mesuré, tous les
  résultats sont comptés et le nœud d'intégration valide la persistance.
- Un `gsie_id` pris par un UUID différent et une racine d'un autre type sont
  refusés explicitement sans création d'enfant incohérent ni altération de
  l'existant. Un enfant de type inattendu est également refusé.
- La stabilité des données lues jusqu'au commit est justifiée par la mesure.
- Les tests détectent la mutation ajoutée sans desserrer les contrôles CI.
- Le hash, la demande de fusion distincte, les résultats CI et la référence
  distante datée sont vérifiables.

## Rapport obligatoire

Remettre le snapshot de départ, le résumé, les fichiers, les commandes et les
codes de sortie, la campagne avant et après avec nombres d'analyses et d'échecs,
la preuve de verrouillage, la CI job par job, la référence de sauvegarde et la
demande de fusion. Signaler les vérifications impossibles, les risques
résiduels et le retour arrière. Recommander `EN_REVUE`, `BLOQUÉE` ou `REJETÉE`
pour la revue indépendante, sans auto-approbation.
