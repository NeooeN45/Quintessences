# Manuel qualité de GSIE

| Champ | Valeur |
|---|---|
| **Document** | QUALITY_MANUAL.md |
| **Dossier** | 23_QUALITY_MANAGEMENT |
| **Version** | 1.0.0 |
| **Date** | 2 juillet 2026 |
| **Statut** | Adopté |
| **Référence** | QUALITY_POLICY.md, ISO 9001:2015 (inspiration) |

---

## 1. Objet

Ce manuel décrit le **système de management de la qualité (QMS)** de GSIE. Il opérationnalise la politique qualité (`QUALITY_POLICY.md`) en processus concrets, indicateurs mesurables, audits planifiés et revues structurées. Il s'inspire de la norme ISO 9001:2015 sans en rechercher la certification formelle dans l'immédiat — la certification pourra être envisagée à partir de la Phase 4.

---

## 2. Structure du QMS

```
23_QUALITY_MANAGEMENT/
├── QUALITY_POLICY.md          ← Politique (intentions)
├── QUALITY_MANUAL.md          ← Manuel (ce document — système)
├── PROCESSES/                 ← Processus documentés
│   ├── CODE_REVIEW.md
│   ├── CI_CD.md
│   ├── KNOWLEDGE_VALIDATION.md
│   ├── INCIDENT_MANAGEMENT.md
│   ├── DOCUMENT_REVIEW.md
│   └── RELEASE_MANAGEMENT.md
├── AUDITS/                    ← Rapports d'audit interne
│   └── TEMPLATE_AUDIT_REPORT.md
├── REVIEWS/                   ← Comptes-rendus de revue de direction
│   └── TEMPLATE_REVIEW_REPORT.md
└── KPI_DASHBOARD.md           ← Tableau de bord des indicateurs
```

---

## 3. Catalogue des processus

### 3.1 Processus de développement

| Processus | Objet | Entrée | Sortie | Pilote |
|---|---|---|---|---|
| **Revue de code** | Garantir la qualité du code avant fusion | PR | Code approuvé ou rejeté | Lead dev |
| **CI/CD** | Automatiser la vérification | Push Git | Build + tests + rapport | CI/CD |
| **Gestion des versions** | Séquencer les releases | Sprint terminé | Release taggée | Lead dev |
| **Gestion des dépendances** | Auditer les dépendances | Nouvelle dépendance | Validation ou refus | Lead dev |

### 3.2 Processus de connaissance

| Processus | Objet | Entrée | Sortie | Pilote |
|---|---|---|---|---|
| **Ingestion de sources** | Intégrer une source au Knowledge Graph | Source (Partie VI) | Nœuds + relations + sources | Data steward |
| **Validation des connaissances** | Valider toute nouvelle connaissance | Knowledge Entry | Evidence qualifiée | Evidence Engine + expert |
| **Versionnement de la KB** | Tracer chaque version du savoir | Ajout de connaissance | Version_KB incrémentée | Knowledge Engine |
| **Audit des licences** | Vérifier la licence de chaque source | Source candidate | Fiche de licence | 19_LEGAL |

### 3.3 Processus de raisonnement

| Processus | Objet | Entrée | Sortie | Pilote |
|---|---|---|---|---|
| **Diagnostic** | Produire un diagnostic stationnel | Données terrain + env | Diagnostic + provenance | Diagnostic Engine |
| **Validation de sortie** | Vérifier la complétude de provenance | Diagnostic + recommandations | ValidationResult | Validation Engine |
| **Reproductibilité** | Garantir la rejouabilité | Intrants + Version_KB | Résultat identique | Tests de non-régression |

### 3.4 Processus organisationnels

| Processus | Objet | Entrée | Sortie | Pilote |
|---|---|---|---|---|
| **Revue de direction** | Piloter le QMS | KPIs + audits | Plan d'action | Direction |
| **Audit interne** | Vérifier le QMS | Plan d'audit | Rapport d'audit | Responsable qualité |
| **Gestion des incidents** | Traiter les non-conformités | Incident | Correction + leçon | Responsable qualité |
| **Revue documentaire** | Maintenir la doc à jour | Documents | Doc mise à jour | Responsable qualité |
| **Gestion des changements** | Évaluer l'impact d'un changement | RFC | Décision + ADR | Comité technique |

---

## 4. Processus détaillés

