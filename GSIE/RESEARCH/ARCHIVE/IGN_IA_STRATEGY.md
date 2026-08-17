# Fiche recherche — IGN : stratégie IA, feuille de route et geocontext MCP

| Champ | Valeur |
|---|---|
| **Document** | RESEARCH/IGN_IA_STRATEGY |
| **Dossier** | GSIE/RESEARCH/ |
| **Phase** | 4 — Implémentation |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Sources primaires** | `GSIE/RESEARCH/ia_feuille_route_ign.pdf` (feuille de route IA IGN 2022-2024, 7 pages), `https://www.ign.fr/institut/ia-en-vigie-du-territoire`, `https://www.ign.fr/feuille-route-ia`, `https://github.com/ignfab/geocontext` |
| **Lois fondatrices** | CON-002 (science), CON-005 (traçabilité) |
| **Documents connexes** | `LIDAR_HD_SPECIFICATIONS.md`, `DATASET_CATALOG.md`, `GIS_001_SPECIFICATION.md` (à créer Phase 4), `COMMAND_CENTER_UNREAL.md` (livrable 211) |

---

## 1. Objet

Synthèse opérationnelle de la stratégie IA de l'IGN (feuille de route
2022-2024, page vigie IA, projet geocontext) pour exploitation dans
GSIE : datasets disponibles, outils MCP, alignement thématique avec
les moteurs.

---

## 2. Feuille de route IA IGN 2022-2024

### 2.1 Orientation : « Démocratiser l'IA »

L'IGN se donne pour boussole de produire des **cartes de
l'Anthropocène** (tous les 1-3 ans) sur les enjeux écologiques majeurs :

- **État de santé des forêts**
- **Érosion du relief et évolution des cours d'eau**
- **Artificialisation des sols**
- **Potentiel de biodiversité**
- Autres thèmes en appui aux politiques publiques

> **Alignement GSIE** : ces 5 thématiques correspondent exactement aux
> domaines des moteurs Forest Dynamics, Hydro, GIS, Botanical et
> Simulation. L'IGN est un partenaire naturel de la connaissance.

### 2.2 Trois objectifs stratégiques (horizon 2024)

1. **Entretenir et renforcer** les capacités techniques IA pour les
   grands projets d'automatisation
2. **Conserver une marge** pour R&D hors grands projets et structuration
   de **communs IA** pour l'information géographique et forestière
3. **Soutenir les communautés IA** pour la cartographie de
   l'Anthropocène et la transition écologique

### 2.3 Six axes

| Axe | Description | Pertinence GSIE |
|---|---|---|
| 1. Gouvernance transverse | Pilote, responsables d'actions, bonnes pratiques | Référence gouvernance |
| 2. Construire en commun | Géo-communs, open source deep learning, **diffusion datasets apprentissage LiDAR HD** | **Datasets GSIE** |
| 3. Rendre accessible l'IA | Formations initiales et pro, communs pédagogiques | Formation équipe |
| 4. Ressources | 30-40 ETP ingénieurs IA cible (vs 9 en 2021), pôle central d'experts | Référence capacité |
| 5. Mettre en débat et réguler | Régulation sociale et écologique du déploiement IA | Alignement CON-001 |
| 6. Orientations scientifiques | Apprentissage machine structurant | R&D conjointe |

### 2.4 Mesures clés pour GSIE

| Mesure | Détail | Impact GSIE |
|---|---|---|
| **Mesure 3** | Diffuser des jeux de données d'apprentissage dans le cadre du **programme LiDAR HD** | **Datasets ML-ready pour Learning Engine** |
| Mesure 3 | Porter et animer la diffusion ouverte d'outils deep learning pour l'information géographique et forestière | Outils candidats |
| Mesure 3 | Consortium **AI4GEO** (R&D télédétection) | Partenariat potentiel |
| Mesure 3 | Valoriser le patrimoine de données d'apprentissage | Source datasets |
| Mesure 4 | Intégrer solutions startups/industriels (forum IGNFab) | Veille techno |
| Mesure 4 | Partenariat stratégique GPU (2022-2024) | Calcul |

---

## 3. IA en vigie du territoire — produits et cas d'usage

### 3.1 CoSIA — Couverture du Sol par Intelligence Artificielle

| Champ | Valeur |
|---|---|
| **Résolution** | **20 cm par pixel** |
| **Méthode** | Deep learning sur images aériennes |
| **Production** | Depuis 2019 |
| **Sortie** | Cartes de prédiction de couverture des sols |
| **Usage** | Première estimation → traitements complémentaires → croisement données existantes |
| **Diffusion** | OCS GE (référentiel national) |

> **Implication GSIE** : CoSIA 20 cm est un **complément majeur** du
> LiDAR HD pour le Forest Dynamics Engine (couverture sol) et Ignis
> (combustible surface). À ajouter au DATASET_CATALOG.

### 3.2 OCS GE — Occupation du Sol à Grande Échelle

