# ============================================================================
# GSIE-IGNIS — VISION DU MOTEUR COGNITIF
# Directive ID : GSIE-DIR-0006
# Version : 1.0
# Statut : Draft
# Priorité : CRITIQUE — guide l'architecture du cerveau Ignis
# Classification : FONDATION
# Auteur : Camille Perraudeau (Fondateur)
# Date : 2026-07-12
# ============================================================================
#
# Cette Directive fondatrice fixe la vision du **moteur cognitif** Ignis
# (le cerveau serveur). Elle est le compagnon de GSIE-DIR-0005, qui fixe la
# vision du **jumeau numérique vivant** côté rendu/GCS.
#
# Articulation :
#   - GSIE-DIR-0005 : « Le moteur graphique montre le monde. »
#   - GSIE-DIR-0006 : « Le moteur cognitif le comprend. »
#
# Elle est subordonnée à la Constitution (00_CONSTITUTION/) et à RFC-0004
# (cadre technique/fonctionnel, ADOPTÉ via DEC-000003).
#
# En cas de conflit :
#   1. La Constitution prime (GSIE-CON-000).
#   2. RFC-0004 §8 (garde-fous) prime sur la présente Directive pour tout ce
#      qui touche à l'autonomie, à l'alerte et au commandement des secours.
#   3. La présente Directive prime sur l'architecture et les spécifications
#      Ignis pour la vision du moteur cognitif.
# ============================================================================

# Principe fondamental

Le serveur Ignis n'est pas un serveur.

Il est un système d'intelligence.

Son rôle n'est pas de stocker des données.
Son rôle est de comprendre le monde.

Chaque seconde, il doit construire la représentation numérique la plus fidèle
possible de la réalité.

Le moteur graphique représente cette réalité.
Le serveur la comprend.

---

# Vision

Le serveur doit agir comme un scientifique observant un incendie.

Il collecte.
Il compare.
Il doute.
Il vérifie.
Il corrige.
Il prédit.
Il explique.
Il apprend.

Jamais il ne se contente d'afficher une donnée.

---

# Objectif ultime

Construire un modèle numérique vivant de l'incendie.

Le système doit connaître, à tout instant :

* où est le feu ;
* pourquoi il évolue ainsi ;
* ce qui influence son comportement ;
* ce qui est incertain ;
* ce qui est confirmé ;
* ce qui risque de se produire ensuite.

---

# Principe d'assimilation permanente

Aucune donnée n'est considérée comme une vérité absolue.

Chaque source possède :

* une précision ;
* une latence ;
* une fiabilité ;
* une incertitude.

Le serveur doit fusionner toutes les observations.
Il ne choisit jamais une source.
Il construit un consensus probabiliste.

> **Cadrage constitutionnel** : toute affirmation doit être traçable et
> incertitude explicitée (GSIE-CON-004, GSIE-CON-005). Le « consensus
> probabiliste » n'est jamais présenté comme une vérité, toujours comme un
> raisonnement justifiable.

---

# Les observateurs

Chaque élément devient un observateur du terrain.

Exemples :

Satellite · Drone RGB · Drone thermique · Caméra fixe · Station météo ·
Capteur CO₂ · Capteur particules · LoRa · Radar · Lidar · Rapports SDIS ·
Signalements citoyens · Historique BDIFF · Météo-France · Copernicus ·
NASA FIRMS · Sentinel.

Chaque observateur apporte une partie de la vérité.

---

# Le monde comme graphe vivant

Le territoire n'est jamais une carte.
Il est un graphe dynamique.

Chaque élément est relié.

Exemples :

un arbre influence un autre arbre.
une pente influence la propagation.
un vent influence une vallée.
une route influence les accès.
un camion influence le temps d'intervention.
une ligne électrique influence le risque d'ignition.

Le serveur manipule des relations.
Pas seulement des coordonnées.

---

# Raisonnement multi-échelle

Le moteur réfléchit simultanément :

à l'échelle du pixel,
de l'arbre,
de la parcelle,
du massif,
du département,
de la région,
du pays.

Chaque niveau échange avec les autres.

---

# Raisonnement temporel

Le système ne connaît pas uniquement le présent.

Il conserve :

le passé,
le présent,
les futurs probables.

Chaque événement possède une histoire.
Chaque simulation possède plusieurs avenirs.

---

# Raisonnement probabiliste

Le serveur ne répond jamais :

« Cela arrivera. »

Il répond :

« Voici les scénarios les plus probables. »

Chaque décision est accompagnée :

* d'un niveau de confiance ;
* d'une justification ;
* des observations ayant conduit à cette conclusion.

> **Cadrage constitutionnel** : explicabilité obligatoire
> (GSIE-CON-004). Aucune sortie n'est présentée sans justification et niveau
> de confiance.

---

# Simulation permanente

Le serveur ne s'arrête jamais.
Même sans utilisateur connecté.

Il exécute en permanence :

des simulations,
des comparaisons,
des recalages,
des validations,
des réapprentissages.

Le monde numérique continue de vivre.

---

# Intelligence distribuée

Chaque module possède une spécialité.

Exemple :

Agent météo · Agent propagation · Agent végétation · Agent drone ·
Agent communication · Agent réseau · Agent RCCI · Agent logistique ·
Agent santé des équipages · Agent cybersécurité.

Chaque agent raisonne indépendamment.
Le moteur cognitif fusionne leurs conclusions.

