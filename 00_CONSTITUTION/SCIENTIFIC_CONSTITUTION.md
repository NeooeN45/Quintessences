# Constitution Scientifique de GSIE

Édition : Première Édition
Version : 1.0 (Draft)
Statut : À valider
Classification : Constitution Sectorielle
Référence : Livrable 007 (GSIE-DIR-0003)
Loi fondatrice : GSIE-CON-002 — La science avant tout

---

## Préambule

La Constitution Scientifique définit les règles opérationnelles qui
gouvernent l'intégration, l'évaluation et l'utilisation des
connaissances scientifiques dans GSIE. Elle opérationnalise le principe
fondamental énoncé par l'article CON-002 : **ce qui n'est pas sourcé
n'existe pas**.

Elle ne répète pas la Constitution — elle en déduit les conséquences
pratiques pour le domaine scientifique.

---

## Article S-1 — Sources acceptées

Toute connaissance intégrée à GSIE doit provenir d'une source
appartenant à l'une des catégories suivantes, par ordre de priorité
décroissante :

1. **Publication peer-reviewed** — revue scientifique indexée, ouvrage
   académique, actes de conférence avec comité de lecture.
2. **Référentiel officiel** — document produit par une institution
   reconnue (INRAE, IGN, ONF, IRSTEA, CEMAGREF, ministère, organismes
   équivalents à l'international).
3. **Document technique validé** — guide technique, manuel sylvicole,
   document d'organisme professionnel, validé par un comité.
4. **Connaissance experte** — témoignage d'un expert identifié
   (forestier, chercheur, ingénieur), daté et signé.
5. **Observation terrain** — mesure ou observation directe, datée,
   localisée, avec protocole décrit.

Aucune autre catégorie n'est acceptée. Les opinions non attribuées, les
estimations non fondées et les règles « de bon sens » sont exclues.

---

## Article S-2 — Niveaux de preuve

Chaque connaissance porte un niveau de preuve attribué par
l'Evidence Engine :

| Niveau | Label | Définition |
|---|---|---|
| A | **Prouvé** | Consensus scientifique large, multiples études peer-reviewed convergentes |
| B | **Établi** | Études peer-reviewed convergentes, consensus partiel |
| C | **Probable** | Études limitées ou contradictoires, tendance dominante |
| D | **Hypothèse** | Publication unique ou études préliminaires |
| E | **Expert** | Connaissance experte non publiée, témoignage d'expert reconnu |
| F | **Observation** | Observation terrain isolée, sans recoupement |

Le niveau de preuve est **affiché à l'utilisateur** à chaque
recommandation. Il n'est jamais masqué.

---

## Article S-3 — Conflits bibliographiques

Lorsque deux sources scientifiques se contredisent :

1. **aucune n'est supprimée** — les deux sont conservées ;
2. **le conflit est documenté** — référence des deux sources, dates,
   contextes ;
3. **le conflit est signalé à l'utilisateur** — GSIE présente les deux
   positions, pas une moyenne arbitraire ;
4. **aucune fusion arbitraire** — calculer une moyenne entre deux
   valeurs contradictoires sans justification scientifique est
   interdit.

Si une résolution est nécessaire, elle passe par une RFC et un
comité scientifique, jamais par une décision automatique.

---

## Article S-4 — Révision des connaissances

Une connaissance peut être révisée lorsque :

- sa source est invalidée par la communauté scientifique ;
- une nouvelle publication contredit significativement la connaissance
  existante ;
- le consensus scientifique évolue.

La révision suit la procédure :
1. identification du besoin de révision ;
2. création d'une RFC de révision ;
3. évaluation par l'Evidence Engine de la nouvelle source ;
4. mise à jour versionnée (l'ancienne version est conservée dans
   l'historique, jamais supprimée) ;
5. mise à jour de la traçabilité.

---

## Article S-5 — Incertitude explicite

Toute incertitude scientifique doit être :

- **identifiée** — la source d'incertitude est nommée ;
- **quantifiée si possible** — intervalle de confiance, marge
  d'erreur, variabilité ;
- **affichée** — l'utilisateur voit l'incertitude, pas seulement le
  résultat ;
- **jamais masquée** — présenter un résultat certain quand la source
  est incertaine est une violation de la Constitution.

---

## Article S-6 — Domaines de connaissance

GSIE couvre les domaines scientifiques suivants, chacun ayant ses
propres sources et référentiels :

- Écologie forestière et stationnelle
- Pédologie
- Dendrométrie et croissance
- Climatologie et bioclimatologie
- Botanique et taxonomie
- Pathologie forestière
- Entomologie forestière
- Sylviculture et gestion
- Biodiversité et conservation
- Dynamique des peuplements

Chaque domaine est géré par son moteur spécialisé, mais tous sont
soumis aux mêmes règles scientifiques définies ici.

---

## Article S-7 — Patrimoine scientifique

Les connaissances de GSIE constituent un patrimoine scientifique. Ce
patrimoine :

- est **versionné** — chaque évolution est tracée ;
- est **réversible** — on peut revenir à une version antérieure ;
- est **citable** — chaque connaissance a un identifiant stable ;
- est **ouvert** — l'objectif est l'open-source et la reproductibilité.

---

## Anti-Lois

Interdiction :
- d'intégrer une connaissance sans source ;
- d'inventer un coefficient ou un seuil sans référence ;
- de masquer un conflit bibliographique ;
- de supprimer une source contradictoire ;
- de présenter une opinion comme un fait ;
- de fusionner des sources divergentes sans justification ;
- de masquer une incertitude ;
- de supprimer l'historique d'une connaissance.

---

## Déclaration finale

« GSIE est un outil scientifique. Sa légitimité repose sur la rigueur
de ses sources. Sans rigueur scientifique, GSIE n'est rien. »