| Champ | Valeur |
|---|---|
| **Type** | Référentiel national d'occupation du sol |
| **Producteur** | IGN (pilote) |
| **Service** | État et collectivités |
| **Thématiques** | Imperméabilité, foncier, nature en ville, surfaces agricoles utiles, haies et bocages |
| **Méthode** | Télédétection d'objets par IA (habitations, végétation) + croisement données |
| **Mise à jour** | Continue |

> **Implication GSIE** : OCS GE est un **dataset de référence** pour
> le GIS Engine (occupation du sol), Forest Dynamics (surfaces
> agricoles/forestières), et Hydro (imperméabilité → ruissellement).

### 3.3 GéoLLM — interrogation naturelle des données IGN

| Champ | Valeur |
|---|---|
| **Type** | Model Context Protocol (MCP) |
| **Producteur** | IGNfab |
| **Statut** | Bêta test |
| **Fonction** | Connecter un LLM aux bases de données IGN |
| **Usage** | Poser des questions en langage naturel, croiser des données, générer des cartes sans compétences géomatiques |

> **Implication Hub** : GéoLLM est un **cas d'usage direct** du Centre
> de Commandement — interrogation naturelle des données IGN par les
> décideurs. Le MCP geocontext (§4) est l'implémentation technique.

### 3.4 Cartes de l'Anthropocène

L'IGN produit régulièrement des cartes sur :

| Thème | Moteur GSIE concerné |
|---|---|
| État de santé des forêts | Forest Dynamics, Botanical |
| Érosion du relief | GIS, Simulation |
| Évolution des cours d'eau | Hydro |
| Artificialisation des sols | GIS |
| Potentiel de biodiversité | Botanical, Forest Dynamics |

> **Alignement parfait** : les cartes de l'Anthropocène de l'IGN sont
> exactement les sorties attendues des moteurs GSIE. Partenariat
> naturel à explorer en Phase 4.

---

## 4. Geocontext — serveur MCP pour la Géoplateforme

### 4.1 Présentation

| Champ | Valeur |
|---|---|
| **Dépôt** | `github.com/ignfab/geocontext` |
| **Package** | `@ignfab/geocontext` (npm) |
| **Statut** | Prototype |
| **Type** | Serveur MCP (Model Context Protocol) |
| **Instance HTTP** | `https://geollm.beta.ign.fr/geocontext/mcp` |
| **Licence** | À vérifier (dépôt GitHub) |
| **Commits** | 208 |
| **Stars** | 23 |
| **Compatibilité** | Claude Desktop, Cursor, MCPJam, ChatGPT, Le Chat Mistral |

### 4.2 Outils MCP disponibles

| Outil MCP | Source GPF | Cas d'usage GSIE |
|---|---|---|
| `geocode` | Autocomplétion GPF | Localiser un lieu (Hub, tous moteurs) |
| `altitude` | Calcul altimétrique GPF | Altitude terrain (ForeFire, Hub, Simulation) |
| `adminexpress` | ADMIN-EXPRESS WFS | Commune, département, région (GIS) |
| `cadastre` | PARCELLAIRE-EXPRESS WFS | Parcelles cadastrales (GIS, foncier) |
| `urbanisme` | GPU WFS | PLU, POS, CC (GIS, urbanisme) |
| `assiette_sup` | GPU WFS | Servitudes d'utilité publique (GIS, Ignis) |
| `gpf_search_types` | gpf-schema-store | Trouver une couche GPF (découverte) |
| `gpf_describe_type` | gpf-schema-store | Schéma d'un type (intégration) |
| `gpf_count_features` | WFS GPF | Compter des features filtrées (statistiques) |
| `gpf_get_features` | WFS GPF | Récupérer des features (ingestion) |

### 4.3 Configuration Devin (projet)

Le MCP geocontext est configuré dans `.devin/config.json` :

```json
{
  "mcpServers": {
    "geocontext": {
      "url": "https://geollm.beta.ign.fr/geocontext/mcp",
      "transport": "http"
    }
  }
}
```

### 4.4 Exemples d'utilisation pour GSIE

| Question | Outils mobilisés | Sortie |
|---|---|---|
| « Combien de bâtiments > 20m à Vincennes ? » | geocode → gpf_search_types → gpf_describe_type → adminexpress → gpf_count_features | 509 bâtiments (BD TOPO) |
| « Altitude de la mairie de Vincennes » | geocode → altitude | Altitude précise (GPF) |
| « PLU en vigueur pour le port de Marseille » | geocode → urbanisme | Document PLU (GPU) |
| « Lycées à moins de 20 min à pied du métro Bérault » | geocode → isochrone → gpf_get_features | Liste lycées (BD TOPO) |
| « SUP autour de la mairie de Vincennes » | geocode → assiette_sup | Servitudes (GPU) |

### 4.5 Pertinence GSIE

