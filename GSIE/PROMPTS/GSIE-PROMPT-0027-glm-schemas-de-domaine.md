# GSIE-PROMPT-0027 — Schémas de domaine : migration des tables métier

| Champ | Valeur |
|---|---|
| Statut | INTÉGRÉE |
| Agent cible | GLM 5.2 |
| Environnement | Devin |
| Dépôt | Quintessences |
| Branche | `feat/schemas-de-domaine` (partir de `feat/inventaire-sources-elargi`) |
| Fichiers possédés | `GSIE/API/alembic/versions/`, `GSIE/API/src/gsie_api/infrastructure/models/`, tests associés |
| Fichiers interdits | `src/gsie_api/engines/**` — aucun moteur ne change |
| Précédents | `RFC-0029` (Validée, `DEC-000039`), migrations `20260728_0011` et `0012` |
| Orchestrateur | Architecte |

## Documents obligatoires

- `02_RFC/RFC-0029.md` — schémas de domaine (validée par `DEC-000039`).
- `GSIE/API/alembic/versions/` — migrations Alembic (baseline `20260726_0001`).
- `GSIE/API/src/gsie_api/infrastructure/models/` — modèles SQLAlchemy.
- `GSIE/API/src/gsie_api/infrastructure/enums.py` — registre de types.
- `03_DECISIONS/DEC-000036.md` — assainissement de l'historique Alembic.
- `GSIE/ARCHITECTURE/ADR-005.md` — Outbox/Inbox.

## Mission

Migrer les tables métier vers sept schémas de domaine PostgreSQL
(botanique, foret, gouvernance, climat, pedologie, hydro, feu) via
migrations Alembic autonomomes. Étendre le rôle applicatif pour qu'il
n'ait accès qu'aux schémas de son moteur. Une migration par schéma,
chacune réversible.

## Constat

`RFC-0029` est validée par `DEC-000039`. Le premier lot — l'isolement RGPD — est
livré : deux schémas, des rôles, un rôle applicatif sans accès aux données
personnelles, douze tests d'intégration.

**Restent sept schémas de domaine.** C'est un travail mécanique, répétitif, et
dont chaque étape est vérifiable. Il n'appelle aucune décision de conception :
elles sont prises.

## Interdictions

## 1. Ce que tu ne dois surtout pas faire

**Ne touche pas au noyau.** `resource` reste dans `public`, et `gsie_noyau` ne
sera pas créé dans ce lot.

La raison est mesurée : **315 des 324 clés étrangères du registre pointent vers
`resource`**, soit 97 %. Déplacer cette table imposerait de réécrire la cible
de 315 contraintes dans les modèles. Et ce renommage n'apporte **aucune
sécurité** — il n'apporte qu'un nom. Le cloisonnement protège parce que les
tables métier *sortent* de `public`, pas parce que `public` change d'étiquette.

Si tu penses devoir toucher au noyau pour avancer, **arrête-toi et signale-le**.

## 2. Les quatre effets de second ordre — ils t'attendent

Déplacer **quatre** tables sur une base **vide** a demandé quatre corrections
d'infrastructure, toutes invisibles à la lecture. Elles se reproduiront :

| Effet | Ce qui casse | Où corriger |
|---|---|---|
| `create_all` ne crée pas les schémas | Toute la suite d'intégration | `tests/conftest.py` — déjà fait, dérive le schéma du registre |
| Le contrôle de dérive lit un `search_path` | Il signale une dérive inexistante **et masque les vraies** | `include_schemas` — déjà posé |
| Le verrou d'ensemble compare des noms nus | Les tables déplacées paraissent disparues | `_public_tables` — déjà qualifié, mais sa **liste de schémas est en dur** : ajoute les tiens |
| SQLite ne connaît pas les schémas | 35 erreurs dans `test_service.py` | `ATTACH DATABASE ':memory:' AS <schema>` — déjà fait, dérive du registre |

Trois sont déjà génériques. **Le quatrième ne l'est pas** :
`test_migration_baseline.py::_public_tables` énumère les schémas en dur. C'est
le premier endroit à corriger, et l'oublier fera échouer le contrôle de dérive
avec un message trompeur.

## 3. Les sept schémas

| Schéma | Domaine |
|---|---|
| `gsie_botanique` | Taxons, autécologie, identification, clés de détermination |
| `gsie_climat` | Stations, observations, normales, scénarios |
| `gsie_pedologie` | Sols, horizons, analyses |
| `gsie_hydro` | Bassins versants, masses d'eau, hydrométrie |
| `gsie_feu` | Historique d'incendies, danger, combustibles |
| `gsie_foret` | Peuplements, itinéraires, règles sylvicoles, dynamique |
| `gsie_gouvernance` | Décisions, recommandations, validations, apprentissage |

**Le rattachement de chaque table est à établir, pas à deviner.** Les modules de
`models/` donnent une première partition (`ecology.py`, `forestry.py`,
`dynamics.py`, `identification.py`…), mais elle ne coïncide pas exactement avec
les domaines. Une table dont le rattachement est ambigu **reste dans `public`**
et est signalée : mieux vaut une table non déplacée qu'une table mal rangée.

