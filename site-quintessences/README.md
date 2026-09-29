# Site public Quintessences

Implémentation de `SITE-001`/`SITE-002` (voir `05_SPECIFICATIONS/SITE/`)
et de l'architecture `GSIE/ARCHITECTURE/SITE_PUBLIC_ARCHITECTURE.md`.
Décision : `DEC-000057`.

Remplace à terme `landing-quintessences/` (conservé en production
jusqu'à bascule explicite du domaine).

**Direction visuelle (SITE-002 v1.1.0)** : thème clair exclusif,
typographie sans-serif et monospace système, inspirée de `papacreative.com`
(hero en titre empilé, légendes capitales très espacées, fiches
« case study » pour les applications) — décision directe du Fondateur,
remplace la direction 1.0.0 « poste de pilotage sombre ».

## Développement

```bash
npm install
npm run dev      # http://127.0.0.1:4100
```

La configuration locale peut être copiée depuis `.env.example`. Les variables
`PUBLIC_*` sont intégrées au build navigateur : elles ne doivent jamais
contenir de secret.

## État des 5 zones (voir SITE-001 §2.1)

| Zone | État |
|---|---|
| Landing (`/`) | Implémentée |
| Contact (`/contact/`) | Implémentée (migrée depuis `landing-quintessences/`) |
| Actualités (`/actualites/`) | Implémentée, contenu versionné dans `src/content/actualites/` |
| Galerie (`/galerie/`) | En construction — voir SITE-001 §9 (processus de vérification vie privée non défini) |
| Compte (`/compte/`) | En construction — voir SITE-001 §9 (hypothèses IDENTITE-001 côté web à vérifier) |

## Reste à faire

- Socle de publication ajouté : `robots.txt`, sitemap dynamique, `_headers`
  Cloudflare Pages et `/.well-known/security.txt`.
- `npm run verify:public` bloque la publication tant que les pages légales
  contiennent des placeholders ou que les fichiers publics requis manquent.
  Il refuse également `PUBLIC_ACCOUNT_ENABLED=true` tant que la session web
  n'est pas approuvée pour la production.
- `npm run verify:static` vérifie les liens internes réellement produits dans
  `dist/` après le build.
- `npm run verify:live` audite en lecture seule le domaine public, les fichiers
  `robots.txt`/`security.txt`, les headers de sécurité, le sitemap et `/health`.
- Le formulaire de contact transmet désormais catégorie + message à
  `POST ${PUBLIC_API_ORIGIN}/api/v1/public/contact` (`PUBLIC_API_ORIGIN` est
  local en développement et doit être défini sur l'API de staging lors d'une
  recette).
  L'endpoint est protégé côté serveur par Turnstile, limitation de débit et
  champ piège ; l'activation reste fermée par défaut jusqu'à configuration du
  destinataire SMTP et validation de la conservation RGPD.
- La zone Compte est fermée par défaut dans les builds publics via
  `PUBLIC_ACCOUNT_ENABLED`. Ne l'activez que dans un environnement contrôlé
  après validation de la session web contre `IDENTITE-001` ; le build de
  production ne doit pas exposer les formulaires actuels basés sur
  `sessionStorage`.
- Déploiement Cloudflare Pages (non fait — nécessite `wrangler login`,
  étape humaine).

## Porte de mise en production

Le build technique peut produire le site, mais la mise en ligne reste
volontairement bloquée tant que les mentions légales ne contiennent pas
l'identité réelle de l'éditeur et du responsable de traitement. Cette garde
évite de publier des informations juridiques inventées ou incomplètes.

## Déploiement Cloudflare Pages

Le script `npm run deploy:pages` exécute d'abord `verify:public`, reconstruit
`dist/`, vérifie les liens internes avec `verify:static`, puis appelle
`wrangler pages deploy`. Il exige la variable
`CLOUDFLARE_PAGES_PROJECT` ; `CLOUDFLARE_PAGES_BRANCH` est facultative pour un
déploiement de prévisualisation. Wrangler n'est pas exécuté automatiquement et
aucun secret ne doit être placé dans le dépôt.

La procédure complète et la recette post-bascule sont documentées dans
[`RELEASE_CHECKLIST.md`](./RELEASE_CHECKLIST.md).
