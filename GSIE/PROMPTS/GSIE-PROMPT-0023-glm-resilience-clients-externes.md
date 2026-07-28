# GSIE-PROMPT-0023 — Résilience des clients d'API externes

| Champ | Valeur |
|---|---|
| Statut | À LANCER |
| Agent cible | GLM 5.2 |
| Environnement | Devin |
| Dépôt | Quintessences |
| Branche | `fix/enterprise-reliability-2026-07-21` |
| Commit de référence | `bf18d84` |
| Orchestrateur | Architecte |
| Relecteur | Architecte puis Fondateur |
| Standard applicable | `23_QUALITY_MANAGEMENT/PROCESSES/CODE_QUALITY_STANDARD.md` |

## Pourquoi cette mission

Un audit de fiabilité mené le 2026-07-28 a établi un fait qui commande tout ce
qui suit : **la couverture était à 99 % et dix-huit défauts réels sont passés au
travers**, dont plusieurs cassaient toute écriture authentifiée. La couverture
mesure les lignes exécutées, jamais les comportements vérifiés.

La mesure en couverture de **branches** désigne une zone précise : les clients
d'API externes sont à 32 %. C'est là que vivent les pannes amont — réseau
coupé, réponse tronquée, schéma fournisseur modifié, quota dépassé. Ces
chemins existent dans le code et ne sont exercés par aucun test.

Mesures du 2026-07-28, `pytest tests/unit --cov-branch` :

| Module | Branches |
|---|---|
| `engines/botanical/gbif_client.py` | 32 % |
| `engines/pedology/soilgrids_client.py` | 32 % |

Deux hypothèses déjà instruites, **à ne pas réinstruire** :

- les dix clients déclarent tous un timeout — « appel réseau sans borne » est
  écarté ;
- la clé Météo-France transite par un en-tête (`headers={"apikey": …}`), pas
  par l'URL — elle ne peut pas fuiter dans un message d'erreur contenant
  l'URL.

## Périmètre possédé

Les dix clients :

```
engines/botanical/gbif_client.py          engines/climate/synop_client.py
engines/botanical/taxref_client.py        engines/climate/vigilance_client.py
engines/climate/arome_client.py           engines/climate/paquet_observation_client.py
engines/climate/dpclim_client.py          engines/gis/ign_client.py
engines/climate/meteofrance_client.py     engines/pedology/soilgrids_client.py
```

Tests : **étendre les fichiers existants**, ne pas en créer de doublons.

```
tests/unit/test_botanical_taxref.py       tests/unit/test_climate_arome.py
tests/unit/test_climate.py                tests/unit/test_climate_arome_edge_cases.py
tests/unit/test_ign_client_extended.py    tests/unit/test_botanical_engine_edge_cases.py
```

Un fichier neuf n'est justifié que pour un client aujourd'hui sans test dédié
(`soilgrids_client`, `gbif_client`, `dpclim_client`, `synop_client`,
`vigilance_client`, `paquet_observation_client`, `meteofrance_client`).

## Mission

Établir puis garantir le comportement de chaque client en cas de défaillance
amont. Un service externe indisponible **n'est pas une panne de GSIE** : il
doit produire une erreur métier nommée, et **jamais une donnée inventée**
(`ADR-009`, `GSIE-CON-002`). Une réponse partielle doit être refusée ou
déclarée incomplète, jamais complétée par une valeur par défaut.

Cinq modes de panne, pour chacun des dix clients :

1. panne réseau — `httpx.ConnectError`, `httpx.ReadTimeout` ;
2. statut HTTP 4xx puis 5xx du fournisseur ;
3. corps malformé — JSON invalide, XML tronqué, GRIB corrompu ;
4. **réponse bien formée mais champ attendu absent** — le cas le plus
   dangereux : c'est celui qui produit silencieusement un `None`, un zéro, ou
   une valeur inventée qui restera citable ;
5. quota ou authentification refusée (401, 403, 429) là où le fournisseur
   l'expose.

## Conventions à préserver

Elles existent déjà dans le dépôt. Les respecter, ne pas en inventer d'autres :

- chaque client lève l'erreur de son moteur (`BotanicalEngineError`,
  `ClimateEngineError`, `GISEngineError`, `PedologyEngineError`) ;
- les routers de ces quatre moteurs traduisent en **502 Bad Gateway** — code
  sémantiquement juste pour une défaillance amont. Les moteurs de calcul
  (correlation, reasoning, diagnostic…) rendent 400 : ne pas mélanger les deux
  régimes ;
- le message d'erreur remonté au client doit être **contrôlé et rédigé**, pas
  un `str(exc)` d'exception amont : celui-ci expose l'URL interne, le nom du
  fournisseur et parfois le corps de sa réponse. Nommer la cause en français,
  sans divulguer la structure interne.