### 4.1 Revue de code (CODE_REVIEW.md)

**Règles.**
- Tout PR DOIT être revu par au moins un pair avant fusion.
- Le reviewer DOIT vérifier : tests, conventions, sécurité, performance, documentation.
- Un PR de plus de 400 lignes DOIT être découpé.
- Le reviewer DOIT laisser un commentaire constructif (pas juste "OK").
- Le PR ne peut être fusionné que si CI est vert ET review approuvée.

**Checklist du reviewer.**
- [ ] Le code respecte les conventions (global_rules.md)
- [ ] Les tests couvrent les cas nominaux et edge cases
- [ ] Pas de secret, pas de donnée personnelle
- [ ] Pas de dépendance non justifiée
- [ ] La documentation est à jour
- [ ] Pas de dette technique introduite

### 4.2 CI/CD (CI_CD.md)

**Pipeline obligatoire.**
```
Push → Lint (ruff/ktlint) → Typecheck (mypy/tsc) → Tests unitaires → Tests intégration → Build → Artefact
```

**Règles.**
- Aucun PR ne peut être fusionné si le CI est rouge.
- La couverture de tests DOIT être ≥ 80 % sur le domaine (moteurs).
- SonarQube DOIT ne pas signaler de bug critique.
- Le build DOIT produire un artefact reproductible.

### 4.3 Validation des connaissances (KNOWLEDGE_VALIDATION.md)

**Processus.**
```
1. Source identifiée (Partie VI) → fiche de source créée
2. Licence vérifiée (19_LEGAL) → fiche de licence
3. Source ingérée (OCR/parsing) → texte extrait
4. Entités/relations extraites (IA) → ExtractionResult
5. Evidence Engine évalue le niveau de preuve → Evidence
6. Validation expert (humain) → validation ou rejet
7. Intégration au Knowledge Graph → KnowledgeEntry + Version_KB
8. Snapshot signé produit → distribution embarquée
```

**Règles.**
- Aucune connaissance sans source (précondition absolue).
- Aucune connaissance sans validation Evidence Engine.
- Les connaissances de niveau CONJECTURAL ne sont pas utilisées dans le raisonnement sans marquage explicite.
- Toute contradiction est tracée et signalée.

### 4.4 Gestion des incidents (INCIDENT_MANAGEMENT.md)

**Classification.**

| Niveau | Définition | Délai de réponse | Délai de résolution | Communication |
|---|---|---|---|---|
| **P1 — Critique** | Service indisponible ou conclusion erronée sans provenance | < 1h | < 24h | Public + clients |
| **P2 — Majeur** | Dégradation significative ou conclusion avec provenance incomplète | < 4h | < 7j | Clients Enterprise |
| **P3 — Mineur** | Bug non bloquant, documentation obsolète | < 48h | < 30j | Suivant cycle |
| **P4 — Observation** | Amélioration suggérée | < 1 semaine | Suivant cycle | Backlog |

**Processus.**
```
1. Détection (monitoring, utilisateur, test)
2. Enregistrement (ticket GitHub + classification)
3. Analyse de cause racine (5 pourquoi)
4. Action corrective (éliminer la cause)
5. Test de non-régression
6. Clôture (traçabilité + leçon apprise)
7. Standardisation (éviter la récurrence)
8. Communication (selon niveau)
```

### 4.5 Gestion des versions (RELEASE_MANAGEMENT.md)

**Versionnement sémantique (SemVer).**
- `MAJOR.MINOR.PATCH` (ex: 1.2.3)
- MAJOR : rupture de compatibilité
- MINOR : nouvelle fonctionnalité compatible
- PATCH : correction compatible

**Processus de release.**
```
1. Fin de sprint → branche release/x.y.z
2. Validation CI complète (lint + tests + build)
3. Revue de direction (KPIs, dette, risques)
4. Tag git + changelog
5. Publication (artefacts, documentation, release notes)
6. Communication (clients, communauté, site web)
7. Archivage (version taggée, reproductible)
```

---

## 5. Tableau de bord des indicateurs (KPI_DASHBOARD.md)

### 5.1 Indicateurs scientifiques

