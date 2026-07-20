# Manifeste — candidats documentaires Phase C (pilote Nouvelle-Aquitaine, RFC-0016)

> Récupéré le 2026-07-19. **Aucun fait n'a été extrait de ces documents.**
> Ce dossier ne contient que des sources candidates, téléchargées
> uniquement depuis des dépôts confirmés en accès libre (licence
> vérifiée via l'API Europe PMC ou la page de l'article), pour revue
> humaine avant tout passage dans le pipeline d'extraction
> (`KnowledgeExtractor`, RFC-0014 §3.2). Aucune donnée scientifique
> n'a été inventée ni approximée — voir §"Ce qui manque encore"
> ci-dessous pour ce qui n'a pas pu être trouvé en accès libre.

Objectif RFC-0016 §4/§10 : 12-20 essences pour le pilote
Nouvelle-Aquitaine (« chênes sessile/pédonculé/pubescent,
châtaignier, hêtre, pin maritime, Douglas, pin sylvestre, pin
laricio, peupliers »). Les tranches 1-6 avaient déjà produit des
`AutecologyProfile` réels pour *Quercus petraea*/*Quercus robur*
(commit `36abef0`, source Parelle et al. 2007). Ce lot cible les
essences restantes.

**Bilan : 10/10 essences du corpus RFC-0016 §4 ont désormais au moins
une source ouverte identifiée** (7 téléchargées ici, 1 source
supplémentaire pour pin maritime + pin laricio identifiée et
licence-vérifiée mais bloquée par une protection anti-bot, pas
encore en main).

## Documents récupérés (accès libre confirmé)

| Fichier | Essence(s) couverte(s) | Référence | Licence | Pertinence |
|---|---|---|---|---|
| `fagus_sylvatica_jump_2012_plosone.pdf` | Hêtre (*Fagus sylvatica*) | Jump A.S. et al. (2012), « Drought-Adaptation Potential in *Fagus sylvatica*: Linking Moisture Availability with Genetic Diversity and Dendrochronology », *PLOS ONE*, DOI [10.1371/journal.pone.0033636](https://doi.org/10.1371/journal.pone.0033636) | CC BY | Tolérance sécheresse, disponibilité en eau du sol, variation génétique par population |
| `pseudotsuga_menziesii_2024_annforsci.pdf` | Douglas (*Pseudotsuga menziesii*) | *Annals of Forest Science* (2024), « Interannual radial growth response of Douglas-fir to severe droughts: an analysis along a gradient of soil properties and rooting characteristics », DOI [10.1186/s13595-024-01240-z](https://doi.org/10.1186/s13595-024-01240-z) | Open access (politique AFS/SpringerOpen) | Propriétés du sol, enracinement, réponse à la sécheresse |
| `castanea_sativa_2025_pmc12598267_fulltext.xml` | Châtaignier (*Castanea sativa*) | Perez-Rial A. et al. (2025), « Decoding drought tolerance from a genomic approach in *Castanea sativa* Mill. », *The Plant Genome*, DOI [10.1002/tpg2.70116](https://doi.org/10.1002/tpg2.70116) | CC BY | Tolérance sécheresse — approche génomique, à filtrer pour ne garder que les observations autécologiques (pas les marqueurs moléculaires bruts) |
| `pinus_pinaster_2013_pmc3815124_fulltext.xml` | Pin maritime (*Pinus pinaster*) | Gaspar M.J. et al. (2013), « Genetic variation of drought tolerance in *Pinus pinaster* at three hierarchical levels: a comparison of induced osmotic stress and field testing », *PLOS ONE*, DOI [10.1371/journal.pone.0079094](https://doi.org/10.1371/journal.pone.0079094) | CC0 | Tolérance sécheresse en conditions de terrain (pas seulement en laboratoire) |
| `quercus_pubescens_petraea_robur_2015_pmc4427272_fulltext.xml` | Chêne pubescent (*Quercus pubescens*) — et confirme *Q. petraea*/*Q. robur* | Hu B. et al. (2015), « Changes in the dynamics of foliar N metabolites in oak saplings by drought and air warming depend on species and soil type », *PLOS ONE*, DOI [10.1371/journal.pone.0126701](https://doi.org/10.1371/journal.pone.0126701) | CC BY | Compare directement les 3 chênes cibles du pilote sur le même protocole — type de sol inclus |
| `pinus_sylvestris_2023_pmc9835711_fulltext.xml` | Pin sylvestre (*Pinus sylvestris*) | Meng F. et al. (2023), « The effects of soil drought stress on growth characteristics, root system, and tissue anatomy of *Pinus sylvestris* var. *mongolica* », *PeerJ*, DOI [10.7717/peerj.14578](https://doi.org/10.7717/peerj.14578) | CC BY | ⚠️ Variété *mongolica* (Chine/Mongolie), pas la variété européenne — à confirmer avec le curateur si la transférabilité autécologique est acceptée, ou chercher une source européenne en complément |
| `populus_nigra_2016_viger_treephysiol_fulltext.xml` | Peuplier noir (*Populus nigra*) | Viger M. et al. (2016), « Adaptive mechanisms and genomic plasticity for drought tolerance identified in European black poplar (*Populus nigra* L.) », *Tree Physiology*, DOI [10.1093/treephys/tpw017](https://doi.org/10.1093/treephys/tpw017) | CC BY | ~500 arbres de 11 populations fluviales européennes — plasticité phénotypique sécheresse/inondation, directement autécologique |

**7 essences nouvelles couvertes** (pubescent, hêtre, châtaignier, pin
maritime, Douglas, pin sylvestre, peuplier noir), en plus des 2 déjà
traitées (petraea, robur) — soit 9/10 essences citées par RFC-0016 §4.

## Identifié mais non téléchargé (bloqué par protection anti-bot, pas par le droit)

- **Pin laricio de Corse** (*Pinus nigra* subsp. *laricio*) — et
  bonus, second document pour **pin maritime** (*Pinus pinaster*) :
  Häusser M. et al. (2021), « The Dry and the Wet Case: Tree Growth
  Response in Climatologically Contrasting Years on the Island of
  Corsica », *Forests* 12(9):1175, DOI
  [10.3390/f12091175](https://doi.org/10.3390/f12091175). Licence
  **CC BY confirmée indépendamment via Unpaywall**
  (`is_oa: true`, `journal_is_oa: true`) — pas seulement la page de
  l'éditeur. URL PDF vérifiée :
  `https://www.mdpi.com/1999-4907/12/9/1175/pdf?version=1630556837`.
  **Non téléchargé ici** : MDPI bloque les requêtes automatisées
  (403/« Access Denied », protection anti-bot) — pas un problème de
  droit d'usage, juste d'automatisation. Téléchargement à faire
  manuellement (navigateur) ou via le fetcher HTTP de Forge, qui n'a
  pas cette restriction en pratique.

## Ce qui manque encore

- **Peupliers cultivés** (cultivars/hybrides *Populus × canadensis*,
  utilisés en populiculture française réelle) : seule la source native
  *Populus nigra* a été retenue ici — les cultivars hybrides
  peupleraies (source d'usage réel en Nouvelle-Aquitaine) restent à
  rechercher séparément si le pilote les inclut.
- Aucune tentative de contourner un paywall ou une protection
  anti-bot n'a été faite : toute source dont le statut « accès
  libre » n'était pas confirmé par Europe PMC/Unpaywall ou la page de
  licence de l'éditeur a été écartée plutôt que téléchargée par
  prudence. Le document CNPF « Pins noirs et laricio de Corse »
  (`hautsdefrance-normandie.cnpf.fr`) reste par ailleurs
  `LEGAL_REVIEW_PENDING` et n'a pas été téléchargé, indépendamment de
  toute protection technique.

## Prochaine étape (après ta revue)

Ces documents ne sont PAS encore passés dans `KnowledgeExtractor`
(RFC-0014 §3.2) — aucun fait n'en a été extrait, contrairement au
pilote Quercus (Parelle et al. 2007) déjà ingéré. Après ta revue,
étape suivante naturelle : lancer l'extraction documentaire (Forge)
sur les documents retenus, puis reproduire le même pont
(`build_autecology_profile_from_quarantined_fact`) pour produire de
nouveaux `AutecologyProfile` réels pour ces 7 essences.
