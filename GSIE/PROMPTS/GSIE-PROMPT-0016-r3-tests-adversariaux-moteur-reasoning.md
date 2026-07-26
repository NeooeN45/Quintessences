# GSIE-PROMPT-0016 — R3 — Tests adversariaux du moteur Reasoning

| Champ | Valeur |
|---|---|
| Statut | VALIDÉE — tranche 1 close, 54 tests unitaires verts |
| Agent cible | SWE 1.7 |
| Environnement | Devin |
| Dépôt | Quintessences |
| Branche | `fix/enterprise-reliability-2026-07-21` |
| Fichiers possédés | `GSIE/API/tests/unit/test_reasoning_engine.py` |
| Résultat | 18 tests ; 8 défauts trouvés, aucun corrigé par l'agent |
| Orchestrateur | Architecte |
| Relecteur | Architecte puis Fondateur |
| Standard applicable | `23_QUALITY_MANAGEMENT/PROCESSES/CODE_QUALITY_STANDARD.md` |

## Mission

Chercher où le moteur produit une sortie fausse, non traçable ou non
reproductible. Interdiction explicite de corriger `engine.py` : tout défaut est
livré sous forme de test rouge et de motif.

Couverture : déterminisme sur dix exécutions et sous permutation des entrées,
exactitude des prémisses, cohérence du plancher de preuve, bornes de profondeur,
non-bouclage sur règles circulaires, contradictions déclarées, robustesse aux
variables absentes.

Mission la plus productive de la tranche : huit défauts trouvés dans du code
qu'elle n'avait pas écrit, dont deux bloquants. L'interdiction de corriger a
tenu.

## Documents obligatoires

1. `AGENTS.md`
2. `23_QUALITY_MANAGEMENT/PROCESSES/CODE_QUALITY_STANDARD.md`
3. `GSIE/ENGINES/REASONING_ENGINE/REASONING_ENGINE.md` (§5 contrat, §6 garanties)
4. `GSIE/API/src/gsie_api/engines/reasoning/schemas.py`
5. `GSIE/ARCHITECTURE/ADR-009-garde-fou-anti-invention.md`
6. `00_CONSTITUTION/GSIE-CON-002.md` et `GSIE-CON-004.md`

## Périmètre v1

Les règles d'inférence sont portées par la requête, chacune avec sa
`SourceReference` et son `evidence_level`, sur le précédent assumé du
Correlation Engine. Le branchement sur le Knowledge Engine se fera sans rupture
de contrat.

## Interdictions

- aucune modification d'un fichier hors du périmètre possédé — quatre agents
  travaillent en parallèle sur des fichiers disjoints ;
- aucune modification de `schemas.py`, propriété de l'Architecte : un invariant
  de type est une décision d'architecture ;
- aucune valeur numérique métier sans source citée (`ADR-009`) ;
- aucun test désactivé, marqué `skip` ou `xfail` pour faire passer la suite ;
- aucune assertion affaiblie pour accommoder une implémentation ;
- aucun commit, push, fusion ou déploiement ;
- l'agent qui trouve un défaut chez un autre ne le corrige pas : il livre un
  test rouge et le motif.

## Commandes de validation

```text
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src --strict
python -m pytest tests/unit -q
python tools/check_governance_consistency.py
```

Chaque commande est rapportée avec son code de sortie réel.

## Format du rapport

1. fichiers créés ou modifiés ;
2. ce que fait le code, en cinq lignes ;
3. les cinq commandes avec leurs codes de sortie ;
4. tests écrits : combien, et ce qu'ils rendent impossible ;
5. décisions prises faute de spécification ;
6. ce qui n'a pas pu être vérifié — section obligatoire ;
7. risques résiduels.

La recommandation de l'agent n'est pas une acceptation.
