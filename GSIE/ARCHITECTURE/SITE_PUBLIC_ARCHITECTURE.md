# Architecture technique — Site public Quintessences

| Champ | Valeur |
|---|---|
| **Répond à** | `SITE-001` (spécification), `SITE-002` (vision créative) |
| **Décision** | DEC-000057 |
| **Statut** | Draft — implémentation en cours |
| **Date** | 2026-08-09 |

## 1. Stack technique

Reprise à l'identique de `GSIE/ADMIN_WEB/` pour cohérence d'outillage
et de compétence dans l'écosystème :

| Composant | Choix | Justification |
|---|---|---|
| Framework | Astro 5 | Rendu statique par défaut (zones Landing/Actualités), îlots React uniquement où l'interactivité l'exige (Compte, indicateurs live, galerie) — cohérent avec `SITE-X-005` (contenu essentiel sans JS) |
| UI interactive | React 19 (îlots) | Déjà en production dans ADMIN_WEB |
| Style | Tailwind CSS 4 | Système de tokens (couleurs par app, §4.1 SITE-002) sans CSS ad hoc dupliqué |
| Animation | Framer Motion | `prefers-reduced-motion` géré nativement, cohérent avec `SITE-X-002` |
| Hébergement | Cloudflare Pages | Déjà utilisé par `landing-quintessences/`, gratuit jusqu'à 100k req/j |
| Contenu | Astro Content Collections (Markdown/MDX) | Répond à `SITE-D-001` (contenu versionné dans le dépôt, pas de CMS tiers) |

## 2. Structure de projet

```
site-quintessences/
├── astro.config.mjs
├── package.json
├── tailwind.config.ts        (tokens de couleur par app, §4.1 SITE-002)
├── src/
│   ├── content/
│   │   ├── actualites/       (collection Markdown, SITE-D-001)
│   │   └── galerie/          (collection Markdown + métadonnées média)
│   ├── components/
│   │   ├── Hero.astro
│   │   ├── EngineChain.tsx    (îlot React — scrollytelling, SITE-F-002)
│   │   ├── AppGrid.tsx        (îlot React — grille interactive, SITE-F-003/004)
│   │   ├── LiveStat.tsx       (îlot React — indicateur live + état dégradé, SITE-F-006/007)
│   │   ├── Principles.astro
│   │   ├── ContactForm.tsx    (îlot React — Turnstile, migration depuis landing-quintessences)
│   │   └── ThemeToggle.tsx
│   ├── layouts/
│   │   └── BaseLayout.astro   (identité visuelle commune aux 5 zones, SITE-F-011)
│   └── pages/
│       ├── index.astro                 (Landing)
│       ├── contact.astro
│       ├── actualites/
│       │   ├── index.astro
│       │   └── [slug].astro            (SITE-F-016, URL stable par entrée)
│       ├── galerie/
│       │   └── index.astro             (état « en construction », SITE-F-018/019/020/021 non résolus)
│       └── compte/
│           └── index.astro             (état « en construction », dépend d'IDENTITE-001 côté web)
└── public/
    └── favicon.svg
```

## 3. Intégration avec l'écosystème existant

- **Icônes des applications** : réutilise directement les fichiers
  déjà livrés par `DEC-000056` (`apps/<App>/branding/icons/*_512x512.png`
  ou équivalent), pas de nouvel asset.
- **Indicateurs live (`SITE-F-006`)** : nécessite un endpoint public
  API GSIE agrégé et non sensible (ex. `GET /public/stats`). **Cet
  endpoint n'existe pas encore** — `LiveStat.tsx` est construit pour
  gérer explicitement l'absence de source (`SITE-F-007`) tant que cet
  endpoint n'est pas livré côté API.
- **Compte (`SITE-F-010`)** : consomme les endpoints déjà exposés par
  l'API GSIE pour `IDENTITE-001` (register/login/profile/verify-email/
  reset-password/Google OIDC). Reste ouvert avant implémentation
  réelle : stratégie de stockage de session côté navigateur (cohérence
  avec `SITE-S-004`) — voir §9 de `SITE-001`.
- **Contact** : migration directe du formulaire existant
  (`landing-quintessences/public/index.html`), même site key
  Turnstile, même destination de message.

## 4. Déploiement

`site-quintessences/` est développé et testé en parallèle de
`landing-quintessences/`, qui reste le site en production sur
`quintessences-platform.com` jusqu'à bascule explicite (DEC dédiée),
conformément à DEC-000057 §3. Aucune interruption de service pendant
le développement.

## 5. Ce que cette architecture ne couvre pas encore

- Le rendu 3D du globe territorial (§5.1 `SITE-002`) — ambition, pas
  engagement (`SITE-002` §6). Une version 2D/illustration reste
  conforme tant que le coût de performance n'est pas validé contre
  `SITE-X-001`.
- Le processus de curation/vérification vie privée de la galerie
  (`SITE-F-021`) — processus humain, hors architecture technique.
- L'endpoint `GET /public/stats` côté API GSIE — à spécifier et
  implémenter séparément dans `GSIE/API/`.
