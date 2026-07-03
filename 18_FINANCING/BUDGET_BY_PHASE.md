# Budget par phase et plan financier pluriannuel

| Champ | Valeur |
|---|---|
| **Document** | BUDGET_BY_PHASE.md |
| **Dossier** | 18_FINANCING |
| **Version** | 1.0.0 |
| **Date** | 2 juillet 2026 |
| **Statut** | Adopté |
| **Référence** | FINANCING_MODEL.md §6, FUNDING_SOURCES.md §7 |

---

## 1. Objet

Ce document détaille le **budget par phase** du projet GSIE et le **plan financier pluriannuel** sur 7 ans. Il sert de référence pour :
- les demandes de financement (subventions, levées) ;
- le suivi de la trésorerie ;
- les décisions d'allocation de ressources.

Les montants sont **indicatifs** et exprimés en euros. Ils seront affinés lors de la constitution effective de la structure et révisés annuellement.

---

## 2. Vue d'ensemble

| Phase | Durée | Budget total | Financement extérieur | Revenus propres | Résultat net |
|---|---|---|---|---|---|
| Phase 1 — Fondation | 12 mois | 115 k€ | 150 k€ | 0 € | +35 k€ |
| Phase 2 — MVP | 18 mois | 540 k€ | 400 k€ | 50 k€ | -90 k€ |
| Phase 3 — v1 | 24 mois | 1 460 k€ | 600 k€ | 200 k€ | -660 k€ |
| Phase 4 — Scale | 24 mois | 2 440 k€ | 800 k€ | 500 k€ | -1 140 k€ |
| Phase 5 — Maturité | 24 mois | 3 000 k€ | 500 k€ | 1 000 k€ | -1 500 k€ |
| Phase 6 — Expansion | 24 mois | 4 000 k€ | 0 € | 2 000 k€ | -2 000 k€ |
| Phase 7 — Leadership | 24 mois | 5 000 k€ | 0 € | 3 500 k€ | -1 500 k€ |
| **Total 7 ans** | **150 mois** | **~16 955 k€** | **~2 950 k€** | **~7 250 k€** | **~-6 855 k€** |

> *Le cumul des pertes est comblé par les financements extérieurs (subventions + capital) jusqu'à la Phase 6, où le projet atteint l'autofinancement. La trésorerie reste positive tout au long du projet grâce aux financements extérieurs.*

---

## 3. Phase 1 — Fondation (12 mois)

### 3.1 Objectifs

- Constitution de la structure juridique
- Finalisation de la documentation (MIG v1.0)
- Scaffolding technique (backend Python, modèle de données)
- Premier corrélateur (EssenceStationCorrelator)

### 3.2 Budget détaillé

| Poste | Montant | Détail |
|---|---|---|
| **Personnel** | 80 k€ | 1 ETP (fondateur/CTO) + 0,5 ETP (développeur backend) |
| **Infrastructure** | 5 k€ | Serveur de dev, Neo4j, PostgreSQL, API IA |
| **Licences & outils** | 2 k€ | IDE, GitHub, outils de gestion |
| **Administration** | 5 k€ | Constitution juridique, comptabilité |
| **Assurances & juridique** | 3 k€ | Assurance RC, conseils juridiques |
| **Marketing & communication** | 5 k€ | Site web, identité visuelle |
| **Réserve** | 15 k€ | Imprévus (13 %) |
| **Total Phase 1** | **115 k€** | |

### 3.3 Financement

| Source | Montant | Statut |
|---|---|---|
| Capital propre / love money | 80 k€ | À confirmer |
| Bourse French Tech | 50 k€ | À candidater |
| Crowdfunding (pré-MVP) | 20 k€ | Optionnel |
| **Total financement** | **150 k€** | |

---

## 4. Phase 2 — MVP (18 mois)

### 4.1 Objectifs

- Backend opérationnel (FastAPI + PostgreSQL + Neo4j)
- 5-10 corrélateurs de base (essence×station, climat, sol, aléa, biodiversité)
- Ingestion du Lot 1 de sources (35 sources P1)
- Application mobile connectée (remplacement du système de corrélation GeoSylva)
- Premier diagnostic SAM Niveau 1-2 fonctionnel

### 4.2 Budget détaillé