> **Cadrage constitutionnel** : modularité obligatoire (GSIE-CON-007). Chaque
> agent = une responsabilité unique, documentée, testée. La fusion reste
> explicable, jamais une boîte noire (GSIE-CON-004).

---

# IA collaborative

Aucune intelligence artificielle unique.

Chaque modèle possède son domaine.

Vision. Texte. Prévision météo. Détection. Classification. Optimisation.
Raisonnement.

Le moteur orchestre leurs compétences.

---

# Mémoire

Chaque incendie devient une expérience.

Le système apprend :

ce qui était juste,
ce qui était faux,
ce qui aurait pu être anticipé.

Le moteur améliore progressivement sa compréhension.
Le passé augmente l'intelligence du futur.

> **Cadrage constitutionnel** : toute connaissance doit pouvoir évoluer sans
> perdre son historique (GSIE-CON-010). L'apprentissage est versionné et
> traçable.

---

# Explicabilité

Chaque résultat doit pouvoir être expliqué.

Pourquoi cette propagation ?
Pourquoi ce risque ?
Pourquoi cette décision ?

Le système cite les données utilisées.
Il expose ses raisonnements.

---

# Auto-évaluation

Le moteur calcule continuellement :

son niveau de confiance,
ses zones d'incertitude,
les informations manquantes,
les observations à demander.

Il sait ce qu'il ignore.

---

# Curiosité artificielle

Lorsque l'incertitude devient trop importante,

le système propose spontanément :

d'envoyer un drone,
de demander une mesure thermique,
de repositionner un capteur,
de recalculer une simulation,
d'interroger une nouvelle source.

Il cherche activement les informations qui amélioreront sa compréhension.

> **Cadrage explicite — RFC-0004 §8.3/§8.4 (prioritaires sur la présente
> Directive)** : la « curiosité artificielle » produit des **propositions**
> d'observation (envoi de drone, repositionnement de capteur). Elle ne
> déclenche **jamais** automatiquement une mission opérationnelle, une alerte
> ou une intervention. La décision de missionner un moyen reste humaine
> (télépilote, COS / CODIS). La reprise manuelle reste toujours possible et
> prioritaire.

---

# Anticipation

Le moteur ne répond pas uniquement aux questions.

Il détecte lui-même :

les risques,
les anomalies,
les incohérences,
les comportements inhabituels.

Il agit avant qu'un humain ne pose la question.

> **Cadrage explicite** : « agit » signifie « signale et propose », jamais
> « décide à la place de l'humain » (GSIE-CON-001, RFC-0004 §8.4). Ignis
> est un outil d'aide à la décision, pas un système de commandement.

---

# Moteur scientifique

Toute nouvelle théorie peut être testée.
Toute nouvelle IA peut être comparée.
Toute nouvelle simulation peut être évaluée.

Ignis devient une plateforme scientifique autant qu'opérationnelle.

---

# Principe absolu

Le serveur ne doit jamais devenir un simple backend.

Il doit devenir un cerveau géospatial capable de comprendre, d'expliquer, de
prédire et d'apprendre continuellement à partir du monde réel.

---

# Vision à long terme

À terme, Ignis ne devra plus seulement représenter les incendies.

Il devra être capable de comprendre les interactions entre le climat, la
végétation, la topographie, les infrastructures, les moyens humains et les
phénomènes physiques afin de devenir un véritable système d'intelligence
environnementale.

Le feu n'est que le premier domaine d'application.

L'architecture devra être conçue dès le départ pour pouvoir accueillir
demain d'autres modules : santé des forêts, biodiversité, tempêtes,
sécheresses, risques naturels, logistique de crise et gestion des
territoires.

> **Cohérence écosystème** : cette vision à long terme rejoint la vocation
> du moteur GSIE (General System Intelligence Engine) et de l'écosystème
> Quintessences (DEC-000006, DEC-000007). Ignis est la spécialisation
> incendie d'un moteur conçu pour être généralisable.

---

# Devise

> **« Le moteur graphique montre le monde. Le moteur cognitif le comprend. »**

---

# Références

- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0005.md` — Directive fondatrice Ignis
  (GCS / jumeau numérique vivant) — vision côté rendu, compagnon de la
  présente
- `00_CONSTITUTION/GSIE-CON-000.md` — Primauté de la Constitution
- `00_CONSTITUTION/GSIE-CON-001.md` — Le décideur reste humain
- `00_CONSTITUTION/GSIE-CON-004.md` — Toute décision doit être explicable
- `00_CONSTITUTION/GSIE-CON-005.md` — Toute connaissance doit être traçable
- `00_CONSTITUTION/GSIE-CON-007.md` — Modularité obligatoire
- `00_CONSTITUTION/GSIE-CON-010.md` — Évolution sans perte d'historique
- `02_RFC/RFC-0004.md` — Ignis : système autonome de surveillance et
  d'analyse des incendies (ADOPTÉ — DEC-000003)
- `03_DECISIONS/DEC-000003.md` — Adoption RFC-0004
- `03_DECISIONS/DEC-000006.md` — Identité Quintessences / GSIE / GeoSylva
- `03_DECISIONS/DEC-000009.md` — Adoption de la présente Directive
- `22_PROJECT_MEMORY/Ignis.md` — Registre d'idées vivant

FIN DE DIRECTIVE.
