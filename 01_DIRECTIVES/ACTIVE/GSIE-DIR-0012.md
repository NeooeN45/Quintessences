# ============================================================================
# GSIE SERVER MESHING — DIRECTIVE FONDATRICE
# Directive ID : GSIE-DIR-0012
# Version : 1.0
# Statut : Draft
# Priorité : STRUCTURANTE — oriente l'évolution long terme du Hub et de l'API
# Classification : FONDATION
# Auteur : Camille Perraudeau (Fondateur)
# Date : 2026-08-03
# ============================================================================
#
# Cette Directive fondatrice fixe la vision du GSIE Server Meshing :
# évolution du Centre de Commandement et de l'API GSIE vers un jumeau
# numérique environnemental distribué, continu et persistant.
#
# Elle est complémentaire à RFC-0035 (cadre technique, Draft) et
# subordonnée à la Constitution (00_CONSTITUTION/).
#
# En cas de conflit :
#   1. La Constitution prime (GSIE-CON-000).
#   2. RFC-0003 (GSIE-Net) prime sur la présente Directive pour tout ce
#      qui touche à l'architecture réseau et offline-first.
#   3. La présente Directive prime sur l'architecture et les
#      spécifications du Hub pour la vision produit Server Meshing.
# ============================================================================

# Principe fondamental

Le but du GSIE Server Meshing n'est pas de créer un système distribué
pour la performance, ni de reproduire un MMO.

Le but est de créer un **jumeau numérique environnemental continu,
persistant et distribué** qui représente le monde réel sans coupure
visible pour l'opérateur, et qui concentre dynamiquement ses
ressources sur les zones qui requièrent attention et précision.

Chaque choix d'architecture du mesh doit servir cette vision.

---

# Vision finale

Lorsqu'un opérateur ouvre le Centre de Commandement GSIE, il ne doit
pas voir de frontières entre serveurs.

Il voit un globe.

Il zoome sur la France.

La France est continue. Il n'y a pas de "région Aquitaine" puis
"région PACA" comme des cases séparées. Il y a un territoire unique.

Il zoome sur un massif forestier en Corse où un incendie est actif.

Le système a automatiquement alloué plus de ressources à la Corse.
L'opérateur ne le voit pas. Il voit juste que la Corse est fluide,
détaillée, temps réel.

Pendant ce temps, l'Aquitaine est en "veille" — moins de ressources,
moins de précision, mais toujours présente, toujours continue.

Si l'opérateur navigue de Corse vers l'Aquitaine, le transfert
d'autorité se fait en arrière-plan. Aucune coupure. Aucun
chargement visible. Aucune perte de données.

Si le serveur de la Corse tombe en panne, un autre serveur prend le
relais. L'opérateur voit peut-être un bref glitch — mais l'état du
jumeau est préservé. Aucune connaissance n'est perdue.

---

# Huit principes directeurs

## 1. Continuité spatiale sans coupure

L'opérateur navigue sur un globe apparemment unique. Les frontières
entre serveurs sont invisibles. Le transfert d'autorité d'une entité
d'un serveur à un autre se fait sans interruption visible.

## 2. Persistance externe obligatoire

Aucune donnée critique du jumeau ne vit uniquement en mémoire d'un
serveur. Tout état est persisté dans la couche de persistance externe
(PostgreSQL/PostGIS + métamodèle v6.2 bitemporel) avant d'être
considéré comme valide. Unreal Engine est un client de rendu, pas la
source de vérité.

## 3. Autorité hybride zone + type

L'autorité sur une entité est déterminée par deux axes : zone spatiale
(serveur régional) et type d'entité (serveur spécialisé). L'autorité
spatiale est primaire, l'autorité par type est secondaire. Les
conflits sont résolus par priorité documentée.

## 4. Concentration dynamique des ressources

Le mesh adapte sa topologie à la charge. Une zone active (incendie,
crise, mission) reçoit dynamiquement plus de ressources. Une zone
inactive libère ses ressources. L'opérateur ne le voit pas.

## 5. Offline-first préservé

Le Server Meshing ne contredit pas le principe offline-first. Les
nœuds terminaux (téléphones, tablettes, GCS-Lite) continuent de
fonctionner hors-ligne. Le mesh est une évolution de l'infrastructure
serveur, pas des nœuds terminaux.

## 6. Traçabilité complète

Toute décision du mesh — transfert d'autorité, redécoupage,
allocation — est journalisée et traçable. L'historique du mesh fait
partie du jumeau numérique. Aucune optimisation ne peut dégrader la
traçabilité.

## 7. Modularité et interchangeabilité

Le mesh est construit sur des interfaces contractuelles. Le client de
rendu (UE5.8, UE6, CesiumJS web) est interchangeable. Les serveurs de
zone sont interchangeables. La couche de persistance est
interchangeable. Aucun composant n'est un point de blocage unique.

## 8. Subordination à la connaissance

Le Server Meshing est un moyen, pas une fin. La connaissance est le
véritable produit. En cas de conflit entre performance du mesh et
qualité de la connaissance, la connaissance prime.

---

# Décisions structurantes actées par le Fondateur

| Décision | Valeur | Date |
|---|---|---|
| Périmètre prototype v0 | Mono-région (Landiras) | 2026-08-03 |
| Stratégie d'autorité | Hybride zone + type | 2026-08-03 |
| Dépendance UE6 | Compatibilité anticipée (interfaces abstraites) | 2026-08-03 |
| Niveau de détail première itération | Complet (Vagues 1+2+3+4) | 2026-08-03 |

---

# Ce que cette Directive n'est PAS

- Ce n'est pas une architecture — c'est une vision. L'architecture
  cible est produite dans `SERVER_MESHING_TARGET.md`.
- Ce n'est pas une priorisation court terme — le mesh est un chantier
  long terme qui s'ajoute aux priorités Phase 4 sans les remplacer.
- Ce n'est pas un abandon du modèle actuel — le Hub monolithique
  actuel reste la cible Phase 4. Le mesh est l'évolution Phase 5+.

---

# Phasage indicatif

| Phase | Périmètre | Horizon |
|---|---|---|
| Phase 4 (courante) | Hub monolithique, API GSIE, moteurs, apps | Court terme |
| Phase 5 (anticipée) | Prototype Server Meshing v0 (Landiras) | Moyen terme |
| Phase 6 (anticipée) | Extension multi-régions, handoff d'autorité | Long terme |
| Phase 7 (vision) | Mesh national, concentration dynamique, UE6 | Cible |

> Le phasage exact sera défini dans la roadmap dédiée
> (`SERVER_MESHING_ROADMAP.md`).

---

# Note de gouvernance

Cette Directive est ouverte en **Draft**. Elle sera activée par la
décision DEC-000053. Toute évolution de cette Directive requiert une
RFC.

> « Le jumeau numérique environnemental doit être aussi continu et
> persistant que le monde qu'il représente. »
