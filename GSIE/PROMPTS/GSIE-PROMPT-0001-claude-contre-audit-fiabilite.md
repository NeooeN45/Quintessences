# GSIE-PROMPT-0001 — Contre-audit du jalon de fiabilité

| Champ | Valeur |
|---|---|
| Statut | BLOQUÉE — snapshot à rendre accessible |
| Agent cible | Claude |
| Environnement | Devin |
| Dépôts | Quintessences, GeoSylva, Forge |
| Branche | `fix/enterprise-reliability-2026-07-21` |
| Commits de départ | À renseigner avant attribution |
| Orchestrateur | Codex |
| Relecteur | Codex |
| Priorité | P0 |

## Mission

Réaliser une contre-revue indépendante et strictement en lecture seule du
jalon de fiabilité du 21 juillet 2026. Rechercher les défauts de sécurité,
d'intégrité, de concurrence, de migration, de documentation et de tests que
l'audit initial aurait pu manquer.

Ne corrige rien. Le livrable est un rapport adversarial étayé par le diff réel
et des commandes reproductibles.

## Précondition bloquante

Les trois snapshots contenant les changements locaux doivent être accessibles
et identifiés par SHA. Si la branche distante ne contient pas les changements
décrits dans RFC-0021 et CHANGELOG, arrête immédiatement avec `BLOQUÉE`.

## Documents obligatoires

- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_MEMORY.md`
- `02_RFC/RFC-0021-fiabilite-entreprise.md`
- `02_RFC/RFC-0022-orchestration-agents-ia.md`
- `03_DECISIONS/DEC-000031.md`
- `03_DECISIONS/DEC-000032.md`
- `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`
- les README et workflows CI de chaque dépôt.

## Périmètre

Examiner uniquement les changements de la branche indiquée dans :

- `GSIE/API/` et la gouvernance transverse du dépôt Quintessences ;
- `apps/GeoSylva/` dans son dépôt Git indépendant ;
- `Forge/` dans son dépôt Git indépendant.

## Angles de revue obligatoires

1. contournement de l'authentification ou des rôles ;
2. rejeu, course concurrente, atomicité et idempotence ;
3. SSRF, redirections, DNS rebinding et limites de lecture ;
4. migrations, rollback, sauvegarde et restauration ;
5. chiffrement local et compatibilité des données historiques ;
6. cohérence entre documentation, code, tests et CI ;
7. dépendances non verrouillées ou conteneurs trop privilégiés ;
8. tests donnant une confiance trompeuse ;
9. changement hors périmètre ou régression métier/scientifique ;
10. risque non déclaré dans RFC-0021.

## Interdictions

- Aucun fichier modifié.
- Aucun commit, push, commentaire GitHub, fusion ou déploiement.
- Aucun secret affiché.
- Aucun constat sans chemin, preuve et scénario d'impact.
- Ne pas traiter un avertissement comme une vulnérabilité sans justification.

## Méthode

1. Confirmer les trois SHA et l'absence de divergence.
2. Comparer chaque branche à sa base.
3. Lire les tests avant de juger les invariants.
4. Exécuter uniquement des commandes non mutantes utiles à la preuve.
5. Classer chaque constat P0, P1, P2, P3 ou observation.
6. Chercher activement à réfuter les garanties annoncées.
7. Remettre aussi une liste des zones examinées sans anomalie.

## Format du rapport

| ID | Gravité | Dépôt/fichier | Preuve | Scénario d'impact | Test manquant | Correction recommandée |
|---|---|---|---|---|---|---|

Terminer par :

- SHA examinés ;
- commandes exécutées et codes de sortie ;
- limites de l'audit ;
- risques résiduels ;
- verdict `EN_REVUE`, `BLOQUÉE` ou `REJETÉE`.

Ne déclare jamais le jalon validé : Codex reproduira les preuves et rendra le
verdict technique.
