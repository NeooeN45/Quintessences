# GSIE-PROMPT-0031 — Préparation frontend et parcours de preuve

| Champ | Valeur |
|---|---|
| Statut | PRÊTE |
| Agent cible | Claude |
| Snapshot | Contrat `GSIE/API/docs/development/contracts/client-existing.route-inventory.json` |
| Priorité | P0 |

## Mission

Le produit actif est GeoSylva V3.1 (Google Play et abonnement Quintessences),
après sa refonte V3.0. Lire `GSIE/API/docs/development/RELEASE_GATES.md`.
Reprendre l'application existante et ses travaux locaux avant de créer des
écrans. La conversation PC est un jalon ultérieur, après GSIE, Artemis,
Ignis et Hub ; ne pas la démarrer dans ce lot.

Préparer le frontend Quintessences avec données synthétiques et contrats
existants. Construire les états compte, hors ligne, synchronisation, conflit,
restauration partielle et rapport. Présenter la conversation PC comme cible
préparée tant que son backend n'est pas livré.

## Documents obligatoires

- `GSIE/API/docs/development/FRONTEND_BRIEF.md` et `CONTRACT_HANDOFF.md`.
- `GSIE/API/docs/development/contracts/client-existing.route-inventory.json`.
- RFC-0042 et les règles de confidentialité et d'accessibilité du frontend.

## Interdictions

- Aucun appel à une base, un bucket ou une clé privée réelle.
- Aucun stockage de refresh token dans `localStorage`.
- Aucune fonction future présentée comme active.
- Aucun changement de contrat backend sans demande tracée.

## Rapport obligatoire

Remettre captures ou tests reproductibles, routes utilisées, états présentés,
limites et demandes de contrat. Les données de démonstration restent synthétiques.
