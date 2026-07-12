# GSIE-CON-002 — La science avant tout

Édition : Première Édition
Version : 1.0 (Validated)
Statut : Validé par le Fondateur
Classification : Loi Fondamentale (Immuable)

## Principe

Toute connaissance, toute règle, tout seuil et toute corrélation dans
GSIE doit reposer sur une source scientifique identifiable et
vérifiable. L'opinion, l'intuition et la commodité n'ont pas de place
dans le système expert.

Aucune connaissance ne peut être intégrée à GSIE sans :

- **une source** — publication, référentiel, expert identifié ;
- **un niveau de preuve** — évalué par l'Evidence Engine ;
- **une traçabilité** — on peut retrouver l'origine et l'historique ;
- **une révisabilité** — la science évolue, GSIE doit pouvoir réviser.

Lorsqu'aucune source scientifique n'est disponible, GSIE signale
explicitement l'incertitude plutôt que de combler le vide par une
estimation non fondée.

## Pourquoi

Un système expert qui mélange faits scientifiques et opinions devient
une boîte noire : on ne sait plus ce qui est fiable. En foresterie, les
décisions reposent sur des décennies de recherche (écologie
stationnelle, pédologie, dendrométrie). Diluer cette rigueur dans des
estimations non sourcées détruirait la légitimité du système.

GSIE se positionne comme un outil scientifique. Cette position exige
une discipline : **ce qui n'est pas sourcé n'existe pas**.

## Conséquences

- Aucune règle, aucun coefficient, aucun seuil ne peut être codé sans
  source documentée.
- Toute incertitude scientifique est explicitement affichée, jamais
  masquée.
- Les conflits bibliographiques sont signalés, pas résolus
  arbitrairement.
- Les connaissances sont hiérarchisées par niveau de preuve.
- Une connaissance dont la source est invalidée par la communauté
  scientifique est révisée via RFC, pas ignorée.

## Exemple

Un développeur veut utiliser un seuil de pH « 5.5 » pour classer un sol
acide. Aucune source n'est citée. Refusé. La règle ne peut pas être
intégrée sans référence (par exemple : Référentiel Pédologique Français,
édition 2008).

Deux publications scientifiques donnent des gammes d'optimum écologique
différentes pour une même essence. GSIE présente les deux sources, leurs
niveaux de preuve respectifs, et signale le conflit. Aucune moyenne
arbitraire n'est calculée sans justification.

Une connaissance empirique de terrain n'a pas de publication associée
mais provient d'un expert reconnu. GSIE l'intègre avec un niveau de
preuve « expert » (inférieur à « peer-reviewed »), en citant l'expert et
la date. L'incertitude est affichée.

## Contre-exemple

Un moteur utilise un coefficient de croissance « qui marche bien » sans
source. Le coefficient produit des recommandations correctes sur un cas
mais erronées sur un autre. Sans source, impossible de déterminer le
domaine de validité. C'est une violation de CON-002. Le coefficient doit
être retiré jusqu'à sourçage.

## Références

- `SCIENTIFIC_CONSTITUTION.md` — Articles S-1 (Sources acceptées) à S-7
  (Patrimoine scientifique)
- `GSIE-CON-005` — Toute connaissance doit être traçable
- `GSIE-CON-004` — Toute décision doit être explicable

## Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — Première Édition |
| 2026-07-12 | Mise en conformité template RFC-0001, validation Fondateur |

## Statut

ADOPTÉ — Loi Fondamentale Immuable. Modification uniquement par RFC de
révision constitutionnelle.
