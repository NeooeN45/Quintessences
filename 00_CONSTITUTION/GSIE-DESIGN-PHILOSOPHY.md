# GSIE Design Philosophy

Livrable : 006 — Philosophie de conception
Édition : Première Édition
Version : 1.0 (Validated)
Statut : Validé par le Fondateur
Classification : Document transverse constitutionnel
Référence : Livrable 006 (GSIE-DIR-0003)
Lois fondatrices : GSIE-CON-003, GSIE-CON-006, GSIE-CON-007

---

## Objectif

Définir la manière officielle de concevoir GSIE. Cette philosophie guide
chaque décision d'architecture, chaque choix technologique et chaque
arbitrage entre approches concurrentes. Elle n'est pas consultative — elle
est opposable.

---

## Principes fondateurs

1. **La connaissance avant le code.** Le produit principal de GSIE est la
   connaissance, pas le logiciel. Le code sert la connaissance.
2. **La science avant l'opinion.** Aucune décision ne repose sur une
   préférence non justifiée. Toute affirmation est sourcée.
3. **La documentation avant l'implémentation.** Rien n'est codé avant
   d'être documenté. La documentation est le premier livrable.
4. **La modularité avant la complexité.** Chaque composant a une
   responsabilité unique. Le couplage est minimal.
5. **L'explicabilité avant la performance.** Un système rapide mais
   inexpliquable est un échec. Un système lent mais explicable est un
   prototype perfectible.
6. **La pérennité avant la rapidité.** GSIE est conçu pour durer des
   décennies. Un raccourci qui compromet la pérennité est rejeté.

---

## Règles d'architecture

- Chaque moteur possède **une responsabilité unique** (GSIE-CON-007).
- Les connaissances sont **indépendantes du code** — un changement de
  moteur ne détruit jamais une connaissance.
- Les interfaces sont **interchangeables** — un moteur peut être remplacé
  sans casser le système.
- Chaque décision est **documentée** — un ADR trace le contexte, la
  décision et ses conséquences.
- Le couplage entre moteurs est **minimal** — la communication se fait
  par contrats d'interface, jamais par accès direct.

---

## Test des 20 ans

Avant toute décision structurante, trois questions doivent trouver une
réponse positive :

1. **Sera-t-elle encore pertinente dans 20 ans ?** — si la décision est
   liée à une technologie éphémère, elle est reléguée à un ADR, pas à la
   Constitution.
2. **Est-elle documentée ?** — une décision non tracée n'existe pas.
3. **Est-elle explicable ?** — un nouveau contributeur doit pouvoir
   comprendre la décision en lisant la documentation, sans interroger
   l'auteur.

Ce filtre s'applique aux choix d'architecture, aux dépendances, aux
formats de données, aux conventions de nommage et aux règles métier. Il
ne s'applique pas aux choix d'implémentation locale (nom de variable,
structure de fonction) qui relèvent du standard de code.

---

## Exemples de décisions guidées par la philosophie

- **ForeFire en processus séparé** (GSIE-Ignis) : la frontière GPL est un
  choix de pérennité (principe 6) et de modularité (principe 4). Un
  couplage direct aurait été plus rapide mais aurait compromis la
  liberté commerciale à long terme.
- **14 moteurs indépendants** plutôt qu'un monolithe : modularité avant
  complexité (principe 4). Chaque moteur est testable, remplaçable et
  documentable isolément.
- **Documentation avant code en Phase 1** : documentation avant
  implémentation (principe 3). La Phase 1 produit la fondation
  documentaire ; le code viendra en Phase 4.

---

## Cas limites

- **Performance critique en opérationnel** : si un moteur doit être
  optimisé au détriment de l'explicabilité, l'optimisation est isolée
  dans un sous-composant documenté et l'interface publique reste
  explicable. L'optimisation ne dégrade jamais la traçabilité.
- **Données scientifiques contradictoires** : les deux sources sont
  conservées, le conflit est documenté (Constitution Scientifique S-3).
  La philosophie n'arbitre pas — elle exige que le conflit soit visible.
- **Fonctionnalité demandée mais non documentée** : la fonctionnalité
  est refusée tant qu'elle n'est pas spécifiée. La documentation précède
  l'implémentation (principe 3).

---

## Anti-patterns

- Choisir une technologie parce qu'elle est populaire sans justifier
  son apport.
- Optimiser prématurément au détriment de la lisibilité.
- Ajouter une dépendance externe sans vérifier les CVE et la pérennité
  du projet.
- Coder une règle métier sans l'avoir documentée au préalable.
- Créer un couplage fort entre deux moteurs pour « gagner du temps ».
- Présenter une estimation comme une certitude.

---

## Conséquences

Cette philosophie est opposable à tout contributeur, humain ou IA. Elle
guide les revues de code, les ADR et les RFC. Un arbitrage qui la
contredit doit être explicitement justifié et tracé.

---

## Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — version initiale (6 principes, test 20 ans) |
| 2026-07-12 | Enrichissement — conformité template RFC-0001, validation Fondateur |

---

## Validation

Validé par le Fondateur (Camille Perraudeau) le 2026-07-12. Ce document
ne peut être modifié que par un RFC dédié.
