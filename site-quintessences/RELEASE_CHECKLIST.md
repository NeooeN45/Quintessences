# Checklist de mise en production — site public Quintessences

Ce document décrit la bascule de `site-quintessences/` vers Cloudflare Pages.
Aucune étape Cloudflare ne doit être exécutée tant que la porte légale et la
recette API ne sont pas vertes.

## Préconditions obligatoires

- [ ] Identité de l'éditeur, directeur de publication et hébergeur confirmés.
- [ ] Responsable de traitement, bases juridiques et durées RGPD validés.
- [ ] `npm run verify:public` réussit sans placeholder.
- [ ] `GSIE_PUBLIC_CONTACT_ENABLED=true` uniquement avec destinataire réel,
      SMTP chiffré, Turnstile actif et procédure de conservation approuvée.
- [ ] `PUBLIC_ACCOUNT_ENABLED` absent ou égal à `false` tant que la session
      web HttpOnly/CSRF n'est pas approuvée.
- [ ] API de production saine sur `https://api.quintessences-platform.com/health`.
- [ ] Nom exact du projet Pages confirmé dans `CLOUDFLARE_PAGES_PROJECT`.
- [ ] Authentification Wrangler réalisée par l'opérateur, sans secret commité.

## Préparer l'artefact

Depuis `site-quintessences/` :

```powershell
npm ci
npm run check
npm run build
npm run verify:static
```

Le build doit produire `dist/` et 13 pages. Le contrôle statique doit confirmer
les liens internes et, par défaut, l'absence du Compte dans le header public.

## Déployer

La commande versionnée est :

```powershell
$env:CLOUDFLARE_PAGES_PROJECT = "NOM_EXACT_CONFIRMÉ"
npm run deploy:pages
```

Pour une prévisualisation, définir éventuellement
`CLOUDFLARE_PAGES_BRANCH`. Le script refuse les placeholders juridiques, le
Compte activé prématurément et les liens internes invalides.

## Vérifier après bascule

```powershell
npm run verify:live
```

Le contrôle doit confirmer le site Astro, `robots.txt`, `security.txt`, le
sitemap, les headers de sécurité et `/health`. Toute réponse Cloudflare 530,
un fichier public renvoyé en HTML ou l'absence de CSP est un `NO-GO`.

## Retour arrière

1. Ne pas modifier les DNS dans l'urgence.
2. Restaurer le dernier déploiement Pages validé depuis le dashboard ou la
   procédure opérateur Cloudflare.
3. Relancer `npm run verify:live`.
4. Consigner l'incident et la décision dans le journal de projet.

Le domaine sert actuellement une ancienne landing ; cette checklist ne vaut
pas preuve de déploiement. La preuve est uniquement la recette live réussie.
