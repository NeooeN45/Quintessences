# Rotation des clés RSA JWT — Procédure d'exploitation

| Champ | Valeur |
|---|---|
| **Statut** | Draft |
| **Date** | 2026-07-26 |
| **Propriétaire** | Fondateur |
| **Portée** | API GSIE — authentification JWT RS256 |
| **Sources** | `core/auth.py`, `core/config.py`, `.env.example`, `docker/generate-jwt-keys.sh` |

---

## 1. Prérequis

- Accès shell au serveur hébergeant l'API GSIE (ou au conteneur Docker).
- Localisation des clés actuelles (variables `GSIE_JWT_PRIVATE_KEY_PATH` et `GSIE_JWT_PUBLIC_KEY_PATH`, par défaut `keys/private.pem` et `keys/public.pem`).
- Sauvegarde des clés actuelles avant toute opération (voir §6 Rollback).
- Fenêtre de maintenance planifiée (voir §4 pour la contrainte de chevauchement).
- Outil `openssl` disponible sur le serveur.

## 2. Génération d'une nouvelle paire de clés

```bash
# RSA 4096 bits, clé privée non chiffrée (à protéger par permissions fichier)
openssl genrsa -out keys/private.pem.new 4096

# Clé publique correspondante
openssl rsa -in keys/private.pem.new -pubout -out keys/public.pem.new

# Vérifier la paire
openssl rsa -in keys/private.pem.new -check -noout
openssl rsa -pubin -in keys/public.pem.new -text -noout | head -5
```

Permissions attendues (POSIX) :
```bash
chmod 600 keys/private.pem.new
chmod 644 keys/public.pem.new
chown <api_user>:<api_group> keys/*.pem.new
```

## 3. Déploiement

1. **Sauvegarder** les clés actuelles (voir §6).
2. **Remplacer** les fichiers :
   ```bash
   mv keys/private.pem keys/private.pem.<date>.bak
   mv keys/public.pem   keys/public.pem.<date>.bak
   mv keys/private.pem.new keys/private.pem
   mv keys/public.pem.new   keys/public.pem
   ```
3. **Redémarrer** l'API : les clés sont chargées au démarrage par `_load_private_key()` et `_load_public_key()` (`core/auth.py`). Un reload à chaud n'est pas supporté.
   ```bash
   # Docker
   docker compose restart api
   # Systemd
   systemctl restart gsie-api
   ```
4. **Vérifier** le démarrage dans les logs : aucune erreur `RuntimeError` concernant les clés JWT ne doit apparaître. En production/staging, une clé manquante provoque un `RuntimeError` bloquant (fail fast).

## 4. Période de chevauchement (grace period) — CONTRAINTE CRITIQUE

### État actuel du code

L'API GSIE **ne supporte pas nativement le multi-clés** (pas de `kid` JWT, pas de JWKS endpoint, pas de liste de clés publiques valides). `verify_token()` décode avec une seule clé publique chargée au démarrage.

**Conséquence** : toute rotation en production invalide **immédiatement** tous les tokens (access 15 min + refresh 7 j) émis avant la rotation. Tous les utilisateurs actifs doivent se reconnecter.

### Procédure applicable sans modification du code

1. **Avant la rotation**, vider le registre des refresh tokens (Redis) pour éviter qu'un client tente de rafraîchir un token signé avec l'ancienne clé :
   ```bash
   redis-cli --scan --pattern "gsie:refresh:*" | xargs -r redis-cli del
   ```
2. **Effectuer la rotation** (§2 + §3).
3. **Informer** les utilisateurs : notification de reconnexion obligatoire.
4. Les nouveaux tokens émis après redémarrage sont signés avec la nouvelle clé et validés correctement.

### Procédure alternative (chevauchement sans interruption) — nécessite une RFC

Pour supporter un chevauchement sans déconnexion (claim `kid`, ensemble de clés publiques valides, JWKS), une **RFC dédiée** doit être ouverte dans `02_RFC/` avant implémentation. Le contrat de `verify_token` et `_load_public_key` devra être étendu pour accepter une liste de clés publiques identifiées par `kid`.

## 5. Vérification post-rotation

1. **Login avec un nouveau compte** :
   ```bash
   curl -X POST https://api.gsie.fr/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test","password":"..."}'
   ```
   → token reçu (signé avec la nouvelle clé).
2. **Validation du token** :
   ```bash
   curl -H "Authorization: Bearer <token>" https://api.gsie.fr/api/v1/auth/me
   ```
   → 200 OK.
3. **Surveiller les logs** pendant 1 heure : rechercher `JWT`, `InvalidSignatureError`, `DecodeError`. Toute erreur récurrente indique un client encore configuré avec l'ancienne clé (à exclure du périmètre de l'API).
4. **Métriques** : surveiller le taux de login et le taux d'erreur 401. Un pic transitoire est attendu (utilisateurs reconnectés), un plateau durable signale un problème.

## 6. Rollback

Si la rotation provoque une régression (authentification cassée, erreurs 500) :

```bash
# Restaurer les anciennes clés
mv keys/private.pem keys/private.pem.<date>.failed
mv keys/public.pem   keys/public.pem.<date>.failed
mv keys/private.pem.<date>.bak keys/private.pem
mv keys/public.pem.<date>.bak   keys/public.pem

# Redémarrer
docker compose restart api   # ou systemctl restart gsie-api
```

Les tokens émis pendant la période problématique seront invalidés (ils étaient signés avec la clé défaillante). Les utilisateurs doivent se reconnecter.

## 7. Fréquence recommandée

- **Rotation préventive** : tous les 90 jours (bonne pratique sécurité).
- **Rotation d'urgence** : en cas de suspicion de compromission de la clé privée (fuite, accès non autorisé au serveur), rotation immédiate + invalidation de toutes les sessions + investigation.
- **Rotation réglementaire** : selon politique sécurité organisationnelle (ex. annuelle minimale).

## 8. Traçabilité

Chaque rotation doit être tracée :

- **Entrée CHANGELOG.md** : `security(jwt): rotation clés RSA — <date> — <raison>`
- **DEC-xxxxxx** dans `03_DECISIONS/` si la rotation modifie la politique (fréquence, procédure, support multi-clés).
- **Sauvegarde des anciennes clés** conservée pendant la durée de rétention légale (ex. 1 an) puis détruite sécuritairement (`shred -u`).

## 9. Points ouverts

- Support multi-clés (`kid` + JWKS) — nécessite RFC (voir §4).
- Alerting automatique sur expiration proche des clés (à intégrer à l'observabilité).
- Rotation automatisée via CI/CD (à évaluer selon le contexte déploiement).
