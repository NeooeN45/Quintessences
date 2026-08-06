# QUINTESSENCES_DOMAIN_AND_CLOUDFLARE_BOOTSTRAP

**Date :** 2026-08-06  
**Statut :** Draft — plan d’exploitation à valider par le Fondateur  
**Domaine :** `quintessences-platform.com` (Cloudflare Registrar, 10,46 $/an)  
**Décision fondatrice :** `DEC-000047` — Cloudflare comme bordure Zero Trust de GSIE  
**Documents connexes :**
- `GSIE/API/docs/CLOUDFLARE_ZERO_TRUST.md` (runbook Zero Trust)
- `GSIE/API/docs/AUDIT_DEPLOYMENT_20260806.md` (rapport d’audit du déploiement)
- `GSIE/API/SECURITY_AUDIT.md` (constats de sécurité historiques)
- `GSIE/API/.env.example` (modèle de configuration)
- `GSIE/API/docker-compose.yml` (services Docker)

---

## 1. État actuel supposé

### 1.1 Domaine

- Nom de domaine `quintessences-platform.com` enregistré chez **Cloudflare Registrar**.
- Coût : 10,46 $/an (prix coutant, renouvellement identique).
- WHOIS privacy gratuit actif.
- Serveurs de noms Cloudflare configurés : `annalise.ns.cloudflare.com`, `fattouche.ns.cloudflare.com`.

### 1.2 DNS actif

| Sous-domaine | Type | Cible / État | Utilité actuelle |
|---|---|---|---|
| `api.quintessences-platform.com` | CNAME via tunnel | Tunnel `gsie-api` | API GSIE publique |
| `quintessences-platform.com` | APEX | Cloudflare edge | Non exploité (landing page à venir) |
| `www.quintessences-platform.com` | Non résolu | — | Site public (à créer) |
| `app.quintessences-platform.com` | Non résolu | — | Portail utilisateur (à réserver) |
| `auth.quintessences-platform.com` | Non résolu | — | Authentification centralisée (à réserver) |
| `docs.quintessences-platform.com` | Non résolu | — | Documentation (à réserver) |
| `status.quintessences-platform.com` | Non résolu | — | Statut des services (à réserver) |
| Autres (dev, staging, geosylva, ignis, hydro, flora, artemis, terra, atmos) | Non résolus | — | À réserver progressivement |

### 1.3 Tunnel Cloudflare

- Tunnel nommé `gsie-api` créé (ID `07e329c5-7e1f-4bdd-898f-bc38a10ad287`).
- Connecteur actif sous Windows avec 2 connexions QUIC vers `cdg07` et `cdg14`.
- L’origine locale est `http://127.0.0.1:8000` (API GSIE lancée sur le host).
- Certificat d’authentification : `C:\Users\camil\.cloudflared\cert.pem`.
- Credentials du tunnel : `C:\Users\camil\.cloudflared\07e329c5-...json`.

### 1.4 API GSIE

- Accessible publiquement en HTTPS : `https://api.quintessences-platform.com`.
- Environnement `development` avec `GSIE_EDGE_PROXY_MODE=cloudflare_tunnel`.
- CORS autorisés : `https://api.quintessences-platform.com`, `https://quintessences-platform.com`, plus les origines localhost de développement.
- Tests : **2080 passed, 63 skipped**, lint (`ruff`) et typecheck (`mypy`) OK.

### 1.5 Services sous-jacents

| Service | État | Port exposé |
|---|---|---|
| PostgreSQL + PostGIS | Docker, healthy | `127.0.0.1:5432` |
| Redis | Docker, healthy | `127.0.0.1:6379` (dev host) |
| Mailpit | Docker, healthy | `127.0.0.1:8025` |
| API GSIE (host) | En cours d’exécution | `127.0.0.1:8000` |

### 1.6 Points de vigilance non corrigés

- ℹ️ L’API tourne sur le **host Windows** et non dans le conteneur Docker `api-api-1`. Le service `cloudflared` avec le profil Docker `edge` est déjà prévu dans `docker-compose.yml` pour une migration future.
- ✅ DNSSEC activé dans le dashboard Cloudflare.
- ✅ SSL/TLS configuré en `Full` dans le dashboard (passer à `Full (Strict)` dès que l’origine a un certificat TLS valide).
- ✅ Landing page déployée sur Cloudflare Pages : `https://quintessences-platform.com` et `https://www.quintessences-platform.com`.
- ✅ `status.quintessences-platform.com` configuré (pointe vers la landing temporairement en attendant une page de statut dédiée).
- ✅ L’adresse e-mail `GSIE_EMAIL_SENDER` est mise à jour vers `noreply@quintessences-platform.com`.
- ✅ WAF Managed Free Ruleset activé, custom firewall ruleset (scanners / auth) créé.
- ✅ Email Routing activé (règles à créer dans le dashboard une fois l’adresse de destination vérifiée).
- ✅ Always Use HTTPS, HSTS, TLS 1.2 minimum activés.
- ✅ DNS records `www` et `status` créés.
- ✅ Script `cloudflared\check-update.ps1` créé.
- ⏸️ Cloudflare Access réservé aux interfaces d’administration (`control`, `dev`, `staging`) quand ces services existeront.

