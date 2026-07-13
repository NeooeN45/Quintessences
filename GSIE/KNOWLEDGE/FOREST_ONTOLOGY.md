# GSIE Forest Ontology — Ontologie forestière complète

| Champ | Valeur |
|---|---|
| **Livrable** | 303 — Forest Ontology (complète) |
| **Phase** | 3 — Connaissance |
| **Statut** | Draft |
| **Date de révision** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-003 |
| **Constitutions liées** | Scientifique (S-6 — Domaines de connaissance) |
| **Directive d'ouverture** | GSIE-DIR-0007 (DEC-000011) |
| **Directives alignées** | GSIE-DIR-0006 (raisonnement multi-échelle, graphe vivant) |
| **Documents connexes** | `GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md` (302), `GSIE/KNOWLEDGE/KNOWLEDGE_GRAPH_SPECIFICATION.md` (304), `GSIE/RESEARCH/RESEARCH_METHOD.md` (301), `GSIE/RESEARCH/EVIDENCE_FRAMEWORK.md` (306), `GSIE/DATASETS/DATASET_CATALOG.md` (305) |

---

## 1. Objet

Définir l'**ontologie forestière** de GSIE : l'ensemble structuré des
concepts, propriétés mesurables, relations et référentiels qui décrivent le
domaine forestier français métropolitain (et, par extension, ultramarin).

Cette ontologie opérationnalise l'article **S-6** de la Constitution
Scientifique, qui fixe les dix domaines de connaissance couverts par GSIE.
Elle fournit au **Knowledge Engine** (livrable 206) et au **Knowledge Graph**
(livrable 304) le vocabulaire contrôlé nécessaire à la représentation
explicable du monde forestier.

L'ontologie est :

- **sourcée** — chaque concept renvoie à un référentiel réel (S-1) ;
- **versionnée** — toute évolution est tracée (CON-010, S-7) ;
- **multi-échelle** — alignée sur DIR-0006 (arbre → peuplement → massif →
  paysage) ;
- **explicable** — les relations sont nommées et justifiées (CON-004).

Conformément à CON-003, l'ontologie est un **actif de connaissance**, pas un
artefact de code. Elle vit dans `GSIE/KNOWLEDGE/` et est consommée par les
moteurs, jamais dupliquée dans le code métier.

---

## 2. Structure de l'ontologie

### 2.1 Principes structurants

L'ontologie est organisée en **10 domaines** correspondant strictement à
l'article S-6. Chaque domaine est un module autonome possédant :

- un **identifiant de domaine** (ex. `DOM-ECO`) ;
- un ensemble de **concepts clés** (5 à 10 par domaine) ;
- des **propriétés mesurables** (avec unité et référentiel) ;
- des **relations** vers les autres domaines ;
- un ou plusieurs **référentiels** institutionnels (INRAE, IGN, ONF, GBIF,
  RPF, WRB, etc.).

### 2.2 Hiérarchie conceptuelle

```
Domaine (S-6)
  └── Concept
        ├── Définition
        ├── Propriétés mesurables (unité, référentiel)
        ├── Relations (prédicats nommés)
        └── Référentiels de rattachement
```

Chaque concept de l'ontologie est destiné à devenir un `KnowledgeObject` de
type `concept` ou `classification` (voir livrable 302, §3). Les relations
deviennent des `KnowledgeObject` de type `relation`. Les seuils et modèles
associés (livrable 308) sont des types `seuil` et `modele`.

### 2.3 Identifiants de domaine

| Code | Domaine (S-6) | Moteur principal |
|---|---|---|
| `DOM-ECO` | Écologie forestière et stationnelle | Forest Dynamics Engine |
| `DOM-PED` | Pédologie | Pedology Engine |
| `DOM-DEN` | Dendrométrie et croissance | Forest Dynamics Engine |
| `DOM-CLI` | Climatologie et bioclimatologie | Climate Engine |
| `DOM-BOT` | Botanique et taxonomie | Botanical Engine |
| `DOM-PAT` | Pathologie forestière | Diagnostic Engine |
| `DOM-ENT` | Entomologie forestière | Diagnostic Engine |
| `DOM-SYL` | Sylviculture et gestion | Recommendation Engine |
| `DOM-BIO` | Biodiversité et conservation | Diagnostic Engine |
| `DOM-DYN` | Dynamique des peuplements | Forest Dynamics Engine |

### 2.4 Types de concepts

Conformément au livrable 302, les concepts de cette ontologie se
matérialisent sous les six types de `KnowledgeObject` :

| Type | Rôle dans l'ontologie | Exemple |
|---|---|---|
| `concept` | Notion scientifique définie | « Station forestière » |
| `relation` | Lien entre concepts | « chêne sessile `est_adapte_a` sol acide » |
| `regle` | Règle d'inférence | « SI pH ∈ [4,5 ; 6,0] ALORS chêne sessile adapté » |
| `seuil` | Valeur seuil | « RUM minimale hêtre = 80 mm » |
| `modele` | Modèle scientifique | « ONF-FFN, douglas » |
| `classification` | Taxonomie référentielle | « Alocrisol (RPF) » |

---

## 3. Domaine `DOM-ECO` — Écologie forestière et stationnelle

### 3.1 Concepts clés

