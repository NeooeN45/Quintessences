# Rapport de validation locale — EXP-0001

| Champ | Valeur |
|---|---|
| **Date** | 2026-07-18 |
| **Environnement** | Python 3.12.13, Linux, environnement virtuel isolé |
| **Dépendance cryptographique** | cryptography 46.0.0 |
| **Statut** | Démonstration locale réussie |
| **Portée** | code expérimental, pas validation scientifique |

## Résultats exécutés

| Contrôle | Commande | Résultat |
|---|---|---|
| Installation éditable | `python -m pip install -e ".[dev]"` | succès |
| Lint | `python -m ruff check src tests` | succès |
| Format | `python -m ruff format --check src tests` | succès, 9 fichiers conformes |
| Typage strict | `python -m mypy src --strict` | succès, 6 fichiers conformes |
| Compilation Python | `python -m compileall -q src tests` | succès |
| Tests unitaires | `python -m unittest discover -s tests -v` | 15/15 réussis |
| Démonstration E2E | `make demo` | succès |
| Cas numériques | intégré à `make demo` | 3/3 dans la tolérance |
| Vérification capsule | intégré à `make demo` | signature valide, 4 fichiers vérifiés |
| Syntaxe JSON | chargement strict de tous les `.json` | succès |
| Contrats JSON Schema | Draft 2020-12 + documents générés | manifeste et signature conformes |
| Syntaxe workflow CI | chargement YAML | succès |
| Espaces de fin / patch | `git diff --check` | succès |
| Recherche basique de secrets | motifs CI du dépôt | aucun motif détecté |

## Scénarios de rejet couverts

- payload modifié après signature ;
- vérification avec une clé publique non approuvée ;
- chemin ZIP contenant `../` ;
- membre ZIP dupliqué ;
- capsule expirée ;
- remplacement silencieux d'une paire de clés ;
- clé privée placée dans le payload ;
- diamètre négatif ;
- régression numérique hors tolérance ;
- cas déclaré revu sans relecteur ;
- cas déclaré approuvé sans deux relecteurs.

## Résultat de la démonstration

```text
DÉMONSTRATION GSIE : SUCCÈS
Signature            : valid
Fichiers vérifiés    : 4
Golden Bench         : 3/3
Revues en attente    : 3
```

Le dernier indicateur est volontaire : la réussite logicielle ne transforme
pas les fixtures en références scientifiques.

## Validations non exécutées localement

- workflow GitHub Actions complet ;
- tests API, PostGIS, Redis, Rust et Docker du dépôt principal, non affectés
  directement par l'expérience mais à rejouer en CI ;
- tests sur Android, réseau interrompu et stockage presque plein ;
- revue cryptographique indépendante ;
- revue scientifique par deux experts.

## Conclusion

EXP-0001 atteint son objectif de preuve locale reproductible. Sa promotion
reste bloquée par les gates explicitement listées dans DEC-000028, ADR-008,
`SECURITY.md` et `GOLDEN_BENCH_CHARTER.md`.
