# GSIE-PROMPT-0026 — Vérification de l'inventaire existant et de l'écosystème INPN

| Champ | Valeur |
|---|---|
| Statut | INTÉGRÉE |
| Agent cible | GLM 5.2 |
| Environnement | Devin |
| Dépôt | Quintessences |
| Branche | `feat/inventaire-sources-elargi` (continuer dessus) |
| Fichiers possédés | `GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md`, `GSIE/DATASETS/DATASET_CATALOG.md` |
| Fichiers interdits | tout `GSIE/API/src/**` et `GSIE/API/tests/**` — **aucun code** |
| Suite de | `GSIE-PROMPT-0025` |
| Orchestrateur | Architecte |

## Documents obligatoires

- `GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md` — inventaire à vérifier.
- `GSIE/DATASETS/DATASET_CATALOG.md` — catalogue des datasets.
- `GSIE/DATASETS/NOMENCLATURE_SOURCES.md` — nomenclature et format.
- `02_RFC/RFC-0029.md` — audit des sources et angles morts.
- `GSIE-PROMPT-0025` — mission précédente (élargissement de l'inventaire).
- `GSIE/ARCHITECTURE/ADR-009.md` — interdiction d'inventer.

## Mission

Vérifier l'inventaire existant : tester chaque URL, classer le verdict
(vivante, déplacée, morte, indéterminée), corriger les URL déplacées,
marquer les mortes comme obsolètes. Couvrir en priorité l'écosystème INPN
et les signalements non vérifiés du contre-audit.

## Constat

`GSIE-PROMPT-0025` a livré du bon travail : 68 URL testées, 26 sources
vérifiées, 17 signalements. Le contre-audit de l'Architecte en a revérifié neuf
indépendamment — **huit exacts, souvent à la date près**.

Il a aussi révélé ce que personne n'avait mesuré : **les ~179 sources
préexistantes n'ont jamais été testées.** Et parmi les quelques-unes que le
hasard a fait examiner, on a trouvé :

- **Prométhée** — fusionnée dans BDIFF en **janvier 2023**, soit deux ans et
  demi d'inventaire périmé ;
- **INPN** — hors service du 26/07/2025 au 22/07/2026 après une cyberattaque ;
- **`donneespubliques.meteofrance.fr`** — en fermeture ;
- **GIS Sol** — bases arrêtées le 18/02/2026, sans date de retour annoncée.

Quatre sources mortes ou changées sur un échantillon non choisi. Le taux réel
est inconnu, et c'est précisément le problème : **un inventaire dont on ignore
la fraîcheur ne vaut pas mieux qu'un inventaire vide**, parce qu'on ne sait pas
lesquelles de ses entrées sont encore vraies.

## 1. Règle absolue — inchangée

Tout le §1 de `GSIE-PROMPT-0025` s'applique intégralement : ne rien inventer,
tester réellement chaque URL, section `À VÉRIFIER` pour l'incertain, jamais de
champ complété par analogie.

**Une règle s'y ajoute, tirée du seul défaut trouvé au contre-audit.**

`GSIE-PROMPT-0025` affirmait « ERA5T devient payant (annonce CDS 30/07/2026) ».
C'est **faux** : le Climate Data Store est passé sous **CC-BY 4.0 le 2 juillet
2025**, soit une libéralisation. Crue, cette alerte aurait fait écarter ou
budgéter une ressource climatique majeure sans raison.

> **Une affirmation de licence ne s'accepte jamais sur parole et ne s'écrit
> jamais sans sa source primaire.** `NOMENCLATURE_SOURCES.md` le pose déjà pour
> les données : « l'oubli refuse, autoriser est un acte ». Cela vaut aussi pour
> ce que tu écris à propos d'une licence.

Toute mention de licence — changement, restriction, passage au payant — doit
citer **l'URL de l'annonce officielle**. Sans elle, elle va en `À VÉRIFIER`.

## 2. Priorité 1 — l'écosystème INPN (bloquant)

La cyberattaque du MNHN a rendu indisponibles **DEPOBIO, FSD Natura 2000, INPN,
ZNIEFF, GINCO/Géonature, OpenObs, NatureFrance, DeterminObs et TAXREF**, ainsi
que **toutes les API associées**.

Fait déterminant : **le MNHN a décidé de ne pas restaurer l'ancien système**,
une refonte étant engagée. Les URL et les points d'entrée d'API ont donc
probablement changé.

Or `GSIE-PROMPT-0025` liste **TAXREF v18 parmi ses 26 sources vérifiées**. Les
deux ne peuvent pas être vrais au même moment, ou alors TAXREF a été restauré
séparément — ce qui reste à établir.

À faire :

1. Tester chaque service de la liste ci-dessus, un par un.
2. Pour chacun : disponible ou non, URL actuelle, API actuelle, et **si l'URL a
   changé**, l'ancienne et la nouvelle.
3. Corriger dans l'inventaire **toutes** les entrées citant ces services — pas
   seulement celles signalées en 0025.
4. Trancher le cas TAXREF : disponible, ou à retirer des sources vérifiées.

## 3. Priorité 2 — vérifier les ~179 sources préexistantes

C'est le gros du travail, et il est mécanique.

Reprends l'inventaire **section par section** — §1 catalogue DS-001 à DS-029,
§2 sources Ignis, §3 sources scientifiques, §4 sources par moteur, §6 sources
de juillet 2026 — et teste chaque URL.

Pour chaque entrée, l'un de ces quatre verdicts :

| Verdict | Ce qu'il signifie | Ce que tu écris |
|---|---|---|
| **VIVANTE** | L'URL répond, le contenu correspond | Rien à changer, compter au bilan |
| **DÉPLACÉE** | Répond ailleurs, nouvelle URL trouvée | Corriger l'URL, mentionner l'ancienne |
| **MORTE** | Ne répond plus, aucun remplaçant trouvé | Marquer **OBSOLÈTE**, jamais supprimer |
| **INDÉTERMINÉE** | 403 anti-bot, service en panne temporaire | `À VÉRIFIER` avec le code HTTP obtenu |

**Ne supprime aucune entrée.** Une source morte marquée obsolète garde sa
valeur : elle dit qu'on l'a cherchée et qu'elle n'existe plus. Une entrée
supprimée sera recherchée à nouveau dans six mois par quelqu'un qui ignorera
qu'elle est morte.

Un 403 anti-bot n'est **pas** une source morte — GBIF en est l'exemple : site
web en 403, mais `api.gbif.org` parfaitement fonctionnel. Quand un site refuse
la lecture automatique, cherche son API avant de conclure.

## 4. Priorité 3 — les quatre signalements non vérifiés

Le contre-audit en a laissé quatre de côté, de moindre enjeu :

| # | Signalement à établir |
|---|---|
| 8 | `feuxdeforet.fr` — accès réellement par convention ? Qui contacter ? |
| 11 | Remonter le Temps — les couches WMS `wxs.ign.fr` répondent-elles, et quelle clé faut-il ? |
| 12 | BD Ortho — quelles zones d'outre-mer ne sont réellement pas couvertes ? |
| 13 | CARTOS VEGETATION DROM — quelles nomenclatures, et diffèrent-elles vraiment par DROM ? |

## 5. Organisation

Un sous-agent par section de l'inventaire, en parallèle. Chacun applique le §1
intégralement.

Travaille **par lots**, en commitant à mesure : un lot de vérifications
terminé, un commit. Ne garde pas une heure de travail non commitée — si la
session est interrompue, tout serait perdu.

## Interdictions

## 6. Ce que tu ne dois pas faire

- **Aucun code.** Ce prompt est documentaire.
- **Ne supprime aucune entrée** — obsolète, jamais effacée.
- **N'ajoute pas de sources nouvelles.** Ce lot vérifie l'existant. Si tu en
  découvres, note-les en fin de compte rendu sous `DÉCOUVERTES INCIDENTES`,
  sans les intégrer.
- **Ne modifie ni `NOMENCLATURE_SOURCES.md` ni `RFC-0029`** — tu en es le
  lecteur.

## Rapport obligatoire

Le rapport de mission est la section `## 7. Compte rendu attendu` ci-dessous,
complétée par les cinq chiffres de vérification. Il est déposé dans la
session Devin et archivé dans `22_PROJECT_MEMORY/sessions/`.

## 7. Compte rendu attendu

Cinq chiffres, et ce sont eux qu'on lira :

1. **Combien d'URL testées** au total.
2. **Combien vivantes, déplacées, mortes, indéterminées.**
3. **Le taux de péremption de l'inventaire** — mortes + déplacées sur le total.
   C'est le chiffre le plus important de ce lot : il dira si l'inventaire est
   fiable ou s'il faut une revérification périodique.
4. **Verdict sur l'écosystème INPN**, service par service.
5. **Ce que tu n'as pas pu tester**, et pourquoi.

Pas de synthèse valorisante. Si le taux de péremption est élevé, dis-le : c'est
une information utile, pas un échec. Un inventaire dont on connaît la fraîcheur
vaut infiniment mieux qu'un inventaire qu'on croit à jour.
