# Tableau de bord des indicateurs qualité (KPI Dashboard)

| Champ | Valeur |
|---|---|
| **Document** | KPI_DASHBOARD.md |
| **Dossier** | 23_QUALITY_MANAGEMENT |
| **Version** | 1.0.0 |
| **Date** | 2 juillet 2026 |
| **Statut** | Actif (mis à jour mensuellement) |
| **Référence** | QUALITY_POLICY.md §5, QUALITY_MANUAL.md §5 |

---

## 1. Objet

Ce tableau de bord consolide l'ensemble des **indicateurs qualité (KPIs)** de GSIE. Il est mis à jour **mensuellement** par le responsable qualité et présenté **trimestriellement** en revue de direction.

---

## 2. KPIs scientifiques

| KPI | Définition | Cible | T1 2026 | T2 2026 | Tendance |
|---|---|---|---|---|---|
| Taux de traçabilité | % conclusions avec chaîne de preuve complète | 100 % | N/A | N/A | — |
| Taux de reproductibilité | % conclusions reproductibles à intrants identiques | 100 % | N/A | N/A | — |
| Taux de citation | % conclusions avec ≥ 1 source citée | 100 % | N/A | N/A | — |
| Précision des diagnostics | % diagnostics validés par expert | ≥ 90 % | N/A | N/A | — |
| Couverture sources P1 | % sources P1 intégrées | 100 % (Phase 2) | 0 % | 0 % | — |

> *N/A = moteurs non encore implémentés (Phase 1). Les KPIs scientifiques seront mesurables dès la Phase 2.*

---

## 3. KPIs techniques

| KPI | Définition | Cible | T1 2026 | T2 2026 | Tendance |
|---|---|---|---|---|---|
| Couverture tests (domaine) | % code domaine couvert | ≥ 80 % | N/A | N/A | — |
| Couverture tests (global) | % code total couvert | ≥ 60 % | N/A | N/A | — |
| Densité de bugs | Bugs / 1000 LOC | < 1 | N/A | N/A | — |
| Latence Correlation Engine | Temps de réponse (200 corr.) | < 5s | N/A | N/A | — |
| Disponibilité backend | Uptime | ≥ 99,5 % | N/A | N/A | — |
| Dette technique | Ratio dette / code | < 5 % | N/A | N/A | — |

> *N/A = infrastructure non encore déployée (Phase 1). Les KPIs techniques seront mesurables dès le scaffolding backend.*

---

## 4. KPIs documentaires

| KPI | Définition | Cible | T1 2026 | T2 2026 | Tendance |
|---|---|---|---|---|---|
| Complétude doc moteurs | % moteurs avec spécification complète | 100 % | 0 % | **100 %** | ↑ |
| Fraîcheur doc | % documents à jour (< 6 mois) | ≥ 90 % | N/A | **100 %** | ↑ |
| Traçabilité ADR | % décisions avec ADR | 100 % | N/A | **100 %** | ↑ |

> *T2 2026 : la Partie IV (moteurs) est complète (MIG v0.6.0), tous les ADR sont consignés.*

---

## 5. KPIs organisationnels

| KPI | Définition | Cible | T1 2026 | T2 2026 | Tendance |
|---|---|---|---|---|---|
| Délai résolution bug (P1) | Temps moyen résolution critiques | < 24h | N/A | N/A | — |
| Délai résolution bug (P2) | Temps moyen résolution majeurs | < 7j | N/A | N/A | — |
| Satisfaction utilisateur | Score satisfaction (enquête) | ≥ 4/5 | N/A | N/A | — |
| Délai réponse support | Temps moyen première réponse | < 24h | N/A | N/A | — |

---

## 6. KPIs financiers (lien 18_FINANCING)

| KPI | Définition | Cible | T1 2026 | T2 2026 | Tendance |
|---|---|---|---|---|---|
| Runway | Mois de trésorerie | ≥ 12 | N/A | N/A | — |
| Burn rate | Dépenses mensuelles | Suivi | N/A | N/A | — |
| ARR | Revenus récurrents annuels | Phase 3: 200 k€ | 0 € | 0 € | — |

---

## 7. Historique des mesures

| Période | KPIs mesurables | Notes |
|---|---|---|
| T1 2026 | Documentaires uniquement | Phase 1 — fondation documentaire |
| T2 2026 | Documentaires uniquement | Phase 1 — MIG v0.6.0, Parties I-IV-VI-VII rédigées |
| T3 2026 (prévu) | + techniques | Scaffolding backend prévu |
| T4 2026 (prévu) | + scientifiques | Premier Correlation Engine MVP prévu |

---

## 8. Versioning

| Version | Date | Changement |
|---|---|---|
| 1.0.0 | 2 juillet 2026 | Création initiale — tableau de bord avec toutes les familles de KPIs (scientifiques, techniques, documentaires, organisationnels, financiers) |

---

> *Ce tableau de bord est le pouls de GSIE. Il est mis à jour mensuellement et présenté trimestriellement. Ce qui n'est pas mesuré n'est pas géré.*
