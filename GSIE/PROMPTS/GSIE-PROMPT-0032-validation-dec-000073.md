# GSIE-PROMPT-0032 — Enregistrer la validation avec mise à jour de DEC-000073

| Champ | Valeur |
|---|---|
| Statut | EN_REVUE |
| Agent principal | Codex |
| Environnement | Workspace partagé, worktree documentaire isolé |
| Dépôt | NeooeN45/Quintessences |
| Branche | docs/gsie-prompt-0032-validation-dec-000073 |
| Commit de départ | 9e6864b353c8c03d15c067dffd2b358f7a57d94f — feat/schemas-de-domaine |
| Date | 2026-11-15 |
| Orchestrateur | Codex |
| Relecteur attendu | Architecte-relecteur Claude ; arbitrage final du Fondateur |
| Autorité de la décision enregistrée | Camille Perraudeau (Fondateur) |
| Priorité | Gouvernance préalable à la poursuite GeoSylva |

## 1. Mission reçue

Le Fondateur a tranché DEC-000073 le 15 novembre 2026 : **« validée avec
mise à jour »**. Enregistrer les quatre éléments suivants :

1. Valider les principes : intention mobile ; règles, qualifications et état
   global uniquement serveur ; refus `AUCUNE_REGLE_QUALIFIEE` et
   `ETAT_GLOBAL_NON_SOURCE` sans repli ; UUID stationnel GSIE lié explicitement,
   révocable et contrôlé par compte ; figement par le `RapportPreparation`.
2. Retenir la façade existante `POST /api/v1/geosylva/analyses`, avec suivi et
   résultat asynchrones, en remplacement du chemin proposé par RFC-0041 §3.1.
3. Maintenir `station-link` de RFC-0041 §4.3 parmi les éléments à construire.
4. Limiter le lancement aux métiers technicien forestier et conducteur de
   travaux forestiers ; geler tout chantier hors GeoSylva jusqu'à sa sortie.

## 2. Livrables et périmètre autorisé

- Créer [DEC-000093](../../03_DECISIONS/DEC-000093.md), complément de DEC-000073
  sans réécrire cette dernière.
- Mettre à jour RFC-0041, encore Draft, en conservant la proposition initiale
  et en séparant exigences validées et état du code.
- Inscrire cette mission dans `REGISTER.md`.
- Produire le [rapport de revue](../../23_QUALITY_MANAGEMENT/AUDITS/AUDIT_DEC_000073_2026-11-15.md),
  les références fichier/ligne et une proposition de synchronisation des trois
  vues canoniques `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md`.

La synchronisation est **proposée**, non appliquée dans cette mission. Le
diff est limité à cinq documents Markdown. La présence du code sur la branche
de départ sert à la relecture ; elle n'est pas une modification de code de ce lot.

## 3. Documents obligatoires

- `AGENTS.md`, `00_CONSTITUTION/README.md`, `PACT_FOR_AI_AGENTS.md` et
  `GSIE-CON-000`, `GSIE-CON-001`, `GSIE-CON-002`, `GSIE-CON-004`, `GSIE-CON-005`.
- `03_DECISIONS/README.md`, DEC-000073, RFC-0041 et ADR-009.
- `GSIE/PROMPTS/README.md`, `REGISTER.md`, `TEMPLATE_TASK.md`.
- `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`.
- Sources du BFF, de la préparation, du worker et des contrats concernés au
  commit de départ, uniquement en lecture.

## 4. Vérification des identifiants

L'inventaire du 15 novembre couvre les **35 branches distantes**, leurs SHA,
les fichiers numérotés et les variantes du registre, ainsi que les deux branches
locales préexistantes. Les maxima observés sont 000092 pour les décisions,
0042 pour les RFC et 0031 pour les prompts. Les identifiants retenus sont donc
**DEC-000093** et **GSIE-PROMPT-0032**. Aucune nouvelle RFC n'est créée.
Le détail de l'inventaire figure dans le rapport de revue.

## 5. Interdictions et conditions d'arrêt

- Aucun changement de code, contrat exécutable, test, SQL ou migration ;
  aucune installation de dépendance ni aucun déploiement.
- Aucun document Locked modifié ; DEC-000073 reste identique au snapshot.
- Aucune donnée, règle, qualification, preuve ou validation manquante inventée.
- Ne pas présenter l'adaptation du chemin comme une homologation du DTO entier.
- Ne pas pousser sur `main`, fusionner ni publier implicitement le résultat.
- Suspendre l'édition en cas de collision d'identifiants ou de changements locaux
  inconnus ; réexaminer le numéro si une branche distante a réservé le même ID.

La production des documents, de la branche dédiée et du commit local est
autorisée par la mission. Toute suite technique est une mission distincte.

## 6. Méthode et acceptation

1. Vérifier les références distantes et les numéros sur toutes les branches.
2. Créer un worktree dédié depuis le snapshot portant le BFF.
3. Lire le trajet des données, de la requête jusqu'à la préparation et au résultat.
4. Enregistrer la décision du Fondateur et les écarts sans auto-homologation.
5. Exécuter `python3 tools/check_governance_consistency.py` et examiner le diff.
6. Vérifier l'absence de modification de DEC-000073, de documents Locked, du code
   et des trois fichiers canoniques dont la synchronisation est seulement proposée.
7. Remettre branche, commit, cinq fichiers, écarts fichier/ligne et résultat du contrôle.

## 7. État de remise

La décision du Fondateur est enregistrée comme validée ; la mission et les
propositions de synchronisation sont remises **EN_REVUE**. Cela ne constitue
ni une fusion ni une acceptation indépendante du rapport de Codex.
