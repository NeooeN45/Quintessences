# SERVER MESHING — Features expérimentales

| Champ | Valeur |
|---|---|
| **Document** | Features expérimentales — GSIE Server Meshing |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **RFC liée** | RFC-0035 |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 |
| **Documents connexes** | `SERVER_MESHING_TARGET.md`, `SERVER_MESHING_ROADMAP.md`, `SERVER_MESHING_RISKS.md` |

---

## 1. Mission du document

Recenser les fonctionnalités expérimentales envisagées pour le Server
Meshing, au-delà du périmètre strict des Phases 5 à 7. Ces features ne
sont **pas engagées** — elles sont documentées pour anticiper les
évolutions possibles et éviter qu'elles ne soient intégrées
silencieusement au périmètre (RISK-MESH-004, sur-ingénierie).

Chaque feature expérimentale est **gated** : elle ne peut entrer en
implémentation qu'après une décision explicite du Fondateur
(DEC-xxxxxx) et une RFC si elle modifie un principe fondateur ou une
interface de mesh.

---

## 2. Features envisagées

### 2.1 Prédiction de charge par apprentissage

| Champ | Détail |
|---|---|
| **Description** | Utiliser le Learning Engine pour prédire les zones de charge future (ex. propagation d'incendie, afflux d'opérateurs) et pré-allouer les ressources du mesh avant le pic. |
| **Bénéfice** | Anticipation au lieu de réaction ; concentration dynamique proactive (P-MESH-04 étendu). |
| **Risque** | Prédiction incorrecte entraînant une allocation erronée ; complexité supplémentaire de l'orchestrateur. |
| **Gating** | RFC dédiée + DEC. Phase 7 au plus tôt (requiert orchestrateur complet et Learning Engine opérationnel). |
| **Statut** | Hypothèse de recherche — pas d'implémentation avant preuve de concept. |

### 2.2 Migration à chaud de serveur de zone (live migration)

| Champ | Détail |
|---|---|
| **Description** | Déplacer un serveur de zone d'un datacenter à un autre sans interruption de service, en transférant l'état en mémoire puis l'autorité. |
| **Bénéfice** | Maintenance infrastructure sans interruption opérateur ; équilibrage de charge cross-datacenter. |
| **Risque** | Complexité du transfert d'état en mémoire (contrairement au handoff d'autorité, ici l'état vivant doit migrer) ; risque de divergence pendant la migration. |
| **Gating** | RFC dédiée + DEC. Phase 7 au plus tôt (requiert handoff multi-régions validé). |
| **Statut** | Envisagé — pas de spécification avant Phase 6 clôturée. |

### 2.3 Réplication cross-région en temps réel (PostgreSQL logical replication)

| Champ | Détail |
|---|---|
| **Description** | Réplication logique PostgreSQL entre datacenters régionaux pour permettre une reprise d'autorité quasi-instantanée en cas de panne régionale. |
| **Bénéfice** | RTO (Recovery Time Objective) réduit à quasi-zéro pour les pannes régionales. |
| **Risque** | Coût d'infrastructure (réplication cross-région continue) ; complexité de résolution de conflit si deux régions divergent. |
| **Gating** | ADR dédié + DEC. Phase 7 (requiert mesh multi-régions stable). |
| **Statut** | Différé — ADR-011 note explicitement le report de la réplication logique cross-région. |

### 2.4 Client de rendu CesiumJS web

| Champ | Détail |
|---|---|
| **Description** | Implémenter `IRenderClient` en CesiumJS pour un accès au mesh via navigateur, sans installation du Hub UE5.8. |
| **Bénéfice** | Accès distant léger ; validation de la neutralité de rendu (ACC-MESH-P7-06) ; déploiement facile pour les opérateurs terrain. |
| **Risque** | Performances limitées par rapport au Hub UE5.8 ; fonctionnalités de rendu avancées indisponibles. |
| **Gating** | Décision Fondateur. Phase 7 (validation de neutralité) ou plus tôt si un besoin terrain est identifié. |
| **Statut** | Envisagé — candidat prioritaire pour valider la neutralité de rendu si UE6 n'est pas disponible. |

### 2.5 Fédération de meshes (inter-organisations)

| Champ | Détail |
|---|---|
| **Description** | Permettre à plusieurs instances de mesh GSIE (ex. Quintessences + partenaire) de s'échanger des entités via un protocole de fédération. |
| **Bénéfice** | Interopérabilité avec d'autres jumeaux numériques environnementaux ; partage de données cross-organisation. |
| **Risque** | Gouvernance de l'autorité inter-organisations (qui possède quoi quand deux meshes se chevauchent ?) ; sécurité de la fédération. |
| **Gating** | RFC majeure + DEC. Post-Phase 7 (requiert mesh national stable). |
| **Statut** | Vision long terme — pas de spécification avant mesh national opérationnel. |

### 2.6 Concentration dynamique sur alerte Ignis

| Champ | Détail |
|---|---|
| **Description** | Cas d'usage spécifique : lors d'une alerte Ignis, l'orchestrateur concentre automatiquement les ressources de simulation et de rendu sur la zone d'incendie, avec une sous-zone haute précision (RFC-0035 §2.1). |
| **Bénéfice** | Démonstration du bénéfice métier du mesh sur un cas réel (incendie = crise = besoin de précision immédiate). |
| **Risque** | Couplage entre Ignis et le mesh — s'assurer que le mesh reste générique et ne code pas de logique Ignis dans l'orchestrateur. |
| **Gating** | Intégré au périmètre Phase 7 (cas de validation de la concentration dynamique). Pas de feature séparée. |
| **Statut** | Cas de validation prioritaire pour Phase 7. |

---

## 3. Règles de gestion des features expérimentales

1. **Aucune implémentation sans gating** — une feature expérimentale
   n'entre en implémentation qu'après décision tracée (DEC-xxxxxx) et,
   si elle modifie une interface ou un principe fondateur, RFC dédiée.
2. **Pas de périmètre implicite** — une feature non listée dans ce
   document ne peut pas être implémentée « au passage » dans une phase
   du chantier. Toute dérive est un écart (RISK-MESH-016).
3. **Révision à chaque phase** — ce document est révisé à la fin de
   chaque phase (5, 6, 7) pour intégrer les nouvelles hypothèses
   identifiées pendant l'implémentation et retirer celles devenues
   obsolètes.
4. **Subordination à la connaissance** (P-MESH-08) — une feature
   expérimentale qui contournerait la persistance ou la traçabilité
   pour un bénéfice technique est rejetée par construction.

---

## 4. Ce que ce document n'est pas

- Ce n'est pas un backlog — les features ne sont pas des tâches
  planifiées, mais des hypothèses documentées.
- Ce n'est pas un engagement — aucune de ces features n'est promise à
  implémentation.
- Ce n'est pas une fermeture — de nouvelles features peuvent être
  ajoutées par révision de ce document, à condition de respecter les
  règles de gestion (§3).
