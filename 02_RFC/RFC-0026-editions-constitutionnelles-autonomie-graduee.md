# RFC-0026 — Éditions constitutionnelles de l'autonomie graduée

| Champ | Valeur |
|---|---|
| **Statut** | Brouillon dormant — preuves et textes cibles absents |
| **Auteur** | Direction technique, sous autorité du Fondateur |
| **Date** | 2026-07-24 |
| **Décision liée** | `DEC-000033` — orientation uniquement, aucune autonomie R3-R5 autorisée |
| **RFC d'origine** | `RFC-0024` |
| **Périmètre** | Autorité humaine, explicabilité et autonomie graduée |
| **Nature** | Enveloppe de révision constitutionnelle conditionnelle |

## 1. Objet

La présente RFC est le véhicule réservé aux éventuels textes
constitutionnels cibles résultant du programme de recherche `RFC-0024`.

Elle est **dormante** : sa création assure la traçabilité de la future
procédure, mais n'autorise ni expérimentation R3 en usage réel, ni autonomie
R3, R4 ou R5, ni modification d'un document `Locked`.

## 2. Condition préalable de réveil

La rédaction des textes cibles ne commence qu'après :

1. démonstration des critères de preuve et de sécurité définis par
   `RFC-0024` ;
2. validation indépendante des jeux d'évaluation ;
3. qualification des erreurs graves et des limites de domaine ;
4. revue métier, scientifique, sécurité et juridique ;
5. décision explicite du Fondateur autorisant uniquement la préparation des
   textes constitutionnels cibles.

À défaut, les Constitutions en vigueur restent intégralement applicables.

## 3. Corpus cible minimal

Lorsque la condition de réveil est satisfaite, la RFC doit contenir le texte
complet et le diff vérifiable des éditions suivantes :

| Document cible | Révision envisagée | État |
|---|---|---|
| `GSIE-CON-001` | Autorité humaine, délégation bornée et interdictions selon le risque | Dormant |
| `GSIE-CON-004` | Justification externe reproductible sans affaiblissement de l'explicabilité | Dormant |
| `AI_CONSTITUTION.md` | Préambule, IA-1 à IA-5, IA-8, anti-lois et déclaration finale | Dormant |
| `GSIE-FND-001` | Absence d'autorité scientifique autonome de l'IA | Dormant |

Un balayage complet du corpus constitutionnel doit confirmer ou étendre cette
liste avant contre-audit.

## 4. Formulation cible minimale pour `GSIE-CON-004`

La future édition doit remplacer l'exigence « la chaîne de raisonnement,
étape par étape » par une exigence de **justification externe reproductible**
conforme à `RFC-0024` §11.

Cette évolution ne peut supprimer ni affaiblir :

- les cinq questions fondamentales ;
- les données et leur provenance ;
- les règles, coefficients et versions de modèles ;
- les calculs et outils déterminants ;
- les hypothèses, alternatives et contraintes ;
- les incertitudes et limites ;
- le lien vérifiable entre les sources mobilisées et la conclusion ;
- la possibilité humaine de contester et corriger la sortie.

## 5. Livrables obligatoires

Avant tout passage à `Proposé`, cette RFC doit inclure :

1. les textes cibles complets dans des annexes versionnées ;
2. les diffs avec les éditions en vigueur ;
3. les preuves scientifiques et de sécurité justifiant chaque modification ;
4. une matrice capacité → classe R0-R5 → responsable → garde-fous ;
5. les procédures de suspension, retour arrière et reprise humaine ;
6. les contrôles de cohérence entre sources, justification et conclusion ;
7. les empreintes cryptographiques des textes soumis au Fondateur.

## 6. Séquence obligatoire

1. satisfaire la condition de réveil ;
2. rédiger les textes et diffs complets ;
3. réaliser un contre-audit scientifique, métier, sécurité, juridique et
   constitutionnel ;
4. reproduire les preuves par Codex ;
5. corriger tout P0 et traiter les P1 ;
6. présenter au Fondateur les capacités, versions et empreintes exactes ;
7. créer une décision limitée au périmètre explicitement adopté ;
8. conserver les éditions antérieures ;
9. publier atomiquement les nouvelles éditions et leurs dépendances ;
10. surveiller les critères d'arrêt et préparer le retour arrière.

## 7. Interdictions

Cette enveloppe ne peut jamais être utilisée pour :

- autoriser une autonomie générale ;
- contourner la validation humaine de R4 ou R5 ;
- commander un drone ou un système physique ;
- publier une connaissance scientifique canonique automatiquement ;
- présenter un prototype comme système certifié ;
- modifier un document `Locked` avant adoption explicite de son texte exact.

## 8. Critère de clôture

La RFC n'est présentable au contre-audit que lorsque les preuves préalables,
les textes cibles, leurs diffs et les garde-fous sont tous complets et
reproductibles.
