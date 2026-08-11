# GSIE Server Meshing — Architecture du prototype v0 (Landiras)

| Champ | Valeur |
|---|---|
| **Chantier** | GSIE Server Meshing — Vague 2 (architecture) |
| **Phase** | 4 — Implémentation (préparation Phase 5) |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **Auteur** | Camille Perraudeau (Fondateur) — instruit par agent architecte |
| **Lois fondatrices** | GSIE-CON-000, GSIE-CON-003, GSIE-CON-007, GSIE-CON-010 |
| **RFC liée** | RFC-0035, RFC-0003 (GSIE-Net), RFC-0011 (métamodèle v6.2) |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 (périmètre prototype v0 : mono-région Landiras) |
| **Documents apparentés** | `SERVER_MESHING_TARGET.md`, `SERVER_MESHING_ROADMAP.md`, `COMMAND_CENTER_UNREAL.md` |

---

## 1. Mission du document

Décrire l'architecture du **prototype v0** du GSIE Server Meshing,
limité à la zone de Landiras (Gironde), conformément à la décision du
Fondateur (DEC-000053, GSIE-DIR-0012). Ce prototype valide un
sous-ensemble volontairement restreint de l'architecture cible
(`SERVER_MESHING_TARGET.md`) : un seul serveur de zone, un seul
serveur spécialisé, aucun handoff inter-serveur.

Statut Draft — ce document oriente l'implémentation à venir, il n'est
pas lui-même du code ni une spécification d'implémentation détaillée.

---

## 2. Périmètre

- **Zone** : Landiras (Gironde), périmètre déjà couvert par la
  configuration Cesium existante et les données Ignis.
- **Données** : jeux de données Ignis actuellement exploités par le
  Hub UE5.8 (incendie, forêt, topographie du secteur).
- **Un seul opérateur** connecté simultanément (pas de test de
  concurrence multi-opérateurs en v0).
- **Aucune extension géographique** au-delà de Landiras.

---

## 3. Objectifs du prototype

1. Valider que la **persistance externe** (P-MESH-02) fonctionne : un
   serveur peut être arrêté et redémarré sans perte d'état.
2. Valider un modèle d'**autorité unique** simplifié (une seule zone,
   sans besoin de résolution de conflit zone/type en v0).
3. Valider le **streaming par pertinence** minimal : le Hub ne reçoit
   que les entités pertinentes à son point de vue, via un flux mesh
   plutôt qu'un flux monolithique statique.
4. Valider la **reconnexion après panne** : le Hub retrouve un état
   cohérent après une interruption du serveur de zone.
5. Valider que l'**offline-first** des nœuds terminaux (P-MESH-05)
   n'est pas dégradé par l'introduction de la couche mesh.

---

## 4. Architecture du prototype

```
                     ┌─────────────────────────────┐
                     │   SERVEUR DE ZONE Landiras    │
                     │   (ZoneServer minimal)        │
                     │   - IZoneServer                │
                     │   - IMeshNode                   │
                     │   - Autorité unique (pas de      │
                     │     handoff, pas de conflit)     │
                     └──────────────┬────────────────┘
                                    │
                     ┌──────────────▼────────────────┐
                     │  SERVEUR SPÉCIALISÉ Simulation │
                     │  (ISpecializedServer)           │
                     │  Héberge le Simulation Engine    │
                     │  et consulte Reasoning Engine     │
                     └──────────────┬────────────────┘
                                    │
                     ┌──────────────▼────────────────┐
                     │   COUCHE DE PERSISTANCE          │
                     │   PostgreSQL/PostGIS existant     │
                     │   Métamodèle v6.2 (déjà en place) │
                     │   Graphe d'autorité simple         │
                     │   (une seule entrée : Landiras)     │
                     └──────────────┬────────────────┘
                                    │
                     ┌──────────────▼────────────────┐
                     │        HUB UE5.8 (modifié)       │
                     │  Consomme le mesh via IRenderClient│
                     │  au lieu du flux WebSocket direct   │
                     │  actuel (livrable 211)              │
                     └───────────────────────────────┘
```

Différence essentielle avec l'architecture cible
(`SERVER_MESHING_TARGET.md`) : il n'y a **qu'un** serveur de zone et
**qu'un** serveur spécialisé. L'orchestrateur de mesh, le service
discovery multi-nœuds et le partitionnement dynamique ne sont pas
implémentés en v0 — leurs interfaces sont respectées de manière
triviale (un registre à une entrée) pour ne pas fermer la porte à leur
implémentation future.

---

## 5. Composants à implémenter

| Composant | Description | Nouveau ou existant |
|---|---|---|
| **ZoneServer minimal** | Implémentation restreinte de `IZoneServer` : une seule zone fixe (Landiras), pas de redécoupage, pas de handoff. Sert de socle pour valider le contrat sans complexité de coordination multi-nœuds. | Nouveau |
| **Graphe d'autorité simple** | Table persistée à une seule entrée (zone Landiras → ZoneServer). Implémente `IAuthorityGraph` sans logique de résolution de conflit zone/type (un seul axe actif). | Nouveau (schéma minimal) |
| **Persistance PostgreSQL existante** | Aucune migration de schéma majeure : extension du schéma v6.2 déjà en place pour porter le graphe d'autorité et le journal d'audit minimal. | Existant, étendu |
| **Hub UE5.8 modifié** | Le Hub cesse de consommer un flux WebSocket/JSON unique statique (livrable 211 actuel) pour consommer le mesh via une implémentation de `IRenderClient`. Le comportement visible pour l'opérateur ne change pas en v0 (une seule zone). | Existant, adapté |

