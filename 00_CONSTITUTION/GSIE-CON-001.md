# GSIE-CON-001 — Le forestier reste le décideur

Édition : Première Édition
Version : 1.0 (Validated)
Statut : Validé par le Fondateur
Classification : Loi Fondamentale (Immuable)

## Principe

L'intelligence artificielle assiste le forestier. Elle ne décide jamais
à sa place. Le forestier est et demeure le seul décideur.

Toute recommandation, tout diagnostic, toute suggestion produite par GSIE
est :

- **contournable** — le forestier peut ignorer ou modifier toute sortie ;
- **explicable** — le forestier comprend le raisonnement avant d'agir ;
- **non-contraignante** — GSIE ne bloque jamais une action humaine
  légitime ;
- **contextuelle** — GSIE présente les alternatives, pas une décision
  unique.

## Pourquoi

Un système expert qui décide à la place de l'humain devient une autorité
opaque. En foresterie, chaque décision engage des décennies : choix
d'essences, interventions sylvicoles, gestion de la biodiversité.
Déléguer ces décisions à une machine, même performante, transfère une
responsabilité que la machine ne peut pas porter.

Le forestier possède ce que GSIE n'a pas : la connaissance du terrain,
l'expérience locale, le jugement sur le long terme, et la
responsabilité légale.

## Conséquences

- Aucun moteur ne produit une décision exécutoire.
- Toute sortie de GSIE est étiquetée comme « recommandation » ou
  « diagnostic », jamais comme « décision ».
- L'interface utilisateur présente toujours la possibilité de refuser,
  modifier ou demander une alternative.
- GSIE documente le désaccord éventuel du forestier (traçabilité).
- Aucun mécanisme de « pilote automatique » ne peut être implémenté.

## Exemple

GSIE recommande de planter du chêne sessile. Le forestier choisit le
hêtre en raison de son expérience locale. GSIE enregistre le choix, la
recommandation et l'écart. Aucun blocage.

GSIE détecte un risque de dépérissement. Le forestier décide de ne pas
intervenir immédiatement. GSIE documente le risque, la décision du
forestier et la justification fournie. Aucun blocage.

## Contre-exemple

Un moteur produit une recommandation que le forestier ne peut pas
contourner (bouton désactivé, action exécutée automatiquement). C'est
une violation de CON-001. Le mécanisme doit être retiré et remplacé par
une sortie contournable.

## Références

- `GSIE-FND-001` — Préambule Philosophique (Locked)
- `AI_CONSTITUTION.md` — Article IA-1 (Rôle de l'IA) et IA-5 (Désaccord
  humain)
- `PACT_FOR_AI_AGENTS.md` — Principe 4 (proposer avant de modifier)

## Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — Première Édition |
| 2026-07-12 | Mise en conformité template RFC-0001, validation Fondateur |

## Statut

ADOPTÉ — Loi Fondamentale Immuable. Modification uniquement par RFC de
révision constitutionnelle.
