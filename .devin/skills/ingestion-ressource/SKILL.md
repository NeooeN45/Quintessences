---
name: ingestion-ressource
description: Qualifie et catalogue une ressource scientifique, technique, logicielle ou de données avec provenance et licence
argument-hint: "[URL, DOI, fichier, dataset ou ressource]"
triggers:
  - user
---

# Ingestion de ressource Quintessences

Tu qualifies les ressources proposées au projet : publication, dataset, API,
bibliothèque, modèle, standard, dépôt de code ou guide métier. Tu produis une
fiche traçable et tu empêches l'ingestion d'une ressource dont la provenance ou
les droits sont inconnus.

## Routage canonique

| Ressource | Destination principale |
|---|---|
| Publication, thèse, guide | `GSIE/RESEARCH/` |
| Dataset ou service de données | `GSIE/DATASETS/` |
| Règle ou connaissance validée | `GSIE/KNOWLEDGE/` après qualification |
| Prototype ou résultat préliminaire | `21_EXPERIMENTS/` |
| Licence, contrat ou accord | `19_LEGAL/` et/ou `20_PARTNERSHIPS/` |
| Outil de développement Devin | `.devin/skills/` uniquement après revue |

Ne crée pas de copie concurrente dans `docs/`, `resources/` ou un dossier par
application.

## Mode d'exécution

Le mode par défaut est **QUALIFICATION** et ne télécharge, n'installe et
n'ingère rien. L'enregistrement ou la copie nécessite une demande explicite du
Fondateur et une vérification adaptée au type de ressource.

## Processus

### 1. Identifier la ressource

Collecter sans deviner :

```text
Titre :
Type : publication / dataset / API / bibliothèque / modèle / standard / code
Producteur :
Version ou édition :
Date de publication :
URL ou DOI :
Date de consultation :
Produit ou moteur concerné :
```

Pour un fichier local, relever le chemin, la taille, le format et le checksum
si une copie est envisagée.

### 2. Vérifier la provenance

- publication : DOI, éditeur, auteurs, version, statut publié/preprint ;
- API : documentation officielle, version, quotas, authentification ;
- bibliothèque : dépôt officiel, version, licence, compatibilité ;
- modèle : publication ou model card, poids, licence, restrictions ;
- dataset : producteur, couverture, millésime, format, distribution ;
- code : dépôt officiel, commit, licence et dépendances.

Une URL seule ne prouve pas la qualité, la licence ou la stabilité de la
ressource.

### 3. Vérifier les droits

Pour un dataset, appliquer `GSIE/DATASETS/NOMENCLATURE_SOURCES.md` :

- régime d'accès ;
- licence ;
- droits d'utilisation ;
- attribution ;
- autorisation d'entraînement IA ;
- couverture et grain si spatial ;
- checksum et archivage si une copie entre dans une conclusion.

Si la licence est absente ou ambiguë :

```text
Statut : CATALOGUÉE — LICENCE À CLARIFIER
Ingestion : INTERDITE
Entraînement IA : INTERDIT
Redistribution : INTERDITE
```

### 4. Évaluer la valeur

Classer :

- pertinence : faible / moyenne / élevée ;
- maturité : publié / validé / preprint / prototype / inconnu ;
- qualité : vérifiée / partielle / inconnue ;
- intégration : immédiate / recherche / veille / rejetée ;
- risque : faible / moyen / élevé.

Ne transforme pas une ressource prometteuse en dépendance du produit sans
preuve d'intégration, de licence et de maintenance.

### 5. Dédupliquer et router

Rechercher les ressources déjà présentes dans les catalogues, les RFC, les
sources et les décisions. Proposer l'enrichissement de l'entrée existante si un
équivalent est trouvé.

Une ressource retenue pour une connaissance ou un moteur doit ensuite passer
par les portes de `gsie-governance`, `documentation-gsie` et, si nécessaire,
`postgresql-postgis` ou `python-scientifique`.

## Format de sortie

```markdown
## Qualification de ressource

### Identification
[Titre, type, producteur, version, URL/DOI]

### Provenance et qualité
[preuves vérifiées, inconnues, date]

### Licence et accès
[licence, droits, attribution, IA, régime]

### Pertinence
[produit/moteur, valeur, maturité, risques]

### Routage proposé
[RESEARCH / DATASETS / KNOWLEDGE / EXPERIMENTS / LEGAL]

### Action
[CATALOGUER / ÉTUDIER / ARCHIVER / INGÉRER APRÈS VALIDATION / REJETER]

### Preuves manquantes
[liste explicite]
```

## Garde-fous

- Ne jamais inventer une licence, un checksum, une métrique ou une couverture.
- Ne jamais télécharger de données sensibles ou protégées sans autorisation.
- Ne jamais ingérer une donnée dont la licence n'est pas formalisée.
- Ne jamais ajouter une connaissance sans source identifiable.
- Ne jamais modifier un document `Locked`.
- Ne jamais faire passer une recommandation de ressource pour une décision.