---

## 2. Vérifications à effectuer

### 2.1 Cloudflare Dashboard

- [ ] Confirmer le domaine dans le bon compte Cloudflare (propriétaire unique).
- [ ] Vérifier les enregistrements DNS (`api`, apex, éventuels autres).
- [ ] Vérifier l’état de **DNSSEC** : désactivé par défaut, à activer.
- [ ] Vérifier le mode **SSL/TLS** : doit être mis sur `Full (Strict)` si l’origine a un certificat TLS, sinon `Full` temporairement. **Jamais `Flexible`.**
- [ ] Vérifier **Always Use HTTPS** : activé.
- [ ] Vérifier **Automatic HTTPS Rewrites** : activé.
- [ ] Vérifier **HSTS** : activer avec `max-age=31536000`, `includeSubDomains`, `preload` si marque stable.
- [ ] Vérifier le compte Cloudflare : MFA activé, clés API restreintes, alertes par e-mail.

### 2.2 Local

- [ ] Confirmer que `cert.pem` et les credentials tunnel ne sont pas dans le dépôt Git.
- [ ] Vérifier que `.env` est dans `.gitignore`.
- [ ] Vérifier que `GSIE_EMAIL_SENDER` est remplacé par une adresse du domaine.
- [ ] Vérifier la version de `cloudflared` et planifier sa mise à jour manuelle.
- [ ] Vérifier que PostgreSQL, Redis et Mailpit ne sont accessibles que localement (127.0.0.1 ou réseau Docker).

### 2.3 Réseau / Sécurité

- [ ] Depuis un réseau externe, vérifier que `api.quintessences-platform.com` répond et que l’IP publique du serveur domestique n’expose pas le port 8000.
- [ ] Vérifier que `CF-Connecting-IP` est utilisé par le rate limiter (déjà en place dans `core/limiter.py`).
- [ ] Tester un appel avec `X-Forwarded-For` usurpé : le rate limiter ne doit pas l’utiliser en mode `cloudflare_tunnel`.

---

## 3. Arborescence recommandée

```
quintessences-platform.com
├── @                    → page d’atterrissage officielle (Cloudflare Pages / S3 statique)
├── www                  → redirect 301 vers @ (ou miroir)
├── app                  → portail utilisateur (future app web GeoSylva/Quintessences)
├── auth                 → authentification centralisée (Keycloak OU API GSIE /auth)
├── api                  → API GSIE publique (Cloudflare Tunnel)
├── docs                 → documentation publique (Cloudflare Pages / Docusaurus)
├── status               → page de statut des services (Cachet / Upptime / Cloudflare Pages)
├── geosylva             → portail spécifique GeoSylva (futur)
├── ignis                → portail spécifique Ignis (futur)
├── hydro                → portail spécifique Hydro (futur)
├── flora                → portail spécifique Flora (futur)
├── artemis              → portail spécifique Artemis (futur)
├── terra                → portail spécifique Terra (futur)
├── atmos                → portail spécifique Atmos (futur)
├── dev                  → environnement de développement (accès restreint)
├── staging              → préproduction (accès restreint)
└── control              → interfaces d’administration (Cloudflare Access + MFA)
```

**Principe :** un seul nom public par service, distinct par environnement. Les noms `dev` et `staging` ne doivent jamais être publics sans Access.

---

## 4. Sous-domaines à créer maintenant

### 4.1 Activation immédiate (gratuit, zéro risque)

| Sous-domaine | Justification | Implémentation |
|---|---|---|
| `www.quintessences-platform.com` | Site public temporaire / landing page | Redirection 301 vers `quintessences-platform.com` ou page statique Cloudflare Pages |
| `status.quintessences-platform.com` | Transparence incident / statut | Cloudflare Pages statique ou Upptime open source |

### 4.2 Création dès que le service est prêt

