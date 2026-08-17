# Audit des livrables de Phase 2 — 201 à 212

| Champ | Valeur |
|---|---|
| **Identifiant** | AUDIT-PHASE2-2026-08-14 |
| **Statut** | Draft |
| **Date** | 2026-08-14 |
| **Périmètre** | Livrables 201 à 212 déclarés dans `ROADMAP.md` |
| **Nature** | Audit documentaire, architectural et de conformité |
| **Effet normatif** | Aucun ; aucune promotion de statut |

## 1. Conclusion exécutive

La Phase 2 ne peut pas être considérée comme validée ni figée. Les douze
livrables restent `Draft` et aucun n'atteint aujourd'hui toutes les portes
requises pour un passage immédiat en `Review`.

`DEC-000011` ne clôt pas et ne valide pas la Phase 2 : il décrit les douze
livrables comme « Draft complets, prêts pour Review ». Une transition vers une
phase ultérieure n'est pas une validation rétroactive. La mention « Phase 2 —
clôturée » de la roadmap est donc plus forte que l'autorité disponible.

| Résultat | Nombre |
|---|---:|
| Prêt pour Review sans correction | 0 |
| Correction bornée avant Review | 3 |
| Rebaselining ou supersession nécessaire | 4 |
| Bloqué par décision, prérequis ou périmètre différé | 5 |

Le dépôt ne doit pas être déclaré figé : au moment de l'audit, le worktree
contient 104 entrées suivies modifiées et 77 entrées non suivies, dont 29 sous
`GSIE/ENGINES/`. Ces nombres décrivent un état de travail et ne préjugent pas de
la propriété des changements.

## 2. Portes utilisées

Un livrable est prêt pour `Review` seulement si toutes les portes suivantes
sont satisfaites :

1. **Gouvernance** : décisions, RFC et directives citées sont adoptées et
   applicables au périmètre revendiqué.
2. **Complétude** : aucune section obligatoire, décision annoncée, ADR ou
   vérification déclarée ne reste à produire.
3. **Traçabilité** : les affirmations scientifiques et technologiques ont des
   références résolubles, datées et attribuées.
4. **Cohérence interne** : en-tête, corps, historique et statut ne se
   contredisent pas.
5. **Conformité effective** : le document distingue la cible de l'existant et
   est réconcilié avec les contrats exécutables, modèles, migrations et tests.
6. **Reproductibilité** : la preuve porte sur un snapshot Git identifiable et
   des contrôles rejouables.

## 3. Matrice des douze livrables

| # | Livrable | Verdict | Preuves principales | Action avant Review |
|---|---|---|---|---|
| 201 | Architecture globale GSIE | Bloqué | Le document prend RFC-0003 comme référence structurante alors que RFC-0003 reste `Proposé` ; cible et état effectif ne sont pas séparés partout. | Faire décider RFC-0003 ou isoler ses éléments non adoptés ; produire une vue « cible » et une vue « as-built ». |
| 202 | Stack technologique | Correction bornée | Le document fixe FastAPI `0.115.x`, tandis que le contrat exécutable épingle `0.134.0`. Plusieurs ADR internes sont dits `Accepté` dans un document global `Draft`, sans table de décisions externes exhaustive. | Générer la matrice des versions depuis les lockfiles, relier chaque ADR accepté à son autorité et isoler les options proposées. |
| 203 | Protocole inter-moteurs | Correction bornée | Le protocole décrit versioning, retries et offline-first, mais dépend de RFC-0003 proposée et ne possède pas de matrice de conformité avec REST, WebSocket, files et erreurs réellement implémentés. | Ajouter une annexe as-built et des tests de contrat rejouables ; isoler les extensions GSIE-Net non adoptées. |
| 204 | Ordre de développement | Rebaselining | Le document affirme qu'aucun moteur n'est implémenté et planifie des vagues futures, alors que les quatorze packages API existent. | Archiver la séquence historique ou la convertir en bilan factuel ; créer séparément l'ordre résiduel de stabilisation. |
| 205 | Modèle de données scientifique | Rebaselining | Le corps conserve `evidence_level` directement sur de nombreuses entités alors que l'en-tête reconnaît son remplacement par `EvidenceAssessment` via RFC-0011/DEC-000022. | Produire une version canonique conforme au métamodèle et conserver l'ancien modèle comme historique clairement supersédé. |
| 206 | Contrats des 14 moteurs | Rebaselining critique | Le document se proclame « source de vérité unique » de l'implémentation, mais annonce encore `contract_test` « à implémenter ». L'orchestration effective appelle Reasoning → Diagnostic → Recommendation → Validation sans Evidence → Knowledge → Correlation. | Versionner les contrats par rapport aux schémas Pydantic/OpenAPI, générer une matrice de conformité et supprimer toute prétention de vérité unique non prouvée. |
| 207 | Documentation des 14 moteurs | Rebaselining critique | Les quatorze documents d'architecture restent `Draft`; la majorité affirme encore « documentation uniquement » alors que les API Phase 4 existent. Les fichiers moteurs sont en cours de modification dans le worktree. | Auditer moteur par moteur : responsabilité, schémas, routes, dépendances, garanties, erreurs, tests et limites ; séparer architecture historique et contrat effectif. |
| 208 | Architecture Ignis | Bloqué | Dépend de DIR-0005 et DIR-0006, toutes deux `Review` dans `PROPOSED`, donc non applicables ; un ADR dédié est encore annoncé à produire. | Faire décider les deux directives ou rendre les éléments concernés explicitement optionnels ; formaliser l'ADR annoncé. |
| 209 | Pipeline Ignis | Bloqué | Repose sur les mêmes directives proposées ; les liens de référence pointent encore vers leur ancien emplacement ACTIVE et la chaîne intégrée complète n'est pas prouvée. | Réparer les références, borner le contrat applicable et fournir une preuve d'intégration bout en bout. |
| 210 | Architecture drone Ignis | Bloqué | Repose sur les directives proposées et contient encore une option de haute priorité au statut « à étudier ». | Trancher ou exclure l'option du périmètre validable ; relier chaque autonomie aux garde-fous et preuves de simulation. |
| 211 | Centre de Commandement Unreal | Correction bornée | Le document contient des marqueurs de citation bruts `<cite index="…">`, donc non résolubles, et mélange des éléments « décidés/validés » avec des technologies explicitement expérimentales dans un document `Draft`. | Remplacer chaque marqueur par une source primaire versionnée, vérifier les affirmations volatiles et séparer décisions, veille et cible expérimentale. |
| 212 | GeoSylva-Unreal | Bloqué | Le document se déclare « piste en attente volontaire », interdit de construire avant le MVP Ignis et reporte un choix d'architecture à une future RFC. | Maintenir `Draft` hors clôture ; définir le critère MVP et ouvrir la RFC seulement lorsque la priorité devient active. |