| KPI | Cible | Phase 1 | Phase 2 | Phase 3 | Phase 4+ |
|---|---|---|---|---|---|
| Taux de traçabilité | 100 % | N/A | 100 % | 100 % | 100 % |
| Taux de reproductibilité | 100 % | N/A | 95 % | 100 % | 100 % |
| Taux de citation | 100 % | N/A | 100 % | 100 % | 100 % |
| Précision des diagnostics | ≥ 90 % | N/A | 70 % | 85 % | ≥ 90 % |
| Couverture des sources P1 | 100 % Phase 2 | 10 % | 100 % | 100 % | 100 % |

### 5.2 Indicateurs techniques

| KPI | Cible | Phase 1 | Phase 2 | Phase 3 | Phase 4+ |
|---|---|---|---|---|---|
| Couverture de tests (domaine) | ≥ 80 % | 50 % | 70 % | 80 % | ≥ 80 % |
| Couverture de tests (global) | ≥ 60 % | 30 % | 50 % | 60 % | ≥ 60 % |
| Densité de bugs | < 1 / kLOC | < 3 | < 2 | < 1 | < 1 |
| Latence Correlation Engine | < 5s (200 corr.) | N/A | < 10s | < 5s | < 3s |
| Disponibilité backend | ≥ 99,5 % | N/A | 99 % | 99,5 % | 99,9 % |
| Dette technique | < 5 % | < 10 % | < 8 % | < 5 % | < 5 % |

### 5.3 Indicateurs organisationnels

| KPI | Cible | Phase 1 | Phase 2 | Phase 3 | Phase 4+ |
|---|---|---|---|---|---|
| Délai résolution bug (P1) | < 24h | < 48h | < 24h | < 24h | < 12h |
| Délai résolution bug (P2) | < 7j | < 14j | < 7j | < 7j | < 5j |
| Satisfaction utilisateur | ≥ 4/5 | N/A | 3,5/5 | 4/5 | ≥ 4/5 |
| Délai réponse support | < 24h (Enterprise) | N/A | < 48h | < 24h | < 12h |

### 5.4 Fréquence de mesure

| Indicateur | Fréquence | Support | Responsable |
|---|---|---|---|
| KPIs techniques | Quotidienne (CI) + Mensuelle (rapport) | SonarQube, GitHub | Lead dev |
| KPIs scientifiques | Mensuelle | Validation Engine logs | Data steward |
| KPIs organisationnels | Mensuelle | Helpdesk, GitHub | Responsable qualité |
| Revue d'ensemble | Trimestrielle | KPI_DASHBOARD.md | Direction |

---

## 6. Audit interne

### 6.1 Plan d'audit

| Audit | Périmètre | Fréquence | Auditeur | Durée |
|---|---|---|---|---|
| **Audit code** | Conventions, tests, dette | Trimestriel | Lead dev + QR | 1 jour |
| **Audit connaissance** | Provenance, sources, contradictions | Trimestriel | Data steward + QR | 1 jour |
| **Audit documentation** | Fraîcheur, complétude, cohérence | Semestriel | QR | 2 jours |
| **Audit QMS complet** | Tous les processus | Annuel | QR + externe | 3 jours |
| **Audit sécurité** | Conformité, accès, chiffrement | Annuel | Externe | 2 jours |

### 6.2 Processus d'audit

```
1. Planification (périmètre, calendrier, auditeurs)
2. Préparation (checklist, documents à auditer)
3. Réalisation (entretiens, inspection, tests)
4. Constatations (conformes / non-conformités)
5. Rapport d'audit (AUDITS/audit_YYYYMMDD.md)
6. Plan d'action correctif
7. Suivi (vérification des actions)
8. Clôture (leçons apprises)
```

### 6.3 Template de rapport d'audit

```markdown
# Audit interne — [date]

## Périmètre
[périmètre audité]

## Auditeurs
[noms]

## Constatations
| # | Constat | Niveau | Cause racine | Action corrective | Délai | Responsable |
|---|---|---|---|---|---|---|

## KPIs mesurés
[tableau des KPIs]

## Recommandations
[recommandations d'amélioration]

## Validation
[signature auditeurs + direction]
```

---

## 7. Revue de direction

### 7.1 Objet

La revue de direction est l'instance suprême du QMS. Elle se réunit **trimestriellement** et examine :
- les KPIs (scientifiques, techniques, organisationnels) ;
- les résultats d'audits ;
- les non-conformités et leur résolution ;
- les retours utilisateurs ;
- les risques qualité ;
- le plan d'action qualité.

