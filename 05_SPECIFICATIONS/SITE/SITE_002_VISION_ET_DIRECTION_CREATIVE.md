# SITE — Vision et direction créative 1.1.0

| Champ | Valeur |
|---|---|
| **Identifiant** | SITE-002 |
| **Statut** | Validé |
| **Version** | 1.1.0 |
| **Date** | 2026-08-09 |
| **Auteur** | Fondateur — proposition instruite par Claude (Anthropic) |
| **Décision** | DEC-000057 |
| **Complète** | `SITE-001` (spécification fonctionnelle) |

**Changelog 1.1.0** : pivot vers un **thème clair exclusif** (retrait
du sombre par défaut, §4.3) et une direction éditoriale inspirée de
`papacreative.com` (§3, §4.2) — décision directe du Fondateur,
remplace la direction 1.0.0 « poste de pilotage sombre ».

## 1. Objet de ce document

`SITE-001` fixe ce que le site doit faire. Ce document fixe **ce que le
site doit donner à ressentir**, et pourquoi. Il nourrit une future
architecture technique et une charte graphique, mais n'impose aucun
choix de librairie ou de code — ce sera le rôle de l'architecture qui
répondra à ces deux documents.

## 2. Positionnement

Quintessences n'est pas une startup SaaS générique. C'est la vitrine
d'un **jumeau numérique environnemental fédéré** — un système qui
qualifie de la preuve scientifique, raisonne dessus, et laisse un
forestier décider. Le site doit ressembler à ce que le projet est
réellement : un laboratoire de très haut niveau, pas une page de
vente. Le ton reste celui de `CLAUDE.md` §8 — sobre, scientifique,
sans emphase commerciale — mais « sobre » ne veut pas dire pauvre :
les références les plus exigeantes du secteur (Stripe, Linear, Apple,
Vercel) sont sobres et pourtant mémorables par la qualité d'exécution,
pas par la surenchère visuelle.

**Ce que le site n'est pas** : un site marketing qui empile des
promesses. **Ce qu'il est** : la démonstration, par l'expérience
elle-même, que Quintessences maîtrise la donnée, la preuve et
l'interaction — les trois choses que GSIE fait pour de vrai.

## 3. Références d'inspiration (esprit, pas copie)

| Référence | Ce qu'on en retient |
|---|---|
| **Linear** (linear.app) | Typographie précise, mode sombre par défaut assumé, motion design minimal mais jamais gratuit, densité d'information maîtrisée |
| **Stripe** (stripe.com) | Storytelling technique élégant — des diagrammes complexes rendus lisibles et beaux, pas simplifiés à l'excès |
| **Vercel** (vercel.com) | La performance et la rigueur technique comme argument visuel — le site est rapide et le montre |
| **Cesium** (cesium.com) | Vitrine d'une techno géospatiale 3D — pertinent car Quintessences a littéralement un Hub Unreal + Cesium for Unreal |
| **Apple — pages produit** | Mise en scène d'un objet réel plutôt qu'une promesse abstraite ; scroll qui raconte une histoire, pas qui décore |
| **Resend** (resend.com) | Design développeur premium : sobre, dense, respire, jamais criard |
| **Papa Creative** (papacreative.com) | Direction principale du thème clair (1.1.0) : typographie d'affiche empilée en hero (mots sur plusieurs lignes, taille dramatique), petites légendes en capitales/police mono très espacées, grille de « fiches projet » avec métadonnées à deux colonnes, fond quasi blanc, un seul accent vif utilisé avec parcimonie, énormément de blanc |

## 4. Identité visuelle

### 4.1 Couleur

Une couleur signature reprise de l'identité GSIE déjà en usage dans
les diagrammes du projet (`#1a5276`, bleu profond) comme couleur
d'ancrage du site — cohérence avec tous les schémas Mermaid déjà
produits dans `README.md`, `ROADMAP.md`, etc.

Chaque application garde sa couleur propre, dérivée de l'icône déjà
livrée par `DEC-000056`, utilisée en accent dans la section
Applications — comme Notion ou Google Workspace colorent chaque
produit différemment sous une même ombrelle visuelle :