| Sous-domaine | Déclencheur |
|---|---|
| `app.quintessences-platform.com` | Portail web utilisateur opérationnel |
| `auth.quintessences-platform.com` | Keycloak ou concentrateur d’authentification déployé |
| `docs.quintessences-platform.com` | Documentation publique consolidée |
| `geosylva.*`, `ignis.*`, etc. | MVP de chaque app publiée |
| `dev.quintessences-platform.com` | Besoin d’un environnement dev exposé avec Access |
| `staging.quintessences-platform.com` | Besoin d’un environnement de préproduction exposé avec Access |

### 4.3 Réservation dans la documentation (pas de DNS)

- `control.quintessences-platform.com` : administratif / plan de contrôle (Cloudflare Access).
- `ws.quintessences-platform.com` : WebSocket public si séparé de `api`.
- `static.quintessences-platform.com` : assets publics (images, JS, CSS).
- `cdn.quintessences-platform.com` : cache dédié pour fichiers volumineux.

---

## 5. Enregistrements DNS nécessaires

### 5.1 Création maintenant

| Type | Nom | Cible | Proxy Cloudflare | TTL | Proxy | Note |
|---|---|---|---|---|---|---|
| CNAME | `www` | `quintessences-landing.pages.dev` | Activé | Auto | Orange | Landing page Cloudflare Pages |
| CNAME | `status` | `quintessences-landing.pages.dev` | Activé | Auto | Orange | Landing page temporaire (status à venir) |

### 5.2 Création avec le tunnel existant

| Type | Nom | Cible | Proxy Cloudflare | Note |
|---|---|---|---|---|
| CNAME | `api` | `07e329c5-7e1f-4bdd-898f-bc38a10ad287.cfargotunnel.com` | Activé | **Déjà en place** |

### 5.3 Réservations (pas d’enregistrement actif)

| Type | Nom | Cible future |
|---|---|---|
| CNAME | `app` | Tunnel ou Cloudflare Pages |
| CNAME | `auth` | Tunnel Keycloak ou API `/auth` |
| CNAME | `docs` | Cloudflare Pages / Docusaurus |
| CNAME | `geosylva` | Tunnel app GeoSylva |
| CNAME | `ignis` | Tunnel app Ignis |
| CNAME | `hydro` | Tunnel app Hydro |
| CNAME | `flora` | Tunnel app Flora |
| CNAME | `artemis` | Tunnel app Artemis |
| CNAME | `terra` | Tunnel app Terra |
| CNAME | `atmos` | Tunnel app Atmos |
| CNAME | `dev` | Tunnel dev + Access |
| CNAME | `staging` | Tunnel staging + Access |
| CNAME | `control` | Tunnel admin + Access |

### 5.4 Apex

| Type | Nom | Cible | Note |
|---|---|---|---|
| CNAME | `quintessences-platform.com` | `quintessences-landing.pages.dev` | Cloudflare CNAME flattening sur l’apex pour la landing page Pages. |

---

## 6. Architecture d’hébergement de la landing page

### 6.1 Solution recommandée : Cloudflare Pages (gratuit)

| Critère | Cloudflare Pages | Alternative : S3 statique |
|---|---|---|
| Coût | Gratuit (100 000 requêtes/jour, 500 builds/mois) | Coût AWS (stockage + egress) |
| SSL | Automatique | Certificat à gérer |
| CDN | Global intégré | CloudFront ou autre |
| CI/CD | GitHub/GitLab intégré | Nécessite pipeline externe |
| Branchements | 1 projet = 1 site, branches preview | Possible mais lourd |
| Vendor lock-in | Moyen (Cloudflare) | Moyen (AWS) |

**Recommandation :** Cloudflare Pages car gratuit, intégré au domaine, et conforme au principe free-first.

### 6.2 Contenu minimal de la landing page

- Logo + nom de marque **Quintessences**.
- Phrase d’accroche : *"Écosystème d’intelligence environnementale — le jumeau numérique fédéré des territoires vivants."*
- Liens vers :
  - `docs.quintessences-platform.com` (documentation publique)
  - `status.quintessences-platform.com` (statut)
  - `api.quintessences-platform.com/docs` (API)
- Mentions légales + politique de confidentialité.
- Formulaire d’inscription newsletter (hors scope RGPD = recueil consentement explicite).
- Turnstile (gratuit) sur tout formulaire pour bloquer les bots.

### 6.3 Structure du projet landing page

```
landing-quintessences/
├── public/
│   ├── index.html
│   ├── css/
│   ├── img/
│   └── robots.txt
├── package.json (optionnel)
└── wrangler.toml
```

### 6.4 Déploiement via Cloudflare Pages

