# TRANCHE_VERTICALE — Chaîne complète GSIE sur données réelles

> **Décision** : DEC-000043 (S2 — Tranche verticale réelle)
> **Date** : 2026-08-02
> **Statut** : Validé — chaîne complète exécutée avec succès

## 1. Objectif

Prouver que la chaîne complète GSIE fonctionne de bout en bout sur un
cas forestier réel, avec des données sourcées et traçables. Cette
tranche verticale est le deuxième livrable de la phase de stabilisation
(DEC-000043).

## 2. Scénario forestier

**Station** : sol acide (pH 4.8) avec engorgement hivernal, profondeur 70 cm.

**Question** : Quelles essences (Quercus robur vs Quercus petraea) sont
adaptées à cette station acide avec engorgement hivernal ?

**Objectif forestier** : production.

**Règles appliquées** (2) :
1. `regle-acidite-quercus` : pH < 5.5 → Q. petraea préférable à Q. robur
   sur sol acide profond
2. `regle-engorgement-quercus` : engorgement hivernal → Q. robur plus
   tolérant à l'engorgement racinaire que Q. petraea

## 3. Données réelles sourcées

### Source 1 : Parelle et al. (2007)

> Parelle J., Brendel O., Jolivet Y. (2007), « Intra- and interspecific
> diversity in the response to waterlogging of two co-occurring white
> oak species (Quercus robur and Q. petraea) », Annals of Forest
> Science, hal-02653679.

29 faits vérifiés (citation retrouvée mot pour mot) sur 31 extraits.
Persistés dans
`GSIE/KNOWLEDGE/pilotes_extraction/parelle_2007_quercus_waterlogging_facts.json`.

Clés GBIF (vérifiées le 2026-07-19) :
- *Quercus petraea* (Matt.) Liebl. : 2880130
- *Quercus robur* L. : 2878688

### Source 2 : Référentiel pédologique français (INRAE 2008)

> INRAE (2008), Référentiel pédologique français, édition 2008.

Utilisé pour les variables pédologiques (pH, profondeur, engorgement).

## 4. Chaîne exécutée

```
Reasoning → Diagnostic → Recommendation → Validation
```

L'endpoint `POST /api/v1/orchestration/analyse` enchaîne les quatre
moteurs sur une session DB unique et retourne chaque étape.

### 4.1. Reasoning Engine

**Entrée** : 2 règles + contexte pédologique (pH=4.8, profondeur=70cm,
engorgement=True).

**Sortie** : 2 conclusions produites.

| Conclusion | Énoncé | Confiance | Source |
|---|---|---|---|
| `48913042...` | Le sol est acide (pH < 5.5) : Q. petraea est préférable à Q. robur sur sol acide profond | 0.85 | Parelle 2007 |
| `1d8ac19a...` | Engorgement hivernal détecté : Q. robur est plus tolérant à l'engorgement racinaire que Q. petraea | 0.80 | Parelle 2007 |

### 4.2. Diagnostic Engine

**Entrée** : 2 conclusions + qualifications déclarées + état global
déclaré (`vigueur_reduite`).

**Sortie** : diagnostic persisté en base.

| Champ | Valeur |
|---|---|
| Diagnostic ID | `a594c335-b764-5635-8a80-c9a0cf1cf6ac` |
| État global | `vigueur_reduite` |
| Plancher de preuve | B |
| Conclusions source | 2 |
| Qualifications | 2 (contrainte pédologique + risque sanitaire) |

### 4.3. Recommendation Engine

**Entrée** : diagnostic ID + objectif forestier (`production`).

**Sortie** : 1 recommandation liée au diagnostic.

| Champ | Valeur |
|---|---|
| Recommandation ID | `53e80ccf-4840-4762-9fef-c5391c374098` |
| Type d'action | `eclaircie` |
| Description | Éclaircie modérée (prélèvement 25 %) pour favoriser la croissance |
| Diagnostic source | `a594c335-b764-5635-8a80-c9a0cf1cf6ac` |
| Contournable | True |

### 4.4. Validation Engine

**Entrée** : diagnostic + recommandations + conclusions.

**Sortie** : validation `valide`, aucune cause de blocage.

| Champ | Valeur |
|---|---|
| Statut | `valide` |
| Causes de blocage | aucune |

## 5. Performance mesurée

