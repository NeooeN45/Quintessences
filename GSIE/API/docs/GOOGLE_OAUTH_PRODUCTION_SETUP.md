# Guide pas-à-pas — Activation Google OAuth en production

| Champ | Valeur |
|---|---|
| **Référence** | RFC-0032, DEC-000044 (Identité Quintessences) |
| **Statut** | Guide opérationnel — aucune étape ne peut être automatisée (compte Google, vérification par Google) |
| **Périmètre** | Écran de consentement OAuth, Client IDs Web + Android, déclaration côté API |

---

## 0. Pourquoi c'est manuel

Le code backend (`src/gsie_api/auth/google_identity.py`) est déjà complet et
fonctionnel : vérification signature/issuer/audience/nonce, anti-rejeu,
confusion de compte empêchée (voir `PENTEST_AUTH_CONNEXION_2026-08-07.md`).
Ce qui manque n'est **pas du code** — c'est la configuration du projet dans
la Google Cloud Console, qui exige un compte Google, des décisions de marque
(nom, logo) et, pour sortir du mode "test" limité à 100 utilisateurs,
une **vérification par Google elle-même** (délai : quelques jours à
quelques semaines selon les scopes demandés). Personne — humain ou IA —
ne peut accélérer cette dernière étape.

---

## 1. Créer/configurer le projet Google Cloud

1. Aller sur [console.cloud.google.com](https://console.cloud.google.com/).
2. Créer un projet dédié, par exemple `quintessences-platform` (ou
   réutiliser un projet existant si tu en as déjà un pour ce domaine).
3. Menu **APIs & Services → OAuth consent screen**.

## 2. Écran de consentement OAuth

| Champ | Valeur recommandée |
|---|---|
| **User Type** | External (les utilisateurs GeoSylva ne sont pas dans un Google Workspace GSIE) |
| **App name** | Quintessences (ou GeoSylva si tu préfères une marque séparée) |
| **User support email** | Une adresse que tu surveilles réellement |
| **App logo** | Logo Quintessences/GeoSylva (format PNG, 120×120px minimum) |
| **Application home page** | `https://quintessences-platform.com` |
| **Application privacy policy** | URL d'une page de politique de confidentialité publique — **obligatoire pour la vérification**, doit exister avant de soumettre |
| **Application terms of service** | Recommandé, pas strictement obligatoire pour les scopes basiques |
| **Authorized domains** | `quintessences-platform.com` |
| **Developer contact email** | Ton adresse |

### Scopes à déclarer

Le code ne demande que l'identité de base — pas d'accès Gmail/Drive/etc :

- `openid`
- `.../auth/userinfo.email`
- `.../auth/userinfo.profile`

Ce sont des scopes **non sensibles** ("basic"), donc la vérification Google
est plus rapide que pour des scopes sensibles/restreints — pas besoin de
justification vidéo ni d'audit de sécurité tiers.

## 3. Créer les Client IDs OAuth

Menu **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
Il faut **un Client ID par plateforme** (le backend accepte une liste, voir
§4) :

### 3.1 Client Web (Admin Web `GSIE/ADMIN_WEB/`)

- **Application type** : Web application
- **Name** : `quintessences-admin-web`
- **Authorized JavaScript origins** :
  - `https://quintessences-platform.com` (une fois l'Admin Web déployé —
    actuellement non déployé, dev local sur `http://localhost:4000`)
  - `http://localhost:4000` (dev)
- **Authorized redirect URIs** : le code utilise le flux **ID token
  direct** (Google Identity Services côté client, pas de code exchange
  serveur), donc en général **aucune redirect URI serveur n'est requise**
  pour ce Client ID — seule l'origine JS compte. Vérifie dans le SDK
  frontend utilisé (Google Identity Services `<script>` + `google.accounts.id`)
  s'il attend une `redirect_uri` explicite ; sinon laisse vide.

### 3.2 Client Android (GeoSylva)

- **Application type** : Android
- **Name** : `quintessences-geosylva-android`
- **Package name** : `com.forestry.counter` (valeur actuelle de
  `applicationId` dans `apps/GeoSylva/app/build.gradle.kts` — **vérifie
  qu'elle n'a pas changé** avant de la coller)
- **SHA-1 certificate fingerprint** : à récupérer avec :
  ```bash
  # Debug (dev/test)
  keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android

  # Release (production — utilise ton vrai keystore de signature)
  keytool -list -v -keystore /chemin/vers/ta-cle-release.jks -alias <alias>
  ```
  Ajouter **les deux empreintes** (debug + release) comme deux Client IDs
  Android distincts, ou un seul Client ID avec plusieurs empreintes selon
  ce que permet l'interface Google Cloud actuelle.

## 4. Déclarer les Client IDs côté API GSIE

Une fois les Client IDs créés (format `XXXXXXXXXX-xxxxxxxxxxxxx.apps.googleusercontent.com`),
les ajouter dans `.env` (jamais commité) :

```bash
GSIE_GOOGLE_OAUTH_CLIENT_IDS=["<web-client-id>.apps.googleusercontent.com","<android-client-id>.apps.googleusercontent.com"]
```

**Aucun secret OAuth n'est nécessaire côté API** — la vérification d'un ID
token Google ne requiert que le Client ID (audience publique), jamais le
Client Secret (`GSIE_GOOGLE_OAUTH_CLIENT_IDS` ne contient que des
identifiants publics, voir `.env.example` ligne 99-101 et
`src/gsie_api/auth/google_identity.py`).

Redémarrer l'API (`docker compose restart api`) pour charger la nouvelle
liste. Le endpoint `/auth/providers` (ou équivalent) doit alors annoncer
Google comme `"status": "available"` au lieu de `"not_configured"`.

## 5. Soumettre à la vérification Google

Une fois testé en interne (le projet reste en mode "Testing", limité aux
utilisateurs explicitement ajoutés comme testeurs dans la Google Cloud
Console — ajoute-toi toi-même et les premiers bêta-testeurs GeoSylva ici
avant de soumettre) :

1. Retour sur **OAuth consent screen**.
2. Bouton **Publish App** puis **Submit for verification**.
3. Google demandera de confirmer : politique de confidentialité
   accessible, logo conforme, domaine vérifié dans **Search Console**
   (`https://search.google.com/search-console` — ajouter et vérifier la
   propriété `quintessences-platform.com` si ce n'est pas déjà fait).
4. Délai typique pour des scopes basiques : quelques jours ouvrés.

**Tant que l'app n'est pas vérifiée**, elle reste utilisable en mode
Testing avec un nombre limité de comptes testeurs déclarés manuellement —
suffisant pour un bêta GeoSylva restreint, pas pour une ouverture large.

## 6. Checklist finale

- [ ] Écran de consentement rempli (logo, politique de confidentialité, domaine)
- [ ] Client ID Web créé (Admin Web)
- [ ] Client ID Android créé (`com.forestry.counter`, empreintes debug + release)
- [ ] `GSIE_GOOGLE_OAUTH_CLIENT_IDS` renseigné en production
- [ ] Domaine vérifié dans Search Console
- [ ] Testeurs bêta ajoutés (si encore en mode Testing)
- [ ] Soumission à vérification Google envoyée (si sortie du mode Testing souhaitée)

---

*Ce guide ne modifie aucun code — `google_identity.py` et
`GSIE_GOOGLE_OAUTH_CLIENT_IDS` sont déjà prêts à recevoir les Client IDs
une fois créés.*