| Concept | Définition | Référentiel |
|---|---|---|
| Station forestière | Portion de territoire homogène par ses conditions écologiques (climat, sol, relief) déterminant la productivité et la composition floristique | Catalogues des stations (INRAE, ONF) |
| Type de station | Unité de classification stationnelle définie par une combinaison de facteurs écologiques | Catalogues régionaux INRAE |
| Groupement végétal | Communauté végétale caractéristique d'un type de station | Phytoécologie (Bardat et al., 2004) |
| Synusie | Sous-ensemble homogène d'une communauté (strate herbacée, strate arbustive) | Phytosociologie sigmatiste |
| Bio-indicateur | Espèce dont la présence indique une condition écologique (pH, humidité, trophie) | Base ECOPHYTO (INRAE) |
| Nitrocline | Seuil de nutrition azotée traduit par la composition floristique | Dupouey et al. (2011) |
| Réserve utile en eau (RUM) | Quantité d'eau maximale que le sol retient et met à disposition des plantes | RPF (INRAE) |
| Potentialité forestière | Aptitude d'une station à produire une essence donnée | Catalogues INRAE/ONF |
| Facteur limitant | Variable écologique qui contraint la croissance ou la présence d'une essence | Autécologie (Rameau et al.) |
| Étage de végétation | Bande altitudinale/latitudinale homogène du point de vue climatique | Ozenda (1982), Rameau (1994) |

### 3.2 Propriétés mesurables

| Propriété | Unité | Référentiel / source |
|---|---|---|
| RUM | mm | RPF, INRAE |
| pH eau | unité pH | RPF |
| Altitude | m | IGN BD Ortho |
| Exposition | degrés | IGN |
| Pente | % | IGN |
| Indice trophique | indice | ECOPHYTO |
| Recouvrement strates | % | Relevés phytoécologiques |

### 3.3 Relations avec autres domaines

| Relation | Domaine cible | Description |
|---|---|---|
| `depend_de` | `DOM-PED` | La station dépend des propriétés du sol |
| `depend_de` | `DOM-CLI` | La station dépend du climat local |
| `determine` | `DOM-BOT` | La station détermine les groupements végétaux |
| `influence` | `DOM-DEN` | La station influence la croissance |
| `est_valide_par` | `DOM-SYL` | Les potentialités sont validées par la sylviculture |

### 3.4 Référentiels

- **Catalogues des types de stations** — INRAE, ONF (par région forestière).
- **RPF (Référentiel Pédologique Forestier)** — INRAE, 2008 (Baize & Jabiol).
- **ECOPHYTO** — base de bio-indication floristique (INRAE).
- **Phytosociologie sigmatiste** — Bardat et al. (2004), Prodrome des
  végétations de France.

---

## 4. Domaine `DOM-PED` — Pédologie

### 4.1 Concepts clés

