# Processus de Revue de Code

| Champ        | Valeur                          |
|--------------|---------------------------------|
| Document     | CODE_REVIEW.md                  |
| Dossier      | 23_QUALITY_MANAGEMENT/PROCESSES |
| Version      | 1.0.0                           |
| Date         | 2 juillet 2026                  |
| Statut       | Adopté                          |
| Référence    | QUALITY_MANUAL.md               |

---

## 1. Objet

Le présent processus définit les règles, responsabilités et étapes de la revue
de code applicables à l'ensemble des contributions au projet GSIE, backend
Python/FastAPI et application Android Kotlin comprises. Son objectif est de
garantir la qualité, la sécurité, la maintenabilité et la cohérence du code
avant toute fusion dans les branches protégées.

---

## 2. Périmètre

Ce processus s'applique à toute Pull Request (PR) ciblant les branches
`main`, `develop` ou `release/*` des dépôts suivants :

- `gsie-backend` (Python / FastAPI)
- `gsie-android` (Kotlin)
- `gsie-knowledge` (moteurs Evidence Engine et Knowledge Engine)
- `gsie-infra` (configuration d'infrastructure et CI/CD)

Aucune fusion ne peut avoir lieu en dehors du cadre décrit ci-après.

---

## 3. Règles générales

| Règle | Description |
|-------|-------------|
| R1 | Toute PR doit être revue par au moins un pair avant fusion. |
| R2 | Le reviewer vérifie les tests, les conventions de codage, la sécurité, la performance et la documentation. |
| R3 | Une PR dont le diff dépasse 400 lignes doit être découpée en PR plus petites. |
| R4 | Les commentaires de revue doivent être constructifs, argumentés et exempts de jugement personnel. |
| R5 | La fusion n'est autorisée que si la CI est verte et que la revue est explicitement approuvée. |
| R6 | L'auteur de la PR ne peut pas approuver ni fusionner sa propre PR. |
| R7 | Toute PR reste ouverte au moins 4 heures ouvrées avant fusion (anti-rush). |

---

## 4. Checklist du reviewer

Le reviewer doit parcourir et valider chaque item de la checklist suivante
avant d'émettre un avis. Une case non cochée doit être justifiée dans le
commentaire de revue.

| # | Item | Critère de validation |
|---|------|-----------------------|
| 1 | Conventions de codage | Respect de PEP 8 / ruff (Python) et ktlint (Kotlin). |
| 2 | Tests nominaux | Les cas nominaux sont couverts par des tests automatisés. |
| 3 | Edge cases | Les cas limites et conditions d'erreur sont testés. |
| 4 | Absence de secret | Aucun token, mot de passe ou clé en clair dans le code. |
| 5 | Dépendances | Aucune dépendance nouvelle non justifiée dans la PR. |
| 6 | Documentation | Docstrings, README et documentation API à jour. |
| 7 | Dette technique | Aucune dette technique introduite sans ticket associé. |
| 8 | Sécurité | Validation des entrées, gestion des erreurs, pas d'injection. |
| 9 | Performance | Pas de régression de performance identifiable en revue. |
| 10 | Lisibilité | Nommage explicite, fonctions courtes, complexité cyclomatique raisonnable. |

---

## 5. Processus de revue

```
1. Création de la PR
       |
2. Assignation d'un reviewer
       |
3. Revue par le reviewer
       |
4. Itération (corrections par l'auteur)
       |
5. Approbation explicite
       |
6. Fusion par le lead dev ou reviewer autorisé
```

### 5.1 Création de la PR

L'auteur crée la PR depuis sa branche `feature/*` ou `hotfix/*` vers la
branche cible. Le modèle de PR doit contenir :

- un résumé des changements ;
- le ticket associé ;
- la liste des tests ajoutés ou modifiés ;
- les éventuels breaking changes.

### 5.2 Assignation d'un reviewer

L'auteur ou le lead dev assigne au moins un reviewer compétent sur le domaine
concerné. Pour les PR touchant à la sécurité ou au Knowledge Graph, deux
reviewers sont requis.

### 5.3 Revue

Le reviewer parcourt le diff, exécute localement les tests si nécessaire et
remplit la checklist de la section 4. Il formule ses commentaires sous forme
de suggestions précises.

### 5.4 Itération

L'auteur répond aux commentaires, corrige le code et pousse les nouveaux
commits. Chaque itération déclenche une nouvelle exécution de la CI.

### 5.5 Approbation

Le reviewer approuve explicitement la PR via l'interface GitHub
(`Approve`). Un commentaire `LGTM` ne constitue pas une approbation.

### 5.6 Fusion

La fusion est effectuée par merge squash vers la branche cible, une fois la CI
verte et l'approbation obtenue. La branche source est supprimée.

---

## 6. Rôles et responsabilités

| Rôle        | Responsabilités |
|-------------|-----------------|
| Auteur      | Rédige le code et les tests, crée la PR, répond aux commentaires, corrige les retours. |
| Reviewer    | Vérifie la qualité selon la checklist, formule des commentaires constructifs, approuve ou demande des modifications. |
| Lead dev    | Arbitre les désaccords, valide les PR sensibles, supervise le respect du processus. |

---

## 7. Métriques

| Métrique               | Définition                                      | Cible       |
|------------------------|-------------------------------------------------|-------------|
| Délai de revue         | Temps moyen entre création et approbation.      | < 24 h      |
| Taux d'approbation     | Part des PR approuvées sans modification.       | 40 - 70 %   |
| Taux de rejet          | Part des PR fermées sans fusion.                | < 10 %      |
| Nombre d'itérations    | Nombre moyen de cycles correction / revue.      | < 2         |

Ces métriques sont collectées mensuellement et présentées lors de la revue
qualité.

---

## 8. Anti-patterns

Les comportements suivants sont proscrits et font l'objet d'un signalement au
lead dev :

| Anti-pattern        | Description |
|---------------------|-------------|
| LGTM sans commentaire | Approbation sans analyse effective du code. |
| Revue de surface    | Lecture du titre et du premier fichier uniquement. |
| Bikeshedding        | Débat prolongé sur des détails mineurs au détriment de la revue fonctionnelle. |
| Revue asymétrique   | Un seul reviewer porte l'ensemble des revues de l'équipe. |
| Commentaire personnel | Critique portant sur l'auteur plutôt que sur le code. |

---

## 9. Références

- `QUALITY_MANUAL.md` -- Manuel qualité du projet GSIE.
- `CI_CD.md` -- Processus d'intégration et de déploiement continus.
- `RELEASE_MANAGEMENT.md` -- Processus de gestion des releases.

---

*Fin du document.*