```bash
# 1. Créer un projet Pages depuis le dashboard ou Wrangler
npx wrangler pages project create quintessences-landing

# 2. Déployer
npx wrangler pages deploy public/ --project-name=quintessences-landing

# 3. Dans le dashboard, lier le domaine personnalisé : quintessences-platform.com
```

---

## 7. Configuration HTTPS

### 7.1 Mode SSL/TLS (obligatoire)

Dans le dashboard Cloudflare :
- Aller à **SSL/TLS > Overview**.
- Choisir **Full (Strict)** dès que possible.
- Si l’origine n’a pas encore de certificat Cloudflare Origin, utiliser temporairement **Full** mais jamais **Flexible**.

### 7.2 Certificat Origin (gratuit)

| Étape | Action |
|---|---|
| 1 | **SSL/TLS > Origin Server** > Créer un certificat |
| 2 | Choix : *Cloudflare Origin CA* |
| 3 | Lister les noms : `api.quintessences-platform.com`, `app.quintessences-platform.com`, etc. |
| 4 | Télécharger le certificat `.pem` et la clé privée `.key` |
| 5 | Déposer dans `GSIE/API/secrets/origin-cert.pem` et `origin-key.pem` |
| 6 | Configurer Uvicorn/Gunicorn en TLS ou utiliser un reverse-proxy local (Caddy/Nginx) |

### 7.3 Configuration Caddy recommandée (open source, auto-HTTPS)

```caddy
{
    auto_https off
}

:8443 {
    tls /etc/caddy/origin-cert.pem /etc/caddy/origin-key.pem
    reverse_proxy 127.0.0.1:8000
    header > Strict-Transport-Security "max-age=31536000; includeSubDomains"
}
```

> Caddy n’est pas obligatoire : dans un premier temps, le tunnel Cloudflare chiffre déjà le trafic de l’edge jusqu’au connecteur local. Le certificat Origin CA renforce la protection contre les interceptions côté Cloudflare.

### 7.4 HSTS / HTTPS forcé

| Paramètre | Valeur | Note |
|---|---|---|
| Always Use HTTPS | ON | Redirection 301 HTTP → HTTPS |
| Automatic HTTPS Rewrites | ON | Réécriture des liens HTTP en HTTPS |
| HSTS | ON | `max-age=31536000`, `includeSubDomains`, pas `preload` tant que pas testé |
| Minimum TLS Version | 1.2 | 1.3 si tous les clients compatibles |

---

## 8. Stratégie d’e-mail professionnel

### 8.1 Solution gratuite recommandée : Cloudflare Email Routing

| Élément | Détails |
|---|---|
| Coût | Gratuit |
| Capacité | Réception et réacheminement d’e-mails vers une boîte existante |
| Quotas | Limités en nombre de règles, suffisants pour un démarrage |
| Avantage | Pas de serveur SMTP à gérer, pas de coût additionnel |

### 8.2 Adresses à créer

| Adresse | Usage | Destination externe temporaire |
|---|---|---|
| `contact@quintessences-platform.com` | Contact général | Adresse e-mail du Fondateur |
| `noreply@quintessences-platform.com` | E-mails transactionnels API | Aucune (adresse d’envoi seule) |
| `security@quintessences-platform.com` | Signalement de vulnérabilité | Adresse du Fondateur |
| `founder@quintessences-platform.com` | Correspondance officielle | Adresse du Fondateur |

### 8.3 Modification côté API

Dans `GSIE/API/.env` :

```env
GSIE_EMAIL_SENDER=noreply@quintessences-platform.com
```

Le SMTP transactionnel reste externe (Mailgun, SendGrid, AWS SES, ou relais du FAI) une fois le volume dépassant les capacités de l’hébergement actuel.

### 8.4 E-mail transactionnel à volume

| Phase | Solution | Coût estimé |
|---|---|---|
| Développement / test | Mailpit (local) | Gratuit |
| Lancement (≤ 100 e-mails/jour) | Cloudflare Email Routing + relais SMTP existant | Gratuit ou quasi |
| Croissance | Mailgun / SendGrid / AWS SES | ~ 10–30 $/mois pour 10 000 e-mails |

### 8.5 SPF / DKIM / DMARC

| Étape | Action |
|---|---|
| 1 | Attendre de disposer du relais d’envoi final |
| 2 | Ajouter l’enregistrement TXT `SPF` |
| 3 | Ajouter la clé publique DKIM fournie par le relais |
| 4 | Publier un DMARC `p=quarantine` puis `p=reject` |

> Avant d’avoir un relais fiable, ne pas publier de DMARC `reject` : les e-mails ne seraient pas authentifiés et seraient rejetés par les destinataires.