| Métrique | Valeur |
|---|---|
| Temps total chaîne | 0.15s |
| Reasoning | < 0.05s |
| Diagnostic | < 0.05s |
| Recommendation | < 0.05s |
| Validation | < 0.01s |

> Mesuré sur API locale (Docker, localhost). Le benchmark complet sera
> mesuré pendant S3.

## 6. Trace de la chaîne

```
[ÉTAPE] Vérification santé API + DB
[OK] /health : healthy
[OK] /ready : healthy
[ÉTAPE] Authentification (dev login)
[OK] Token JWT obtenu
[ÉTAPE] Exécution chaîne : Reasoning → Diagnostic → Recommendation → Validation
[INFO] Station : pH=4.8, profondeur=70cm, engorgement=True
[INFO] Règles : 2 (acidité Quercus, engorgement Quercus)
[INFO] Objectif : production
[OK] Chaîne complète en 0.15s

[ÉTAPE] 1. Reasoning Engine — 2 conclusion(s)
   • 48913042... : Le sol est acide (pH < 5.5) : Quercus petraea est
     préférable à Quercus robur sur sol acide profond
     Confiance : 0.85, Source : Parelle 2007
   • 1d8ac19a... : Engorgement hivernal détecté : Quercus robur est plus
     tolérant à l'engorgement racinaire que Quercus petraea
     Confiance : 0.80, Source : Parelle 2007
[OK] 2 conclusion(s) produite(s)

[ÉTAPE] 2. Diagnostic Engine — état : vigueur_reduite
   Diagnostic ID : a594c335-b76...
   Plancher preuve : B
   Conclusions source : 2
[OK] Diagnostic persisté : a594c335-b76...

[ÉTAPE] 3. Recommendation Engine — 1 recommandation(s)
   Diagnostic source : a594c335-b76...
   • eclaircie — Éclaircie modérée (prélèvement 25 %)
     Priorité : ?, Contournable : True
[OK] 1 recommandation(s) produite(s)

[ÉTAPE] 4. Validation Engine — statut : valide
[OK] Validation : valide

RÉSUMÉ : 2 conclusions → état vigueur_reduite → 1 recommandation → validation valide
```

## 7. Ce qui est prouvé

1. **La chaîne complète fonctionne** : Reasoning → Diagnostic →
   Recommendation → Validation s'enchaîne sans erreur sur un appel HTTP
   unique.
2. **Les sources sont traçables** : chaque conclusion cite Parelle 2007,
   avec niveau de preuve B et niveau de confiance déclaré.
3. **Le diagnostic est persisté** : le DiagnosticEngine écrit en base,
   et le RecommendationEngine relit ce diagnostic par son ID.
4. **La validation contrôle la chaîne** : le ValidationEngine vérifie
   le diagnostic et les recommandations, et ne bloque pas.
5. **L'explication est complète** : les quatre sorties intermédiaires
   sont retournées dans la réponse (GSIE-CON-004).

## 8. Ce qui reste à faire

### Court terme (S3 — Validation scientifique + performance)

- **Ground truth** : comparer la recommandation produite avec la
  recommandation d'un expert forestier sur la même station
- **Benchmark** : mesurer latence, throughput, mémoire sur un volume
  de requêtes
- **Reproductibilité** : script qui rejoue le benchmark

### Moyen terme

- **Evidence → Knowledge** : la chaîne actuelle démarre au Reasoning
  Engine. L'amont (ingestion → evidence qualification → knowledge
  extraction) n'est pas encore orchestré en un seul appel
- **Données terrain** : le scénario utilise des règles déclarées dans
  la requête. La version cible récupère les règles depuis le Knowledge
  Engine à partir du territoire (voir schema `AnalyseRequest.regles`)
- **Validation humaine** : la recommandation doit être validée par un
  forestier avant application (CON-001)

## 9. Fichiers

| Fichier | Rôle |
|---|---|
| `scripts/tranche_verticale.py` | Script d'exécution de la tranche verticale |
| `tranche_verticale_resultat.json` | Rapport JSON complet de la dernière exécution |
| `GSIE/DOCUMENTATION/TRANCHE_VERTICALE.md` | Ce document |

## 10. Reproduction

```bash
# Prérequis : API démarrée (docker compose up)
cd GSIE/API
python scripts/tranche_verticale.py
# Sortie : trace sur stdout + rapport JSON
```
