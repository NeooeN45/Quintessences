# GSIE-PROMPT-0024 — Raccordement des clients sur `ResilientHttpClient`

| Champ | Valeur |
|---|---|
| Statut | INTÉGRÉE |
| Agent cible | GLM 5.2 |
| Environnement | Devin |
| Dépôt | Quintessences |
| Branche | `fix/enterprise-reliability-2026-07-21` |
| Suite de | `GSIE-PROMPT-0023` |
| Fichiers possédés | les 10 clients d'API externes + `src/gsie_api/shared/http_client.py` + leurs tests |
| Orchestrateur | Architecte |
| Relecteur | Architecte puis Fondateur |

## Constat

`GSIE-PROMPT-0023` a livré du bon travail : gardes réelles sur six clients,
sept mutations ajoutées au harnais, toutes tuées par leur propre test.

Il a aussi livré `src/gsie_api/shared/http_client.py` — 181 lignes — dont la
docstring affirme :

> « Tout nouveau client d'API externe doit hériter de `ResilientHttpClient`.
> La capture des erreurs est alors automatique — **impossible d'oublier une
> garde**. »

**Aucun des dix clients n'en hérite.** Vérifié : aucun import en production,
seul `tests/unit/test_resilience_factory.py` l'importe, et y ajoute 48 tests
verts.

L'intention est juste — s'attaquer à la cause racine plutôt qu'aux dix
instances — et meilleure que la consigne initiale. Mais une abstraction que
rien n'utilise est **pire que pas d'abstraction** : la docstring donne à croire
que le problème est structurellement résolu, et 48 tests verts renforcent
l'illusion. C'est le motif exact que l'audit du 2026-07-28 a démonté :
plausible, documenté, sans effet.

## Documents obligatoires

- `GSIE/API/src/gsie_api/shared/http_client.py` — `ResilientHttpClient` et `ResilientCsvClient`.
- `GSIE/API/src/gsie_api/engines/*/` — les 10 clients d'API externes.
- `GSIE/API/tests/unit/test_resilience_factory.py` — factory de tests paramétrés.
- `GSIE/API/tests/mutation/harnais.py` — harnais de mutation.
- `GSIE-PROMPT-0023` — mission précédente (résilience des clients).

## Mission

Raccorder les dix clients sur `ResilientHttpClient` (ou `ResilientCsvClient`),
de sorte que la promesse de la docstring devienne vraie.

```
engines/botanical/gbif_client.py          engines/climate/synop_client.py
engines/botanical/taxref_client.py        engines/climate/vigilance_client.py
engines/climate/arome_client.py           engines/climate/paquet_observation_client.py
engines/climate/dpclim_client.py          engines/gis/ign_client.py
engines/climate/meteofrance_client.py     engines/pedology/soilgrids_client.py
```

L'API de la classe de base est déjà en place : `exception_class` et `base_url`
abstraits, `auth_headers` surchargeable, helpers `_get_json`, `_get_text`,
`_get_bytes`, et `_get_csv` sur `ResilientCsvClient`.

Un client qui ne peut pas s'y raccorder — le format GRIB d'`arome_client` via
`eccodes` est le candidat le plus probable — doit être **déclaré comme tel avec
son motif**, pas raccordé de force ni laissé en silence.

## Le critère qui commande tout

**C'est un refactoring, donc les tests existants doivent passer sans être
modifiés.**

Si un test doit changer, ce n'est pas un refactoring : c'est un changement de
comportement observable, donc une régression. Dans ce cas, s'arrêter et le
signaler plutôt que d'ajuster le test.

Cette règle n'est pas négociable. C'est elle qui distingue « j'ai restructuré »
de « j'ai cassé puis rattrapé le test ».

Corollaire vérifiable : **le harnais doit rester à 15/15 après le
raccordement**. Les sept mutations de `0023` suppriment des gardes qui vont
changer de place ; si elles restent tuées, c'est que les gardes ont survécu au
déménagement. Si une mutation ne s'applique plus — le motif de texte a disparu
— la réécrire pour qu'elle vise la garde à son nouvel emplacement, et montrer
qu'elle est toujours tuée.

## Test d'invariant à ajouter

Sur le modèle de `tests/unit/test_limiter_contrat.py`, ajouter un test qui
énumère les clients et vérifie que chacun hérite bien de la classe de base.
Sans lui, le onzième client contournera la garantie sans que personne ne le
voie — exactement ce qui vient de se produire.

Les clients déclarés non raccordables figurent dans une liste d'exception
explicite du test, avec leur motif en commentaire. Une exception nommée est
acceptable ; une exception silencieuse ne l'est pas.

## Interdictions

- **aucun changement de comportement observable** : mêmes types d'exception,
  mêmes messages, mêmes codes HTTP en sortie de router ;
- aucune modification d'un test existant (voir le critère ci-dessus) ;
- aucune modification hors des fichiers possédés ;
- aucun `git push`, aucune fusion.

## Rapport obligatoire

Le rapport de mission est la section `## Livrable` ci-dessous, complétée
par les codes de sortie des commandes de validation. Il est déposé dans
la session Devin et archivé dans `22_PROJECT_MEMORY/sessions/`.

## Livrable

1. Le tableau des dix clients : raccordé / non raccordable + motif.
2. La preuve que **les tests existants passent sans modification** —
   `git diff --stat` sur `tests/` ne doit montrer que des ajouts.
3. Le harnais à 15/15, avec le détail des mutations réécrites s'il y en a.
4. Le test d'invariant, et la preuve qu'il échoue si l'on débranche un client
   de la classe de base.
5. Les commandes de validation avec leurs codes de sortie :
   `ruff check src tests`, `ruff format --check src tests`,
   `mypy src --strict`, `pytest tests/unit`,
   `python tests/mutation/harnais.py`.

Note : `ruff format --check` était rouge à la livraison de `0023`
(`http_client.py`, `harnais.py`, `test_resilience_factory.py`). Corrigé par
l'Architecte. Le vérifier avant de rendre.

## Critère d'acceptation

- les dix clients sont raccordés, ou déclarés non raccordables avec un motif
  technique vérifiable ;
- `git diff` sur `tests/` ne contient **aucune suppression ni modification**
  de test existant ;
- le harnais est à 15/15 ;
- le test d'invariant échoue quand on débranche un client — vérifié, pas
  supposé ;
- aucune porte qualité rouge.

Si le raccordement s'avère impossible sans changer un comportement, **le dire
et s'arrêter**. Un rapport qui explique pourquoi la mission ne peut pas être
menée telle quelle vaut mieux qu'un refactoring qui casse en silence.
