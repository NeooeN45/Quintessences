# Processus d'Intégration et de Déploiement Continus

| Champ        | Valeur                          |
|--------------|---------------------------------|
| Document     | CI_CD.md                        |
| Dossier      | 23_QUALITY_MANAGEMENT/PROCESSES |
| Version      | 1.0.0                           |
| Date         | 2 juillet 2026                  |
| Statut       | Adopté                          |
| Référence    | QUALITY_MANUAL.md               |

---

## 1. Objet

Le présent processus définit le pipeline d'intégration continue et de
déploiement continu (CI/CD) du projet GSIE. Il garantit que tout changement
de code est automatiquement vérifié, construit et déployable dans des
conditions reproductibles, sur l'ensemble des composants : backend
Python/FastAPI, application Android Kotlin et moteurs de connaissance.

---

## 2. Périmètre

Le processus s'applique à tous les dépôts du projet GSIE et à toutes les
branches actives. Il couvre l'exécution des pipelines depuis le push d'un
commit jusqu'à la production d'un artefact déployable.

---

## 3. Pipeline obligatoire

Tout push sur une branche déclenche le pipeline suivant. Aucune étape ne peut
être sautée sans dérogation explicite du lead dev.

```
Push
  |
  +--> 1. Lint          (ruff pour Python, ktlint pour Kotlin)
  |
  +--> 2. Typecheck      (mypy pour Python, tsc si applicable)
  |
  +--> 3. Tests unitaires
  |
  +--> 4. Tests d'intégration
  |
  +--> 5. Build          (packaging Wheel / APK / AAB)
  |
  +--> 6. Artefact       (publication vers registre ou stockage signé)
```

| Étape                | Outil               | Seuil de réussite |
|----------------------|---------------------|-------------------|
| Lint                 | ruff, ktlint        | 0 erreur           |
| Typecheck            | mypy --strict       | 0 erreur           |
| Tests unitaires      | pytest, JUnit       | 100 % des tests passent |
| Tests d'intégration  | pytest, emulator    | 100 % des tests passent |
| Build                | build, gradle       | Artefact produit    |
| Artefact             | GitHub Artifacts    | Upload réussi       |

---

## 4. Règles

| Règle | Description |
|-------|-------------|
| R1 | Aucun PR ne peut être fusionné si la CI est rouge. |
| R2 | La couverture de tests doit être >= 80 % sur le code de domaine et >= 60 % globale. |
| R3 | L'analyse SonarQube ne doit signaler aucun bug critique ni aucune vulnérabilité bloquante. |
| R4 | Le build doit être reproductible : même commit, même artefact (hash vérifié). |
| R5 | Tout échec de pipeline doit être traité en priorité par l'auteur du commit. |
| R6 | Les pipelines doivent s'exécuter en moins de 20 minutes en conditions nominales. |

---

## 5. Configuration GitHub Actions

### 5.1 Structure des workflows

```
.github/workflows/
├── ci.yml          # Pipeline complet sur push et PR
├── release.yml     # Build, tag et publication sur fusion vers main
```

### 5.2 Workflow `ci.yml`

Le workflow `ci.yml` s'exécute sur tout push et sur toute PR ciblant
`develop` ou `main`. Il contient les jobs suivants :

| Job                | Runs-on          | Dépend de |
|--------------------|------------------|-----------|
| lint               | ubuntu-latest    | -         |
| typecheck          | ubuntu-latest    | lint      |
| unit-tests         | ubuntu-latest    | typecheck |
| integration-tests  | ubuntu-latest    | unit-tests|
| sonarqube          | ubuntu-latest    | unit-tests|
| build              | ubuntu-latest    | integration-tests, sonarqube |

Chaque job utilise un cache des dépendances pour réduire la durée
d'exécution. Les jobs s'exécutent en parallèle lorsque les dépendances le
permettent.

### 5.3 Workflow `release.yml`

Le workflow `release.yml` s'exécute sur fusion vers `main`. Il construit
l'artefact final, génère le tag Git, publie le changelog et déploie vers
l'environnement cible selon le type de release.

---

## 6. Environnements

| Environnement | Branche source | Déclenchement             | Accès |
|---------------|----------------|---------------------------|-------|
| dev           | develop        | Push sur develop          | Équipe de développement |
| staging       | release/*      | Création branche release  | Équipe + QA |
| prod          | main           | Tag de release            | Restreint, approbation requise |

Le passage vers `prod` requiert une approbation manuelle dans GitHub
Environments. Aucun déploiement automatique vers la production n'est autorisé.

---

## 7. Gestion des secrets

| Règle | Description |
|-------|-------------|
| S1 | Les secrets sont stockés exclusivement dans GitHub Secrets ou un gestionnaire externe (Vault). |
| S2 | Aucun secret n'apparaît en clair dans le code, les logs ou les fichiers de configuration versionnés. |
| S3 | Les variables d'environnement sont injectées au moment de l'exécution du pipeline. |
| S4 | Les secrets de production sont isolés des secrets de développement. |
| S5 | Les tokens et clés sont rotés au moins une fois par trimestre. |

Les références dans les workflows utilisent la syntaxe
`${{ secrets.NOM_DU_SECRET }}`. Les logs sont automatiquement masqués par
GitHub Actions pour les valeurs sensibles.

---

## 8. Métriques

| Métrique                 | Définition                                        | Cible       |
|--------------------------|---------------------------------------------------|-------------|
| Durée du pipeline        | Temps moyen d'exécution du pipeline complet.      | < 20 min    |
| Taux de succès           | Part des exécutions de pipeline en succès.        | > 95 %      |
| Fréquence de déploiement | Nombre de déploiements vers staging par semaine.  | >= 3        |
| Délai de restauration    | Temps moyen entre échec CI et pipeline vert.      | < 1 h       |
| Couverture               | Couverture de tests mesurée par job unit-tests.   | >= 60 %     |

Ces métriques sont collectées automatiquement par GitHub Insights et
présentées lors de la revue qualité mensuelle.

---

## 9. Gestion des échecs

En cas d'échec du pipeline, la procédure suivante s'applique :

1. L'auteur du commit reçoit une notification automatique.
2. L'auteur consulte les logs et identifie l'étape en échec.
3. L'auteur corrige le problème et pousse un nouveau commit.
4. Le pipeline est relancé automatiquement.
5. Si l'échec persiste au-delà de 2 heures, le lead dev est notifié.
6. Aucune fusion ne peut contourner un échec de CI.

---

## 10. Références

- `QUALITY_MANUAL.md` -- Manuel qualité du projet GSIE.
- `CODE_REVIEW.md` -- Processus de revue de code.
- `RELEASE_MANAGEMENT.md` -- Processus de gestion des releases.

---

*Fin du document.*
