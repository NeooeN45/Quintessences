# GSIE-CON-005 — Toute connaissance doit être traçable

Édition : Première Édition
Version : 1.0 (Validated)
Statut : Validé par le Fondateur
Classification : Loi Fondamentale (Immuable)

## Principe

Toute connaissance intégrée à GSIE doit posséder une origine, un
historique, un niveau de preuve et une version.

Chaque élément de connaissance doit être relié à :

- **sa source** — publication, référentiel, expert identifié, observation
  terrain ;
- **son auteur ou organisme** — qui a produit la connaissance ;
- **sa date d'intégration** — quand elle est entrée dans GSIE ;
- **sa version** — quelle version de la connaissance est utilisée ;
- **son Evidence Level** — niveau de preuve évalué par l'Evidence Engine
  (A à F) ;
- **son historique de modifications** — toutes les révisions sont
  conservées.

## Pourquoi

Sans traçabilité, impossible d'auditer une recommandation. Si une
recommandation s'avère erronée, il faut pouvoir remonter à la source
fautive pour la corriger. Si une connaissance est contestée, il faut
pouvoir identifier sa provenance et son niveau de fiabilité.

La traçabilité est aussi la condition de la révision scientifique : pour
qu'une connaissance évolue, il faut savoir d'où elle vient et par quel
chemin elle est arrivée.

## Conséquences

- Aucune donnée ne peut être intégrée anonymement ou sans justification
  documentaire.
- Chaque modification d'une connaissance est versionnée et archivée.
- L'ancienne version est conservée — jamais supprimée.
- Un audit complet de chaque recommandation doit être possible a
  posteriori.
- Les connaissances sans traçabilité sont purgées ou mises en quarantaine
  jusqu'à sourçage.

## Exemple

Une règle de corrélation entre pH et présence d'une essence est intégrée.
GSIE enregistre : source (Référentiel Pédologique Français 2008), auteur
(INRAE), date d'intégration (2026-07-15), version (1.0), Evidence Level
(B — Établi). Si la règle est révisée en 2028, la version 1.0 est
archivée et la version 2.0 remplace, avec référence à la nouvelle
publication.

## Contre-exemple

Un fichier de données d'essences est importé sans métadonnées. On ne
sait pas qui l'a produit, quand, ni selon quel protocole. C'est une
violation de CON-005. Les données sont mises en quarantaine jusqu'à
sourçage complet.

## Références

- `SCIENTIFIC_CONSTITUTION.md` — Article S-1 (Sources acceptées) et S-7
  (Patrimoine scientifique)
- `GSIE-CON-002` — La science avant tout
- `GSIE-CON-010` — Toute connaissance doit pouvoir évoluer sans perdre
  son historique

## Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — Première Édition |
| 2026-07-12 | Mise en conformité template RFC-0001, validation Fondateur |

## Statut

ADOPTÉ — Loi Fondamentale Immuable. Modification uniquement par RFC de
révision constitutionnelle.
