# GSIE-PROMPT-0033 — Réconcilier les branches serveur de Quintessences

| Champ | Valeur |
|---|---|
| Statut | EN_COURS |
| Agent principal | Codex |
| Environnement | Workspace partagé, worktree d'intégration isolé |
| Dépôt | NeooeN45/Quintessences |
| Branche | integration/reconciliation-serveur-2026-11 |
| Commit de départ | 9e6864b353c8c03d15c067dffd2b358f7a57d94f |
| Branche de départ | feat/schemas-de-domaine |
| Date | 2026-11-16 |
| Orchestrateur | Codex |
| Relecteurs | Architecte et QA indépendants ; architecte-relecteur Claude |
| Autorité finale | Camille Perraudeau (Fondateur) |

## Mission

Réconcilier `feat/schemas-de-domaine`, puis `main`, puis
`chore/securite-depots-2026-10-18` sur la seule branche d'intégration.
Résoudre les conflits sans perdre les tests ni les données, obtenir une seule
tête Alembic et remettre une demande de fusion vers `main`, sans la fusionner.

## Pourquoi maintenant

L'architecte a identifié quatre conflits Git et une collision de création de
`field_intake` entre deux lignées issues de `20260815_0050`. L'essai local a été
annulé. Au démarrage de cette mission, la PR nº 73 reste ouverte et non fusionnée :
ses cinq documents ne sont pas intégrés implicitement à la branche de départ.

L'inventaire du 16 novembre couvre 41 références locales et distantes ; le
plus grand identifiant de prompt observé est 0032. Le numéro 0033 est réservé
ici sans renuméroter les missions déjà publiées.

## Documents obligatoires

- `AGENTS.md`, `GSIE/API/AGENTS.md`, `GSIE/API/README.md`.
- `00_CONSTITUTION/README.md`, `PACT_FOR_AI_AGENTS.md`, les articles applicables
  et ADR-009 : préserver les données et ne rien inventer.
- `GSIE/PROMPTS/README.md`, `TEMPLATE_TASK.md`, `REGISTER.md`.
- `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`.
- Les skills `consortium-agents`, `git-flow-gsie`, `postgresql-postgis`,
  `tests-gsie` et les contrats applicables de migration et d'intake.
- Les migrations, modèles, consommateurs et tests des trois snapshots.

## Périmètre autorisé

- Fusionner `main` au SHA `d7b400cb15d9f2216f3296d92754a6e67e55a63f`.
- Résoudre les conflits d'OpenAPI, du registre des modèles, du contrat de
  migration et des tests de couverture des routeurs ; conserver les assertions.
- Régénérer `GSIE/API/docs/openapi.json` par
  `GSIE/API/scripts/extract_openapi.py`.
- Comparer les deux définitions de `field_intake`, leurs usages et leur
  historique ; tester une solution explicite pour chaque lignée existante.
- Fusionner ensuite la branche sécurité au SHA
  `e3e18d47cfae176077473962d910e0df30125cc3`.
- Ajouter les tests nécessaires à la conservation des données et du contrat.
- Refaire les revues `etat_projet` et `directives_actives` du registre des
  sources de vérité, en documentant les éléments réellement examinés.
- Rédiger un bilan de résolution et proposer la synchronisation des trois vues
  canoniques ; leur réécriture n'est pas déduite de cette proposition.
- Publier la branche d'intégration, une PR de relecture et une sauvegarde datée.

## Non-objectifs

- Fusionner la PR nº 73 ou copier ses documents sans décision explicite.
- Corriger les écarts métier E01 à E06 ou ajouter une fonctionnalité serveur.
- Migrer une base utilisateur, publier un service ou déployer en production.
- Modifier une règle scientifique, inventer une donnée ou valider une livraison.

## Interdictions

- Aucun push sur `main`, aucune fusion de PR, aucun contournement de protection.
- Aucune réécriture de l'historique Git.
- Aucun test supprimé, ignoré ou affaibli pour obtenir un passage vert.
- Aucun document Locked modifié.
- Aucune suppression de migration sans expliquer le sort des bases déjà migrées.
- Aucune connexion implicite à une base réelle ; les essais utilisent des bases
  jetables identifiées et isolées.
- Aucun secret, fichier personnel ou sortie de build ajouté au dépôt source.

## Conditions d'arrêt

Signaler une colonne ou une règle impossible à déterminer, une perte de données
requise ou des changements locaux inconnus. Suspendre l'action concernée sans
inventer de conversion ; poursuivre les autres travaux indépendants autorisés.

## Méthode attendue

1. Confirmer les SHA, l'absence de fusion de la PR nº 73 et la numérotation.
2. Faire analyser les migrations et les risques par un architecte en lecture seule.
3. Fusionner et résoudre par petits lots sur la branche d'intégration.
4. Comparer les colonnes, types, contraintes, index et consommateurs d'intake.
5. Vérifier la lignée neuve et les deux lignées historiques sur des bases isolées.
6. Exécuter les tests sans affaiblissement et la revue indépendante du diff.
7. Remettre les preuves, les limites, la procédure locale et la sauvegarde distante.

## Validations obligatoires

```text
python3 tools/check_governance_consistency.py
python3 tools/check_source_of_truth.py
python3 tools/check_ai_prompts.py
python3 tools/check_build_consistency.py
alembic heads
python -m pytest tests/ -q
```

Les commandes API sont exécutées depuis `GSIE/API` dans l'environnement Python
préparé. Les résultats, les variantes de commande nécessaires, les codes de
sortie et les éventuels tests non exécutés restent explicites dans le bilan.

## Critères d'acceptation

- Les deux fusions sont traçables sans réécriture d'historique ni push sur `main`.
- Les quatre conflits ont une résolution motivée et OpenAPI est régénéré.
- Une seule tête Alembic est observée ; les deux schémas sont comparés colonne
  par colonne et le sort de chaque base existante est documenté et testé.
- Tous les tests existants et leurs assertions sont conservés.
- Les quatre contrôles ont des résultats explicites, avec preuves de revue.
- La PR, les résultats CI par job et la sauvegarde datée sont remis au Fondateur.

## Rapport obligatoire

Remettre la branche, le commit, la PR et les SHA d'origine ; la résolution de
chaque conflit ; la comparaison d'intake et la décision de migration ; la sortie
`alembic heads` ; les tests et quatre contrôles avec codes de sortie ; les
résultats CI par job ; les risques résiduels et la procédure de reprise locale.
La proposition de synchronisation de `PROJECT_MEMORY.md`, `ROADMAP.md` et
`CHANGELOG.md` reste distincte des faits vérifiés. Indiquer la sauvegarde datée
et son SHA relu sur GitHub. Remettre en revue sans auto-approbation ni fusion.
