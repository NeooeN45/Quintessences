# JUNN — Veille partenariat : Jumeau Numérique National de la France

| Champ | Valeur |
|---|---|
| **Document** | JUNN_VEILLE |
| **Dossier** | 20_PARTNERSHIPS/ |
| **Phase** | 3 — Connaissance |
| **Statut** | Draft — veille stratégique (pas un partenariat actif) |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-005 (traçabilité), GSIE-CON-007 (modularité), GSIE-CON-008 (vision) |
| **Documents connexes** | `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211), `GSIE/ARCHITECTURE/GSIE_MASTER_ARCHITECTURE.md` (livrable 201), `PROJECT_MEMORY.md` |

---

## 1. Objet

Recenser le programme **JUNN** (Jumeau Numérique National) piloté par
l'IGN, le Cerema et Inria, comme **partenaire d'infrastructure souveraine
potentiel** pour l'écosystème Quintessences. Ce document est une **veille
stratégique**, pas un partenariat actif — aucune démarche de contact n'a
été engagée à ce jour.

---

## 2. Fiche d'identité JUNN

| Champ | Valeur |
|---|---|
| **Nom** | JUNN — Programme national des jumeaux numériques des territoires français |
| **Pilotes** | IGN, Cerema, Inria |
| **Coordination opérationnelle** | 1Spatial France |
| **Financement** | France 2030 — **25 M€** (Banque des territoires / Caisse des Dépôts) |
| **Lancement officiel** | 13 avril 2026 |
| **Horizon** | Premier ensemble opérationnel d'applications fin 2026 |
| **Site web** | https://junn.info |
| **Consortium** | 14 partenaires + 200+ acteurs intéressés dès 2024 |

### Partenaires recherche

- Inria, LASTIG (UGE-Géodata Paris), BRGM, CNES, IFPEN

### Partenaires industriels géo 3D

- Camptocamp, Siradel, IGO-Geofit, LuxCarta, GeometryFactory

### Pôle de compétitivité

- Cap Digital (animation filière géonumérique / data / IA)

---

## 3. Les 4 composantes du jumeau (définition IGN)

L'IGN définit le jumeau numérique national autour de 4 composantes. La
comparaison avec l'architecture Quintessences est frappante :

| # | Composante JUNN | Équivalent Quintessences |
|---|---|---|
| 1 | Données + maquette 3D + données métier connectées | `GSIE/DATASETS/` + Centre de Commandement (Cesium 3D) |
| 2 | Services de visualisation (immersive), interrogation, enrichissement, croisement | Centre de Commandement GSIE (livrable 211, Unreal Engine 5.8) |
| 3 | Simulateurs (approche thématique et systémique) | 14 moteurs GSIE (Simulation, Reasoning, Diagnostic...) |
| 4 | Place de sciences (écosystème recherche) | `GSIE/RESEARCH/` + `20_PARTNERSHIPS/` |

> **Lecture stratégique :** JUNN construit le **socle infrastructurel
> souverain** (données, visualisation, simulateurs génériques) ;
> Quintessences construit les **apps métier forestières/incendie** au-
> dessus. Les deux sont **complémentaires, pas concurrentes**.

---

## 4. Domaines couverts par JUNN

Le programme vise à outiller la transition écologique dans :

- Aménagement du territoire
- Transition énergétique
- **Gestion durable des ressources agricoles et forestières**
- **Prévention des risques naturels** (dont incendies)
- Adaptation au changement climatique
- Sensibilisation citoyenne (solutions immersives)

> Les domaines en **gras** sont exactement le périmètre de Quintessences
> (GeoSylva + Ignis + Hydro + Flora + Artemis).

---

## 5. Alignement stratégique avec Quintessences

| Critère | JUNN | Quintessences | Synergie |
|---|---|---|---|
| **Souveraineté** | Outil souverain open source (France 2030) | Constitution GSIE-CON-008 (vision) | JUNN = socle souverain, Quintessences = apps au-dessus |
| **Données** | Géoplateforme IGN (LiDAR HD, BD Forêt, BD Ortho) | DS-001 à DS-026 (même sources IGN) | Source de données commune — pas de duplication |
| **Visualisation 3D** | Maquette 3D nationale (à définir) | Centre de Commandement UE 5.8 + Cesium | Quintessences peut consommer la maquette JUNN comme couche de contexte |
| **Simulation** | Simulateurs génériques (multi-thématiques) | 14 moteurs spécialisés (forêt, feu, sol, climat) | Quintessences apporte la profondeur métier que JUNN ne couvrira pas |
| **Recherche** | Place de sciences (Inria, BRGM, CNES, IFPEN) | `GSIE/RESEARCH/` (FIRETWIN, ForeFire, etc.) | Accès à l'écosystème recherche JUNN pour Quintessences |
| **Financement** | 25 M€ France 2030 | `18_FINANCING/` (à structurer) | JUNN = levier de cofinancement potentiel |

---

## 6. Cas d'usage IGN LiDAR HD déjà validés (intersection JUNN / Quintessences)

Les cas d'usage documentés par l'IGN (`ign.fr/usages-des-donnees-lidar-hd`)
sont les **premiers briques du jumeau national** et correspondent
directement à nos apps :

| Cas d'usage IGN | App Quintessences | Acteur validé |
|---|---|---|
| Forêt (hauteur, accessibilité, dessertes) | GeoSylva | ONF, Arbonaut |
| Risque incendie (3 strates, continuité 0-3m, CCF) | Ignis | SDIS 63 |
| Hydrographie (morphologie cours d'eau) | Hydro | — |
| Risque inondation (topographie zones inondables) | Hydro | — |
| Végétation urbaine (canopée, strates) | Flora | — |

---

## 7. Actions recommandées (veille, pas engagement)

| # | Action | Priorité | Quand |
|---|---|---|---|
| 1 | **Surveiller junn.info** — premiers jeux de données tests mi-2026, premier ensemble opérationnel fin 2026 | Haute | Continu |
| 2 | **Identifier le contact IGN JUNN** (programme LiDAR HD — déjà notre contact DS-002) | Moyenne | Quand GeoSylva MVP approche |
| 3 | **Évaluer l'interopérabilité** : la maquette 3D JUNN est-elle consommable via Cesium for Unreal (3D Tiles) ? | Moyenne | Quand JUNN publie sa maquette |
| 4 | **Explorer le cofinancement France 2030** pour Quintessences (via JUNN ou appel à communs) | Basse | Phase 4 |
| 5 | **Contact Cap Digital** (pôle géonumérique) pour entrer dans l'écosystème JUNN | Basse | Phase 4 |

---

## 8. Garde-fous

- Ce document est une **veille**, pas un partenariat. Aucune démarche
  officielle n'est engagée.
- Un partenariat réel nécessiterait une **décision tracée** (`DEC-`) et
  l'accord du Fondateur (GSIE-CON-001).
- JUNN est un programme **public souverain** — aucune exclusivité ni
  dépendance commerciale à craindre (contrairement à un partenaire
  privé).
- L'architecture Quintessences reste **modulaire** (CON-007) : JUNN est
  un socle potentiel, pas une dépendance. Le Centre de Commandement
  fonctionne avec ou sans JUNN.

---

> Statut : *Draft — veille stratégique Phase 3. À convertir en
> partenariat actif (décision `DEC-`) si le Fondateur valide l'approche.*