---

## 9. Règles de sécurité

### 9.0 Permissions du token API Cloudflare

Lors de la création d’un token `Quintessences-Devin-Setup` (ou équivalent), activer **au minimum** les permissions suivantes pour permettre la configuration automatisée via l’API. Les numéros correspondent aux libellés affichés dans le dashboard Cloudflare pour le compte `eeae29da23faaa394198aec9f6d0d0b6`.

| Périmètre | Permission | # | Utilité |
|---|---|---|---|
| **DNS zone** | DNS View Read | 109 | Lire les enregistrements DNS |
| **DNS zone** | DNS View Write | 108 | Créer/modifier les enregistrements DNS |
| **DNS zone** | Account DNS Settings Read | 119 | Lire DNSSEC et autres paramètres DNS du compte |
| **DNS zone** | Account DNS Settings Write | 118 | Modifier DNSSEC |
| **SSL/TLS** | Account: SSL and Certificates Read | 176 | Lire les paramètres SSL |
| **SSL/TLS** | Account: SSL and Certificates Write | 177 | Modifier SSL/TLS, HSTS, Always Use HTTPS |
| **WAF** | Account WAF Read | 215 | Lire les règles WAF gérées |
| **WAF** | Account WAF Write | 214 | Activer les Managed Rules |
| **Rate limiting** | Account Rulesets Read | 226 | Lire les rulesets |
| **Rate limiting** | Account Rulesets Write | 227 | Créer/modifier les rulesets WAF/rate limiting |
| **Rate limiting** | Account Rule Lists Read | 248 | Lire les listes de règles |
| **Rate limiting** | Account Rule Lists Write | 247 | Gérer les listes de règles |
| **E-mail** | Email Routing Addresses Read | 201 | Lire les routes e-mail |
| **E-mail** | Email Routing Addresses Write | 200 | Créer les routes e-mail |
| **Pages** | Pages Read | 202 | Lire les projets Pages |
| **Pages** | Pages Write | 203 | Déployer les projets Pages |
| **Tunnel** (optionnel) | Cloudflare Tunnel Read | 233 | Lire la configuration tunnel |
| **Tunnel** (optionnel) | Cloudflare Tunnel Write | 232 | Modifier les tunnels |
| **Turnstile** (optionnel) | Turnstile Sites Read | 198 | Lire les sites Turnstile |
| **Turnstile** (optionnel) | Turnstile Sites Write | 197 | Créer/mettre à jour Turnstile |

**Ressources :** dans le token, inclure le compte `eeae29da23faaa394198aec9f6d0d0b6` avec `*` (accès à toutes les zones du compte) ou spécifier `quintessences-platform.com` si l’interface le permet.

> **Important :** le token précédent a été roulé car il manquait `DNS View Write` et `Account: SSL and Certificates Write`. Sans ces deux permissions, les appels API sur `/zones/{zone_id}/dns_records` et `/zones/{zone_id}/settings/ssl` retournent `Authentication error` ou `Unauthorized`.

### 9.1 DNSSEC

- Activer DNSSEC dans le dashboard Cloudflare :
  - **DNS > DNSSEC > Enable DNSSEC**.
- Cela protège contre l’empoisonnement du cache DNS.
- Coût : gratuit.

### 9.2 WAF (Web Application Firewall)

| Niveau | Solution | Coût | Action |
|---|---|---|---|
| Gratuit | Cloudflare Managed Rules (OWASP Core Rule Set) | Gratuit | Activer dans **Security > WAF > Managed Rules** |
| Payant (si besoin) | Cloudflare Pro WAF | 20 $/mois | Seulement si le trafic justifie des règles avancées |

Règles minimales recommandées :
- Bloquer les requêtes avec `User-Agent` vide ou anormal.
- Limiter `/auth/*` à 10 requêtes/minute par IP.
- Bloquer les scanners connus (`/phpmyadmin`, `/.env`, `/wp-admin`, etc.).

### 9.3 Rate limiting

| Couche | Mécanisme | Note |
|---|---|---|
| Origine (GSIE) | slowapi avec `CF-Connecting-IP` en mode `cloudflare_tunnel` | **Déjà en place** |
| Bordure (Cloudflare) | Rate Limiting Rules | Gratuit jusqu’à 10 000 requêtes/mois, puis payant. À activer sur `/auth/*` et `/api/v1/auth/*`. |

### 9.4 Cloudflare Access (Zero Trust)

