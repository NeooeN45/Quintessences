# ============================================================================
# GSIE-IGNIS — DIRECTIVE FONDATRICE (GCS / GROUND CONTROL SYSTEM)
# Directive ID : GSIE-DIR-0005
# Version : 1.0
# Statut : Draft
# Priorité : CRITIQUE — guide toutes les décisions futures de Ignis
# Classification : FONDATION
# Auteur : Camille Perraudeau (Fondateur)
# Date : 2026-07-12
# ============================================================================
#
# Cette Directive fondatrice fixe la vision produit de Ignis en tant que
# jumeau numérique vivant des opérations de lutte contre les incendies.
#
# Elle est complémentaire à RFC-0004 (cadre technique/fonctionnel, ADOPTÉ via
# DEC-000003) et subordonnée à la Constitution (00_CONSTITUTION/).
#
# En cas de conflit :
#   1. La Constitution prime (GSIE-CON-000).
#   2. RFC-0004 §8 (garde-fous) prime sur la présente Directive pour tout ce
#      qui touche à l'autonomie, à l'alerte et au commandement des secours.
#   3. La présente Directive prime sur l'architecture et les spécifications
#      Ignis pour la vision produit.
# ============================================================================

# Principe fondamental

Le but de Ignis n'est pas de créer un logiciel de cartographie, un
logiciel de drones ou un simulateur d'incendie.

Le but de Ignis est de créer un **jumeau numérique vivant** des
opérations de lutte contre les incendies.

Chaque choix d'architecture, chaque ligne de code et chaque fonctionnalité
doivent servir cette vision.

---

# Vision finale

Lorsqu'un utilisateur ouvre Ignis, il ne doit pas avoir l'impression
d'utiliser un logiciel.

Il doit avoir l'impression d'observer le terrain réel.

L'expérience doit être naturelle, fluide et immersive.

L'utilisateur ouvre Ignis.

Il voit la Terre.
Il zoome.
La France apparaît.
Puis les régions.
Puis les massifs forestiers.
Puis le relief.
Puis les orthophotographies.
Puis les forêts.
Puis les routes.
Puis les pistes DFCI.
Puis les points d'eau.
Puis les bâtiments.
Puis les réseaux.
Puis les capteurs.
Puis les drones.
Puis les véhicules.
Puis les vents.
Puis la fumée.
Puis le feu.

Le monde devient progressivement vivant.
Toutes les informations sont superposées au même espace.
L'utilisateur ne navigue plus entre plusieurs fenêtres.
Il navigue dans le monde réel.

---

# Objectif principal

Permettre à un décideur de comprendre une situation complexe en quelques
secondes.

Le système doit réduire la charge cognitive.
Les informations ne doivent jamais être dispersées.
Le terrain devient l'interface.
Toutes les données viennent s'y projeter.

---

# Philosophie

Ignis ne montre pas des données.
Ignis raconte ce qui se passe.

Le terrain devient le support unique de compréhension.
Toutes les informations doivent être visibles directement dans leur contexte
géographique.

---

# Exemples d'interactions

L'utilisateur clique sur un camion.
Une fiche apparaît :

* indicatif
* équipage
* niveau d'eau
* autonomie
* vitesse
* destination
* mission
* ETA

L'utilisateur clique sur un drone.
Il voit :

* le flux vidéo
* la caméra thermique
* la batterie
* les capteurs
* la mission
* la possibilité de reprendre le contrôle.

L'utilisateur clique sur le front de feu.
Il voit :

* l'intensité
* la vitesse
* la direction
* les incertitudes
* les scénarios de propagation
* les enjeux menacés.

Toutes ces informations apparaissent sans quitter la scène principale.

---

# Le moteur 3D

Le moteur de rendu (Unreal Engine ou son successeur) n'est jamais le cœur du
système.

Il est la représentation graphique du jumeau numérique.
Il ne contient pas la logique métier.
Il reçoit les informations calculées par Ignis.

Son rôle est :

* représenter le monde ;
* afficher les effets physiques ;
* permettre l'interaction ;
* offrir une immersion maximale.

