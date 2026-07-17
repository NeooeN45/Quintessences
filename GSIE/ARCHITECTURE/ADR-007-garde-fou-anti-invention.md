# ADR-007 — Garde-fou transverse anti-invention de données

| Champ | Valeur |
|---|---|
| **ID** | ADR-007 |
| **Statut** | Accepté |
| **Date** | 2026-07-17 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Décision liée** | DEC-000025, RFC-0014 |

## Contexte

RFC-0014 (§3.1) pose un principe transverse : aucun moteur GSIE ne peut
faire circuler une valeur numérique, une corrélation ou une conclusion
sans un `SourceReference` résolvable et un `evidence_level` hérité
d'une donnée réelle. Ce principe est décrit dans la RFC mais n'était
pas encore formalisé comme décision d'architecture opposable, au même
niveau que les ADR régissant le reste du schéma v6.2 (ADR-001 à
ADR-006). Cet ADR comble cet écart.

Le déclencheur concret : le Correlation Engine (livré le 2026-07-17)
fonctionne sur un périmètre volontairement réduit — il accepte des
valeurs numériques fournies directement dans la requête. Rien
n'empêchait techniquement qu'un futur appelant fournisse des valeurs
inventées plutôt que des données réelles. Le premier pilote
d'ingestion documentaire (RFC-0014 §3.6, *Lettre du DSF n°61*) a
confirmé que la vérification automatique de citation est le mécanisme
concret qui rend ce garde-fou opposable, pas seulement déclaratif.

## Décision

**Tout moteur GSIE qui produit, transforme ou fait circuler une valeur
numérique, une corrélation, une classification ou une conclusion doit
pouvoir répondre, pour chaque valeur, aux trois questions suivantes :**

1. **D'où vient cette valeur ?** — un `SourceReference` résolvable
   (Assertion Knowledge Engine, dataset catalogué `GSIE/DATASETS/`, ou
   observation terrain avec provenance).
2. **Quel est son niveau de preuve ?** — un `evidence_level` hérité de
   la source, jamais recalculé à partir de la seule plausibilité
   statistique du résultat (voir RFC-0014 §3.2 — un coefficient de
   corrélation ne détermine pas la crédibilité de sa source).
3. **Cette chaîne est-elle reconstructible après coup ?** — le moteur
   doit exposer un moyen (méthode `explain()` ou équivalent, champs de
   metadata) de retracer la provenance complète d'une conclusion,
   conformément à CON-001 (recommandation explicable et contournable).

Sont **interdits** en production, sur tout moteur de raisonnement
(Correlation, Reasoning, Diagnostic, Recommendation, Forest Dynamics,
Learning, Simulation) :

- Toute valeur par défaut non documentée utilisée comme donnée réelle
- Toute interpolation silencieuse comblant une donnée manquante sans
  le signaler dans les métadonnées de sortie
- Toute sortie de LLM non citée (voir RFC-0014 §3.2/3.3 — le LLM est
  un assistant d'extraction sous contrainte, jamais un oracle)
- Toute promotion automatique d'un pattern statistique détecté
  (Learning Engine) en connaissance validée, sans repasser par
  l'Evidence Engine

## Mise en œuvre

1. **Detection statique (best-effort)** — `tools/check_governance_consistency.py`
   étendu pour signaler les littéraux numériques suspects dans les
   modules `engines/*/engine.py` autres que des constantes de
   classification déjà documentées (ex. seuils Evans 1996 du
   Correlation Engine, qui sont eux-mêmes sourcés en commentaire).
2. **Revue de code obligatoire** — checklist pour toute contribution à
   un moteur de raisonnement : « chaque donnée d'entrée est-elle
   traçable jusqu'à une Assertion sourcée ou un dataset catalogué ? »
3. **Tests contractuels** — tout moteur de raisonnement doit avoir au
   moins un test vérifiant qu'une sortie porte bien un
   `SourceReference`/`evidence_level` valides (voir
   `tests/integration/test_correlation.py` pour le précédent).

## Conséquences

### Positives

- Le principe « aucune fausse donnée » devient une décision
  d'architecture opposable, pas seulement une intention documentée
  dans une RFC.
- Cohérent avec les garanties déjà posées par `CORRELATION_ENGINE.md`
  §6 (sourcé, pas de causalité non justifiée) — cet ADR généralise ces
  garanties à tous les moteurs de raisonnement à venir.

### Négatives

- Ralentit le développement des futurs moteurs (Reasoning, Diagnostic,
  Recommendation) — chaque sortie doit être instrumentée pour la
  traçabilité, ce n'est pas un ajout a posteriori facile.
- La détection statique (point 1) reste best-effort — elle attrape les
  cas évidents, pas une preuve formelle d'absence de donnée inventée.

## Statut de suivi

- 2026-07-17 : Accepté (RFC-0014 / DEC-000025)
- Prochaine étape : étendre `check_governance_consistency.py` (voir
  mise en œuvre point 1)
