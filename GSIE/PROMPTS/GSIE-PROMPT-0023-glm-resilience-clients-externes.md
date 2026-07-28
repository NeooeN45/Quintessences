# GSIE-PROMPT-0023 — Résilience des clients d'API externes

| Champ | Valeur |
|---|---|
| Statut | À LANCER |
| Agent cible | GLM 5.2 |
| Environnement | Devin |
| Dépôt | Quintessences |
| Branche | `fix/enterprise-reliability-2026-07-21` |
| Fichiers possédés | `GSIE/API/src/gsie_api/engines/*/[a-z]*client*.py` + leurs tests dédiés |
| Orchestrateur | Architecte |
| Relecteur | Architecte puis Fondateur |
| Standard applicable | `23_QUALITY_MANAGEMENT/PROCESSES/CODE_QUALITY_STANDARD.md` |

## Pourquoi cette mission

Un audit de fiabilité mené le 2026-07-28 a établi un fait qui commande tout ce
qui suit : **la couverture était à 99 % et dix-huit défauts réels sont passés au
travers**, dont plusieurs cassaient toute écriture authentifiée. La couverture
mesure les lignes exécutées, jamais les comportements vérifiés.

La mesure en couverture de **branches** (et non de lignes) désigne une zone
précise : les clients d'API externes sont à 32 %. Or c'est exactement là que
vivent les modes de panne — réseau coupé, réponse tronquée, schéma amont
modifié, quota dépassé. Ces chemins existent dans le code mais ne sont
exercés par aucun test.

Mesures relevées le 2026-07-28 (`pytest tests/unit --cov-branch`) :

| Module | Couverture de branches |
|---|---|
| `engines/botanical/gbif_client.py` | 32 % |
| `engines/pedology/soilgrids_client.py` | 32 % |
| `engines/gis/engine.py` | 46 % |
| `engines/evidence/wrapper.py` | 62 % |

Point déjà vérifié, à ne pas réinstruire : les dix clients déclarent tous un
timeout. L'hypothèse « appel réseau sans borne » est écartée.

## Mission

Pour chacun des dix clients de `src/gsie_api/engines/*/[a-z]*client*.py`,
établir puis garantir le comportement en cas de défaillance amont.

Un service externe indisponible **n'est pas une panne de GSIE**. Il doit
produire une erreur métier nommée, jamais un 500 opaque, et **jamais une donnée
inventée** — c'est le sens d'`ADR-009` et de `GSIE-CON-002`. Une réponse
partielle doit être refusée ou déclarée incomplète, pas complétée par défaut.

Modes de panne à couvrir, pour chaque client :

1. panne réseau (`httpx.ConnectError`, `httpx.ReadTimeout`) ;
2. réponse HTTP 4xx et 5xx du fournisseur ;
3. corps de réponse malformé (JSON invalide, XML tronqué, GRIB corrompu) ;
4. réponse bien formée mais **champ attendu absent** — le cas le plus
   dangereux, car c'est celui qui produit silencieusement une valeur nulle ou
   une donnée inventée ;
5. quota ou authentification refusée (401, 403, 429) quand le fournisseur
   l'expose.

## Obligations de preuve

Ces obligations ne sont pas des formalités : elles existent précisément parce
qu'une suite volumineuse a déjà échoué à détecter des défauts réels.

1. **Reproduire avant de corriger.** Tout défaut trouvé doit d'abord être
   reproduit par un test qui échoue, avec `respx` (déjà en dépendance) pour
   simuler la réponse amont. Un raisonnement sur le code ne vaut pas preuve.
2. **Un test qui ne peut pas échouer ne compte pas.** Proscrire
   `assert x is not None`, `assert status in (200, 400, 422, 500)` et toute
   assertion qu'un code cassé satisferait encore. Chaque test doit affirmer
   une valeur ou un type d'erreur précis.
3. **Ajouter la mutation correspondante** dans
   `GSIE/API/tests/mutation/harnais.py` pour chaque garde ajoutée, et vérifier
   qu'elle est *tuée* : `python tests/mutation/harnais.py` doit rester à 100 %.
   Une garde sans mutation est une garde que personne ne surveille.
4. **Interdiction de neutraliser l'existant** : aucun `xfail`, `skip`,
   `skipif`, assertion commentée, ni exclusion de couverture. Si un test
   existant devient faux, le signaler — ne pas le désactiver.
5. **Aucun appel réseau réel** en test. Tout passe par `respx`.

## Organisation attendue (sous-agents)

Le volume se prête au parallélisme. Organisation recommandée :

- **un sous-agent par famille de clients** — botanical (2), climate (6),
  gis (1), pedology (1) — travaillant sur des fichiers disjoints ;
- **un sous-agent réfuteur** distinct, qui reprend chaque défaut annoncé par
  les autres et tente de le *démolir* : reproduire réellement, chercher le
  garde plus haut dans la pile, la valeur par défaut, le chemin mort jamais
  atteint. Un constat non reproduit est rejeté. Ce rôle est le plus important
  de la mission : il est ce qui manquait au travail précédent.

## Interdictions

- aucune modification hors des fichiers possédés — un autre agent travaille en
  parallèle sur le dépôt ;
- aucune modification des schémas Pydantic ni des contrats de moteur : un
  invariant de type est une décision d'architecture ;
- aucune valeur scientifique inventée ou « par défaut » pour compenser une
  donnée amont absente ;
- aucun document `Locked` touché ;
- aucun `git push`, aucune fusion.

## Livrable

Un rapport comprenant :

1. le tableau des dix clients × cinq modes de panne, avec pour chaque case le
   comportement **constaté avant** et **après** ;
2. la liste des défauts trouvés, chacun avec la commande qui le reproduit et
   sa sortie ;
3. les mutations ajoutées au harnais et le score obtenu ;
4. les commandes de validation avec leurs codes de sortie :
   `ruff check src tests`, `ruff format --check src tests`,
   `mypy src --strict`, `pytest tests/unit`,
   `python tests/mutation/harnais.py` ;
5. la couverture de branches avant/après sur les modules visés ;
6. ce qui n'a pas été fait et pourquoi.

## Critère d'acceptation

Le travail est accepté si, et seulement si :

- chaque défaut annoncé est reproductible par la commande fournie ;
- le harnais de mutation reste à 100 % ;
- la couverture de branches des dix clients dépasse 85 % ;
- aucune porte qualité ne régresse.

Un rapport qui annonce des corrections sans preuve exécutée sera rejeté, comme
l'a été `GSIE-PROMPT-0015`.
