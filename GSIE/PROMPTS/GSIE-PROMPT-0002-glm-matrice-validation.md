# GSIE-PROMPT-0002 — Matrice de validation des trois dépôts

| Champ | Valeur |
|---|---|
| Statut | BLOQUÉE — snapshot à rendre accessible |
| Agent cible | GLM 5.2 |
| Environnement | Devin |
| Dépôts | Quintessences, GeoSylva, Forge |
| Branche | `fix/enterprise-reliability-2026-07-21` |
| Commits de départ | À renseigner avant attribution |
| Orchestrateur | Codex |
| Relecteur | Codex |
| Priorité | P0 |

## Mission

Reproduire la matrice de validation du jalon de fiabilité dans un environnement
propre. Ne corrige aucun échec. Mesure exactement les tests passés, échoués et
ignorés, les avertissements, la couverture et les artefacts construits.

## Précondition bloquante

Les changements doivent être accessibles par trois SHA identifiés. Si un dépôt
est sale, si la branche manque ou si les changements du jalon sont absents,
arrête avec `BLOQUÉE`.

## Documents obligatoires

- `AGENTS.md`
- `PROJECT_MEMORY.md`
- `02_RFC/RFC-0021-fiabilite-entreprise.md`
- `02_RFC/RFC-0022-orchestration-agents-ia.md`
- les trois fichiers `.github/workflows/ci.yml`
- les README de l'API GSIE, de GeoSylva et de Forge.

## Interdictions et règles d'exécution

- Utiliser les versions et lockfiles du dépôt.
- Ne pas mettre à jour de dépendance.
- Ne pas modifier les sources ou les tests.
- Ne pas masquer un échec par un filtre supplémentaire.
- Conserver les logs et les rapports de test comme artefacts Devin.
- Ne pas afficher les valeurs des secrets.
- Ne pas committer, pousser, fusionner ou déployer.

## Matrice GSIE

Depuis `GSIE/API`, reproduire les jobs définis par le workflow courant, puis
au minimum :

```bash
uv lock --check
uv sync --locked --extra dev
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy --strict src
uv run pytest
docker compose config --quiet
sh -n docker/entrypoint.sh
docker compose build api
```

Distinguer explicitement les tests unitaires des tests d'intégration
dépendants de Docker. Ne présenter aucun test ignoré comme réussi.

## Matrice GeoSylva

Depuis le dépôt GeoSylva :

```bash
./gradlew --no-daemon testDebugUnitTest lintDebug
./gradlew --no-daemon assembleDebug
```

Extraire les nombres de suites, tests, échecs, erreurs Lint et avertissements.
Vérifier que les rapports XML/HTML sont produits. Ne lancer aucun test
instrumenté nécessitant un appareil si l'environnement n'en fournit pas ;
le signaler comme non vérifié.

## Matrice Forge

Depuis le dépôt Forge :

```bash
uv lock --check
uv sync --locked --extra dev
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy --strict src
uv run pytest --cov=dataset_forge --cov-report=term-missing --cov-fail-under=80
docker compose config --quiet
docker compose build
```

Signaler séparément les avertissements provenant de l'environnement et ceux
provenant du projet.

## Contrôles transverses

```bash
git diff --check
```

Dans Quintessences, exécuter également :

```bash
uv run --project GSIE/API python tools/check_source_of_truth.py
uv run --project GSIE/API python -m unittest discover -s tools/tests
```

Analyser syntaxiquement les trois workflows YAML sans les modifier.

## Critères d'acceptation

- Toutes les commandes requises ont un code de sortie consigné.
- Aucun test en échec.
- Ruff et mypy strict sans erreur sur les deux projets Python.
- Android Lint sans erreur.
- Couverture Forge au moins égale à 80 %.
- Builds Docker et Android réussis, ou limite d'environnement démontrée.
- Registre documentaire conforme.
- Aucun diff produit par l'exécution, hors artefacts ignorés.

## Rapport obligatoire

Produire une table :

| Dépôt | SHA | Commande | Durée | Code | Réussis | Échoués | Ignorés | Avertissements | Artefact |
|---|---|---|---|---|---|---|---|---|---|

Ajouter :

- versions Java, Python, uv, Docker et Gradle ;
- fichiers modifiés ou générés par les commandes ;
- limites de l'environnement ;
- liens vers les logs et rapports ;
- verdict `EN_REVUE`, `BLOQUÉE` ou `REJETÉE`.

Ne corrige rien : tout échec doit revenir à Codex pour diagnostic et nouvelle
tâche bornée.