## 4. Méthode imposée — une migration par schéma

**Un schéma, une migration, un commit, une suite complète verte.** Sept lots
séparés, jamais groupés.

C'est plus lent et c'est le but : si le lot 5 casse quelque chose, on sait que
les lots 1 à 4 étaient sains. Une migration unique déplaçant 100 tables ne
laisserait aucun point de reprise.

Pour chaque lot :

1. Migration `ALTER TABLE public.<table> SET SCHEMA <schema>`.
2. `__table_args__ = {"schema": "<schema>"}` sur les modèles concernés.
3. Bump de `_HEAD` dans **les deux** verrous : `test_migration_baseline.py` et
   `test_migration_contract.py`.
4. Ajout du schéma à la liste en dur de `_public_tables` (§2).
5. Rôle du moteur : `USAGE` sur son schéma **et sur `public`**, rien d'autre.
6. Tests d'intégration sur base **réellement migrée** — pas `create_all`, qui
   produit les tables mais ni les rôles ni les droits.
7. Une mutation par garde, attribuée au **bon test** (§6).
8. Suite complète verte **avant** de passer au lot suivant.

## 5. Le rôle applicatif, à étendre

`20260728_0012` a créé `gsie_application` : lecture-écriture sur `public`,
**aucun accès** aux schémas RGPD, et **pas de `DELETE`** — `CON-010` interdit la
suppression physique, et le retirer des droits rend l'interdit structurel plutôt
que conventionnel.

Chaque nouveau schéma de domaine doit lui être accordé dans les mêmes termes :
`SELECT, INSERT, UPDATE`, jamais `DELETE`, plus `ALTER DEFAULT PRIVILEGES` pour
que les tables ajoutées ensuite héritent des droits.

**Un test doit vérifier l'absence de `DELETE` sur chaque nouveau schéma.**
L'oublier annulerait silencieusement une garantie constitutionnelle.

## 6. Attribution des mutations — l'erreur à ne pas refaire

Deux mutations RGPD ont **survécu** au premier lot. Elles portaient sur les
**modèles**, tandis que les tests d'isolement éprouvent la **base construite par
la migration** : un changement de modèle leur est invisible.

Ce qui détecte une divergence modèle ↔ base, c'est le **contrôle de dérive**.

| La mutation porte sur… | Le test qui la détecte |
|---|---|
| Un modèle (`__table_args__`, une colonne) | `test_migration_baseline.py` — contrôle de dérive |
| Une migration (un `GRANT`, un `SET SCHEMA`) | Les tests d'intégration du lot |

Huit tests verts avaient laissé croire que la protection était vérifiée. Elle
l'était — mais pas par ce qu'on croyait. **Vérifie chaque mutation en la jouant**,
et ne conclus jamais d'un test vert qu'il protège ce que tu penses.

## 7. Ce que tu dois signaler plutôt que de trancher

- Une table dont le domaine est ambigu.
- Une table référencée par deux domaines.
- Un moteur ayant besoin de lire le schéma d'un autre — cela indiquerait que la
  partition est mauvaise, et c'est une information précieuse.
- Toute tentation de toucher au noyau.

## 8. Critères d'acceptation

1. Sept migrations distinctes, une par schéma, chacune rejouable
   (`upgrade`/`downgrade`/`upgrade`).
2. Le contrôle de dérive strict passe **sans tolérance** après chaque lot.
3. La suite complète est verte après chaque lot — pas seulement à la fin.
4. Le harnais de mutation passe en mode `--complet` après chaque lot.
5. `gsie_application` a `SELECT, INSERT, UPDATE` et **jamais `DELETE`** sur
   chaque nouveau schéma, vérifié par test.
6. Aucun rôle de moteur n'atteint `gsie_rgpd` ni `gsie_rgpd_identites`.
7. `resource` est toujours dans `public`.
8. Aucune table applicative non rattachée n'a été déplacée « pour faire
   nombre » : les ambiguïtés sont signalées, pas résolues au jugé.

## Rapport obligatoire

Le rapport de mission est la section `## 9. Compte rendu attendu` ci-dessous,
complétée par les codes de sortie des commandes de validation. Il est déposé
dans la session Devin et archivé dans `22_PROJECT_MEMORY/sessions/`.

## 9. Compte rendu attendu

1. **Combien de tables déplacées, par schéma.**
2. **Combien laissées dans `public`, et pourquoi** — c'est l'information la plus
   utile du rapport.
3. Les effets de second ordre rencontrés, au-delà des quatre annoncés.
4. Les mutations ajoutées, et **lesquelles ont survécu au premier essai** — une
   mutation qui survit désigne un test qui ne protège pas ce qu'il prétend, et
   c'est ce qu'on veut savoir.
5. Ce que tu n'as pas fait, et pourquoi.

Pas de synthèse valorisante. Un lot livré proprement vaut mieux que sept livrés
approximativement — si tu n'en fais que trois, dis-le et laisse la base saine.
