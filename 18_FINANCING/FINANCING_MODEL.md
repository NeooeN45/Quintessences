# Modèle économique de GSIE

| Champ | Valeur |
|---|---|
| **Document** | FINANCING_MODEL.md |
| **Dossier** | 18_FINANCING |
| **Version** | 1.0.0 |
| **Date** | 2 juillet 2026 |
| **Statut** | Adopté |
| **Référence constitutionnelle** | CON-006 (licences), CON-007 (open source), FND-001 (souveraineté) |
| **Référence MIG** | Partie II §II.2 (non-dépendance), §II.3 (objectifs économiques) |

---

## 1. Objet

Ce document définit le **modèle économique** de GSIE — c'est-à-dire la manière dont le projet se finance, génère des revenus, structure ses coûts et assure sa pérennité financière. Il est conçu pour une institution d'envergure nationale, dans la continuité de l'écosystème GeoSylva (double licence AGPL-3.0 / commerciale).

Le modèle économique de GSIE repose sur un principe fondateur : **la connaissance est un bien commun, l'infrastructure de service est payante**. Ce principe est décliné en cinq flux de revenus et quatre catégories de coûts.

---

## 2. Principe fondateur : le bien commun payant

| Ce qui est bien commun (gratuit, open source) | Ce qui est service (payant) |
|---|---|
| Le code source (AGPL-3.0) | L'hébergement managé du backend |
| La base de connaissances (sources ouvertes) | Les modèles prédictifs avancés |
| Les API publiques (quota gratuit) | L'API à haut débit (quota commercial) |
| L'application mobile ( gratuite) | L'application Desktop (licence commerciale) |
| La documentation | La formation et la certification |
| Les diagnostics de base (SAM Niveau 1) | L'augmentation scientifique (SAM Niveau 2-3) |

Ce principe garantit que :
- **l'utilisateur individuel** (forestier, étudiant, propriétaire privé) accède gratuitement à l'outil de terrain et au diagnostic de base ;
- **l'institution** (ONF, CNPF, coopérative, bureau d'études) paie pour l'infrastructure, la puissance, le support et la garantie ;
- **le projet** se finance sans compromettre l'open source ni la souveraineté.

---

## 3. Structure juridique

### 3.1 Forme juridique recommandée

GSIE est porté par une **structure dédiée** distincte de l'éditeur de GeoSylva, pour trois raisons :

1. **Séparation des risques** — GSIE a une ambition institutionnelle qui dépasse le cadre d'un projet individuel.
2. **Éligibilité aux subventions** — Les appels à projets (France 2030, ANR, Horizon Europe) exigent souvent une structure juridique distincte.
3. **Gouvernance multi-acteurs** — Une structure dédiée permet d'accueillir des partenaires (ONF, CNPF, INRAE) au capital ou au conseil.