| Ressource | Politique | Coût |
|---|---|---|
| `control.quintessences-platform.com` | MFA + e-mail du Fondateur | Gratuit pour ≤ 50 utilisateurs |
| `dev.quintessences-platform.com` | MFA + e-mail du Fondateur | Gratuit |
| `staging.quintessences-platform.com` | MFA + e-mails de l’équipe | Gratuit |

### 9.5 Turnstile

- Activer Cloudflare Turnstile (gratuit) sur tous les formulaires publics.
- Clé du site dans `GSIE/API/.env`, clé secrète côté API.
- Avantage : remplacement invisible de captcha, respect RGPD.

### 9.6 MFA compte Cloudflare

- Activer l’authentification multifacteur sur le compte Cloudflare.
- Limiter les clés API au strict minimum (zone:read, dns_records:edit si nécessaire).
- Ne jamais partager le compte Cloudflare.

### 9.7 Clés et secrets

| Secret | Emplacement | Gestion |
|---|---|---|
| Tunnel token | `C:\Users\camil\.cloudflared\07e329c5-...json` | Hors Git, permissions restreintes |
| Origin CA cert | `GSIE/API/secrets/` | Hors Git |
| JWT RS256 keys | `GSIE/API/keys/` | Hors Git, déjà en place |
| API keys Cloudflare | Dashboard + gestionnaire de mots de passe | Jamais dans `.env.example` |

### 9.8 Journalisation

- Journaliser dans `GSIE/API/audit/` ou via outbox toute modification DNS, rotation de token, changement de politique Access.
- Cloudflare Audit Log est disponible dans le dashboard pour les actions dashboard.

---

## 10. Coûts estimés

### 10.1 Coûts fixes annuels

| Service | Coût | Justification |
|---|---|---|
| Domaine `quintessences-platform.com` | 10,46 $/an | Cloudflare Registrar, prix coutant |
| **Total annuel minimal** | **10,46 $** | — |

### 10.2 Coûts optionnels potentiels

| Service | Coût | Seuil d’activation |
|---|---|---|
| Cloudflare Pro | 20 $/mois | WAF avancé, cache par page, analytics détaillés si trafic important |
| Cloudflare Load Balancing | 5 $/mois + 0,50 $/probe | 2+ origines en production |
| Cloudflare R2 | 0,015 $/Go stockage + egress | Stockage de fichiers > Cloudflare Pages limites |
| Workers (unpaid usage limit) | Gratuit jusqu’à 100 000 requêtes/jour | Edge functions sans état |
| KV | Gratuit jusqu’à 100 000 lectures/jour | Configuration edge, flags |
| Pages | Gratuit jusqu’à 100 000 requêtes/jour | Landing + docs |
| Email Routing | Gratuit | Tant que relais et quotas suffisants |
| Mailgun / SendGrid | 10–30 $/mois | > 100 e-mails transactionnels/jour |
| Azure / serveur dédié | Variable | Migration progressive si charge > matériel local |

### 10.3 Coûts évolutifs à surveiller

- Si le trafic dépasse les quotas gratuits de Workers/KV/Pages, évaluer Workers Paid (5 $/mois pour 10 M requêtes).
- Si le stockage de fichiers croît, évaluer R2 vs un object storage Azure (compatible hybride).
- Si la charge GSIE dépasse le PC local, migrer vers un VPS cloud (~ 20–50 $/mois) ou Azure B2s.

---

## 11. Limites des offres gratuites

### 11.1 Cloudflare Free

| Service | Quota gratuit | Limite | Risque de dépassement |
|---|---|---|---|
| DNS | Illimité | — | Négligeable |
| Universal SSL | Illimité | 1 niveau de sous-domaine max pour certains certificats anciens | Aucun avec SNI moderne |
| CDN / Cache | Illimité | Cache statique, pas API par défaut | Négligeable |
| DDoS Protection | Illimité | — | Négligeable |
| Pages | 100 000 requêtes/jour | 500 builds/mois | Très faible au début |
| Workers | 100 000 requêtes/jour | 10 ms CPU, 50 ms init | Très faible au début |
| KV | 100 000 lectures/jour, 1 000 écritures/jour, 1 Go stockage | Latence propagation ~ 60 s | Très faible au début |
| R2 | 10 Go stockage gratuit, egress gratuit jusqu’à un seuil | — | Très faible au début |
| Email Routing | Règles limitées | 200 e-mails/re-routage/jour approximativement | Faible |
| Turnstile | 1 M widget affichages/mois | — | Très faible au début |
| Web Analytics | Illimité | Données retenues 7 jours | Acceptable |
| Rate Limiting Rules | 10 000 requêtes/mois | Au-delà : payant | Surveiller sur `/auth/*` |
| Access | 50 utilisateurs | Au-delà : 3 $/utilisateur/mois | Acceptable pour équipe restreinte |

