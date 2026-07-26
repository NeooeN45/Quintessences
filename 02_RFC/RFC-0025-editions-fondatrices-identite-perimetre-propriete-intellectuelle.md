# RFC-0025 — Éditions fondatrices d'identité, de périmètre et de propriété intellectuelle

| Champ | Valeur |
|---|---|
| **ID** | RFC-0025 |
| **Statut** | Brouillon — textes cibles absents, adoption interdite |
| **Auteur** | Direction technique, sous autorité du Fondateur |
| **Date** | 2026-07-24 |
| **Décision liée** | `DEC-000033` — orientation uniquement, aucune adoption |
| **RFC d'origine** | `RFC-0023` |
| **Périmètre** | Vision, identité, champ environnemental et propriété intellectuelle |
| **Nature** | Enveloppe de révision constitutionnelle |

## 1. Objet

La présente RFC est l'unique véhicule prévu pour porter les textes cibles
complets résultant de `RFC-0023`.

Elle existe afin qu'aucune décision d'adoption ni publication d'un document
`Locked` ne puisse reposer sur une intention générale dépourvue du texte
exact, de son diff et de son contre-audit.

Cette version est une **enveloppe procédurale**. Elle ne contient pas encore
les éditions cibles et ne peut donc pas être présentée pour adoption.

## 2. Autorité et absence d'effet normatif

`DEC-000033` autorise la correction des RFC de cadrage et fixe l'orientation
du bloc fondateur. Elle n'adopte aucun texte de la présente RFC.

Tant que les critères de clôture ne sont pas remplis :

- `VISION.md` ne peut pas être créée comme source canonique ;
- aucun document constitutionnel ou `Locked` ne peut être modifié ;
- aucune politique de licence finale ne peut être appliquée ;
- les éditions constitutionnelles en vigueur restent pleinement applicables.

## 3. Corpus cible minimal

La version présentable au contre-audit doit contenir le texte complet et le
diff vérifiable de chaque nouvelle édition suivante :

| Document cible | Révision attendue | État |
|---|---|---|
| `VISION.md` | Mission, ambition, périmètre et engagements durables | À rédiger |
| `GSIE-FND-001` | Identité, ambition, champ environnemental et déclaration fondatrice | À rédiger |
| `GSIE-FND-002` | Définition officielle de GSIE et champ d'application | À rédiger |
| `GSIE-CON-000` | Bloc fondateur, identité et primauté de la Constitution en cas de conflit | À rédiger |
| `GSIE-CON-008` | Vision multi-domaines et politique de propriété intellectuelle | À rédiger |
| `GSIE-CON-009` | Ouverture, reproductibilité scientifique et licence par composant | À rédiger |
| `SCIENTIFIC_CONSTITUTION.md` | Ouverture scientifique et licence logicielle | À rédiger |

Un balayage complet du corpus constitutionnel doit confirmer cette liste
avant contre-audit. Tout autre texte contradictoire est ajouté au périmètre ou
fait l'objet d'une justification explicite.

## 4. Règle de rang de la Vision

Les textes cibles doivent appliquer `DEC-000033` :

- Vision et Constitution dans le même bloc fondateur ;
- autorité de registre égale à `100` ;
- Constitution prioritaire en cas de contradiction ;
- revue annuelle limitée à un contrôle de fraîcheur ;
- toute modification de sens soumise à RFC, contre-audit, décision du
  Fondateur, nouvelle édition et conservation de l'édition antérieure.

## 5. Livrables obligatoires

Avant tout changement de statut, cette RFC doit inclure :

1. les textes cibles complets dans des annexes versionnées ;
2. un diff lisible entre chaque édition en vigueur et chaque édition cible ;
3. une matrice de propagation vers le registre, la mémoire, la roadmap, le
   changelog, les README, la licence et les documents juridiques ;
4. une analyse de compatibilité constitutionnelle, scientifique, juridique
   et technique ;
5. les contrôles automatiques empêchant le retour des anciennes définitions
   dans les chemins actifs, sans invalider les archives ;
6. les empreintes cryptographiques des textes soumis au Fondateur.

## 6. Séquence obligatoire

1. rédiger et relire toutes les annexes ;
2. exécuter les contrôles documentaires ;
3. réaliser un contre-audit indépendant ;
4. reproduire les preuves par Codex ;
5. corriger tout P0 et traiter les P1 ;
6. présenter au Fondateur les versions et empreintes exactes ;
7. créer une décision d'adoption explicite ;
8. conserver les éditions antérieures ;
9. publier atomiquement le bloc fondateur et ses dépendances ;
10. réaliser une revue indépendante du diff publié.

## 7. Critères de passage à `Proposé`

La RFC reste `Brouillon` tant que :

- une annexe cible manque ;
- un diff n'est pas reproductible ;
- une contradiction active n'est pas couverte ou justifiée ;
- les conséquences de licence et de protection des données ne sont pas
  qualifiées ;
- les contrôles automatiques ne sont pas définis.

Le passage à `Proposé` ne vaut ni adoption ni autorisation de modifier un
document `Locked`.

## 8. Critère de clôture

Cette enveloppe est prête pour contre-audit lorsque chaque ligne du corpus
cible est complète, versionnée, diffable et accompagnée de ses impacts.