| Moteur/App | Apport geocontext |
|---|---|
| **GIS Engine** | BD TOPO, ADMIN-EXPRESS, cadastre, PLU, SUP directement interrogeables |
| **Simulation Engine** | Altitude temps réel via `altitude` (ForeFire) |
| **Hub** | GéoLLM = interrogation naturelle par décideurs |
| **Forest Dynamics** | BD TOPO forêts, OCS GE |
| **Ignis** | SUP (servitudes), bâtiments à risque, altitude terrain |
| **Learning Engine** | Découverte de couches via `gpf_search_types` |

> **Recommandation** : geocontext est la **première brique
> d'interopérabilité** GSIE avec la Géoplateforme. À utiliser comme
> dépendance candidate pour le GIS Engine Phase 4. Le MCP est
> configuré dans Devin (`.devin/config.json`) et peut être testé
> immédiatement.

---

## 5. AI4GEO — consortium R&D télédétection

| Champ | Valeur |
|---|---|
| **Type** | Consortium |
| **Membres** | IGN + partenaires (industriels, recherche) |
| **Domaine** | R&D télédétection, deep learning |
| **Pertinence** | Méthodologie, briques de base pour l'IA géographique |

> **Implication** : AI4GEO est un **partenariat potentiel** pour GSIE
> Phase 4-5. Les briques développées (modèles, pipelines) pourraient
> être réutilisées ou adaptées pour les moteurs GSIE.

---

## 6. IGNfab — usine à POCs et démonstrateurs

| Champ | Valeur |
|---|---|
| **Type** | Structure IGN |
| **Rôle** | Usine à POCs, démonstrateurs, intégration solutions externes |
| **Produits** | geocontext (MCP), GéoLLM, gpf-schema-store |
| **Forum** | Intégration startups/industriels |

> **Implication** : IGNfab est le **point d'entrée naturel** pour
> explorer les briques IGN réutilisables dans GSIE. Le dépôt
> `ignfab/geocontext` est déjà intégré comme MCP.

---

## 7. Datasets IGN pour l'apprentissage (mesure 3)

La feuille de route prévoit la diffusion de :

| Dataset | Programme | Statut | Pertinence GSIE |
|---|---|---|---|
| **Jeux de données LiDAR HD** | Programme LiDAR HD | Diffusion en cours | Learning Engine, Forest Dynamics, Botanical |
| **Jeux OCS GE** | Suivi artificialisation | Court terme | GIS, Forest Dynamics |
| **Modèles entraînés** | Chaînes de production IGN | À diffuser | Learning Engine (transfer learning) |
| **Données d'apprentissage couverture du sol** | CoSIA | Diffusion | Botanical, Forest Dynamics |

> **Implication Learning Engine** : ces datasets sont directement
> exploitables pour entraîner les classificateurs d'essences
> (Botanical), de couverture du sol (GIS), et de structure forestière
> (Forest Dynamics). À référencer dans DATASET_CATALOG.

---

## 8. Recommandations pour la Phase 4

| ID | Recommandation | Moteur / App | Priorité |
|---|---|---|---|
| REC-IA-01 | Utiliser geocontext MCP pour interroger BD TOPO, cadastre, altitude, PLU, SUP | GIS Engine | P0 |
| REC-IA-02 | Intégrer CoSIA (20cm) comme couche de couverture du sol | Forest Dynamics, Ignis | P1 |
| REC-IA-03 | Référencer OCS GE comme dataset de référence occupation du sol | GIS Engine | P1 |
| REC-IA-04 | Évaluer les datasets apprentissage LiDAR HD pour le Learning Engine | Learning Engine | P1 |
| REC-IA-05 | Explorer partenariat AI4GEO pour R&D télédétection | Transverse | P2 |
| REC-IA-06 | Contacter IGNfab pour intégration de briques (geocontext, gpf-schema-store) | Transverse | P2 |
| REC-IA-07 | Cas d'usage GéoLLM dans le Hub (interrogation naturelle par décideurs) | Hub | P2 |
| REC-IA-08 | Aligner les sorties moteurs GSIE sur les cartes de l'Anthropocène IGN | Tous moteurs | P2 |

---

## 9. Critères d'acceptation

- [x] Feuille de route IA IGN documentée (3 objectifs, 6 axes, mesures clés)
- [x] Produits IA IGN référencés (CoSIA, OCS GE, GéoLLM, cartes Anthropocène)
- [x] Serveur MCP geocontext documenté (10 outils, configuration Devin)
- [x] Configuration MCP créée (`.devin/config.json`)
- [x] Datasets apprentissage IGN identifiés (LiDAR HD, OCS GE, CoSIA)
- [x] Alignement thématique IGN ↔ moteurs GSIE établi
- [x] AI4GEO et IGNfab référencés (partenariats potentiels)
- [x] 8 recommandations Phase 4 priorisées

---

> Statut : *Draft — fiche recherche Phase 4. Sources primaires :
> PDF feuille de route IA IGN + 3 pages web officielles. MCP geocontext
> configuré et testable. Aucun code métier (CON-003).*