### 11.2 Points d’attention

- **Universal SSL** ne couvre pas plus d’un niveau de sous-domaine sur certains certificats legacy. Avec SNI moderne et le tunnel, ce n’est pas un problème.
- **Workers** ne doivent pas stocker d’état métier : KV est un cache, pas une base de données.
- **R2 egress** est gratuit dans le plan gratuit jusqu’à un certain seuil, mais au-delà, facturé. Ne pas en faire le stockage principal des données scientifiques volumineuses sans migration planifiée.

### 11.3 Solutions de remplacement

| Service Cloudflare | Remplacement possible | Quand l’envisager |
|---|---|---|
| Pages | Netlify, Vercel, GitHub Pages | Si CI/CD GitHub préférée |
| Workers | Deno Deploy, Fly.io, Azure Functions | Si logique complexe edge ou migration hybride |
| KV | Redis, PostgreSQL hmac | Si forte consistance requise |
| R2 | MinIO, Azure Blob, S3 | Si multi-cloud ou gros volumes |
| Tunnel | WireGuard + reverse proxy, Tailscale Funnel | Si vendor lock-in Cloudflare à réduire |
| Access | Keycloak, Authentik, Zitadel | Si contrôle d’identité interne requis |

---

## 12. Étapes d’évolution

### 12.1 Phase 1 — Bootstrap (immédiat, 0–2 semaines)

1. Corriger les points de vigilance de l’audit (voir §1.6).
2. Activer DNSSEC, HSTS, Always Use HTTPS.
3. Créer `www` et `status`.
4. Mettre en place une landing page minimale sur Cloudflare Pages.
5. Configurer Email Routing pour `contact@` et `noreply@`.
6. Activer Managed Rules WAF gratuit.
7. Renforcer MFA et clés API Cloudflare.

### 12.2 Phase 2 — Consolidation (2–8 semaines)

1. Créer `docs.quintessences-platform.com` (Docusaurus ou Astro Starlight).
2. Préparer `app.quintessences-platform.com` (portail utilisateur).
3. Mettre en place `control.quintessences-platform.com` avec Cloudflare Access.
4. Déployer un environnement `staging` avec un tunnel dédié.
5. Ajouter Turnstile sur les formulaires publics.
6. Mettre en place un relais SMTP transactionnel et configurer SPF/DKIM/DMARC.

### 12.3 Phase 3 — Multi-app (3–6 mois)

1. Créer les sous-domaines spécifiques (`geosylva`, `ignis`, `hydro`, `flora`, `artemis`, `terra`, `atmos`) au fur et à mesure des MVP.
2. Migrer l’API du host Windows vers le conteneur Docker `api-api-1` ou un VPS.
3. Mettre en place un Load Balancer Cloudflare si 2+ origines.
4. Évaluer Cloudflare Pro si le trafic le justifie.

### 12.4 Phase 4 — Hybride / cloud (6–18 mois)

1. Évaluer Azure, Hetzner ou OVH pour l’hébergement de la charge métier.
2. Conserver Cloudflare comme bordure (décision `DEC-000047`).
3. Migrer progressivement les données et services sans changer les contrats API.
4. Mettre en place un plan de continuité d’activité multi-région si critique.

---

## 13. Checklist de mise en production

### 13.1 Avant activation publique

- [ ] DNSSEC activé.
- [ ] SSL/TLS en `Full` ou `Full (Strict)`.
- [ ] HSTS activé.
- [ ] Always Use HTTPS activé.
- [ ] WAF Managed Rules activé.
- [ ] Rate limiting sur `/auth/*` activé (Cloudflare + origine).
- [ ] API `GSIE_EDGE_PROXY_MODE=cloudflare_tunnel`.
- [ ] CORS restreints aux origines de production.
- [ ] `GSIE_EMAIL_SENDER` = `noreply@quintessences-platform.com`.
- [ ] Landing page déployée.
- [ ] `status` déployé.
- [ ] Email Routing configuré.
- [ ] Secrets hors Git (`cert.pem`, credentials tunnel, JWT keys).
- [ ] MFA sur le compte Cloudflare.
- [ ] Clés API Cloudflare restreintes.
- [ ] `GSIE_ENVIRONMENT=production` sur le serveur de prod.
- [ ] Logs et audit activés.

### 13.2 Tests de validation