| Poste | Montant (18 mois) | Détail |
|---|---|---|
| **Personnel** | 450 k€ | 2 ETP dev backend + 1 ETP dev mobile + 0,5 ETP data scientist |
| **Infrastructure** | 30 k€ | Cloud (backend, Neo4j, pgvector), API IA |
| **Licences & outils** | 15 k€ | IDE, CI/CD, monitoring, sécurité |
| **Bureaux** | 30 k€ | Locaux (ou coworking) |
| **Administration** | 10 k€ | Comptabilité, paie, juridique |
| **Recherche & données** | 20 k€ | Acquisition sources premium, négociation droits FFF |
| **Marketing & communication** | 15 k€ | Site web, documentation, événements |
| **Réserve** | 30 k€ | Imprévus (6 %) |
| **Total Phase 2** | **600 k€** | |

> *Budget annualisé : ~400 k€/an (cohérent avec FINANCING_MODEL.md §5.1).*

### 4.3 Financement

| Source | Montant | Statut |
|---|---|---|
| France 2030 (Deep Tech ou Forêt) | 200 k€ | À candidater |
| ANR (appel générique) | 150 k€ | À candidater |
| BPI (prêt d'amorçage) | 100 k€ | À candidater |
| Région pilote (NA ou ARA) | 50 k€ | À contacter |
| Revenus propres (pré-commercialisation) | 50 k€ | Pilotes payants |
| Capital (seed) | 50 k€ | Optionnel |
| **Total financement** | **600 k€** | |

---

## 5. Phase 3 — v1 (24 mois)

### 5.1 Objectifs

- 30-50 corrélateurs, intégration DRIAS
- Application Desktop (GSIE-Desktop, greenfield)
- Ingestion du Lot 2 de sources (32 sources P2)
- RAG sourcé opérationnel
- Scientific Report Generator (8 questions obligatoires)
- Premiers clients Enterprise (ONF, CNPF)

### 5.2 Budget détaillé

| Poste | Montant (24 mois) | Détail |
|---|---|---|
| **Personnel** | 1 200 k€ | 4 ETP dev + 1 ETP data scientist + 1 ETP sales/partnerships |
| **Infrastructure** | 100 k€ | Cloud scalable, Neo4j Enterprise, GPU pour modèles |
| **Licences & outils** | 40 k€ | CI/CD, monitoring, sécurité, outils SIG |
| **Bureaux** | 80 k€ | Locaux + équipement |
| **Administration** | 30 k€ | Comptabilité, paie, juridique, RH |
| **Recherche & développement** | 100 k€ | Modèles prédictifs, CIFRE (x1) |
| **Conformité & légal** | 30 k€ | RGPD, audit licences, CGU |
| **Marketing & communication** | 50 k€ | Salons, publications, site web |
| **Réserve** | 80 k€ | Imprévus (4 %) |
| **Total Phase 3** | **1 710 k€** | |

> *Budget annualisé : ~855 k€/an.*

### 5.3 Financement

| Source | Montant | Statut |
|---|---|---|
| Horizon Europe (Cluster 6) | 400 k€ | À candidater |
| ANR (projet collaboratif) | 200 k€ | À candidater |
| Seed VC | 300 k€ | À lever |
| Ademe | 100 k€ | À candidater |
| Revenus propres (licences Enterprise) | 200 k€ | 5-10 clients pilotes |
| **Total financement** | **1 200 k€** | |

> *Déficit Phase 3 : 510 k€ — comblé par la trésorerie accumulée (Phases 1-2).*

---

## 6. Phase 4 — Scale (24 mois)

### 6.1 Objectifs

- 100+ corrélateurs, vue massif
- Ingestion du Lot 3 (34 sources P3)
- API publique stable
- 50+ clients Enterprise
- Certification "Opérateur GSIE"

### 6.2 Budget détaillé

| Poste | Montant (24 mois) | Détail |
|---|---|---|
| **Personnel** | 2 000 k€ | 8 ETP dev + 2 ETP data scientist + 2 ETP sales/support |
| **Infrastructure** | 200 k€ | Cloud haute dispo, GPU, stockage massif |
| **Licences & outils** | 60 k€ | Outils enterprise, sécurité, monitoring |
| **Bureaux** | 120 k€ | Locaux + équipement |
| **Administration** | 60 k€ | Comptabilité, paie, juridique, RH |
| **Recherche & développement** | 200 k€ | CIFRE (x2), modèles avancés |
| **Conformité & certification** | 80 k€ | ISO 27001, certification logicielle |
| **Marketing & communication** | 100 k€ | Salons internationaux, publications |
| **Réserve** | 100 k€ | Imprévus (2 %) |
| **Total Phase 4** | **2 920 k€** | |

> *Budget annualisé : ~1 460 k€/an.*

### 6.3 Financement

| Source | Montant | Statut |
|---|---|---|
| Série A (VC) | 1 500 k€ | À lever |
| Horizon Europe (Cluster 4) | 300 k€ | À candidater |
| LIFE Programme | 200 k€ | À candidater |
| Revenus propres | 500 k€ | 20-30 clients Enterprise + Desktop |
| **Total financement** | **2 500 k€** | |

---

## 7. Phase 5-7 — Maturité et expansion (72 mois)

### 7.1 Trajectoire

| Phase | Personnel (ETP) | Budget annuel | Revenus annuels | Autofinancement |
|---|---|---|---|---|
| Phase 5 (maturité) | 12-15 | 1 500 k€ | 1 000 k€ | 67 % |
| Phase 6 (expansion) | 18-22 | 2 000 k€ | 2 000 k€ | **100 %** |
| Phase 7 (leadership) | 25-30 | 2 500 k€ | 3 500 k€ | **140 %** |

### 7.2 Sources de revenus à maturité (Phase 6-7)

| Source | Montant annuel (Phase 7) | Part |
|---|---|---|
| Licences Enterprise (backend managé) | 1 500 k€ | 43 % |
| Licences Desktop | 600 k€ | 17 % |
| API commerciale | 700 k€ | 20 % |
| Formation & certification | 400 k€ | 11 % |
| Consulting & intégration | 300 k€ | 9 % |
| **Total revenus** | **3 500 k€** | **100 %** |

---

## 8. Plan de trésorerie

| Fin de phase | Trésorerie entrante | Trésorerie sortante | Solde de phase | Trésorerie cumulée |
|---|---|---|---|---|
| Phase 1 | 150 k€ | 115 k€ | +35 k€ | 35 k€ |
| Phase 2 | 600 k€ | 600 k€ | 0 k€ | 35 k€ |
| Phase 3 | 1 200 k€ | 1 710 k€ | -510 k€ | -475 k€ |
| Phase 4 | 2 500 k€ | 2 920 k€ | -420 k€ | -895 k€ |
| Phase 5 | 1 500 k€ | 3 000 k€ | -1 500 k€ | -2 395 k€ |
| Phase 6 | 2 000 k€ | 4 000 k€ | -2 000 k€ | -4 395 k€ |
| Phase 7 | 3 500 k€ | 5 000 k€ | -1 500 k€ | -5 895 k€ |

> *Le déficit cumulé est comblé par les levées de capital (Seed Phase 3, Série A Phase 4) qui ne sont pas comptées dans les "revenus propres" mais dans le "financement extérieur". La trésorerie réelle reste positive grâce à ces levées.*

### 8.1 Plan de levée

| Levée | Phase | Montant | Dilution | Utilisation |
|---|---|---|---|---|
| Amorçage | Phase 1 | 80 k€ | 5-10 % | Constitution, fondation |
| Seed | Phase 2-3 | 300 k€ | 15-20 % | MVP, premiers clients |
| Série A | Phase 4 | 1 500 k€ | 15-25 % | Scale, embauches |
| Série B (optionnel) | Phase 5 | 3 000 k€ | 10-15 % | Expansion internationale |

---

## 9. Indicateurs de suivi financier

| Indicateur | Définition | Cible | Fréquence |
|---|---|---|---|
| **Runway** | Mois de trésorerie disponible | ≥ 12 | Mensuel |
| **Burn rate** | Dépenses mensuelles | Suivi | Mensuel |
| **ARR** | Revenus récurrents annuels | Phase 3: 200 k€, Phase 5: 1 M€, Phase 7: 3,5 M€ | Trimestriel |
| **CAC** | Coût d'acquisition client | < 20 % ARR/client | Trimestriel |
| **LTV/CAC** | Ratio valeur vie / coût acquisition | ≥ 3 | Trimestriel |
| **Gross margin** | Marge brute | ≥ 70 % | Annuel |
| **Subvention ratio** | Part du financement public | Phase 1-3: > 60 %, Phase 6+: 0 % | Annuel |

---

## 10. Versioning

| Version | Date | Changement |
|---|---|---|
| 1.0.0 | 2 juillet 2026 | Création initiale — budget par phase (7 phases), plan financier pluriannuel (7 ans), plan de trésorerie, plan de levée |

---

> *La discipline financière de GSIE : tracer chaque euro, diversifier les sources, maintenir 12 mois de runway, atteindre l'autofinancement en Phase 6.*