| Option | Avantages | Inconvénients | Recommandation |
|---|---|---|---|
| **SAS** | Flexibilité, levée possible, parts de société | Pas d'éligibilité à certains financements associatifs | À utiliser si levée prévue |
| **SCIC** (coopérative) | Gouvernance multi-acteurs, éligibilité financements, ancrage territorial | Complexité de gouvernance | **Recommandé** — aligné avec la vocation institutionnelle |
| **Association** | Simplicité, éligibilité subventions | Pas de levée, pas de distribution | À utiliser si phase purement R&D |
| **GIP** (groupement d'intérêt public) | Monture institutionnelle idéale, partenaires publics | Lourdeur de création, dépendance à l'État | À envisager à maturité |

**Décision provisoire.** Phase 1-2 : **SCIC** (coopérative d'intérêt collectif) ou **SAS** si levée. Phase 3+ : évaluation d'un **GIP** si l'État devient partenaire structurel. Cette décision DOIT être validée par un RFC (§0.6 MIG) et un avis juridique (19_LEGAL).

### 3.2 Capital et gouvernance

| Acteur | Rôle | Part (indicative) |
|---|---|---|
| Fondateur / éditeur GeoSylva | Direction technique | 30-40 % |
| Partenaires institutionnels (ONF, CNPF, INRAE) | Conseil scientifique | 20-30 % (collectif) |
| Investisseurs / financeurs | Capital | 20-30 % |
| Utilisateurs / coopératives forestières | Gouvernance usage | 10-20 % |

> *Les pourcentages sont indicatifs et seront précisés lors de la constitution effective. La forme SCIC impose une répartition multi-parties prenantes.*

---

## 4. Flux de revenus

GSIE génère cinq flux de revenus distincts, ordonnés du plus récurrent au plus ponctuel.

### 4.1 Licences commerciales (recurrent)

| Produit | Cible | Tarif indicatif (annuel) | Justification |
|---|---|---|---|
| **GSIE-Desktop** (licence commerciale) | Experts, bureaux d'études, coopératives | 1 200 – 3 600 € / poste / an | Logiciel d'analyse approfondie, hors licence AGPL |
| **GSIE-Enterprise** (backend managé) | ONF, CNPF, grandes structures | 10 000 – 50 000 € / an | Hébergement, maintenance, support, SLA |
| **API commerciale** (quota haut débit) | Intégrateurs, tiers | 0,01 – 0,10 € / appel | Au-delà du quota gratuit (1000 appels/jour) |

**Modèle de licence.** La licence AGPL-3.0 s'applique à tout usage non commercial et à toute redistribution. La licence commerciale s'applique à :
- l'application Desktop (qui n'est pas publiée en AGPL) ;
- l'usage commercial du backend managé ;
- les intégrations propriétaires (clause AGPL → obligation de partager ou d'acheter une licence commerciale).

### 4.2 Services professionnels (recurrent)

| Service | Cible | Tarif indicatif | Justification |
|---|---|---|---|
| **Formation** (initiale + continue) | Forestiers, étudiants, professionnels | 500 – 1 500 € / jour | Formation à GSIE, à l'interprétation des diagnostics, à la traçabilité |
| **Certification** | Professionnels | 300 – 800 € / personne | Certification "Opérateur GSIE" (niveau 1, 2, 3) |
| **Consulting & intégration** | Institutions, entreprises | 800 – 1 500 € / jour | Intégration sur mesure, développement de corrélateurs spécifiques |
| **Support technique** (SLA) | Clients Enterprise | Inclus dans la licence Enterprise | Support prioritaire, garantie de réponse |

### 4.3 Subventions et financements publics (ponctuel + recurrent)

| Source | Montant indicatif | Phase | Conditions |
|---|---|---|---|
| **France 2030** (BPI) | 200 k€ – 1 M€ | Phase 2-3 | Appels à projets "deep tech", "forêt", "IA" |
| **ANR** (Agence Nationale de la Recherche) | 150 – 500 k€ | Phase 2-3 | Projets collaboratifs de recherche |
| **Horizon Europe** | 500 k€ – 2 M€ | Phase 3-4 | Programmes "Green Deal", "AI", "Data" |
| **FEADER** (fonds européen agricole) | 50 – 200 k€ | Phase 2 | Mesures forestières régionales |
| **Régions** (fonds propres) | 50 – 300 k€ | Phase 2-3 | Selon région, en lien avec SRGS |
| **Ademe** | 100 – 500 k€ | Phase 3 | Adaptation climatique, carbone forestier |

> *Le détail des sources de financement est consigné dans `FUNDING_SOURCES.md`.*

### 4.4 Partenariats de recherche (ponctuel)

| Type | Montant indicatif | Phase | Conditions |
|---|---|---|---|
| **Contrats de recherche** (INRAE, CIRAD) | 50 – 300 k€ / projet | Phase 2-4 | Collaborations sur les moteurs scientifiques |
| **Thèses CIFRE** | 30 – 50 k€ / an / thèse | Phase 2-4 | Financement doctoral en entreprise |
| **Conventions de données** | Variable | Phase 1-4 | Accès à des données propriétaires (FFF, guides CNPF) |

### 4.5 Contribution communautaire (indirect)

| Type | Valeur estimée | Phase | Conditions |
|---|---|---|---|
| **Développement open source** (bénévole) | 50 – 200 k€ / an (valeur estimée) | Phase 2+ | Contributions de la communauté (corrélateurs, sources, traductions) |
| **Validation de connaissances** (experts) | Inestimable | Phase 2+ | Validation bénévole de connaissances du graphe |

> *La contribution communautaire n'est pas un revenu monétaire, mais une **valeur créée** qui réduit les coûts de développement et de validation. Elle DOIT être reconnue et tracée.*

---

## 5. Structure de coûts

### 5.1 Coûts fixes (annuels)

| Poste | Phase 1 | Phase 2 | Phase 3 | Phase 4+ |
|---|---|---|---|---|
| **Personnel** (développement, recherche) | 100 k€ | 300 k€ | 600 k€ | 1 000 k€+ |
| **Infrastructure** (serveurs, cloud, API) | 5 k€ | 20 k€ | 50 k€ | 100 k€+ |
| **Licences & outils** | 2 k€ | 10 k€ | 20 k€ | 30 k€ |
| **Bureaux & administration** | 5 k€ | 20 k€ | 40 k€ | 60 k€ |
| **Assurances & juridique** | 3 k€ | 10 k€ | 20 k€ | 30 k€ |
| **Total fixes** | **~115 k€** | **~360 k€** | **~730 k€** | **~1 220 k€+** |

### 5.2 Coûts variables (par utilisateur / par projet)

| Poste | Unité | Coût unitaire | Phase |
|---|---|---|---|
| **Inférence IA** (API Claude, Mistral) | par diagnostic | 0,05 – 0,20 € | 2+ |
| **Stockage** (base de connaissances, corpus) | par Go / mois | 0,02 € | 1+ |
| **Bande passante** (snapshots, API) | par Go | 0,01 € | 1+ |
| **Acquisition de données** (sources premium) | par source | Variable | 2+ |

### 5.3 Coûts d'investissement (ponctuels)

| Poste | Montant indicatif | Phase | Justification |
|---|---|---|---|
| **Infrastructure initiale** (serveurs, Neo4j, PostgreSQL) | 20 – 50 k€ | Phase 1-2 | Mise en place du backend |
| **Recherche & développement** (modèles prédictifs) | 100 – 300 k€ | Phase 2-3 | Développement des moteurs scientifiques |
| **Ingestion du corpus initial** | 50 – 100 k€ | Phase 2 | Acquisition et structuration des 101 sources |
| **Certification & conformité** | 20 – 50 k€ | Phase 3 | RGPD, ISO, certification logicielle |

---

## 6. Projection financière pluriannuelle

> *Les montants sont indicatifs et exprimés en euros. Ils seront affinés lors de la constitution effective de la structure et de chaque levée de financement.*

| Année | Phase | Revenus | Coûts | Résultat | Financement extérieur | Cumul trésorerie |
|---|---|---|---|---|---|---|
| Année 1 | Phase 1 (fondation) | 0 € | 115 k€ | -115 k€ | 150 k€ (subventions + capital) | +35 k€ |
| Année 2 | Phase 2 (MVP) | 50 k€ | 360 k€ | -310 k€ | 400 k€ (France 2030 + ANR) | +125 k€ |
| Année 3 | Phase 3 (v1) | 200 k€ | 730 k€ | -530 k€ | 600 k€ (Horizon + régions) | +195 k€ |
| Année 4 | Phase 4 (scale) | 500 k€ | 1 220 k€ | -720 k€ | 800 k€ (levée + subventions) | +275 k€ |
| Année 5 | Phase 5 (maturité) | 1 000 k€ | 1 500 k€ | -500 k€ | 500 k€ (revenus croissants) | +275 k€ |
| Année 6 | Phase 6 (expansion) | 2 000 k€ | 2 000 k€ | 0 € | 0 € (autofinancement) | +275 k€ |
| Année 7 | Phase 7 (leadership) | 3 500 k€ | 2 500 k€ | +1 000 k€ | 0 € | +1 275 k€ |

**Point d'autofinancement** : année 6 (Phase 6). Avant cette date, le projet dépend de financements extérieurs (subventions, capital). Après, les revenus commerciaux couvrent les coûts.

**Hypothèses.**
- 50 clients Enterprise à 20 k€ / an en Phase 5 (1 M€).
- 200 licences Desktop à 2 000 € / an en Phase 5 (400 k€).
- 100 jours de formation / consulting à 1 000 € / jour en Phase 5 (100 k€).
- API commerciale : 500 k€ en Phase 5.
- Subventions dégressives à partir de la Phase 5.

---

## 7. Politique de prix

### 7.1 Gratuit (AGPL-3.0)

| Bénéficiaire | Ce qui est gratuit | Limites |
|---|---|---|
| Utilisateur individuel | App mobile, diagnostic SAM Niveau 1, API (1000 appels/jour) | Pas de support, pas de SLA |
| Étudiant / chercheur | Tout ce qui est AGPL, accès API étendu (sur demande) | Usage non commercial uniquement |
| Projet open source | Tout le code, la documentation, la base de connaissances | Attribution requise (AGPL) |

### 7.2 Payant (licence commerciale)

| Offre | Cible | Tarif | Inclus |
|---|---|---|---|
| **Desktop Pro** | Expert individuel, bureau d'études | 1 200 € / an / poste | App Desktop, SAM Niveau 2 local, mises à jour |
| **Desktop Enterprise** | Coopérative, ONF, CNPF | 3 600 € / an / poste | Desktop Pro + support + customisation |
| **Backend Managed** | Institution | 10 000 – 50 000 € / an | Hébergement, maintenance, SLA, API haut débit |
| **API Commercial** | Intégrateur, tiers | 0,01 – 0,10 € / appel | Au-delà du quota gratuit, SLA |
| **Formation** | Tous | 500 – 1 500 € / jour | Formation initiale et continue |
| **Certification** | Professionnels | 300 – 800 € / personne | Certification "Opérateur GSIE" |

### 7.3 Tarification sociale

GSIE applique une **tarification sociale** pour réduire les inégalités d'accès :

| Bénéficiaire | Réduction | Condition |
|---|---|---|
| Étudiurs | Gratuit | Justificatif d'inscription |
| Petites coopératives (< 10 salariés) | -50 % | Sur justificatif |
| Pays en développement | -70 % | Sur liste de l'OCDE |
| Projets de recherche non commerciaux | Gratuit | Sur convention |

---

## 8. Gestion de la trésorerie

### 8.1 Principes

- **Trésorerie minimale** : 6 mois de coûts fixes en réserve (principe de prudence).
- **Séparation des comptes** : un compte par source de financement (subventions) pour assurer la traçabilité.
- **Audit annuel** : un commissaire aux comptes DOIT être nommé dès la Phase 2 (obligation légale selon la forme juridique et le chiffre d'affaires).
- **Transparence** : le rapport financier annuel est publié (principe de transparence, CON-007).

### 8.2 Indicateurs financiers

| Indicateur | Définition | Cible |
|---|---|---|
| **Runway** | Nombre de mois de trésorerie disponible | ≥ 12 mois |
| **Burn rate** | Dépenses mensuelles | Suivi mensuel |
| **ARR** (Annual Recurring Revenue) | Revenus récurrents annuels | Croissance ≥ 50 % / an (Phase 3-5) |
| **CAC** (Customer Acquisition Cost) | Coût d'acquisition client | < 20 % de l'ARR par client |
| **LTV** (Lifetime Value) | Valeur vie client | ≥ 3 × CAC |
| **Gross margin** | Marge brute | ≥ 70 % (logiciel) |

---

## 9. Risques financiers et mitigation

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| **Non-obtention des subventions** | Moyenne | Élevé | Diversification des sources (≥ 3 sources simultanées) |
| **Retard de commercialisation** | Élevée | Moyen | Phase 1 sans revenus prévue ; ajustement du runway |
| **Coûts d'IA supérieurs aux prévisions** | Moyenne | Moyen | Quotas, cache, modèles locaux (poste PC) |
| **Concurrence d'un acteur gratuit** | Faible | Élevé | Ancrage institutionnel, base de connaissances unique, traçabilité |
| **Perte d'un client majeur (ONF, CNPF)** | Faible | Élevé | Diversification de la base client |
| **Changement réglementaire (RGPD, IA Act)** | Moyenne | Moyen | Veille juridique (19_LEGAL), conformité proactive |

---

## 10. Liens avec les autres documents

| Document | Lien |
|---|---|
| `FUNDING_SOURCES.md` | Détail des sources de financement par programme |
| `BUDGET_BY_PHASE.md` | Budget détaillé par phase du projet |
| `MULTI_YEAR_PLAN.md` | Plan financier pluriannuel (version détaillée) |
| `FINANCIAL_GOVERNANCE.md` | Gouvernance financière, contrôles, audits |
| `19_LEGAL/LICENSE_POLICY.md` | Politique de licences (AGPL + commerciale) |
| `20_PARTNERSHIPS/INSTITUTIONAL_PARTNERS.md` | Partenaires institutionnels et financeurs |
| MIG Partie II §II.3 | Objectifs économiques du projet |
| MIG Partie II §II.6 | Objectifs open source |

---

## 11. Versioning

| Version | Date | Changement |
|---|---|---|
| 1.0.0 | 2 juillet 2026 | Création initiale — modèle économique complet (5 flux de revenus, 4 catégories de coûts, projection 7 ans, politique de prix, tarification sociale) |

---

> *GSIE se finance comme une infrastructure publique : gratuit pour l'usage individuel, payant pour l'usage institutionnel, financé par l'État et l'Europe pendant la phase de construction, autofinancé à maturité.*
