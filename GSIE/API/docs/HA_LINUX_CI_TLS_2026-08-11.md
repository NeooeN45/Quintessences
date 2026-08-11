# Qualification HA Linux native avec TLS — preuve distante

## État

Le workflow `.github/workflows/ha-linux.yml` est implémenté et déclenchable
manuellement ou par une pull request touchant la chaîne HA. Le run GitHub
Actions `31479643460`, sur le commit `6442655`, est réussi et constitue la
première preuve distante Linux/TLS du banc.

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

## Validation distante GitHub Actions

L'artefact `ha-linux-tls-results` du run `31479643460` contient les métriques
suivantes :

| Mesure | Résultat | Porte |
|---|---:|---:|
| Réponses HTTP 200 | 6 000/6 000 | 100 % |
| Erreurs de transport | 0 | 0 |
| Débit | 298,03 req/s | >= 120 req/s |
| p95 | 164,71 ms | <= 250 ms |
| p99 | 245,58 ms | <= 400 ms |
| Maximum observé | 545,90 ms | informatif |

Le replica A a été retiré pendant la charge, le replica B a servi les requêtes
restantes et `/ready` est demeuré disponible. Toutes les étapes de construction,
d'initialisation PostgreSQL, de migration, de TLS et de nettoyage sont vertes.
L'action de publication de l'artefact est épinglée sur une révision immuable.

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

## Conclusion

La qualification « Linux natif + TLS » du banc de drainage est clôturée. Elle
ne constitue pas encore un SLO de production : la requête longue réelle,
l'écriture HTTP idempotente et une qualification sur infrastructure cible
restent des travaux séparés.
