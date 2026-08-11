# Quintessences — Page de statut

Page statique affichant l’état de l’écosystème GSIE en temps réel.

## Services surveillés

- API GSIE (`/health`)
- Landing page Quintessences
- Spécification OpenAPI (`/api/v1/openapi.json`)

## Déploiement

Prérequis : un token Cloudflare API avec les droits `Pages Read/Write`.

```powershell
$env:CLOUDFLARE_API_TOKEN = "<token>"
npx wrangler pages deploy public --project-name=quintessences-status --branch=main
```

## Domaine

Après déploiement, lier `status.quintessences-platform.com` au projet
Cloudflare Pages et mettre à jour son CNAME vers `quintessences-status.pages.dev`.