| Concept | Définition | Référentiel |
|---|---|---|
| Sol | Corps naturel tridimensionnel à la surface de la terre, résultant de l'altération de la roche mère | WRB (IUSS) |
| Horizon | Couche du sol homogène et parallèle à la surface | RPF, WRB |
| Profil pédologique | Succession verticale d'horizons | RPF |
| Roche mère | Matériau parental à partir duquel le sol s'est développé | Carte géologique BRGM |
| Texture | Granulométrie (sable, limon, argile) | Triangle USDA / GEPPA |
| Structure | Organisation des agrégats du sol | RPF |
| Réserve utile en eau (RUM) | Eau disponible pour les plantes (cf. DOM-ECO) | RPF |
| Humus | Couche superficielle organique | RPF (formes d'humus) |
| Drainage | Capacité du sol à évacuer l'eau excédentaire | RPF |
| Référentiel pédologique | Système de classification des sols français | RPF (INRAE 2008) |

### 4.2 Propriétés mesurables

| Propriété | Unité | Référentiel / source |
|---|---|---|
| Profondeur de sol | cm | RPF |
| pH eau (1:2,5) | unité pH | RPF, norme AFNOR |
| Texture (argile/limon/sable) | % | GEPPA / USDA |
| CEC (capacité d'échange cationique) | cmol+/kg | RPF |
| Matière organique | % | RPF |
| RUM | mm | RPF |
| Indice de drainage | classe | RPF |
| CaCO3 total | % | RPF |

### 4.3 Relations avec autres domaines

| Relation | Domaine cible | Description |
|---|---|---|
| `determine` | `DOM-ECO` | Le sol détermine la station |
| `influence` | `DOM-BOT` | Le sol influence la flore |
| `influence` | `DOM-DEN` | Le sol influence la croissance |
| `depend_de` | `DOM-CLI` | La pédogenèse dépend du climat |
| `influence` | `DOM-PAT` | Le sol influence les pathologies racinaires |

### 4.4 Référentiels

- **RPF (Référentiel Pédologique Forestier)** — INRAE, Baize & Jabiol (2008).
- **WRB (World Reference Base for Soil Resources)** — IUSS, 2014/2015.
- **Carte géologique** — BRGM (InfoGéol).
- **Triangle textural GEPPA / USDA** — classification granulométrique.

---

## 5. Domaine `DOM-DEN` — Dendrométrie et croissance

### 5.1 Concepts clés

| Concept | Définition | Référentiel |
|---|---|---|
| Dendrométrie | Mesure quantitative des arbres et peuplements | IGN, ONF |
| Diamètre à hauteur de poitrine (DHP, 1,30 m) | Diamètre mesuré à 1,30 m du sol | Norme IGN |
| Hauteur dominante (hdom) | Hauteur des 100 plus gros arbres par hectare | IGN, ONF |
| Surface terrière (G) | Somme des sections des arbres à 1,30 m, par hectare | IGN |
| Volume bois fort tige | Volume de la tige au-dessus de 7 cm de diamètre | IGN, ONF |
| Accroissement courant | Accroissement annuel en volume ou circonférence | IGN IFN |
| Indice de productivité (classe de fertilité) | Niveau de production potentielle d'une station | IGN, ONF |
| Densité de peuplement | Nombre d'arbres par hectare | IGN |
| Indice de densité relative | Rapport entre densité observée et densité maximale | Reineke (1933) |
| Forme de la tige (décroissance) | Profil de la tige du sol à la cime | ONF, tarifs de cubage |

### 5.2 Propriétés mesurables

| Propriété | Unité | Référentiel / source |
|---|---|---|
| DHP | cm | IGN BD Forêt |
| Hauteur totale | m | IGN, lidar |
| Surface terrière (G) | m²/ha | IGN |
| Volume | m³/ha | IGN IFN |
| Accroissement | m³/ha/an | IGN IFN |
| Densité | tiges/ha | IGN |
| Âge | années | IGN (carottes) |

### 5.3 Relations avec autres domaines

| Relation | Domaine cible | Description |
|---|---|---|
| `depend_de` | `DOM-ECO` | La croissance dépend de la station |
| `depend_de` | `DOM-PED` | La croissance dépend du sol |
| `depend_de` | `DOM-CLI` | La croissance dépend du climat |
| `alimente` | `DOM-DYN` | Les mesures dendrométriques alimentent la dynamique |
| `alimente` | `DOM-SYL` | Les mesures guident les décisions sylvicoles |

### 5.4 Référentiels

- **IGN BD Forêt** — carte forestière vectorielle (ex-IFN).
- **IGN IFN (Inventaire Forestier National)** — données de terrain
  systématiques (5 000 points/an en plaine, 10 000 en montagne).
- **ONF — tarifs de cubage** — équations de volume par essence.
- **INRAE — modèles de croissance** (ONF-FFN, MARGINAL, capsis).

---

## 6. Domaine `DOM-CLI` — Climatologie et bioclimatologie

### 6.1 Concepts clés

| Concept | Définition | Référentiel |
|---|---|---|
| Climat | Ensemble des conditions atmosphériques moyennes sur une longue période | Météo-France, IPCC |
| Bioclimat | Climat interprété du point de vue de la végétation | Rameau (1994), Ozenda |
| Étage bioclimatique | Bande altitudinale définie par des seuils thermiques et hydriques | Rameau, Ozenda |
| Diagramme ombrothermique | Représentation des précipitations et températures mensuelles | Gaussen & Bagnouls |
| Déficit hydrique climatique | Différence entre ETP et précipitations sur une période | Météo-France, INRAE |
| ETP (évapotranspiration potentielle) | Quantité d'eau évaporée par une surface couverte de végétation bien alimentée | Météo-France (Penman-Monteith) |
| Indice d'aridité | Rapport précipitations/ETP | UNEP, Météo-France |
| Gel tardif | Gel survenant après le débourrement | Météo-France, INRAE |
| Sécheresse édaphique | Déficit hydrique du sol | INRAE, RPF |
| Changement climatique | Évolution à long terme des paramètres climatiques | DRIAS (Météo-France) |

### 6.2 Propriétés mesurables

| Propriété | Unité | Référentiel / source |
|---|---|---|
| Température moyenne annuelle | °C | Météo-France (SAFRAN) |
| Précipitations annuelles | mm | Météo-France |
| ETP | mm | Météo-France (Penman-Monteith) |
| Déficit hydrique climatique | mm | Météo-France, INRAE |
| Nombre de jours de gel | jours | Météo-France |
| Date de débourrement | jour julien | INRAE (phénologie) |
| Indice d'aridité | sans unité | UNEP |

### 6.3 Relations avec autres domaines

| Relation | Domaine cible | Description |
|---|---|---|
| `determine` | `DOM-ECO` | Le bioclimat détermine les étages de végétation |
| `influence` | `DOM-DEN` | Le climat influence la croissance |
| `influence` | `DOM-PAT` | Le climat influence les pathologies |
| `influence` | `DOM-ENT` | Le climat influence les pullulations d'insectes |
| `influence` | `DOM-DYN` | Le climat influence la dynamique des peuplements |

### 6.4 Référentiels

- **Météo-France — SAFRAN, ARPEGE, AROME** — réanalyses et prévisions.
- **DRIAS (Météo-France)** — scénarios climatiques régionalisés (RCP/SSP).
- **Ozenda (1982), Rameau (1994)** — étages de végétation.
- **IPCC / GIEC** — scénarios globaux.

---

## 7. Domaine `DOM-BOT` — Botanique et taxonomie

### 7.1 Concepts clés

| Concept | Définition | Référentiel |
|---|---|---|
| Espèce | Unité taxonomique de base regroupant des individus interféconds | GBIF, BDNFF, Tela Botanica |
| Genre | Rang taxonomique regroupant des espèces apparentées | GBIF, BDNFF |
| Famille | Rang taxonomique regroupant des genres | APG IV (2016) |
| Essence | Espèce arborée constitutive des peuplements forestiers | IGN BD Forêt |
| Essence objective | Essence visée par la sylviculture | ONF, CRPF |
| Essence accompagnatrice | Essence secondaire favorisant l'objectif | ONF, CRPF |
| Autécologie | Écologie individuelle d'une espèce | Rameau et al. (2008) |
| Synécologie | Écologie des communautés végétales | Phytosociologie |
| Plante bio-indicatrice | Espèce indicatrice de conditions écologiques | ECOPHYTO (INRAE) |
| Provenance | Origine géographique d'un matériel forestier de reproduction | Registre ONF, FRM |

### 7.2 Propriétés mesurables

| Propriété | Unité | Référentiel / source |
|---|---|---|
| Nom scientifique | texte | GBIF, BDNFF |
| Nom vernaculaire | texte | BDNFF, Tela Botanica |
| Statut de protection | enum | INPN (MNHN) |
| Rareté / menaces | enum (UICN) | Liste rouge UICN France |
| Exigences autécologiques | structure | Rameau et al. (2008) |
| Phénologie (débourrement, floraison) | jour julien | INRAE |

### 7.3 Relations avec autres domaines

| Relation | Domaine cible | Description |
|---|---|---|
| `est_adapte_a` | `DOM-ECO` | Une essence est adaptée à un type de station |
| `croit_mieux_sur` | `DOM-PED` | Une essence pousse mieux sur un type de sol |
| `est_substituable_par` | `DOM-BOT` | Substitution d'essence (chêne sessile ↔ hêtre) |
| `est_hote_de` | `DOM-PAT` | Une essence est hôte d'un pathogène |
| `est_hote_de` | `DOM-ENT` | Une essence est hôte d'un insecte |

### 7.4 Référentiels

- **GBIF (Global Biodiversity Information Facility)** — taxonomie mondiale.
- **BDNFF (Base de Données Nomenclaturale de la Flore de France)** —
  nomenclature française, Tela Botanica / F. Bioret.
- **Tela Botanica** — réseau et base collaborative de la flore francophone.
- **APG IV (2016)** — classification phylogénétique des angiospermes.
- **INPN (MNHN)** — statuts de protection et listes rouges UICN France.
- **Rameau, Mansion, Dumé (2008)** — Flore forestière française (autécologie).

---

## 8. Domaine `DOM-PAT` — Pathologie forestière

### 8.1 Concepts clés

| Concept | Définition | Référentiel |
|---|---|---|
| Pathogène | Organisme causant une maladie chez un arbre | DSF (Département Santé des Forêts) |
| Maladie cryptogamique | Maladie causée par un champignon | DSF, INRAE |
| Rouille | Maladie fongique produisant des pustules orangées | DSF |
| Chancre | Lésion corticale localisée | DSF |
| Pourriture | Décomposition du bois par des champignons lignicoles | DSF |
| Dépérissement | Déclin progressif de la vitalité d'un arbre ou peuplement | DSF, INRAE |
| Symptôme | Manifestation observable d'une maladie | DSF |
| Agent biotique | Pathogène vivant (champignon, bactérie, virus, oomycète) | DSF |
| Agent abiotique | Facteur non vivant causant des dommages (gel, sécheresse) | DSF |
| Foyer | Zone localisée d'attaque pathologique | DSF (BCF) |

### 8.2 Propriétés mesurables

| Propriété | Unité | Référentiel / source |
|---|---|---|
| Taux de défoliation | % (classes 0-4) | ICP Forests, DSF |
| Taux de mortalité | % | IGN, DSF |
| Intensité d'attaque | classe | DSF |
| Surface touchée | ha | DSF (BCF) |
| Classes de dépérissement | 0-4 | ICP Forests (Level I/II) |

### 8.3 Relations avec autres domaines

| Relation | Domaine cible | Description |
|---|---|---|
| `cible` | `DOM-BOT` | Un pathogène cible une essence |
| `est_favorise_par` | `DOM-CLI` | Un pathogène est favorisé par le climat |
| `est_favorise_par` | `DOM-SYL` | Un pathogène est favorisé par la sylviculture |
| `influence` | `DOM-DYN` | Les pathologies influencent la dynamique |
| `depend_de` | `DOM-ENT` | Co-interactions insectes/pathogènes |

### 8.4 Référentiels

- **DSF (Département Santé des Forêts)** — Ministère de l'Agriculture, réseau
  d'observatoires (BCF — Bilan de la Santé des Forêts).
- **INRAE — unités MYCSA, BIOGECO** — recherche en pathologie forestière.
- **ICP Forests (International Co-operative Programme)** — réseau européen
  de suivi (Level I et II).
- **EPPO (European and Mediterranean Plant Protection Organization)** —
  organismes de quarantaine.

---

## 9. Domaine `DOM-ENT` — Entomologie forestière

### 9.1 Concepts clés

| Concept | Définition | Référentiel |
|---|---|---|
| Ravageur | Insecte causant des dégâts aux arbres ou peuplements | DSF, INRAE |
| Défoliateur | Insecte consommant les feuilles/aiguilles | DSF |
| Xylophage | Insecte se nourrissant de bois | INRAE, ONF |
| Scolyte | Coléoptère creusant des galeries sous l'écorce | DSF, INRAE |
| Pullulation | Augmentation explosive d'une population | DSF |
| Cycle de vie | Succession de stades (œuf, larve, nymphe, adulte) | INRAE |
| Stade larvaire | Phase de développement entre œuf et adulte | INRAE |
| Hôte | Espèce végétale servant de support à l'insecte | DSF |
| Auxiliaire | Insecte prédateur ou parasite d'un ravageur | INRAE |
| Piégeage | Méthode de suivi des populations (phéromones) | DSF |

### 9.2 Propriétés mesurables

| Propriété | Unité | Référentiel / source |
|---|---|---|
| Densité de population | individus/m² ou /piège | DSF |
| Surface défoliée | ha | DSF, IGN (télédétection) |
| Taux d'attaque | % | DSF |
| Nombre de générations/an | entier | INRAE |

### 9.3 Relations avec autres domaines

| Relation | Domaine cible | Description |
|---|---|---|
| `cible` | `DOM-BOT` | Un ravageur cible une essence |
| `est_favorise_par` | `DOM-CLI` | Les pullulations sont favorisées par le climat |
| `interagit_avec` | `DOM-PAT` | Insectes vecteurs de pathogènes |
| `influence` | `DOM-DYN` | Les ravageurs influencent la dynamique |
| `est_surveille_par` | `DOM-SYL` | La sylviculture surveille et gère les ravageurs |

### 9.4 Référentiels

- **DSF** — réseau de surveillance entomologique (BCF).
- **INRAE — unité Zoologie Forestière** (Orléans).
- **INPN (MNHN)** — inventaire des insectes forestiers.
- **IGN — télédétection des défoliations** (satellite, drone).

---

## 10. Domaine `DOM-SYL` — Sylviculture et gestion

### 10.1 Concepts clés

| Concept | Définition | Référentiel |
|---|---|---|
| Sylviculture | Ensemble des pratiques appliquées au peuplement pour atteindre un objectif | ONF, CRPF, IDF |
| Itinéraire sylvicole | Succession d'opérations appliquées à un peuplement sur sa durée de vie | ONF, IDF |
| Régénération | Mise en place d'une nouvelle génération d'arbres | ONF |
| Régénération naturelle | Régénération par semis provenant des arbres en place | ONF |
| Plantation | Régénération par introduction de plants | ONF, FRM |
| Éclaircie | Prélèvement partiel d'arbres pour favoriser les restants | ONF, IDF |
| Coupe définitive | Coupe finale d'un peuplement arrivé à maturité | ONF |
| Futaie régulière | Peuplement d'âge uniforme | ONF, IGN |
| Futaie irrégulière | Peuplement d'âges mélangés (mélange futaie-jardinée) | ONF |
| Taillis-sous-futaie | Régime mixte combinant taillis et réserves | ONF, IGN |
| Cycle / révolution | Durée entre deux régénérations | ONF, IDF |
| Densité initiale | Nombre de plants/tiges à la plantation ou régénération | ONF, CRPF |

### 10.2 Propriétés mesurables

| Propriété | Unité | Référentiel / source |
|---|---|---|
| Densité de plantation | tiges/ha | ONF, CRPF |
| Intensité d'éclaircie | % surface terrière prélevée | ONF, IDF |
| Âge d'exploitabilité | années | ONF, IDF |
| Volume prélevé | m³/ha | ONF, IGN |
| Surface régénérée | ha | ONF |

### 10.3 Relations avec autres domaines

| Relation | Domaine cible | Description |
|---|---|---|
| `applique` | `DOM-DYN` | La sylviculture applique des choix à la dynamique |
| `depend_de` | `DOM-ECO` | Les itinéraires dépendent de la station |
| `depend_de` | `DOM-BOT` | Les itinéraires dépendent de l'essence objective |
| `gere` | `DOM-PAT` | La sylviculture gère les risques sanitaires |
| `gere` | `DOM-ENT` | La sylviculture gère les ravageurs |
| `alimente` | `DOM-BIO` | La sylviculture influence la biodiversité |

### 10.4 Référentiels

- **ONF — guides de sylviculture** (par essence et région).
- **CRPF (Centres Régionaux de la Propriété Forestière)** — recommandations
  pour la forêt privée.
- **IDF (Institut pour le Développement Forestier)** — guides techniques.
- **IGN BD Forêt** — types de peuplements et régimes forestiers.
- **Code forestier** — cadre légal français.

---

## 11. Domaine `DOM-BIO` — Biodiversité et conservation

### 11.1 Concepts clés

| Concept | Définition | Référentiel |
|---|---|---|
| Biodiversité | Diversité du vivant à trois niveaux (génétique, spécifique, écosystémique) | MNHN, INPN |
| Habitat forestier | Milieu naturel défini par sa flore et sa faune | Eurhabitat, EUNIS |
| Habitat d'intérêt communautaire | Habitat listé à l'annexe I de la directive Habitats | Natura 2000 |
| Espèce patrimoniale | Espèce remarquable justifiant des mesures de conservation | MNHN, listes rouges UICN |
| Espèce invasive | Espèce exotique envahissante perturbant les écosystèmes | INPN, EEE |
| Corridor écologique | Continuité spatiale permettant le déplacement des espèces | SRCE, TVB |
| Trame verte et bleue (TVB) | Réseau écologique national | Grenelle, SRCE |
| Zone protégée | Espace à statut de conservation (réserve, parc, Natura 2000) | INPN |
| Micro-habitat | Structure locale (cavité, bois mort) abritant des espèces | INRAE, MNHN |
| Bois mort | Bois mort sur pied ou au sol, support de saproxyliques | INRAE, MNHN |

### 11.2 Propriétés mesurables

| Propriété | Unité | Référentiel / source |
|---|---|---|
| Richesse spécifique | nombre d'espèces | INPN, MNHN |
| Indice de Shannon | indice | MNHN |
| Volume de bois mort | m³/ha | IGN, INRAE |
| Surface d'habitat | ha | INPN, Natura 2000 |
| Nombre d'espèces patrimoniales | entier | MNHN |

### 11.3 Relations avec autres domaines

| Relation | Domaine cible | Description |
|---|---|---|
| `depend_de` | `DOM-BOT` | La biodiversité dépend de la flore |
| `depend_de` | `DOM-SYL` | La biodiversité dépend de la sylviculture |
| `depend_de` | `DOM-DYN` | La biodiversité dépend de la dynamique |
| `influence` | `DOM-ECO` | La biodiversité reflète l'état écologique |
| `est_valide_par` | `DOM-CLI` | La distribution des espèces est validée par le climat |

### 11.4 Référentiels

- **INPN (Inventaire National du Patrimoine Naturel)** — MNHN.
- **Listes rouges UICN France** — statut de menace des espèces.
- **Natura 2000** — directives Habitats (92/43/CEE) et Oiseaux
  (2009/147/CE).
- **EUNIS / Eurhabitat** — classification européenne des habitats.
- **SRCE / TVB** — Schéma Régional de Cohérence Écologique.

---

## 12. Domaine `DOM-DYN` — Dynamique des peuplements

### 12.1 Concepts clés

| Concept | Définition | Référentiel |
|---|---|---|
| Dynamique des peuplements | Évolution temporelle d'un peuplement (structure, composition, croissance) | INRAE, ONF |
| Succession secondaire | Évolution de la végétation après perturbation | INRAE, phytoécologie |
| Cycle sylvogénétique | Cycle naturel de développement d'un peuplement | ONF, INRAE |
| Stade de développement | Phase du cycle (semis, gaulis, perchis, futaie jeune, futaie adulte) | ONF, IGN |
| Recrutement | Entrée de jeunes arbres dans la strate mesurée | IGN IFN |
| Mortalité | Taux d'arbres mourant par unité de temps | IGN, INRAE |
| Autoéclaircie | Réduction naturelle de la densité avec l'âge | Reineke, Yoda |
| Mélange d'essences | Composition multi-spécifique d'un peuplement | INRAE, ONF |
| Régénération naturelle | Renouvellement par semis (cf. DOM-SYL) | ONF |
| Perturbation | Événement modifiant la structure (tempête, incendie, attaque) | IGN, DSF |

### 12.2 Propriétés mesurables

| Propriété | Unité | Référentiel / source |
|---|---|---|
| Taux de recrutement | %/an | IGN IFN |
| Taux de mortalité | %/an | IGN IFN, INRAE |
| Structure diamétrique | distribution | IGN |
| Indice de mélange | indice | INRAE |
| Âge moyen | années | IGN |
| Surface terrière | m²/ha | IGN |

### 12.3 Relations avec autres domaines

| Relation | Domaine cible | Description |
|---|---|---|
| `depend_de` | `DOM-DEN` | La dynamique dépend des mesures dendrométriques |
| `depend_de` | `DOM-ECO` | La dynamique dépend de la station |
| `depend_de` | `DOM-CLI` | La dynamique dépend du climat |
| `influence` | `DOM-SYL` | La dynamique guide les choix sylvicoles |
| `influence` | `DOM-BIO` | La dynamique influence la biodiversité |
| `est_perturbe_par` | `DOM-PAT` | Les pathologies perturbent la dynamique |
| `est_perturbe_par` | `DOM-ENT` | Les ravageurs perturbent la dynamique |

### 12.4 Référentiels

- **IGN IFN** — données de suivi permanent (ré-observations).
- **INRAE — modèles de dynamique** (capsis, MARGINAL, ONF-FFN).
- **ONF — réseaux de placettes permanentes** (RPS).
- **ICP Forests Level II** — suivi intensif européen.

---

## 13. Échelles de raisonnement (alignement DIR-0006)

DIR-0006 exige un raisonnement **multi-échelle** : le moteur cognitif
raisonne simultanément à plusieurs niveaux d'organisation. L'ontologie doit
donc expliciter, pour chaque concept, l'échelle à laquelle il s'applique.

### 13.1 Les quatre échelles GSIE

| Échelle | Code | Entité principale | Ordre de grandeur |
|---|---|---|---|
| Arbre | `EC-ARB` | Individu arbre | 1 entité (cm à m) |
| Peuplement | `EC-PEU` | Parcelle / peuplement homogène | 0,1 à 50 ha |
| Massif | `EC-MAS` | Massif forestier continu | 10² à 10⁴ ha |
| Paysage | `EC-PAY` | Mosaïque de massifs, territoire | 10⁴ à 10⁶ ha |

> Note : DIR-0006 mentionne également les échelles pixel, département,
> région et pays. Pour l'ontologie forestière, les quatre échelles ci-dessus
> sont les unités sémantiques de référence ; les échelles administrative et
> pixel sont des projections spatiales, gérées par le GIS Engine.

### 13.2 Attribution des concepts par échelle

| Concept | Échelle(s) | Domaine |
|---|---|---|
| DHP, hauteur d'un arbre | `EC-ARB` | DOM-DEN |
| Pathogène sur un arbre | `EC-ARB` | DOM-PAT |
| Ravageur sur un arbre | `EC-ARB` | DOM-ENT |
| Station forestière | `EC-PEU` | DOM-ECO |
| Sol (profil) | `EC-PEU` | DOM-PED |
| Type de peuplement | `EC-PEU` | DOM-SYL |
| Surface terrière (G) | `EC-PEU` | DOM-DEN |
| Dynamique d'un peuplement | `EC-PEU` | DOM-DYN |
| Étage bioclimatique | `EC-MAS` | DOM-CLI |
| Massif forestier | `EC-MAS` | DOM-SYL |
| Foyer pathologique | `EC-MAS` | DOM-PAT |
| Pullulation de ravageur | `EC-MAS` | DOM-ENT |
| Trame verte et bleue | `EC-PAY` | DOM-BIO |
| Paysage forestier | `EC-PAY` | DOM-BIO |
| Changement climatique | `EC-PAY` | DOM-CLI |

### 13.3 Relations inter-échelles

DIR-0006 stipule que « chaque niveau échange avec les autres ». L'ontologie
définit les prédicats de transition :

| Prédicat | Description | Exemple |
|---|---|---|
| `agrege_en` | Une entité d'échelle n agrège des entités d'échelle n-1 | Arbres `agrege_en` peuplement |
| `emerge_de` | Une propriété d'échelle n émerge de l'échelle n-1 | Surface terrière `emerge_de` DHP individuels |
| `contraint` | Une entité d'échelle supérieure contraint l'inférieure | Climat massif `contraint` station peuplement |
| `contextualise` | Une entité d'échelle supérieure fournit le contexte | Massif `contextualise` peuplement |

Ces prédicats sont des `KnowledgeObject` de type `relation` (livrable 302,
§3.2) et sont implémentés dans le Knowledge Graph (livrable 304).

---

## 14. Alignement taxonomique et référentiel

GSIE ne réinvente pas les référentiels : elle s'aligne sur les systèmes
existants, français et internationaux. Cette section formalise le
rattachement de chaque domaine à son référentiel de référence.

### 14.1 Référentiels principaux par domaine

| Domaine | Référentiel principal | Producteur | Usage GSIE |
|---|---|---|---|
| DOM-ECO | Catalogues des stations | INRAE, ONF | Classification stationnelle |
| DOM-PED | RPF | INRAE (Baize & Jabiol, 2008) | Types de sols forestiers |
| DOM-PED | WRB | IUSS (2014/2015) | Correspondance internationale |
| DOM-DEN | BD Forêt, IFN | IGN | Mesures dendrométriques |
| DOM-CLI | SAFRAN, DRIAS | Météo-France | Données et scénarios climatiques |
| DOM-BOT | GBIF | GBIF Secretariat | Taxonomie mondiale |
| DOM-BOT | BDNFF | Tela Botanica | Nomenclature française |
| DOM-BOT | Tela Botanica | Tela Botanica | Flore collaborative |
| DOM-BOT | Rameau et al. (2008) | IDF | Autécologie des essences |
| DOM-PAT | BCF, ICP Forests | DSF, ICP | Suivi sanitaire |
| DOM-ENT | BCF, INPN | DSF, MNHN | Suivi entomologique |
| DOM-SYL | Guides ONF/CRPF/IDF | ONF, CRPF, IDF | Itinéraires sylvicoles |
| DOM-BIO | INPN, Natura 2000 | MNHN, MEEM | Habitats et espèces |
| DOM-DYN | IFN, RPS, capsis | IGN, ONF, INRAE | Suivi et modèles de dynamique |

### 14.2 Alignement taxonomique botanique

La nomenclature botanique suit une chaîne de référence :

```
GBIF (taxonomie mondiale)
  └── BDNFF (nomenclature française, Tela Botanica)
        └── Rameau et al. (2008) — autécologie forestière
              └── IGN BD Forêt (codes essences)
```

Chaque essence forestière possède :

- un `taxon_key` GBIF (identifiant mondial stable) ;
- un nom scientifique BDNFF (référence française) ;
- un code essence IGN (pour les données IFN) ;
- une fiche autécologique Rameau (exigences écologiques).

Conformément à S-3, les conflits nomenclaturaux (synonymies, révisions
taxonomiques) sont **documentés et conservés**, jamais résolus arbitrairement.

### 14.3 Alignement pédologique

```
WRB (international, IUSS)
  └── RPF (français, INRAE 2008)
        └── Carte des sols IGN / BRGM
```

Chaque type de sol possède :

- un `reference_soil_group` WRB (ex. `Alocrisol`) ;
- un rattachement RPF (ex. `Alocrisol typique`) ;
- des propriétés mesurables (RUM, pH, texture).

---

## 15. Relations inter-domaines (matrice)

La matrice ci-dessous synthétise les relations directes entre les dix
domaines. Une croix (`x`) indique qu'au moins une relation nommée existe
entre les deux domaines (voir sections 3 à 12 pour le détail des prédicats).

| | ECO | PED | DEN | CLI | BOT | PAT | ENT | SYL | BIO | DYN |
|---|---|---|---|---|---|---|---|---|---|---|
| **ECO** | — | x | x | x | x |  |  | x | x | x |
| **PED** | x | — | x | x | x | x |  |  |  |  |
| **DEN** | x | x | — | x |  |  |  | x |  | x |
| **CLI** | x | x | x | — |  | x | x |  | x | x |
| **BOT** | x | x |  |  | — | x | x | x | x |  |
| **PAT** |  | x |  | x | x | — | x | x |  | x |
| **ENT** |  |  |  | x | x | x | — | x |  | x |
| **SYL** | x |  | x |  | x | x | x | — | x | x |
| **BIO** | x |  |  | x | x |  |  | x | — | x |
| **DYN** | x |  | x | x |  | x | x | x | x | — |

### 15.1 Prédicats inter-domaines récurrents

| Prédicat | Sens | Domaines typiques |
|---|---|---|
| `depend_de` | Le concept sujet nécessite le concept objet | DYN → ECO, DEN → PED |
| `influence` | Le sujet affecte l'objet | CLI → DEN, PED → BOT |
| `determine` | Le sujet fixe l'objet | ECO → BOT, PED → ECO |
| `est_adapte_a` | L'essence est adaptée à la condition | BOT → ECO, BOT → PED |
| `croit_mieux_sur` | L'essence pousse mieux sur le type de sol | BOT → PED |
| `est_hote_de` | L'essence est hôte du pathogène/ravageur | BOT → PAT, BOT → ENT |
| `est_favorise_par` | Le pathogène/ravageur est favorisé par le facteur | PAT → CLI, ENT → CLI |
| `gere` | La sylviculture gère le risque ou la ressource | SYL → PAT, SYL → ENT |
| `est_perturbe_par` | La dynamique est perturbée par l'agent | DYN → PAT, DYN → ENT |
| `agrege_en` | Transition d'échelle ascendante | ARB → PEU, PEU → MAS |
| `emerge_de` | Propriété émergeant d'une échelle inférieure | PEU → ARB |

### 15.2 Conflits potentiels (S-3)

Certains domaines peuvent produire des connaissances contradictoires. Ces
conflits sont **conservés et documentés**, conformément à S-3 :

- **Autécologie vs. observation terrain** — une essence réputée acidiphile
  peut être observée sur sol neutre (micro-station, provenance).
- **Pathologie vs. climat** — un pathogène peut être favorisé par un climat
  humide dans une source et limité dans une autre (souches différentes).
- **Sylviculture vs. biodiversité** — une éclaircie favorable à la
  production peut défavoriser un habitat saproxylique.

Chaque conflit est matérialisé par une relation `contredit` entre deux
`KnowledgeObject`, avec référence aux deux sources et dates.

---

## 16. Conformité constitutionnelle

### 16.1 Articles respectés

| Article | Application dans l'ontologie |
|---|---|
| CON-002 | Chaque concept renvoie à un référentiel sourcé |
| CON-003 | L'ontologie est un actif de connaissance, pas du code |
| CON-004 | Les relations sont nommées et justifiées (explicabilité) |
| CON-010 | L'ontologie est versionnée (historique en §17) |
| S-1 | Référentiels officiels uniquement (INRAE, IGN, ONF, GBIF...) |
| S-2 | Chaque concept destiné à porter un niveau de preuve A-F |
| S-3 | Conflits documentés (§15.2) |
| S-5 | Incertitudes et domaines de validité à préciser par concept |
| S-6 | Couverture exhaustive des 10 domaines |
| S-7 | Versionnement et citabilité (identifiants stables) |

### 16.2 Domaines de validité

Chaque concept de l'ontologie doit, lorsqu'il devient un `KnowledgeObject`,
spécifier son `domaines_validite` (livrable 302, §6). À titre indicatif :

| Concept | Domaine de validité typique |
|---|---|
| Chêne sessile adapté pH 4,5–6,0 | France métropolitaine, plaine à moyenne montagne |
| Hêtre vulnérable au déficit hydrique | Altitude < 800 m, France atlantique |
| Douglas croissance 12 m³/ha/an | Sols profonds, pH 4,5–6,5, précipitations > 800 mm |
| Étage submontagnard | Vosges, Jura, Alpes, Massif central (seuils variables) |

---

## 17. Historique

| Date | Événement |
|---|---|
| 2026-07-02 | Création — stub Phase 1 (liste de domaines, 6 lignes) |
| 2026-07-13 | Détaillage Phase 3 — ontologie complète : 10 domaines (S-6), concepts, propriétés, relations, référentiels, échelles (DIR-0006), alignement taxonomique, matrice inter-domaines |

---

> Statut : *Draft — Phase 3 (Connaissance). Documentation uniquement,
> aucune implémentation (Phase 4).*
