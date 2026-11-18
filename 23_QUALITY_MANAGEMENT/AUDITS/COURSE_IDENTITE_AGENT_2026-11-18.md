# Course d'identité Agent — preuve PostgreSQL du 18 novembre 2026

[GSIE-PROMPT-0036](../../GSIE/PROMPTS/GSIE-PROMPT-0036-corriger-course-agent.md)
· [Ticket nº 76](https://github.com/NeooeN45/Quintessences/issues/76)
· Base `47be2044e1af9082a47dc1ad2d673fd16080f592`.

## Campagne avant et après

| Code | Analyses lancées | Commits vérifiés | Échecs |
| --- | ---: | ---: | ---: |
| `main` à `47be204` | 96 | 92 | 4 |
| Correctif GSIE-PROMPT-0036 | 96 | 96 | 0 |

Les quatre échecs du jour proviennent tous de `23505` sur `ix_resource_gsie_id`.
Ils concernent la salve 2/session 3, la salve 5/sessions 3 et 4 et la salve
9/session 3. Le constat historique du 16 novembre était de 2 échecs sur 96.

Le [harnais](../../GSIE/API/tests/integration/harnais_f.py) et
son [plan](../../GSIE/API/tests/integration/harnais_f_plan.json) sont une
reconstruction du §7.2. Les originaux cités dans ce bilan étaient archivés
hors du dépôt et n'ont pas été retrouvés dans les copies accessibles.
Le banc exécute les moteurs réels en 12 salves de huit transactions
indépendantes sous PostgreSQL 16.15. Chaque salve clone le même modèle migré
à `20260929_0059`. La barrière est placée immédiatement avant l'insertion
racine. Le banc contrôle les PID et XID, les commits, les recommandations
durables et leur attribution à l'unique couple Resource/Agent attendu. Les
erreurs comptent comme des échecs sans nouvelle tentative.

Le test existant à une salve reste en place. Le nouveau test est collecté
par le job d'intégration de la CI. Reproduction sur un hôte avec Docker et
le verrou Python de GSIE/API, depuis ce répertoire :

```bash
docker build -f Dockerfile.db -t gsie-testdb:latest .
uv sync --locked --extra dev
sh docker/generate-jwt-keys.sh
GSIE_REQUIRE_DOCKER=1 GSIE_REQUIRE_MIGRATION_IMAGE=true \
  TESTCONTAINERS_RYUK_DISABLED=true \
  uv run pytest -n 0 --no-cov -s tests/integration/test_orchestration.py \
  -k campagne_agent_moteur
```

## Refus et maintien jusqu'au commit

Une insertion racine sans cible arbitre la clé UUID et l'index sur `gsie_id`.
Sous `READ COMMITTED`, une instruction distincte relit directement les
colonnes en base après cet arbitrage. Le moteur vérifie l'UUID, le type
`agent` et le `gsie_id` canonique avant l'insertion de l'enfant. Il relit
ensuite le type de l'enfant. Une incohérence lève une erreur de domaine
explicite sans écraser les lignes existantes ni créer d'alias. Le nom
existant reste conservé. Une interruption entre les deux écritures suivie
du rollback de l'appelant ne laisse aucune racine partielle.

Les deux lectures prennent `FOR SHARE` dans l'ordre racine puis enfant.
Le verrou est nécessaire car chacun des deux types peut être modifié sans
modifier une clé. `FOR KEY SHARE` permettrait cette mise à jour. La mesure
utilise un Agent préalablement commité et un `lock_timeout` de 250 ms :

| Ligne | Modification avant commit | Modification après commit |
| --- | --- | --- |
| Racine | Refus PostgreSQL `55P03` à 253,2 ms | Réussite en 2,4 ms |
| Enfant | Refus PostgreSQL `55P03` à 251,9 ms | Réussite en 0,9 ms |

Le code de départ laissait passer les deux modifications avant le commit.
Avec le correctif, une seconde matérialisation du même Agent déjà commité
se termine pendant que la première transaction reste ouverte. Aucun verrou
consultatif ou verrou exclusif n'est requis pour ce chemin. Les temps de
la sonde illustrent le verrouillage, sans constituer un benchmark de latence.

Les sondes vérifient le `gsie_id` occupé par un autre UUID, la racine de type
`concept`, le `gsie_id` incorrect au même UUID et le type de l'enfant
incompatible. La mutation `agent_racine_conflit_limite_a_uuid` rétablit
l'arbitrage historique. Le test unitaire de compilation SQL et la sonde
PostgreSQL sont associés à ce mutant dans le harnais existant.

Le retour arrière est un revert de code. Il ne nécessite aucune modification
de schéma et réexpose la course historique. Les invariants du projet gardent
leur état actuel pendant la revue de cette proposition.
