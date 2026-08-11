# Qualification HA Linux native avec TLS — workflow candidat

## État

Le workflow `.github/workflows/ha-linux.yml` est implémenté et déclenchable
manuellement ou par une pull request touchant la chaîne HA. Il n'est pas encore
qualifié comme preuve distante tant que GitHub Actions ne l'a pas exécuté après
push.

## Chaîne automatisée

```text
runner ubuntu-latest
→ construction PostgreSQL/PostGIS/AGE et API
→ migrations explicites
→ deux replicas API
→ HAProxy TLS
→ validation de la CA et du SAN
→ charge 6 000 requêtes
→ drainage de replica A
→ assertions p95, p99, débit, statuts et erreurs
→ artefact JSON
→ nettoyage intégral
```

Les identifiants du workflow sont strictement jetables. Le certificat est créé
pour une journée, sa clé ne sort pas du runner et le client reçoit uniquement
la CA. La vérification TLS reste active.

## Validation locale du câblage TLS

Un smoke test fonctionnel a été exécuté dans le runtime Linux Docker :

- route `/ready` ;
- 500/500 réponses 200 ;
- répartition 250/250 ;
- 277,84 req/s ;
- p95 71,87 ms ;
- p99 115,42 ms ;
- zéro erreur ;
- certificat vérifié via la CA éphémère.

Cette mesure valide le câblage TLS, pas la capacité du runner GitHub.

## Blocages honnêtes de la tranche suivante

### Requête longue

L'API n'expose pas de route de test artificiellement lente, ce qui est sain.
Il faut sélectionner une vraie opération métier longue ou définir un harnais
interne non publié avant de mesurer sa survie à un drainage.

### Écriture HTTP idempotente

Le rejeu idempotent du manifeste Data Registry existe, mais l'API ne possède
pas encore de contrat général `Idempotency-Key` pour une écriture REST. Rejouer
un POST ou un PUT actuel ne prouverait pas l'absence de doublon ou d'effet
ambigu. Une RFC doit définir clé, portée, TTL, empreinte de requête, stockage,
réponse rejouée et concurrence avant implémentation.

## Acceptation future

Après push, le run GitHub doit être relié à cette preuve avec son identifiant,
son artefact JSON et les métriques réelles. Seulement ensuite la qualification
« Linux natif + TLS » pourra être clôturée.