```bash
# DNS
nslookup api.quintessences-platform.com
nslookup www.quintessences-platform.com
nslookup status.quintessences-platform.com

# SSL
curl -I https://api.quintessences-platform.com/health
curl -I https://quintessences-platform.com
curl -I https://www.quintessences-platform.com

# Headers
curl -s -D - https://api.quintessences-platform.com/health | grep -iE "strict-transport|x-frame|content-security|referrer|permission"

# API
curl https://api.quintessences-platform.com/health
curl https://api.quintessences-platform.com/api/v1/openapi.json

# Taille limite
curl -X POST https://api.quintessences-platform.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  --data-binary @/dev/zero  # Doit être rejeté par 413
```

### 13.3 Rollback rapide

1. Supprimer le CNAME du sous-domaine problématique dans Cloudflare.
2. Ou arrêter le connecteur `cloudflared` : `docker compose --profile edge stop cloudflared`.
3. Ou modifier `config.yml` pour pointer le sous-domaine vers `http_status:404`.
4. Vérifier que l’origine locale reste accessible en interne pour le diagnostic.

---

## 14. Procédure de retour arrière

### 14.1 Scénarios de retour arrière

| Scénario | Action | Durée |
|---|---|---|
| Incident tunnel | Arrêter `cloudflared`, recréer un nouveau tunnel, mettre à jour le CNAME DNS | 5–15 min |
| Fuite credentials tunnel | Révoquer le tunnel dans le dashboard, en créer un nouveau, redéployer le fichier secret | 10–20 min |
| Mauvais déploiement DNS | Restaurer les enregistrements DNS depuis une sauvegarde CSV ou le dashboard history | 2–10 min |
| Problème certificat SSL | Passer temporairement en `Full` puis reprovisionner le certificat Origin CA | 5–15 min |
| Migration hors Cloudflare | Basculer vers un reverse-proxy externe (Caddy/Nginx) avec un certificat Let’s Encrypt, puis couper le tunnel | 1–2 h |

### 14.2 Sauvegarde DNS

Exporter les enregistrements DNS régulièrement :

```bash
# Via Cloudflare API (nécessite une clé API avec zone:read)
curl -X GET "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/dns_records" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" > dns_backup.json
```

### 14.3 Restauration du tunnel

```powershell
# 1. Arrêter le tunnel
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel cleanup gsie-api

# 2. Révoquer dans le dashboard
# Cloudflare Dashboard > Zero Trust > Networks > Tunnels > gsie-api > Delete

# 3. Créer un nouveau tunnel
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel create gsie-api-new
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel route dns gsie-api-new api.quintessences-platform.com

# 4. Mettre à jour le config.yml avec le nouveau credentials-file
# 5. Relancer start-tunnel.ps1
```

### 14.4 Retour à un reverse proxy classique

1. Arrêter `cloudflared`.
2. Ouvrir un port 443 sur un reverse-proxy (Caddy/Nginx) avec Let’s Encrypt.
3. Mettre à jour l’enregistrement DNS `api` en A/AAAA vers l’IP publique du serveur.
4. **Ne jamais ouvrir les ports PostgreSQL, Redis, Mailpit sur Internet.**
5. Limiter le firewall aux ports 443 et 80.
6. Cette procédure n’est recommandée qu’en cas de sortie de Cloudflare complète, car elle expose directement le serveur.

---

## 15. Synthèse décisionnelle

| Choix | Recommandation | Coût | Risque | Remplacement |
|---|---|---|---|---|
| DNS | Cloudflare gratuit | Inclus domaine | Faible | Tout DNS anycast |
| SSL | Universal SSL + Origin CA | Gratuit | Faible | Let’s Encrypt |
| Bordure | Cloudflare Tunnel | Gratuit | Faible | WireGuard/Tailscale |
| Landing | Cloudflare Pages | Gratuit | Faible | Netlify/Vercel |
| Docs | Cloudflare Pages / Docusaurus | Gratuit | Faible | GitHub Pages |
| E-mail | Cloudflare Email Routing | Gratuit | Moyen (quotas) | Relais SMTP externe |
| Auth edge | Cloudflare Access (≤ 50 users) | Gratuit | Faible | Keycloak/Zitadel |
| WAF | Managed Rules gratuit | Gratuit | Faible | ModSecurity/Nginx |
| Cache | Cloudflare CDN | Gratuit | Faible | Varnish/ATS |
| Fichiers | R2 (si volume) | Gratuit jusqu’au seuil | Moyen | MinIO/Azure Blob |

**Verdict :** le déploiement actuel est conforme aux principes free-first, open-source first, low-cost, secure-by-design et évolutif. Les actions prioritaires sont les corrections des points de vigilance (§1.6), l’activation DNSSEC/HSTS, la mise en place de la landing page et la configuration e-mail.
