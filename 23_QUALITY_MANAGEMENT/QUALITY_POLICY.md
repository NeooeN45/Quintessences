# Politique qualité de GSIE

| Champ | Valeur |
|---|---|
| **Document** | QUALITY_POLICY.md |
| **Dossier** | 23_QUALITY_MANAGEMENT |
| **Version** | 1.0.0 |
| **Date** | 2 juillet 2026 |
| **Statut** | Adopté |
| **Référence constitutionnelle** | CON-001 (explicabilité), CON-005 (reproductibilité), CON-007 (transparence) |
| **Référence MIG** | Partie II §II.1 (objectifs scientifiques), §II.4 (objectifs UX) |

---

## 1. Objet

Ce document énonce la **politique qualité** de GSIE. Il est l'équivalent, pour un projet d'envergure institutionnelle, de la politique qualité exigée par la norme ISO 9001:2015. Il engage l'ensemble des contributeurs — humains et agents IA — et sert de référence ultime pour toute décision touchant à la qualité.

---

## 2. Déclaration de politique qualité

> **GSIE est une infrastructure de connaissance forestière dont la qualité est non-négociable.**
>
> Chaque conclusion produite par GSIE DOIT être :
> - **traçable** — reliée à ses sources par une chaîne de preuve complète ;
> - **reproductible** — rejouable à intrants et versions identiques ;
> - **honnête** — accompagnée de son incertitude, sans masquage ;
> - **défendable** — conforme aux connaissances scientifiques et réglementaires du moment.
>
> La qualité de GSIE se mesure non pas par la vitesse de production, mais par la **confiance** que les utilisateurs placent dans ses conclusions. Cette confiance est le produit le plus précieux du projet.

---

## 3. Principes qualité

### 3.1 Cinq principes directeurs

| # | Principe | Déclinaison |
|---|---|---|
| 1 | **La qualité par construction** | La qualité n'est pas une vérification finale : elle est conçue dans le système (provenance, validation, tests) |
| 2 | **L'erreur est une opportunité** | Tout bug, toute conclusion erronée est tracé, analysé, corrigé — et la cause racine est éliminée |
| 3 | **L'utilisateur juge la qualité** | La qualité se mesure du point de vue de l'utilisateur, pas du développeur |
| 4 | **L'amélioration continue** | Chaque cycle (sprint, phase, version) améliore la qualité du précédent |
| 5 | **La transparence qualité** | Les indicateurs qualité sont publics, les incidents sont divulgués |

### 3.2 Alignement avec la Constitution

| Article constitutionnel | Implication qualité |
|---|---|
| CON-001 (explicabilité) | Toute conclusion DOIT avoir une chaîne de preuve — qualité = traçabilité |
| CON-005 (reproductibilité) | Deux exécutions identiques produisent le même résultat — qualité = stabilité |
| CON-007 (transparence) | Les indicateurs qualité sont publiés — qualité = visibilité |
| CON-009 (non-substitution) | GSIE assiste le forestier, ne le remplace pas — qualité = contournabilité |

---

## 4. Périmètre du système de management de la qualité (QMS)

Le QMS de GSIE couvre l'ensemble du cycle de vie du projet :

| Domaine | Périmètre | Référence |
|---|---|---|
| **Documentation** | MIG, Constitution, RFC, ADR, spécifications | 17_DOCUMENTATION, 00_CONSTITUTION |
| **Développement** | Code, tests, revue, CI/CD | 09_ENGINES, 15_TESTS |
| **Données** | Ingestion, validation, versionnement | 08_DATASETS, 07_KNOWLEDGE |
| **Connaissances** | Knowledge Graph, provenance, sources | 07_KNOWLEDGE, MIG Partie VI |
| **Moteurs** | Contrats, algorithmes, validation | 09_ENGINES, MIG Partie IV |
| **Infrastructure** | Backend, API, sécurité | 13_API, MIG Partie III |
| **Applications** | Mobile, Desktop, UX | 12_APPLICATIONS |
| **Recherche** | Modèles, expérimentations | 06_RESEARCH, 11_MODELS |
| **Organisation** | Gouvernance, processus, audits | 23_QUALITY_MANAGEMENT |

---

## 5. Objectifs qualité (KPIs)

### 5.1 KPIs scientifiques

| KPI | Définition | Cible | Mesure |
|---|---|---|---|
| **Taux de traçabilité** | % de conclusions avec chaîne de preuve complète | 100 % | Validation Engine |
| **Taux de reproductibilité** | % de conclusions reproductibles à intrants identiques | 100 % | Tests de non-régression |
| **Taux de citation** | % de conclusions avec au moins une source citée | 100 % | Validation Engine |
| **Précision des diagnostics** | % de diagnostics validés par un expert humain | ≥ 90 % | Évaluation expert |
| **Couverture des sources** | % de sources P1 intégrées | 100 % Phase 2 | Suivi ingestion |

### 5.2 KPIs techniques

| KPI | Définition | Cible | Mesure |
|---|---|---|---|
| **Couverture de tests** | % de code couvert par les tests | ≥ 80 % (domaine), ≥ 60 % (global) | CI/CD |
| **Densité de bugs** | Bugs / 1000 lignes de code | < 1 | SonarQube |
| **Latence moteur** | Temps de réponse du Correlation Engine | < 5s (200 corrélateurs) | Monitoring |
| **Disponibilité** | Uptime du backend | ≥ 99,5 % | Monitoring |
| **Dette technique** | Ratio dette / code | < 5 % | SonarQube |

### 5.3 KPIs documentaires

