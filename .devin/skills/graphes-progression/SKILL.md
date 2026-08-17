---
name: graphes-progression
description: Maintient à jour le site des graphes Mermaid de Quintessences (`graphes-quintessences/`) quand une grosse progression du projet est réalisée.
triggers:
  - user
  - model
---

# Skill — Mise à jour des graphes Mermaid du projet

Ce skill est invoqué quand le projet fait une **grosse progression** :
- une phase est clôturée / activée
- un moteur GSIE est déclaré implémenté ou stabilisé
- une décision structurante (DEC-xxxxxx) change l'architecture / la roadmap
- une spécification est validée
- un jalon Phase 4 notable est atteint (data registry, app, hub, etc.)

## 1. Objectif

Rafraîchir le site statique `graphes-quintessences/` (13 diagrammes, 4
catégories) pour qu'il reflète l'état courant de Quintessences :
écosystème, applications, gouvernance, identité, phases, moteurs,
décisions, data registry, infrastructure territoriale.

## 2. Sources de vérité

Lire **avant** d'agir :

1. `graphes-quintessences/diagrams/meta.json` — liste, ordre, catégories.
2. `graphes-quintessences/diagrams/*.mmd` — code Mermaid existant.
3. `PROJECT_MEMORY.md` — phase courante, moteurs, livrables.
4. `ROADMAP.md` — jalons, prochaine étape.
5. `03_DECISIONS/DEC-*.md` — nouvelles décisions structurantes (pour
   `12_timeline_decisions.mmd`).
6. `README.md`, `GSIE/ARCHITECTURE/*.md` — écosystème, chaîne
   d'intelligence, hiérarchie, mesh territorial/serveur, identité.

## 3. Processus

### 3.1 Identifier ce qui a changé

| Catégorie | Événement | Fichier à mettre à jour |
|---|---|---|
| Écosystème | nouvelle app / rôle | `01_ecosysteme.mmd`, `13_applications_ecosysteme.mmd` |
| Écosystème | chaîne d'intelligence modifiée | `02_chaine_intelligence.mmd` |
| Écosystème | métamodèle Encyclopédie modifié | `06_metamodele_encyclopedie.mmd` |
| Gouvernance | hiérarchie documentaire modifiée | `03_hierarchie_documentaire.mmd` |
| Gouvernance | statuts de document modifiés | `08_cycle_vie_document.mmd` |
| Gouvernance | identité / auth modifiée | `07_identite_quintessences.mmd` |
| Progression | phase basculée | `04_phases_projet.mmd` |
| Progression | moteur livré / stabilisé | `05_moteurs_gsie.mmd` |
| Progression | nouvelle DEC structurante | `12_timeline_decisions.mmd` |
| Progression | data registry modifié | `09_pipeline_data_registry.mmd` |
| Infrastructure | server meshing modifié | `10_architecture_mesh.mmd` |
| Infrastructure | territorial mesh modifié | `11_hierarchie_territoriale.mmd` |

### 3.2 Éditer le(s) `.mmd` concerné(s)

Les graphes doivent rester sourçables et conformes au ton GSIE :
- titres en français
- `description` (1 phrase), source **et** `date_maj` (YYYY-MM-DD) tenues
  à jour dans `meta.json`
- catégorie cohérente (`Écosystème`, `Gouvernance`, `Progression`,
  `Infrastructure`, ou une nouvelle catégorie si le sujet ne rentre dans
  aucune des quatre — la sidebar et les puces de filtre du site groupent
  automatiquement par `categorie`)
- couleurs cohérentes avec le projet (`#1a5276` pour GSIE, etc.)
- privilégier un type de diagramme adapté au contenu (flowchart pour un
  flux, `stateDiagram-v2` pour un cycle de vie, `timeline` pour une
  chronologie, `sequenceDiagram` pour un protocole) — le site détecte et
  affiche automatiquement le type en badge

Ne créer un **nouveau** `.mmd` que si un nouvel objet de synthèse
architecturale apparaît (ex. : jumeau numérique fédéré détaillé,
matrice de traçabilité). Sinon, modifier l'existant. Un nouveau `.mmd`
nécessite une entrée correspondante dans `diagrams/meta.json` (id,
titre, categorie, description, source, date_maj).

### 3.3 Régénérer le site

```powershell
cd graphes-quintessences
python generate_site.py
```

Puis vérifier le rendu :

```powershell
python -m http.server 4300 --directory public
# http://127.0.0.1:4300
```

### 3.4 Vérifier

- Le site s'affiche sans erreur dans le navigateur (thème clair **et**
  sombre — la bascule est dans le pied de la sidebar).
- Les diagrammes Mermaid rendent correctement (pas d'erreur de syntaxe).
- Les titres, sources, catégories et dates sont à jour dans la sidebar
  et dans chaque carte.
- `python -m ruff check generate_site.py` et
  `python -m mypy generate_site.py` passent (mypy strict, ruff — voir
  `AGENTS.md`).

## 4. Commit

Utiliser Conventional Commit, en français :

```
feat(graphes): [description du changement]

Mise à jour des graphes Mermaid suite à [événement].
Sources : [liste].
```

Exemples :
- `feat(graphes): ajoute Aeris/Atlas/Terra à l'écosystème`
- `feat(graphes): marque les 14 moteurs GSIE implémentés`
- `feat(graphes): bascule Phase 4 en clôturée et active Phase 5`

## 5. Quand **ne pas** l'invoquer

- Pour un changement mineur qui n'affecte pas la vue d'ensemble
  (typo, refactor, test supplémentaire d'un moteur existant).
- Si la progression n'est pas encore traçable dans `PROJECT_MEMORY.md`
  ou `ROADMAP.md` (attendre la fin de la tâche et la mise à jour de la
  mémoire).

## 6. Fichiers concernés

```
graphes-quintessences/
├── public/
│   ├── index.html           ← généré, ne jamais éditer à la main
│   ├── favicon.svg
│   ├── css/main.css         ← thème clair/sombre, sidebar, cartes, modale
│   └── js/site.js           ← recherche, filtres, zoom/pan, thème, copie,
│                               code, plein écran, export SVG, nav active
├── diagrams/
│   ├── meta.json            ← ordre, catégorie, description, source, date
│   ├── 01_ecosysteme.mmd
│   ├── 02_chaine_intelligence.mmd
│   ├── 03_hierarchie_documentaire.mmd
│   ├── 04_phases_projet.mmd
│   ├── 05_moteurs_gsie.mmd
│   ├── 06_metamodele_encyclopedie.mmd
│   ├── 07_identite_quintessences.mmd
│   ├── 08_cycle_vie_document.mmd
│   ├── 09_pipeline_data_registry.mmd
│   ├── 10_architecture_mesh.mmd
│   ├── 11_hierarchie_territoriale.mmd
│   ├── 12_timeline_decisions.mmd
│   └── 13_applications_ecosysteme.mmd
└── generate_site.py         ← générateur HTML (stdlib uniquement)
```

`public/js/site.js` et `public/css/main.css` sont écrits à la main (pas
générés) : ne les régénérer jamais via `generate_site.py`, seul
`index.html` l'est.
