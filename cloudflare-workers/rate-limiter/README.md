# Worker — Rate Limiter Edge

Ce Cloudflare Worker ajoute une première couche de rate limiting devant `api.quintessences-platform.com`.
Il utilise Cloudflare KV pour stocker des compteurs par IP et par bucket de chemin.

## Seuils

| Chemin | Limite | Fenêtre |
|---|---|---|
| `/api/v1/auth/*` | 10 req | 60 s |
| `/api/v1/auth/turnstile/*` | 30 req | 60 s |
| autre `/api/v1/*` | 100 req | 60 s |

## Prérequis

- Node.js >= 18
- `npx wrangler` configuré avec `CLOUDFLARE_API_TOKEN` ou `wrangler login`

## Déploiement

```powershell
cd cloudflare-workers\rate-limiter
.\deploy.ps1 -CreateRoute
```

Le script :
1. crée le namespace KV `RATE_LIMITS`,
2. met à jour `wrangler.toml`,
3. déploie le Worker,
4. attache la route `api.quintessences-platform.com/*`.

## Test

```bash
curl -s -o /dev/null -w "%{http_code}" https://api.quintessences-platform.com/health
# attendu : 200
```

Après plus de 100 requêtes/minute depuis une IP, le Worker retourne `429 Too Many Requests`.

## Fallback

Si KV est indisponible, le Worker laisse passer le trafic. Le rate limiting applicatif
(`slowapi` + `limits` dans `GSIE/API/src/gsie_api/app.py`) reste le garde-fou principal.
