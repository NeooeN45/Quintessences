# SERVER MESHING — Critères d'acceptation

| Champ | Valeur |
|---|---|
| **Document** | Critères d'acceptation — GSIE Server Meshing |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **RFC liée** | RFC-0035 |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 |
| **Documents connexes** | `SERVER_MESHING_PROTOTYPE_V0.md`, `SERVER_MESHING_ROADMAP.md`, `SERVER_MESHING_BACKLOG.md`, `SERVER_MESHING_TEST_STRATEGY.md` |

---

## 1. Mission du document

Définir les critères d'acceptation explicites, mesurables et traçables
de chaque phase du chantier Server Meshing. Un critère est **binaire** :
satisfait ou non satisfait, jamais « partiellement ». Un critère non
satisfait bloque le passage à la phase suivante, sauf acceptation
explicite et tracée (DEC-xxxxxx) par le Fondateur.

---

## 2. Critères transverses (toutes phases)

| ID | Critère | Vérification |
|---|---|---|
| ACC-MESH-T01 | Aucune modification d'un contrat d'interface de moteur GSIE existant n'a été nécessaire | Diff des `GSIE/ENGINES/*/README.md` |
| ACC-MESH-T02 | Aucune dépendance hard à une version spécifique d'Unreal Engine dans les contrats de mesh | Revue de code des interfaces abstraites |
| ACC-MESH-T03 | PostgreSQL/PostGIS reste l'unique source de vérité ; aucun état métier n'est considéré valide sans écriture persistée | Test d'arrêt brutal + redémarrage |
| ACC-MESH-T04 | Toute décision de mesh (transfert, redécoupage, allocation) est journalisée dans le journal d'audit immuable | Requête sur le journal d'audit |
| ACC-MESH-T05 | Les 8 principes P-MESH-01 à P-MESH-08 sont respectés (audit de conformité) | Grille d'audit documentaire |
| ACC-MESH-T06 | Aucune régression sur les priorités Phase 4 (14 moteurs, API, Hub, GeoSylva, Ignis) | Comparaison ROADMAP.md avant/après |

---

## 3. Phase 5 — Prototype v0 Landiras

### 3.1 Critères fonctionnels

| ID | Critère | Vérification |
|---|---|---|
| ACC-MESH-P5-01 | Le Hub affiche la zone Landiras via le mesh sans régression visible par rapport au livrable 211 actuel | Test de navigation opérateur + capture comparative |
| ACC-MESH-P5-02 | Un arrêt/redémarrage brutal du ZoneServer ne provoque aucune perte de donnée persistée | Comparaison d'état PostgreSQL avant/après |
| ACC-MESH-P5-03 | Après redémarrage, le ZoneServer reconstitue son état depuis PostgreSQL et reprend l'autorité | Test de reconnexion automatique |
| ACC-MESH-P5-04 | Le Hub se reconnecte automatiquement après une interruption du ZoneServer et retrouve un état cohérent | Test de reconnexion client |
| ACC-MESH-P5-05 | Le comportement offline-first des nœuds terminaux reste identique à celui garanti par RFC-0003 | Test offline/online d'un nœud terminal simulé |
| ACC-MESH-P5-06 | Le journal d'audit minimal enregistre démarrage, arrêt et reconnexion du ZoneServer avec identifiant traçable | Requête sur le journal d'audit |

### 3.2 Critères de non-régression

| ID | Critère | Vérification |
|---|---|---|
| ACC-MESH-P5-07 | Aucune modification d'un contrat d'interface d'un moteur GSIE existant | Diff des contrats |
| ACC-MESH-P5-08 | Performance du Hub équivalente (latence de rendu, framerate) au livrable 211 actuel | Benchmark comparatif |
| ACC-MESH-P5-09 | Tests existants de l'API GSIE toujours verts | `pytest tests/ -q` |

### 3.3 Critère de sortie Phase 5

Les 6 critères fonctionnels (P5-01 à P5-06) et les 3 critères de
non-régression (P5-07 à P5-09) sont **tous** satisfaits, ou chaque
écart est documenté et accepté par le Fondateur via une décision tracée.

---

## 4. Phase 6 — Multi-régions, handoff

### 4.1 Critères fonctionnels