## 4. Constats transversaux

### 4.1 Autorité de clôture absente

- [DEC-000004](../../03_DECISIONS/DEC-000004.md) ouvre la Phase 2.
- [DEC-000011](../../03_DECISIONS/DEC-000011.md) ouvre la Phase 3 et qualifie
  les livrables 201-212 de `Draft` prêts pour Review.
- Aucune décision examinée ne prononce leur validation individuelle ou la
  clôture terminale de la Phase 2.

La formulation correcte, tant qu'une décision n'est pas prise, est « sortie de
phase avec revue pendante » ou « validation suspendue », pas « clôturée ».

### 4.2 Contrats déclarés contre contrats exécutables

Le livrable 206 définit une chaîne complète et des schémas formels, mais les
preuves exécutables ne sont pas liées au document par une version ou un hash.
Le service d'orchestration courant importe et appelle seulement Reasoning,
Diagnostic, Recommendation et Validation. Cette différence peut être un
périmètre volontaire, mais elle doit être explicitée comme telle.

### 4.3 Gouvernance Ignis non terminale

DIR-0005 et DIR-0006 sont en `Review`, donc proposées et non applicables. Les
livrables 208-210 peuvent les analyser comme cible candidate, mais ne peuvent
pas les présenter comme fondations validées avant décision du Fondateur.

### 4.4 Documentation technologique volatile

Le livrable 211 contient des informations datées sur Unreal, Cesium et des
plugins expérimentaux. Une validation exige des sources primaires résolubles,
une date de consultation, une version et la séparation entre capacité stable et
expérimentation. Les marqueurs `<cite index="…">` ne satisfont pas cette porte.

## 5. Plan de remise à niveau recommandé

### Lot A — Corriger l'état de gouvernance

1. Remplacer « Phase 2 clôturée » par « sortie de phase, validation pendante ».
2. Conserver les douze statuts `Draft`.
3. Interdire toute validation en bloc ou rétroactive.

### Lot B — Rebaseliner le socle transversal

1. 201 : cible contre as-built.
2. 202 : versions générées depuis les lockfiles et décisions ADR.
3. 203 : protocole versionné et tests de conformité.
4. 205 : modèle conforme au métamodèle v6.1/v6.2.
5. 206 : contrats générables et matrice code/documentation.

### Lot C — Revoir les 14 moteurs

Traiter un moteur à la fois, avec une preuve commune : routes, schémas,
dépendances, erreurs, invariants, tests, limites et statut. Le livrable 207 ne
passe en Review qu'après 14 dossiers conformes sur 14.

### Lot D — Décider ou différer explicitement Ignis et les Hubs

1. Décision du Fondateur sur DIR-0005 et DIR-0006.
2. Revue 208-210 après décision, sans automatisme opérationnel.
3. Nettoyage des sources du 211.
4. Maintien du 212 en Draft différé jusqu'au critère MVP et à sa RFC.

## 6. Décision recommandée au Fondateur

Adopter le **Lot A** immédiatement : reconnaître que la Phase 2 a été quittée
pour permettre les phases suivantes, mais qu'elle n'est pas clôturée au sens
documentaire. Cette correction ne ferme pas la Phase 4 et ne rétrograde aucun
travail ; elle retire seulement une affirmation non démontrée.

Les promotions futures doivent être individuelles, dans l'ordre de la roadmap,
après preuve des six portes. Le livrable 212 doit rester hors clôture tant que
son propre prérequis MVP n'est pas atteint.

> **Décision du 2026-08-14 : recommandation adoptée par le Fondateur et tracée
> dans [DEC-000070](../../03_DECISIONS/DEC-000070.md).**

## 7. Contrôles reproduits

- `python tools/check_governance_consistency.py` : 12 incohérences, une par
  livrable Draft sous Phase 2 déclarée clôturée.
- `python tools/check_source_of_truth.py` : registre conforme.
- `python GSIE/TOOLS/verifier_integrite_references.py` : aucune cible
  d'identifiant manquante lors du dernier contrôle précédant ce rapport.
- Comptage des fences Markdown : pair pour les onze documents unitaires et les
  quatorze documents moteurs examinés.
- Inspection du service d'orchestration, de `pyproject.toml`, de `uv.lock` et
  des métadonnées de chaque livrable.

## 8. Limites

L'audit n'accorde aucun statut terminal et ne remplace pas une revue experte
scientifique, sécurité, Unreal ou aéronautique. Le worktree étant en cours de
modification, toute preuve de validation devra être rejouée sur un snapshot Git
stabilisé.