| App | Accent (dominante de l'icône livrée) |
|---|---|
| GeoSylva | Vert feuille |
| Ignis | Orange/rouge flamme |
| Hydro | Bleu goutte d'eau |
| Flora | Violet/vert fleur |
| Artemis | Vert sombre (lynx) |
| QGISIA | Vert-bleu carte |
| Terra | Brun/vert sol |
| Aeris | Teal atmosphère |
| Atlas | Vert-bleu cartographie |

### 4.2 Typographie

Reprise directe de la paire typographique observée sur `papacreative.com` :
une police display géométrique à forte présence pour les titres et le
corps de texte (**Space Grotesk**), et une police mono pour les
légendes, la navigation et les métadonnées en capitales très espacées
(**Space Mono**) — le même procédé que « UI UX, BRAND, MOTION,
PRODUCT DESIGN » ou « PROJECT TYPE / INDUSTRY » sur le site de
référence, appliqué à nos propres contenus (domaine d'application,
statut, catégorie d'actualité). Nombres tabulaires pour tous les
indicateurs chiffrés (alignement propre des statistiques live).

Le hero adopte le même procédé d'affiche que la référence : un titre
empilé sur plusieurs lignes, en très grande taille, plutôt qu'un
paragraphe de sous-titre classique.

### 4.3 Thème

**Thème clair exclusif** — décision explicite du Fondateur (1.1.0),
qui remplace la direction « sombre par défaut » de la version 1.0.0.
Fond quasi blanc, texte presque noir, un seul accent vif utilisé avec
parcimonie (jamais en grande surface) — cohérent avec la retenue de
`papacreative.com`, où l'accent néon ne sert que la ponctuation
visuelle (mots-clés du hero, puces, liens actifs), jamais le fond.
Aucun mode sombre n'est proposé dans cette version ; `SITE-001`
(`SITE-X-007`) est amendée en conséquence.

## 5. Moments d'interaction signature

Ce sont les idées concrètes qui rendent le site mémorable — chacune
répond à une exigence de `SITE-001` (référencée entre parenthèses) et
respecte `prefers-reduced-motion` (`SITE-X-002`) sans exception.

1. **Globe territorial en hero** — un globe 3D léger qui zoome
   doucement sur un territoire pilote (Landiras) au défilement, avec
   les couches (forêt, incendie, eau) qui s'allument une à une. C'est
   la représentation littérale du « jumeau numérique fédéré », pas une
   image décorative. (`SITE-F-001`)
2. **Chaîne d'intelligence en scrollytelling** — le diagramme
   Evidence → Knowledge → Correlation → Reasoning → Diagnostic →
   Recommendation → Validation s'anime étape par étape pendant le
   défilement, avec une micro-explication qui apparaît à chaque étape
   plutôt qu'un schéma statique. (`SITE-F-002`)
3. **Grille d'applications interactive** — les 9 icônes livrées par
   `DEC-000056`, chaque carte réagissant légèrement au survol (profondeur
   subtile, jamais gadget), un clic ouvre un panneau détaillé sans
   quitter la page. (`SITE-F-003`, `SITE-F-004`)
4. **Compteurs vivants** — les indicateurs publics (`SITE-F-006`)
   s'animent à l'arrivée dans le viewport, avec un état de chargement
   soigné et un état d'indisponibilité explicite et assumé
   (`SITE-F-007`) plutôt que masqué.
5. **Actualités en fil vertical** — chronologie avec un repère temporel
   clair, chaque entrée badgée de la couleur de l'application
   concernée (§4.1). (`SITE-F-013`, `SITE-F-015`)
6. **Galerie en grille libre avec visionneuse** — médias affichés en
   grille dense, ouverture en plein écran avec légende et contexte
   toujours visibles (`SITE-F-019`, `SITE-F-020`), jamais un média sans
   sa mention de contexte.
7. **Transitions de page fluides** — le passage entre zones (landing →
   compte, actualités → détail) évite les ruptures brutales, sans
   sacrifier le fonctionnement sans JavaScript du contenu essentiel
   (`SITE-X-005`).

## 6. Ce que ce document ne fixe pas

- Aucune librairie, framework ou choix de rendu 3D précis — c'est le
  rôle de l'architecture technique à écrire après validation de ce
  document et de `SITE-001`.
- Aucune maquette pixel-perfect — ce document fixe une intention, pas
  un design final.
- Le globe 3D (§5.1) est une ambition, pas un engagement : s'il s'avère
  disproportionné en coût/performance face à `SITE-X-001`, une
  alternative plus sobre (carte 2D interactive, illustration statique
  animée) reste conforme à l'esprit de cette vision.

## 7. Prochaine étape

Une fois `SITE-001` et `SITE-002` validés par le Fondateur, l'étape
suivante est une **architecture technique** (stack, structure de
projet, intégration avec l'API GSIE et `IDENTITE-001`) — pas de code
avant cette étape, conformément à la hiérarchie documentaire du projet
(`CLAUDE.md` §3).
