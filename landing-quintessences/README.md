# Landing page Quintessences

Landing page statique officielle pour `quintessences-platform.com`.

## Hébergement recommandé

Cloudflare Pages (gratuit jusqu'à 100 000 requêtes/jour).

## Déploiement rapide

```powershell
cd E:\Projets\Quintessences\landing-quintessences
# Installe wrangler si nécessaire
npm install -g wrangler
# Authentification (une seule fois)
npx wrangler login
# Créer le projet Pages si non existant
npx wrangler pages project create quintessences-landing
# Déployer
npx wrangler pages deploy public --project-name=quintessences-landing
# Lier le domaine personnalisé depuis le dashboard Cloudflare
```

## Contenu

- `public/index.html` : page d'atterrissage.
- `public/css/main.css` : styles.

## Domaine cible

`quintessences-platform.com` (apex) et `www.quintessences-platform.com`.