| ID | Critère | Vérification |
|---|---|---|
| ACC-MESH-P6-01 | Le mesh gère au moins deux régions actives simultanément | Test multi-régions |
| ACC-MESH-P6-02 | Un transfert d'autorité entre deux régions s'exécute sans perte de données | Test de handoff instrumenté |
| ACC-MESH-P6-03 | Aucune coupure visible côté opérateur pendant un handoff | Test de navigation traversant une frontière |
| ACC-MESH-P6-04 | Le graphe d'autorité bidimensionnel (zone + type) résout correctement les conflits documentés | Tests unitaires de résolution |
| ACC-MESH-P6-05 | La traçabilité des transferts inter-régions est complète dans le journal d'audit | Requête sur le journal d'audit |
| ACC-MESH-P6-06 | Le service discovery multi-nœuds fonctionne (enregistrement, heartbeat, détection de panne) | Test de panne simulée |

### 4.2 Critères de résilience

| ID | Critère | Vérification |
|---|---|---|
| ACC-MESH-P6-07 | En cas de partition réseau, le mode dégradé offline-first s'active correctement | Test de coupure réseau simulée |
| ACC-MESH-P6-08 | À la reconnexion après partition, la réconciliation bitemporelle résout les divergences sans perte d'historique | Test de réconciliation |
| ACC-MESH-P6-09 | La perte d'un serveur de zone déclenche une reprise d'autorité par un autre serveur, sans perte d'état | Test de panne serveur |

### 4.3 Critère de sortie Phase 6

Les 9 critères (P6-01 à P6-09) sont tous satisfaits, ou chaque écart
est documenté et accepté par le Fondateur.

---

## 5. Phase 7 — Mesh national, concentration dynamique, UE6

### 5.1 Critères fonctionnels

| ID | Critère | Vérification |
|---|---|---|
| ACC-MESH-P7-01 | Le mesh fonctionne à l'échelle nationale (couverture complète du territoire) | Test de déploiement national |
| ACC-MESH-P7-02 | Le partitionnement spatial dynamique s'active sur un scénario de charge réelle (ex. alerte incendie) | Test de charge simulée |
| ACC-MESH-P7-03 | La concentration dynamique des ressources est observée et mesurée | Métriques d'orchestrateur |
| ACC-MESH-P7-04 | L'observabilité du mesh national est complète (tableau de bord, métriques, traçage distribué) | Revue du tableau de bord |
| ACC-MESH-P7-05 | La résilience face à la panne d'un serveur régional est démontrée (reprise automatique) | Test de panne régionale |

### 5.2 Critères de neutralité de rendu

| ID | Critère | Vérification |
|---|---|---|
| ACC-MESH-P7-06 | L'interface `IRenderClient` est validée sur un second moteur de rendu (UE6 ou CesiumJS web) sans modification du mesh | Test de compatibilité |
| ACC-MESH-P7-07 | Aucune dépendance hard à UE5.8 ou UE6 dans les contrats de mesh | Revue de code |

### 5.3 Critères de gouvernance

| ID | Critère | Vérification |
|---|---|---|
| ACC-MESH-P7-08 | Audit de conformité aux 8 principes P-MESH-01 à P-MESH-08 : tous satisfaits | Grille d'audit |
| ACC-MESH-P7-09 | Le registre de risques est à jour, tous les risques Élevée/Critique sont mitigés ou acceptés | Revue du registre |

### 5.4 Critère de sortie Phase 7

Les 9 critères (P7-01 à P7-09) sont tous satisfaits. Le mesh national
est alors considéré comme opérationnel.

---

## 6. Règle de gestion des écarts

Un critère non satisfait n'invalide pas nécessairement le chantier
entier, mais :

1. L'écart est **documenté** (description, cause racine, impact).
2. L'écart est **tracé** par une décision (DEC-xxxxxx).
3. Le Fondateur **accepte explicitement** l'écart ou demande sa
   résolution avant passage à la phase suivante.
4. L'écart est mentionné dans `PROJECT_MEMORY.md` s'il affecte un
   principe fondateur ou un risque classé Élevée/Critique.

Aucun écart ne peut être ignoré silencieusement — la traçabilité est
non négociable (CON-005, CON-010, P-MESH-06).