| KPI | Définition | Cible | Mesure |
|---|---|---|---|
| **Complétude doc** | % de moteurs avec spécification complète | 100 % | Revue doc |
| **Fraîcheur doc** | % de documents à jour (< 6 mois) | ≥ 90 % | Revue doc |
| **Traçabilité ADR** | % de décisions avec ADR | 100 % | Revue ADR |

### 5.4 KPIs organisationnels

| KPI | Définition | Cible | Mesure |
|---|---|---|---|
| **Délai de résolution bug** | Temps moyen de résolution | < 7j (critique), < 30j (majeur) | GitHub |
| **Satisfaction utilisateur** | Score de satisfaction (enquête) | ≥ 4/5 | Enquête annuelle |
| **Délai de réponse support** | Temps moyen de première réponse | < 24h (Enterprise), < 72h (community) | Helpdesk |

---

## 6. Processus qualité clés

| Processus | Description | Document |
|---|---|---|
| **Revue de code** | Tout code est revu par au moins un pair avant fusion | `PROCESSES/CODE_REVIEW.md` |
| **Tests automatisés** | CI/CD : lint + typecheck + tests + build à chaque push | `PROCESSES/CI_CD.md` |
| **Validation des connaissances** | Toute connaissance intégrée au graphe est validée (Evidence Engine + expert) | `PROCESSES/KNOWLEDGE_VALIDATION.md` |
| **Gestion des incidents** | Tout incident est tracé, analysé, corrigé | `PROCESSES/INCIDENT_MANAGEMENT.md` |
| **Revue de direction** | Revue trimestrielle des KPIs et du QMS | `REVIEWS/` |
| **Audit interne** | Audit annuel du QMS | `AUDITS/` |
| **Revue documentaire** | Revue semestrielle de la documentation | `PROCESSES/DOCUMENT_REVIEW.md` |

---

## 7. Responsabilités qualité

| Rôle | Responsabilité qualité |
|---|---|
| **Direction** | Définit la politique qualité, alloue les ressources, préside les revues de direction |
| **Responsable qualité** (QR) | Maintient le QMS, anime les audits, suit les KPIs, pilote l'amélioration continue |
| **Comité scientifique** | Valide la qualité scientifique des moteurs et des connaissances |
| **Lead développeur** | Garantit la qualité du code (revue, tests, CI/CD) |
| **Data steward** | Garantit la qualité des données et des sources |
| **Chaque contributeur** | Applique les processus qualité dans son travail quotidien |

---

## 8. Amélioration continue (PDCA)

GSIE adopte le cycle **PDCA** (Plan-Do-Check-Act) de l'ISO 9001 :

```
     Plan (Planifier)
    ┌──────────────────┐
    │ Objectifs qualité │
    │ KPIs cibles       │
    │ Plan d'action     │
    └────────┬─────────┘
             │
             ▼
    Do (Faire)          Check (Vérifier)
   ┌──────────────┐    ┌──────────────┐
   │ Exécution     │───→│ Mesure KPIs   │
   │ des actions   │    │ Audit interne │
   │               │    │ Revue de dir. │
   └──────────────┘    └──────┬───────┘
                                │
                                ▼
                       Act (Agir)
                      ┌──────────────┐
                      │ Correctifs    │
                      │ Standardiser  │
                      │ Améliorer     │
                      └──────────────┘
```

| Phase | Fréquence | Acteur | Livrable |
|---|---|---|---|
| **Plan** | Trimestriel | Direction + QR | Plan qualité trimestriel |
| **Do** | Continue | Tous | Exécution |
| **Check** | Mensuel (KPIs), Annuel (audit) | QR | Rapport KPIs, rapport d'audit |
| **Act** | Trimestriel | Direction + QR | Plan correctif |

---

## 9. Gestion des non-conformités

### 9.1 Classification

| Niveau | Définition | Exemple | Délai de correction |
|---|---|---|---|
| **Critique (N1)** | Conclusion erronée sans provenance | Diagnostic sans source | Immédiat (bloquant) |
| **Majeure (N2)** | Conclusion avec provenance incomplète | Source orpheline | < 7 jours |
| **Mineure (N3)** | Documentation obsolète, dette technique | Doc non mise à jour | < 30 jours |
| **Observation (N4)** | Amélioration suggérée | Optimisation possible | Suivant cycle |

### 9.2 Processus

```
1. Détection (test, audit, utilisateur, monitoring)
2. Enregistrement (ticket + classification)
3. Analyse de cause racine (5 pourquoi, diagramme Ishikawa)
4. Action corrective (éliminer la cause, pas le symptôme)
5. Vérification (test de non-régression)
6. Clôture (traçabilité + leçon apprise)
7. Standardisation (éviter la récurrence)
```

---

## 10. Culture qualité

La qualité de GSIE n'est pas un processus : c'est une **culture**. Elle repose sur :

- **La transparence de l'erreur** — signaler un bug est un acte positif, pas une faute.
- **La revue par les pairs** — aucun code, aucune connaissance n'entre sans revue.
- **L'utilisateur final comme juge** — la qualité se mesure sur le terrain, pas en bureau.
- **L'amélioration continue** — chaque version est meilleure que la précédente.
- **La traçabilité absolue** — chaque décision, chaque conclusion, chaque correction est tracée.

---

## 11. Versioning

| Version | Date | Changement |
|---|---|---|
| 1.0.0 | 2 juillet 2026 | Création initiale — politique qualité complète (5 principes, 4 familles de KPIs, 7 processus, PDCA, gestion des non-conformités, culture qualité) |

---

> *La qualité de GSIE se mesure par la confiance. La confiance se construit par la traçabilité. La traçabilité se garantit par la qualité.*
