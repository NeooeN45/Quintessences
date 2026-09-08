# Quintessences — Release Readiness Score

## Objectif

Donner une réponse factuelle à la question : **Qu'est-ce qui empêche aujourd'hui Quintessences d'être prêt pour une bêta terrain ou une release ?**

Le score ne remplace jamais les critères bloquants. Un projet à 95/100 reste **NO-GO** s'il possède un P0 ouvert, une fuite inter-tenant ou une perte silencieuse de données.

## État courant

**Score global : NOT SCORED**

Aucun score initial n'est inventé. Chaque domaine doit être évalué à partir de preuves actuelles : CI, tests, benchmarks, tickets, rapports de simulation et validation scientifique.

## Score /100

| Domaine | Poids | État initial |
|---|---:|---|
| Sécurité & isolation | 18 | À mesurer |
| Intégrité des données & transactions | 14 | À mesurer |
| Tests & invariants | 14 | À mesurer |
| Résilience & offline-first | 12 | À mesurer |
| Performance & capacité | 10 | À mesurer |
| Validation scientifique | 12 | À mesurer |
| Observabilité & diagnostic | 6 | À mesurer |
| Migrations / sauvegarde / restauration | 6 | À mesurer |
| Documentation & contrats | 4 | À mesurer |
| Supply chain & reproductibilité build | 4 | À mesurer |
| **Total** | **100** | **NOT SCORED** |

## Barème par domaine

Chaque domaine reçoit un score de 0 à 100 puis est pondéré.

- **90–100** : preuves automatisées solides, scénarios adverses couverts, aucune dette critique connue.
- **75–89** : niveau bêta crédible, quelques risques P2/P3 maîtrisés.
- **60–74** : fonctionnement réel mais couverture insuffisante ou dette importante.
- **40–59** : risques significatifs non mesurés ou non couverts.
- **0–39** : domaine incompatible avec une bêta sérieuse.

## Gates absolus

Les conditions suivantes forcent `NO-GO` indépendamment du score :

1. P0 ouvert.
2. P1 de sécurité ou corruption non accepté explicitement.
3. fuite inter-tenant reproductible ou isolation RLS non démontrée sur les chemins critiques.
4. perte silencieuse de donnée terrain légitime.
5. migration non réversible ou restauration non testée avant une release impliquant des données persistées.
6. contrat API public incohérent avec le code ou les migrations sur une fonction critique.
7. résultat scientifique décisionnel sans provenance minimale exigée.
8. dépendance critique compromise ou vulnérabilité exploitable non mitigée.

## Évaluation Sécurité & isolation — 18 points

Preuves attendues :
- tests authN/authZ ;
- tests RLS multi-tenant ;
- scan secrets ;
- SAST / CodeQL / Bandit / Trivy selon périmètre ;
- dépendances ;
- validation uploads/inputs ;
- tests de contournement sur environnement contrôlé ;
- permissions CI minimales.

Décote forte si un contrôle existe uniquement sous forme de documentation.

## Intégrité données & transactions — 14 points

Évaluer :
- atomicité ;
- idempotence ;
- rollback ;
- contraintes DB ;
- cohérence `resource` / sous-types ;
- absence d'orphelins ;
- soft-delete ;
- concurrence réelle PostgreSQL.

Références principales : INV-001, INV-003, INV-004, INV-005, INV-010.

## Tests & invariants — 14 points

Évaluer :
- couverture globale et par couche ;
- mutation testing ;
- intégration réelle ;
- property-based ;
- tests de concurrence ;
- tests de contrat ;
- chaque invariant P0/P1 relié à une preuve automatisée.

Un taux de couverture élevé ne compense pas un invariant critique non testé.

## Résilience & offline-first — 12 points

Évaluer :
- coupures réseau ;
- retry ;
- reprise après crash ;
- Redis/DB indisponibles ;
- synchronisation longue durée ;
- conflits ;
- reprise d'upload ;
- perte de paquets ;
- état local ancien.

Référence : INV-008 et `V1_BETA_SIMULATION_PLAN.md`.

## Performance & capacité — 10 points

Source obligatoire : `BENCHMARK_BASELINE.md` et campagnes reproductibles.

Évaluer :
- p50/p95/p99 ;
- débit ;
- mémoire ;
- saturation pools ;
- SQL ;
- géospatial ;
- ingestion ;
- coût IA ;
- régressions entre commits/releases.

Un domaine non mesuré ne peut pas obtenir > 60/100.

## Validation scientifique — 12 points

Pour chaque moteur décisionnel :
- référence indépendante ;
- erreur / tolérance ;
- unités ;
- CRS ;
- incertitude ;
- provenance ;
- version modèle/dataset ;
- comportement hors domaine ;
- cas limites ;
- reproductibilité.

Un test logiciel vert ne prouve pas la validité scientifique.

## Observabilité — 6 points

Évaluer :
- logs structurés ;
- correlation/request IDs ;
- métriques ;
- traces ;
- erreurs actionnables ;
- audit trail ;
- visibilité des retries, rollback et dégradations.

## Migrations / sauvegarde / restauration — 6 points

Évaluer :
- Alembic cycle ;
- upgrade depuis version précédente ;
- données réalistes ;
- backup ;
- restore ;
- temps d'indisponibilité ;
- vérification d'intégrité après restauration.

## Documentation & contrats — 4 points

Évaluer :
- OpenAPI synchronisé ;
- RFC/ADR cohérents ;
- documentation déploiement ;
- runbooks incidents ;
- versions et compatibilités explicites.

## Supply chain — 4 points

Évaluer :
- dépendances épinglées ;
- actions GitHub pinées par SHA quand pertinent ;
- SBOM ;
- licences ;
- vulnérabilités ;
- builds reproductibles ;
- provenance artefacts.

## Décision de release

| Score global | Décision par défaut |
|---:|---|
| 90–100 | GO si aucun gate absolu |
| 80–89 | GO bêta / GO avec risques documentés |
| 70–79 | GO limité / pilote contrôlé uniquement |
| 60–69 | NO-GO public ; bêta interne possible selon risques |
| < 60 | NO-GO |

## Format d'une évaluation

```text
READINESS-YYYYMMDD-NNN
Commit / tag:
Cible: V1 beta / RC / V1
Score global:
Gates absolus: PASS/FAIL
Sécurité:
Intégrité:
Tests & invariants:
Résilience:
Performance:
Validation scientifique:
Observabilité:
Migrations/restauration:
Documentation:
Supply chain:
P0 ouverts:
P1 ouverts:
Principaux risques:
Top 5 actions avant release:
Décision: GO / GO AVEC RISQUES / NO-GO
Sources de preuve:
```

## Règle d'évolution

À chaque campagne significative, corriger le score uniquement à partir de nouvelles preuves. La progression du score doit pouvoir être expliquée par des commits, tests, benchmarks ou tickets fermés.