> **Cadrage constitutionnel** : le moteur graphique est interchangeable
> (GSIE-CON-007, modularité). L'intelligence reste dans GSIE ; le rendu n'est
> qu'une fenêtre sur cette intelligence. Aucune logique métier ne vit dans le
> client 3D.

---

# Le cerveau

Le serveur Ignis constitue le cerveau du système.

Il réalise :

* les simulations physiques ;
* l'intelligence artificielle ;
* les prévisions ;
* l'assimilation des données ;
* les calculs géospatiaux ;
* les analyses de risques ;
* les communications.

Le client 3D ne fait qu'interpréter ces résultats.

---

# Les trois usages

Le même socle technologique doit servir simultanément :

## 1. Opération

Suivi temps réel d'un incendie.

## 2. Formation

Simulation et entraînement des COS, SDIS et écoles.

## 3. Recherche

Validation scientifique, expérimentation, génération de données synthétiques
et amélioration continue des modèles.

Une seule architecture.
Trois usages.

---

# L'autonomie

L'utilisateur ne commande pas les moyens.
Il exprime une intention.

Exemple :

« Observer cette vallée. »

Le système choisit automatiquement :

* le drone le plus pertinent ;
* le meilleur itinéraire ;
* les capteurs adaptés ;
* les communications ;
* les relais réseau nécessaires.

L'humain conserve toujours la décision finale.

> **Cadrage explicite — RFC-0004 §8.3 et §8.4 (prioritaires sur la présente
> Directive)** :
>
> 1. L'« autonomie d'intention » décrite ici s'applique à la **sélection des
>    moyens d'observation** (drone, itinéraire, capteurs, relais) et à la
>    **navigation / vol**. Elle ne s'étend pas à la décision d'alerte, à la
>    décision d'intervention, ni au commandement des secours.
> 2. La **décision d'alerte opérationnelle** reste humaine : elle relève du
>    télépilote et du commandement des secours (COS / CODIS), jamais du
>    système (RFC-0004 §3.1, §8.4).
> 3. La **reprise manuelle** par le télépilote sous supervision humaine reste
>    toujours possible et prioritaire (RFC-0004 §3.5).
> 4. Ignis est un **outil d'aide à la décision**, pas un système de
>    commandement. Il ne remplace jamais le COS / CODIS (RFC-0004 §8.4,
>    GSIE-CON-001).
> 5. Aucune alerte directe à la population : prérogative régalienne
>    (FR-Alert) (RFC-0004 §3.4).

---

# L'immersion

Le rendu 3D n'est pas un effet visuel.
Il est un outil de compréhension.

Chaque élément doit avoir une signification opérationnelle.

La fumée indique un comportement.
Le vent montre une direction.
Les flammes représentent une intensité.
Les véhicules évoluent en temps réel.

Le terrain devient un tableau de bord vivant.

---

# Principe architectural fondamental

Ignis est une plateforme d'intelligence.

Le moteur graphique est interchangeable.
Aujourd'hui Unreal Engine.
Demain un autre moteur si nécessaire.

L'intelligence reste dans GSIE.
Le rendu n'est qu'une fenêtre ouverte sur cette intelligence.

---

# Devise du projet

> **Ne jamais construire un logiciel qui affiche des cartes. Construire un
> monde numérique vivant qui permet de comprendre, anticiper et décider.**

---

# Références

- `00_CONSTITUTION/GSIE-CON-000.md` — Primauté de la Constitution
- `00_CONSTITUTION/GSIE-CON-001.md` — Le décideur reste humain
- `00_CONSTITUTION/GSIE-CON-007.md` — Modularité obligatoire
- `02_RFC/RFC-0004.md` — Ignis : système autonome de surveillance et
  d'analyse des incendies (ADOPTÉ — DEC-000003)
- `03_DECISIONS/DEC-000003.md` — Adoption RFC-0004
- `03_DECISIONS/DEC-000008.md` — Adoption de la présente Directive
- `apps/Ignis/REGISTRE.md` — Registre d'idées vivant

FIN DE DIRECTIVE.
