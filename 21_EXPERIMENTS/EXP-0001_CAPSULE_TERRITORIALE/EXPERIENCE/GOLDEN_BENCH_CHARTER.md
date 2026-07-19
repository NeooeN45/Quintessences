# Charte du Golden Bench scientifique

## Finalité

Le Golden Bench empêche qu'une optimisation, une migration de langage ou une
évolution de modèle modifie silencieusement les résultats scientifiques. Il
ne décrète pas qu'une formule est vraie : il conserve des cas dont la
justification, les limites et la revue sont explicites.

## Deux gates séparés

1. **Gate numérique** — le code retourne la valeur attendue dans la tolérance
   fixée. Cette gate est automatisable.
2. **Gate scientifique** — la méthode, les données et la tolérance ont été
   examinées par des experts compétents et indépendants. Cette gate est
   humaine, datée et révisable.

Un cas peut donc réussir numériquement tout en restant interdit pour une
décision professionnelle.

## Champs obligatoires d'un cas

| Champ | Rôle |
|---|---|
| `case_id` | identifiant stable et unique |
| `title` | formulation compréhensible par le métier |
| `algorithm` / `algorithm_version` | implémentation évaluée |
| `inputs` | valeurs avec unités explicites |
| `expected.value` / `expected.unit` | résultat de référence |
| `expected.absolute_tolerance` | écart maximal admis |
| `provenance.sources` | références vérifiables ou origine synthétique |
| `applicability` | domaine et limites d'emploi |
| `scientific_review.status` | état réel de validation |
| `scientific_review.reviewers` | identité et date des relecteurs |

## États de revue

| État | Sens | Usage autorisé |
|---|---|---|
| `draft` | cas incomplet | développement local uniquement |
| `needs_domain_review` | calcul reproductible, expertise manquante | CI expérimentale, aucune décision |
| `reviewed` | une revue métier documentée | préproduction |
| `approved` | double revue et décision de gouvernance | référence de production |
| `deprecated` | remplacé, conservé pour l'historique | compatibilité seulement |

Le passage à `reviewed` ou `approved` ne doit jamais être effectué par un
agent IA seul.

## Règles de qualité

- Les valeurs attendues ne sont jamais générées par le même code que celui
  testé sans contre-calcul indépendant.
- Une tolérance est justifiée par la méthode, pas choisie pour faire passer le
  test.
- Les unités sont obligatoires et les conversions sont testées séparément.
- NaN, infini, valeurs négatives impossibles et entrées vides sont refusés.
- Les cas limites accompagnent les cas nominaux.
- Les données réelles ne sont ajoutées qu'avec licence, provenance,
  anonymisation et autorisation de redistribution vérifiées.
- Un LLM peut aider à préparer un cas, jamais en être l'oracle scientifique.

## Promotion vers le Golden Bench de production

1. data card complète ;
2. sources primaires archivées ou identifiées durablement ;
3. contre-calcul indépendant ;
4. revue par l'expert de domaine ;
5. revue par un second expert ;
6. validation de gouvernance ;
7. fixture figée, versionnée et signée ;
8. tests contractuels Python, Kotlin et C++ si le calcul existe sur ces trois
   plateformes.

