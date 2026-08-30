# Banc de gouvernance des sources à grande échelle

**Statut :** exécutable localement, preuve de production non publiée
**Date :** 2026-08-30

## Ce qui est mesuré

Le banc vérifie le coût et la stabilité des contrôles déterministes du Data
Registry et de la matrice des 14 moteurs lorsque les audits sont répétés. Il
ne simule pas un fournisseur, une licence, PostgreSQL, PostGIS, Redis ou une
charge HTTP et ne doit pas être présenté comme une preuve de SLO production.

Depuis `GSIE/API` :

```powershell
$env:PYTHONPATH = "src"
python scripts/benchmark_source_governance.py --iterations 10000
```

Le script refuse les volumes absurdes, n'ouvre aucun réseau et n'écrit aucune
donnée. Il affiche le nombre de sources, le nombre de moteurs, le temps total
et le débit d'audit.

## Campagnes encore nécessaires

Avant d'ouvrir la promotion ou de publier une capacité, une campagne séparée
doit couvrir :

1. un flux Forge complet avec manifest, checksum, archive et rejeu idempotent ;
2. un volume PostGIS représentatif, avec index, pagination et concurrence ;
3. Redis, files de tâches, timeouts, retry et reprise après panne ;
4. quotas réels des fournisseurs et respect des allowlists ;
5. défaillance d'une source pendant l'exécution des 14 moteurs ;
6. répétition d'un même lot sans doublon ni mutation silencieuse ;
7. séparation stricte des partitions d'entraînement et d'évaluation ;
8. validation experte des résultats avant toute promotion.

Les sources `METADATA_ONLY`, `PARTNER_GATE`, `EPHEMERAL_TDM` et `BLOCKED`
restent exclues de ces campagnes d'acquisition automatique.
