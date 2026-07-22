# 23 — Quality Management

## Objectif

Définir, piloter et améliorer en continu le système de management de la qualité (QMS) de GSIE. Assurer que chaque conclusion produite par le système est traçable, reproductible, honnête et défendable.

## Structure

```
23_QUALITY_MANAGEMENT/
├── README.md                  ← Ce document
├── QUALITY_POLICY.md          ← Politique qualité (intentions, principes, KPIs)
├── QUALITY_MANUAL.md          ← Manuel qualité (processus, audits, revues)
├── KPI_DASHBOARD.md           ← Tableau de bord des indicateurs
├── SOURCE_OF_TRUTH_REGISTRY.json ← Registre contrôlé des sources de vérité
├── PROCESSES/                 ← Processus documentés
│   ├── CODE_REVIEW.md         ← Revue de code
│   ├── CI_CD.md               ← Intégration et déploiement continus
│   ├── KNOWLEDGE_VALIDATION.md← Validation des connaissances
│   ├── DOCUMENT_CONTROL.md    ← Sources de vérité et fraîcheur
│   ├── AI_AGENT_ORCHESTRATION.md ← Missions IA, rôles et acceptation
│   ├── INCIDENT_MANAGEMENT.md ← (à rédiger)
│   └── RELEASE_MANAGEMENT.md  ← (à rédiger)
├── AUDITS/                    ← Rapports d'audit interne
│   └── TEMPLATE_AUDIT_REPORT.md ← (à rédiger)
└── REVIEWS/                   ← Comptes-rendus de revue de direction
    └── TEMPLATE_REVIEW_REPORT.md ← (à rédiger)
```

## Documents actuels

| Document | Contenu | Version |
|---|---|---|
| `QUALITY_POLICY.md` | Politique qualité (5 principes, 4 familles de KPIs, PDCA, non-conformités, culture) | 1.0.0 |
| `QUALITY_MANUAL.md` | Manuel qualité (catalogue des processus, processus détaillés, KPIs, audits, revues, contrôle doc) | 1.2.0 |
| `KPI_DASHBOARD.md` | Tableau de bord des indicateurs | 1.0.0 |
| `SOURCE_OF_TRUTH_REGISTRY.json` | Sources autorisées, propriétaires et dates de revue | 1 |
| `PROCESSES/CODE_REVIEW.md` | Porte de revue par les pairs | 1.0.0 |
| `PROCESSES/CI_CD.md` | Portes automatiques de livraison | 1.0.0 |
| `PROCESSES/DOCUMENT_CONTROL.md` | Hiérarchie, fraîcheur, archivage et contradictions | 1.0.0 |
| `PROCESSES/AI_AGENT_ORCHESTRATION.md` | Orchestration, séparation des rôles et preuves des agents IA | 1.0.0 |

## Principes

- **Qualité par construction** — la qualité est conçue dans le système, pas vérifiée à la fin
- **L'erreur est une opportunité** — tracer, analyser, corriger, standardiser
- **L'utilisateur juge la qualité** — la qualité se mesure sur le terrain
- **Amélioration continue** — cycle PDCA (Plan-Do-Check-Act)
- **Transparence qualité** — les indicateurs sont publics, les incidents sont divulgués

## Responsabilités

- Définir et maintenir la politique qualité
- Piloter les KPIs (scientifiques, techniques, organisationnels)
- Planifier et réaliser les audits internes
- Animer les revues de direction trimestrielles
- Gérer les non-conformités et les actions correctives
- Maintenir le contrôle documentaire
- Orchestrer et contrôler les contributions des agents IA

## Ce qui est interdit

- Fusionner du code sans revue par les pairs
- Intégrer une connaissance sans validation Evidence Engine
- Publier une conclusion sans chaîne de provenance complète
- Masquer une non-conformité
- Ignorer un retour utilisateur

## Liens

- **00_CONSTITUTION** : principes fondateurs (CON-001, CON-005, CON-007)
- **15_TESTS** : tests automatisés (CI/CD)
- **17_DOCUMENTATION** : contrôle documentaire
- **19_LEGAL** : conformité et audit des licences
- **MIG Partie II §II.1** : objectifs scientifiques
- **MIG Partie II §II.4** : objectifs UX
