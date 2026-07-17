# ADR-003 — Benchmark Apache AGE : stratégie d'évaluation

| Champ | Valeur |
|---|---|
| **ID** | ADR-003 |
| **Statut** | Accepté |
| **Date** | 2026-07-15 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Décision liée** | DEC-000022, RFC-0011 |

## Contexte

Le métamodèle v6.1 retient PostgreSQL 16 comme vérité canonique. Les
requêtes de traversée de graphe (toutes les assertions liées à
`Quercus robur`, puis les assertions liées à leurs participants, etc.)
peuvent nécessiter un moteur de graphe pour les traversées profondes
(multi-sauts).

Le livrable 309 (supersédé) prescrivait Neo4j. La v6.1 diffère Neo4j et
évalue **Apache AGE** (extension PostgreSQL qui ajoute Cypher natif à
PG) comme alternative. AGE est déjà installé dans l'environnement
actuel (migration 0001 crée l'extension + un graphe
`gsie_knowledge_graph`), mais **aucune requête Cypher n'existe dans le
code** — AGE est inerte.

L'arbitrage Fondateur (T2) : **benchmark dès Vague 1**, décision basée
sur des données réelles, pas sur des hypothèses.

## Options envisagées

1. **AGE uniquement** — utiliser Apache AGE pour toutes les traversées
  de graphe. Avantage : un seul service (PG), pas de Neo4j. Inconvénient
  : maturité d'AGE non prouvée à l'échelle (million d'assertions).

2. **Neo4j uniquement** — réintroduire Neo4j comme dans le livrable 309.
  Avantage : graphe natif mature, écosystème riche. Inconvénient :
  service supplémentaire, synchronisation PG↔Neo4j, complexité
  opérationnelle.

3. **SQL pur (jointures récursives)** — pas de graphe, uniquement des
  CTE récursives PostgreSQL. Avantage : zéro dépendance. Inconvénient :
  performances dégradées sur traversées profondes (3+ sauts).

4. **Benchmark AGE puis décision** — évaluer AGE sur données réelles en
  Vague 1, avec seuils mesurés. Si AGE passe : option 1. Si AGE ne passe
  pas : option 2 (Neo4j) ou option 3 (SQL pur selon le seuil).

## Décision

**Option 4 : benchmark AGE puis décision.**

### Protocole de benchmark (Vague 1)

1. **Données** : charger 100 000 assertions + 300 000 participants +
   50 000 entités (échelle réduite mais représentative).
2. **Requêtes test** :
   - Traversée 1 saut : toutes les assertions liées à une entité
   - Traversée 2 sauts : assertions liées aux entités liées
   - Traversée 3 sauts : traversée profonde
   - Recherche par claim_kind + lifecycle_status + spatial_scope
3. **Seuils** :
   - Traversée 1 saut : < 100ms (P95)
   - Traversée 2 sauts : < 500ms (P95)
   - Traversée 3 sauts : < 2000ms (P95)
4. **Comparaison** : exécuter les mêmes requêtes en SQL pur (CTE
   récursives) et en AGE (Cypher).
5. **Décision** :
   - Si AGE passe tous les seuils → AGE adopté
   - Si AGE échoue sur 3 sauts mais SQL pur passe → SQL pur
   - Si aucun ne passe → Neo4j réintroduit

### Implémentation du benchmark

- Script Python avec `asyncpg` + `age` (driver AGE)
- Données générées à partir des seeds Essence 360° (chêne sessile,
  hêtre, pin maritime, douglas, sapin pectiné)
- Mesures P50/P95/P99 sur 1000 exécutions par requête

## Conséquences

- **Positives** : décision empirique, pas hypothétique. Évite
  l'introduction prématurée de Neo4j (YAGNI) tout en gardant la porte
  ouverte.
- **Négatives** : délai de décision (Vague 1). Si AGE ne passe pas,
  réintroduction de Neo4j ajoute de la complexité en cours de Vague 1.
- **Mitigation** : le benchmark est planifié en début de Vague 1. La
  décision est prise avant la fin de la Vague 1, laissant le temps
  d'ajuster si Neo4j est nécessaire.

## Statut de suivi

- 2026-07-15 : Proposé (RFC-0011 / DEC-000022)
- Vague 1 (début) : exécution du benchmark
- Vague 1 (mi-parcours) : décision AGE vs Neo4j vs SQL pur

## Validation (2026-07-17)

ADR-003 accepté par le Fondateur, conformément à DEC-000022 (§ « Adopte
les 6 ADR-001 à ADR-006 »), déjà Validated depuis le 2026-07-16. Le
benchmark AGE reste à exécuter en Vague 1 — l'acceptation porte sur la
stratégie d'évaluation, pas sur un résultat déjà obtenu.
