# Gouvernance financière

| Champ | Valeur |
|---|---|
| **Document** | FINANCIAL_GOVERNANCE.md |
| **Dossier** | 18_FINANCING |
| **Version** | 1.0.0 |
| **Date** | 2 juillet 2026 |
| **Statut** | Adopté |
| **Référence** | FINANCING_MODEL.md §8, CON-007 (transparence) |

---

## 1. Objet

Ce document définit la **gouvernance financière** de GSIE : qui décide, qui contrôle, qui rend compte. Il assure la **transparence** (principe constitutionnel CON-007) et la **traçabilité** des décisions financières.

---

## 2. Acteurs financiers

| Acteur | Rôle | Composition | Fréquence |
|---|---|---|---|
| **Assemblée des partenaires** | Organe souverain (SCIC) | Tous les partenaires (fondateur, institutions, financeurs, utilisateurs) | Annuelle |
| **Conseil d'administration** | Direction stratégique | 5-12 membres élus par l'assemblée | Trimestrielle |
| **Comité financier** | Contrôle financier | 3 membres du CA + expert-comptable | Mensuelle |
| **Comité scientifique** | Validation des investissements R&D | Experts externes (INRAE, INRIA, ONF) | Trimestrielle |
| **Direction** | Exécution opérationnelle | CEO/CTO | Continue |
| **Commissaire aux comptes** | Audit externe | Cabinet indépendant | Annuelle |

---

## 3. Processus de décision financière

### 3.1 Seuils de validation

| Montant | Décision par | Délai | Documentation requise |
|---|---|---|---|
| < 5 k€ | Direction | Immédiat | Note de dépense |
| 5 – 20 k€ | Comité financier | 1 semaine | Note d'opportunité + budget |
| 20 – 100 k€ | Conseil d'administration | 1 mois | Dossier complet + ROI |
| > 100 k€ | Assemblée des partenaires | 1 mois | Dossier complet + vote |

### 3.2 Processus de demande de financement

```
1. Identification d'un appel → Direction
2. Rédaction du dossier → Direction + Comité scientifique
3. Validation interne → Comité financier (budget, cofinancement)
4. Soumission → Direction
5. Suivi → Comité financier (mensuel)
6. En cas de succès → allocation par le CA
7. Reporting → trimestriel au financeur + annuel public
```

### 3.3 Processus de dépense

```
1. Besoin identifié → demandeur (tout employé)
2. Validation selon seuil (§3.1)
3. Engagement (bon de commande)
4. Réception + facture
5. Validation facture (comité financier si > 5 k€)
6. Paiement
7. Comptabilisation + traçabilité
```

---

## 4. Contrôle et audit

### 4.1 Contrôle interne

| Contrôle | Fréquence | Responsable | Indicateur |
|---|---|---|---|
| **Rapprochement bancaire** | Mensuel | Expert-comptable | Écart = 0 |
| **Suivi budgétaire** | Mensuel | Comité financier | Écart < 10 % |
| **Validation des dépenses** | Continue | Direction | 100 % tracé |
| **Inventaire** | Annuel | Direction | Actifs tracés |

### 4.2 Audit externe

| Audit | Fréquence | Par | Objet |
|---|---|---|---|
| **Commissaire aux comptes** | Annuel | Cabinet indépendant | Comptes annuels |
| **Audit subventions** | Selon financeur | Cabinet ou financeur | Éligibilité des dépenses |
| **Audit fiscal** | Annuel | Expert-comptable | Conformité fiscale |

---

## 5. Transparence et publication

### 5.1 Documents publiés annuellement

| Document | Contenu | Délai | Public |
|---|---|---|---|
| **Rapport financier annuel** | Comptes, bilan, résultat, financements | 6 mois après clôture | Public (site web) |
| **Rapport d'activité** | Avancement, indicateurs, impacts | 6 mois après clôture | Public |
| **Rapport de transparence** | Sources de financement, conflits d'intérêt | 6 mois après clôture | Public |
| **Rapport subventions** | Utilisation des fonds publics | Selon financeur | Financeur + public |

### 5.2 Conflits d'intérêt

Tout membre d'un organe de gouvernance DOIT :
- déclarer ses intérêts (financiers, personnels, familiaux) à l'entrée en fonction et annuellement ;
- se récuser des décisions où il a un intérêt direct ;
- rendre publique la liste des conflits déclarés (anonymisés si nécessaire).

---

## 6. Gestion des risques financiers

| Risque | Indicateur d'alerte | Action |
|---|---|---|
| **Runway < 6 mois** | Trésorerie / burn rate | Levée d'urgence ou réduction des coûts |
| **Écart budgétaire > 15 %** | Suivi mensuel | Analyse des causes + plan correctif |
| **Perte d'un financement** | Notification du financeur | Diversification accélérée |
| **Non-respect d'un contrat** | Réclamation client | Médiation + plan de remédiation |

---

## 7. Versioning

| Version | Date | Changement |
|---|---|---|
| 1.0.0 | 2 juillet 2026 | Création initiale — gouvernance financière complète (acteurs, processus, contrôles, transparence, risques) |

---

> *La transparence financière n'est pas une option : c'est une obligation constitutionnelle (CON-007). Chaque euro public DOIT être tracé et justifié.*
