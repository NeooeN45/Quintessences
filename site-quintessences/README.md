# Site public Quintessences

Implémentation de `SITE-001`/`SITE-002` (voir `05_SPECIFICATIONS/SITE/`)
et de l'architecture `GSIE/ARCHITECTURE/SITE_PUBLIC_ARCHITECTURE.md`.
Décision : `DEC-000057`.

Remplace à terme `landing-quintessences/` (conservé en production
jusqu'à bascule explicite du domaine).

**Direction visuelle (SITE-002 v1.1.0)** : thème clair exclusif,
typographie Space Grotesk/Space Mono, inspiré de `papacreative.com`
(hero en titre empilé, légendes capitales très espacées, fiches
« case study » pour les applications) — décision directe du Fondateur,
remplace la direction 1.0.0 « poste de pilotage sombre ».

## Développement

```bash
npm install
npm run dev      # http://127.0.0.1:4100
```

## État des 5 zones (voir SITE-001 §2.1)

| Zone | État |
|---|---|
| Landing (`/`) | Implémentée |
| Contact (`/contact/`) | Implémentée (migrée depuis `landing-quintessences/`) |
| Actualités (`/actualites/`) | Implémentée, contenu versionné dans `src/content/actualites/` |
| Galerie (`/galerie/`) | En construction — voir SITE-001 §9 (processus de vérification vie privée non défini) |
| Compte (`/compte/`) | En construction — voir SITE-001 §9 (hypothèses IDENTITE-001 côté web à vérifier) |

## Reste à faire

- Endpoint public `GET /public/stats` côté API GSIE (`SITE-F-006`) —
  `LiveStat.tsx` affiche un état « indisponible » tant qu'il n'existe
  pas. Configurable via `PUBLIC_STATS_API_URL`.
- Le formulaire de contact vérifie Turnstile mais ne transmet pas
  encore la catégorie/le message à un système de routage — même
  limite que `landing-quintessences/` actuel (DEC-000055).
- Déploiement Cloudflare Pages (non fait — nécessite `wrangler login`,
  étape humaine).
