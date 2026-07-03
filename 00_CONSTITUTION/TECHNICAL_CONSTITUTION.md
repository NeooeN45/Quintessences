# Constitution Technique de GSIE

Édition : Première Édition
Version : 1.0 (Draft)
Statut : À valider
Classification : Constitution Sectorielle
Référence : Livrable 008 (GSIE-DIR-0003)
Lois fondatrices : GSIE-CON-003, GSIE-CON-007

---

## Préambule

La Constitution Technique définit les règles opérationnelles qui
gouvernent l'architecture logicielle, l'organisation du code et les
choix technologiques de GSIE. Elle opérationnalise les principes
CON-003 (connaissance avant code) et CON-007 (modularité obligatoire).

Elle ne dicte pas un langage de programmation — elle dicte des
contraintes que tout choix technologique doit respecter.

---

## Article T-1 — Architecture modulaire

GSIE est composé de **moteurs indépendants**. Chaque moteur a :

- **UNE responsabilité** — pas de moteur multi-rôle ;
- **ses propres tests** — unitaires, d'intégration, fonctionnels ;
- **sa propre documentation** — README, API, schémas ;
- **une API explicite** — interface publique documentée ;
- **aucune dépendance circulaire** — le graphe de dépendances est
  acyclique.

Aucun moteur ne peut accéder à l'implémentation interne d'un autre. La
communication se fait exclusivement par les API documentées.

---

## Article T-2 — Couplage faible

Les moteurs communiquent par **interfaces contractuelles**, jamais par
accès direct. Un contrat d'interface définit :

- les **entrées** — format, type, unité, domaine de validité ;
- les **sorties** — format, type, unité, niveau de confiance ;
- les **erreurs** — codes, significations, récupérations possibles ;
- la **version** — toute évolution de contrat est versionnée.

Un moteur peut être remplacé sans casser les autres si le contrat est
respecté.

---

## Article T-3 — Subordination du code à la connaissance

Le code est un **moyen**, pas une fin. En cas de conflit entre la
qualité de la connaissance et la performance du code, la connaissance
prime.

Conséquences :
- aucune optimisation ne peut dégrader la traçabilité ;
- aucune performance ne peut justifier une boîte noire ;
- aucun raccourci ne peut contourner l'explicabilité ;
- la lisibilité prime sur la concision.

---

## Article T-4 — Pas de logique métier dupliquée

Toute règle métier (seuil, coefficient, formule) existe à **un seul
endroit** du système. La duplication est interdite.

Si deux moteurs ont besoin de la même règle :
- la règle est extraite dans un module partagé ;
- ou un moteur fournit la règle via son API et l'autre la consomme.

---

## Article T-5 — Tests obligatoires

Aucun composant n'est considéré terminé sans :

- **tests unitaires** — couverture ≥ 80% sur la logique métier ;
- **tests d'intégration** — aux frontières entre moteurs ;
- **tests fonctionnels** — sur les cas d'usage utilisateur ;
- **validation documentaire** — la doc correspond au comportement.

Les tests font partie du produit, au même titre que le code.

---

## Article T-6 — Versionnement

Tout est versionné :

- **code** — Git, commits conventionnels, branches par fonctionnalité ;
- **connaissances** — chaque modification est tracée, l'ancienne
  version est conservée ;
- **API** — les contrats d'interface sont versionnés ;
- **documents** — la Constitution et les RFC ont des éditions
  numérotées.

Aucune modification destructive sans versionnement préalable.

---

## Article T-7 — Gestion des erreurs

Les erreurs sont :

- **loggées** — avant d'être propagées ;
- **explicites** — codes et messages clairs ;
- **jamais masquées** — un `catch` silencieux est interdit ;
- **jamais transformées en comportement par défaut** — une erreur
  n'est pas un cas normal.

---

## Article T-8 — Fonctionnement hors-ligne

GSIE doit fonctionner en terrain isolé, sans connexion réseau. Les
règles :

- les **données de référence** sont mises en cache local ;
- les **moteurs critiques** (Knowledge, Evidence, Reasoning,
  Diagnostic) fonctionnent hors-ligne ;
- les **moteurs nécessitant des données externes** (Climate, GIS)
  disposent d'un mode dégradé documenté ;
- la **synchronisation** se fait quand la connexion revient, avec
  traçabilité des opérations hors-ligne.

---

## Article T-9 — Sécurité

- aucune donnée sensible en clair dans le code ou les logs ;
- les credentials sont en variables d'environnement ;
- les entrées utilisateur sont sanitizées aux frontières ;
- les requêtes sont paramétrées, jamais concaténées ;
- HTTPS en production, pas de fallback HTTP.

---

## Article T-10 — Dépendances

- toute dépendance externe doit être **justifiée** — que donne-t-elle
  que la stdlib ne donne pas ?
- les versions sont **épinglées** en production ;
- les CVE sont vérifiées avant ajout ;
- pas de dépendance flottante (`latest`, `*`) en production.

---

## Anti-Lois

Interdiction :
- de créer une architecture monolithique ;
- de créer un couplage fort entre moteurs ;
- de dupliquer une logique métier ;
- de créer une boîte noire ;
- de masquer une erreur ;
- de contourner la traçabilité pour la performance ;
- de livrer sans tests ;
- de modifier sans versionner.

---

## Déclaration finale

« Le code sert la connaissance. L'architecture sert la pérennité.
Aucun raccourci technique ne justifie de compromettre l'un ou
l'autre. »