---

## 6. Ce qui est volontairement exclu du v0

Ces exclusions ne sont pas des oublis : elles délimitent le périmètre
minimal viable et sont reportées aux phases suivantes
(`SERVER_MESHING_ROADMAP.md`, Phase 6 et 7).

- **Handoff inter-serveurs** — un seul serveur de zone existe, aucun
  transfert d'autorité n'est nécessaire ni testé.
- **Partitionnement spatial dynamique** — la zone Landiras est fixe,
  aucun redécoupage automatique.
- **Multi-régions** — aucune autre zone géographique n'est intégrée au
  mesh en v0.
- **Concentration dynamique de ressources** — aucun mécanisme
  d'allocation adaptative n'est implémenté ; l'orchestrateur de mesh
  n'existe pas encore en tant que composant actif.
- **Résolution de conflit zone/type** — un seul serveur spécialisé,
  pas de scénario de conflit d'autorité à arbitrer.

---

## 7. Plan de validation

| Scénario | Description | Résultat attendu |
|---|---|---|
| **Navigation** | L'opérateur navigue dans la scène Landiras via le Hub modifié. | Comportement visuel équivalent à l'actuel (livrable 211) ; flux issu du mesh au lieu du flux direct. |
| **Panne serveur** | Le ZoneServer est arrêté volontairement pendant une session active. | Le Hub signale l'indisponibilité sans corrompre l'état affiché ; aucune perte de données côté persistance. |
| **Reconnexion** | Le ZoneServer est redémarré après la panne. | Le ZoneServer reconstitue son état depuis PostgreSQL (P-MESH-02) ; le Hub se reconnecte et retrouve un état cohérent avec l'état pré-panne. |
| **Offline** | Un nœud terminal simulé (GCS-Lite ou équivalent) est déconnecté puis reconnecté. | Le comportement offline-first (RFC-0003) est inchangé ; la synchronisation au retour de connectivité fonctionne comme avant l'introduction du mesh. |

Chaque scénario est validé par un test reproductible, avec critère de
réussite/échec explicite, avant passage en Phase 6
(`SERVER_MESHING_ROADMAP.md` §critères de sortie).

---

## 8. Dépendances

- **API GSIE existante** (FastAPI, ADR-007) — le ZoneServer s'appuie
  sur les mêmes modèles de données et la même couche d'accès que
  l'API actuelle, sans duplication de logique métier.
- **PostgreSQL/PostGIS** — infrastructure de persistance déjà en
  production.
- **Redis** — déjà utilisé pour le WebSocket temps réel (ADR-007) ;
  réutilisé pour le canal de réplication par pertinence du prototype.
- **Hub UE5.8** — base de code existante (livrable 211), modifiée pour
  consommer `IRenderClient` plutôt que le flux WebSocket direct
  actuel.

---

## 9. Estimation d'effort (qualitative)

| Composant | Effort | Justification |
|---|---|---|
| ZoneServer minimal | M | Nouveau composant, mais périmètre restreint (une zone, pas de handoff). |
| Graphe d'autorité simple | S | Schéma à une entrée, pas de logique de résolution de conflit. |
| Extension persistance (journal d'audit minimal) | S | Extension additive du schéma v6.2 existant. |
| Hub modifié (adaptateur IRenderClient) | M | Changement du mode de consommation du flux sans changement du rendu visible. |
| Plan de test et scénarios de validation | S | Scénarios ciblés, environnement mono-région déjà disponible. |

Légende : S = effort faible (quelques jours), M = effort moyen
(une à deux semaines), L = effort élevé (non requis en v0).

---

## 10. Critères de succès du prototype

Le prototype v0 est considéré réussi si, et seulement si :

1. Le Hub affiche la zone Landiras via le mesh sans régression visible
   pour l'opérateur par rapport au comportement actuel (livrable 211).
2. Un arrêt/redémarrage du ZoneServer ne provoque aucune perte de
   donnée persistée (vérifié par comparaison d'état avant/après).
3. Le comportement offline-first des nœuds terminaux reste identique
   à celui garanti par RFC-0003 avant l'introduction du mesh.
4. Le journal d'audit minimal enregistre correctement les événements
   de démarrage, arrêt et reconnexion du ZoneServer (P-MESH-06).
5. Aucune modification de contrat d'interface d'un moteur GSIE
   existant n'a été nécessaire pour atteindre les points 1 à 4.

L'échec d'un seul critère n'invalide pas nécessairement le chantier
mesh dans son ensemble, mais doit être documenté et tracé avant
d'envisager le passage à la Phase 6 (`SERVER_MESHING_ROADMAP.md`).