### 7.2 Participants

| Participant | Rôle |
|---|---|
| Direction | Présidence |
| Responsable qualité | Animation + présentation KPIs |
| Lead développeur | KPIs techniques |
| Data steward | KPIs scientifiques |
| Comité scientifique (représentant) | Qualité scientifique |

### 7.3 Template de compte-rendu

```markdown
# Revue de direction — [trimestre année]

## KPIs
[tableau des KPIs vs cibles]

## Audits réalisés
[résumé des audits du trimestre]

## Non-conformités
[non-conformités ouvertes + résolues]

## Retours utilisateurs
[résumé des retours]

## Risques qualité
[matrice des risques]

## Décisions
[décisions prises + actions]

## Plan d'action
| Action | Responsable | Délai | Statut |
|---|---|---|---|

## Validation
[signature direction + QR]
```

---

## 8. Contrôle documentaire

### 8.1 Cycle de vie d'un document

```
Création → Revue par les pairs → Validation → Publication → Maintenance → Archivage
```

### 8.2 Règles de contrôle

| Règle | Description |
|---|---|
| **Versionnage** | Tout document a une version (SemVer) et un changelog |
| **Revue** | Tout document technique est revu par au moins un pair |
| **Fraîcheur** | Tout document est revu au moins une fois par an |
| **Cohérence** | Les références croisées entre documents sont vérifiées |
| **Accessibilité** | Les documents sont stockés dans le dépôt (Git, versionnés) |
| **Traçabilité** | Toute modification est tracée (Git + RFC pour les majeures) |

### 8.3 Matrice de responsabilité documentaire

| Type de document | Auteur | Reviewer | Approbateur | Fréquence de revue |
|---|---|---|---|---|
| MIG | Direction | Comité scientifique + technique | Direction | Semestrielle |
| Constitution | Direction | Assemblée | Assemblée | Annuelle |
| RFC | Auteur du RFC | Comité technique | Direction | Sur modification |
| ADR | Auteur de l'ADR | Lead dev | Direction | Sur création |
| Spécifications moteur | Lead dev | Comité technique | Direction | Semestrielle |
| Processus qualité | Responsable qualité | Direction | Direction | Annuelle |
| README de dossier | Responsable du dossier | QR | Direction | Annuelle |

---

## 9. Gestion des changements

### 9.1 Processus RFC

Tout changement significatif (architecture, processus, organisation) DOIT suivre le processus RFC :

```
1. Identification du besoin → auteur
2. Rédaction du RFC (02_RFC/) → auteur
3. Revue par les pairs (commentaires) → communauté
4. Arbitrage → comité technique
5. Décision (03_DECISIONS/) → direction
6. Implémentation → équipe
7. Validation → tests + audit
8. Clôture du RFC → archivage
```

### 9.2 Impact sur le QMS

Tout changement qui affecte le QMS DOIT :
- être évalué pour son impact sur les KPIs ;
- être validé par le responsable qualité ;
- être documenté dans le manuel qualité ;
- être communiqué à tous les contributeurs.

---

## 10. Culture qualité et formation

### 10.1 Formation initiale

Tout nouveau contributeur (humain ou agent IA) DOIT :
- lire la Constitution (00_CONSTITUTION/) ;
- lire la politique qualité (QUALITY_POLICY.md) ;
- lire les processus pertinents à son rôle ;
- passer un quiz de compréhension (à développer).

### 10.2 Formation continue

| Formation | Fréquence | Public |
|---|---|---|
| Revue des processus qualité | Annuelle | Tous |
| Retour d'expérience sur incidents | Trimestriel | Tous |
| Nouvelles pratiques (outils, méthodes) | Selon besoin | Tous |
| Formation spécifique (moteur, source) | Selon besoin | Équipe concernée |

---

## 11. Versioning

| Version | Date | Changement |
|---|---|---|
| 1.0.0 | 2 juillet 2026 | Création initiale — manuel qualité complet (catalogue des processus, processus détaillés, KPIs, audit interne, revue de direction, contrôle documentaire, gestion des changements, formation) |

---

> *Le manuel qualité n'est pas un document figé : il évolue avec le projet, s'enrichit des retours d'expérience et s'adapte aux nouvelles réalités. Il est le reflet vivant de la culture qualité de GSIE.*