Si une correction exige de toucher un moteur ou un router — hors périmètre —
**la signaler dans le rapport sans la faire**.

## Obligations de preuve

Ces obligations existent parce qu'une suite de plus de mille tests a déjà
échoué à détecter dix-huit défauts réels. Elles ne sont pas négociables.

1. **Reproduire avant de corriger.** Tout défaut doit d'abord être reproduit
   par un test qui échoue, avec `respx` pour simuler la réponse amont. Un
   raisonnement sur le code ne vaut pas preuve.
2. **Un test qui ne peut pas échouer ne compte pas.** Sont proscrits
   `assert x is not None`, `assert status in (200, 400, 502)`, et toute
   assertion qu'un code cassé satisferait encore. Affirmer une valeur précise
   ou un type d'erreur précis.
3. **Vérifier que chaque test mord.** Pour chaque test ajouté, casser
   volontairement la garde qu'il protège et constater qu'il échoue, puis
   restaurer. Reporter les deux résultats. Un test jamais vu échouer n'a rien
   prouvé.
4. **Ajouter la mutation au harnais** `tests/mutation/harnais.py` pour chaque
   garde ajoutée, et montrer qu'elle **survit avant** le correctif et qu'elle
   est **tuée après**. Ajouter une mutation déjà tuée par construction ne
   démontre rien.
5. **Interdiction de neutraliser l'existant** : aucun `xfail`, `skip`,
   `skipif`, assertion commentée, ni exclusion de couverture. Si un test
   existant devient faux, le signaler — ne pas le désactiver.
6. **Aucun appel réseau réel.** Tout passe par `respx`. Pour les formats non
   HTTP (GRIB via `eccodes`), injecter un fichier corrompu depuis
   `tests/fixtures/`.

## Organisation attendue (sous-agents)

Le volume se prête au parallélisme, sur fichiers disjoints :

- **botanical** (2 clients) — **climate** (6) — **gis** (1) — **pedology** (1) ;
- **un sous-agent réfuteur distinct**, qui reprend chaque défaut annoncé par
  les autres et tente de le **démolir** : le reproduire réellement, chercher
  le garde plus haut dans la pile, la valeur par défaut, le chemin mort jamais
  atteint en pratique. Un constat non reproduit est rejeté.

Ce rôle de réfuteur est le plus important de la mission. C'est précisément ce
qui manquait au travail précédent : des constats plausibles que personne ne
reproduisait.

## Environnement

```
cd GSIE/API
./.venv/Scripts/python.exe -m pytest tests/unit -q --no-cov
./.venv/Scripts/python.exe -m ruff check src tests
./.venv/Scripts/python.exe -m ruff format --check src tests
./.venv/Scripts/python.exe -m mypy src --strict
./.venv/Scripts/python.exe tests/mutation/harnais.py
```

Tests d'intégration : préfixer `TESTCONTAINERS_RYUK_DISABLED=true` (Docker requis).

## Interdictions

- aucune modification hors du périmètre possédé — un autre agent travaille en
  parallèle sur ce dépôt ;
- aucune modification des schémas Pydantic ni des contrats de moteur : un
  invariant de type est une décision d'architecture ;
- aucune valeur scientifique inventée ou « par défaut » pour compenser une
  donnée amont absente ;
- aucun document `Locked` touché ;
- aucun `git push`, aucune fusion, aucun commit sur une autre branche.

## Livrable

1. Le tableau **dix clients × cinq modes de panne**, chaque case portant le
   comportement **constaté avant** et **après**. Une case non instruite doit
   être déclarée comme telle, pas laissée vide.
2. La liste des défauts, chacun avec la commande qui le reproduit et sa sortie.
3. Pour chaque test ajouté : la preuve qu'il échoue quand la garde est cassée.
4. Les mutations ajoutées, avec leur état **avant** (survivante) et **après**
   (tuée).
5. Les commandes de validation ci-dessus avec leurs **codes de sortie**.
6. Ce qui n'a pas été fait, et pourquoi.

## Critère d'acceptation

Le travail est accepté si, et seulement si :

- les cinquante cases du tableau sont instruites — traitées ou explicitement
  déclarées hors d'atteinte avec le motif ;
- chaque défaut annoncé est reproductible par la commande fournie, vérifiée
  par l'Architecte ;
- chaque test ajouté a été vu échouer au moins une fois ;
- le harnais de mutation reste à 100 %, mutations nouvelles comprises ;
- aucune porte qualité ne régresse.

**Aucun objectif chiffré de couverture n'est fixé, volontairement.** Viser un
pourcentage produit des tests qui traversent le code sans rien vérifier —
c'est exactement ce qui a permis aux dix-huit défauts de passer. Ce qui est
demandé est un comportement établi, pas une métrique atteinte.

Un rapport annonçant des corrections sans preuve exécutée sera rejeté, comme
l'a été `GSIE-PROMPT-0015`.
