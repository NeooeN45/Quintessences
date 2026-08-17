# Audit d'intégrité - GSIE-ARCH-EVOLUTION-001 v1.2.0

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-AUDIT-ARCH-2026-08-12-001 |
| **Statut** | Draft |
| **Date** | 2026-08-12 |
| **Auditeur** | Codex |
| **Document audité** | `GSIE_EVOLUTION_AND_AI_INTEGRATION.md` |
| **Périmètre** | Cohérence Constitution/RFC/DEC, architecture canonique, code API et ressources locales |

## 1. Verdict

Le document v1.1 était riche et globalement aligné avec l'intention de GSIE,
mais il ne séparait pas assez clairement architecture cible et capacités
réellement implémentées. Six incohérences fonctionnelles importantes et
plusieurs ambiguïtés ont été corrigées dans la version 1.2.0.

**Verdict actuel : cohérent pour une relecture du Fondateur, statut Draft à
conserver.** Aucun blocage P0 n'a été découvert. Le document ne doit pas passer
en `Validated` avant arbitrage des éléments ouverts au §5.

## 2. Sources contrôlées

- Constitution et hiérarchie documentaire du dépôt ;
- `ARCHITECTURE_PRINCIPLES.md` ;
- `GSIE_MASTER_ARCHITECTURE.md` et liste canonique des 14 moteurs ;
- `ENGINE_INTERFACE_CONTRACTS.md` ;
- `ECOSYSTEM_METAMODEL.md` ;
- RFC-0012, RFC-0038 et RFC-0039 ;
- DEC-000060, 000061, 000062, 000064, 000065 et 000067 ;
- implémentations `QualityAssessment`, `DatasetHealth`, `FieldIntake`, identité
  et benchmark dans `GSIE/API/src/gsie_api/` ;
- audit local `GSIE-DATA-AUDIT-EDOCUMENTS-001`.

## 3. Corrections importantes appliquées

| Priorité | Incohérence v1.1 | Correction v1.2 |
|---|---|---|
| P1 | Les cinq dimensions QualityAssessment étaient décrites comme complétude, cohérence, exactitude, accessibilité et traçabilité. | Alignement sur l'énumération réelle : complétude, exactitudes positionnelle, temporelle et thématique, cohérence logique. |
| P1 | DatasetHealth utilisait les statuts fictifs `up/down` et des champs non persistés. | Alignement sur `healthy/degraded/unavailable/invalid/unknown` et sur les champs SQL réels. |
| P1 | FieldIntake était présenté comme complet avec des statuts non implémentés. | Distinction entre tranche actuelle (`quarantined/accepted/rejected`) et cible riche. |
| P1 | La qualification Gold/Silver/Bronze du benchmark était assimilée à QualityAssessment. | Séparation entre qualité d'un dataset et qualification juridique/scientifique d'une annotation Benchmark. |
| P1 | `Data Selection Engine` pouvait être lu comme un quinzième moteur. | Renommage en service de sélection/resolver, explicitement hors liste des 14 moteurs. |
| P1 | Candidate et Run du benchmark étaient artificiellement rattachés à DatasetVersion/DataAsset. | Candidate référencé par version moteur/commit ou futur Model Registry ; Run par protocole/configuration/artefacts. |
| P1 | Sécurité formulée comme entièrement acquise : RLS globale, chiffrement au repos et bcrypt/argon2 interchangeables. | RLS limitée aux tables prouvées, chiffrement au repos à vérifier, Argon2id canonique et bcrypt identifié comme legacy de développement. |
| P2 | Les mots Gold/Silver/RAW mélangeaient zone data, statut DatasetVersion et niveau Benchmark. | Préfixes `DATA_*` et `BENCHMARK_ASSET`, avec promotion dédiée. |
| P2 | L'indisponibilité d'un fournisseur pouvait être interprétée comme un échec readiness. | Séparation readiness interne et santé fournisseur DatasetHealth. |
| P2 | Le protocole Codex créait une procédure parallèle dans un document d'architecture. | Renvoi vers le processus canonique d'orchestration des agents. |
| P2 | Les ressources locales n'avaient pas de porte d'entrée explicite. | Ajout d'un cycle metadata-only, droits, sensibilité, quarantaine et revue scientifique. |

## 4. Contrôles d'intégrité scientifique issus des documents locaux

L'examen des deux fiches stationnelles a confirmé que l'architecture doit
imposer une séparation stricte entre :

```text
mesure brute
    -> calcul et méthode versionnés
    -> interprétation sourcée
    -> recommandation contournable
```

Le diagnostic des Farges contient au moins une contradiction dendrométrique
forte : `G = 20,5 m²/ha` et `N = 325 tiges/ha` impliquent un diamètre quadratique
d'environ 28,4 cm, alors que le document annonce 53 cm. Il est donc un excellent
cas Benchmark `contradictory_data`, mais pas une vérité Gold.

La fiche vierge offre une bonne structure de saisie, tout en contenant des
rappels pédagogiques trop généraux pour devenir des règles moteur : convention
du déficit hydrique, classes de pH, seuil H/D, objectif S % et méthode de volume.

## 5. Arbitrages encore ouverts

| Sujet | État | Décision nécessaire |
|---|---|---|
| Schéma FieldIntake stationnel complet | cible | RFC/contrat de schéma, méthodes, unités, rétractation et migration |
| Service de promotion `DATA_GOLD` | absent | politique combinant qualité, droits, opérateur et actifs |
| Registre de modèles IA | cible | RFC séparée avant toute intégration de modèle |
| Contrat exécutable Forge → GSIE | cible | manifeste versionné et tests d'idempotence inter-repos |
| Chiffrement au repos | preuve incomplète | matrice PostgreSQL/MinIO/volumes/sauvegardes avec test de configuration |
| Couverture RLS | partielle | inventaire table par table et tests croisés tenant/territoire |
| Scénarios stationnels Gold | bloqués | droits des annotations, sources par champ et double revue experte |
| Ressources `E:\Documents` | candidats | aucune ingestion avant qualification ressource par ressource |

## 6. Risques résiduels

- Le document reste très large : il doit conserver des liens vers les contrats
  spécialisés et ne pas devenir leur duplicata.
- Les preuves de déploiement local/CI ne permettent pas encore d'annoncer un SLO
  de production.
- Le score heuristique de l'inventaire local sert au tri, jamais à la promotion.
- Vingt-trois PDF candidats nécessitent probablement un OCR ; une absence de
  texte extrait ne signifie pas une absence de contenu.
- La possession locale d'un guide ou d'une couche ne prouve aucun droit de
  copie, d'annotation, de redistribution ou d'entraînement.

## 7. Porte de validation proposée

Avant le passage de `Draft` à `Review` :

- [x] références principales présentes ;
- [x] liste des 14 moteurs non étendue implicitement ;
- [x] état implémenté séparé de la cible ;
- [x] QualityAssessment et DatasetHealth alignés sur les enums/modèles ;
- [x] FieldIntake actuel décrit sans surpromesse ;
- [x] Benchmark et Data Registry séparés ;
- [x] ressources locales soumises aux droits et à la quarantaine ;
- [ ] arbitrages du §5 relus par le Fondateur ;
- [x] liens locaux et table des matières validés automatiquement ;
- [ ] décision explicite du Fondateur pour passer le document en `Review`.

## 8. Historique

| Version | Date | Modification |
|---|---|---|
| 1.0.0 | 2026-08-12 | Audit initial et corrections intégrées dans GSIE-ARCH-EVOLUTION-001 v1.2.0. |
