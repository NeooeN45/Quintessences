# FOUNDER_JOURNAL — Journal du fondateur

| Champ | Valeur |
|---|---|
| **Fondateur** | Camille Perraudeau |
| **Créé le** | 2026-07-01 |

---

## 2026-07-01 — Fondation du projet GSIE
**Décisions** : `GSIE-DIR-0001` (Directive fondatrice, ACTIVE) ; `DEC-000001`
(GSIE est une Fondation scientifique) ; `DEC-000002` (Phase 1 : Fondation, aucun
développement métier). Constitution amorcée : 6 documents transverses + 100
articles vides, RFC-0001 à RFC-0010 créées (RFC-0001 rédigée).
**Motivations** : formaliser la vision — GSIE n'est pas une application Android,
c'est une plateforme scientifique. GeoSylva Mobile n'est qu'une interface ; le
moteur est le produit. La connaissance est le véritable produit.
**Impact** : entrée officielle en Phase 1 — Fondation. Aucun développement
métier. Arborescence officielle (22 dossiers numérotés) et mémoire du projet
créées.

---

## 2026-07-03 — Configuration Claude Code, skills et outillage
**Décisions** : initialisation du dépôt git + `.gitignore` ; création de
`CLAUDE.md` (gouvernance opérationnelle pour les agents IA) ; mise en place de
`.claude/` (`settings.json`, hook `guard-locked` protégeant les `Locked`,
6 commandes métier, 3 sous-agents, skill projet `gsie-governance`).
**Motivations** : outiller le respect de la gouvernance dès le départ — la
Constitution prime, les `Locked` sont inviolables hors RFC, aucune décision ne
doit être perdue. La skill `gsie-governance` s'auto-déclenche dès qu'on touche un
document GSIE.
**Impact** : installation vendorisée et épinglée de la skill `mermaid` (MIT,
commit `8ab1815`, provenance tracée) ; création de la skill `skill-management` ;
`.claude/SKILLS_GSIE.md` sélectionnant les meilleures skills par phase. En
Phase 1, aucune skill ne produit de code métier.

---

## 2026-07-06 — Audit de conformité et ouverture de RFC-0002
**Décisions** : cartographie complète du dépôt (277 fichiers `.md`) confrontée
au ROADMAP et à la mémoire ; correction des en-têtes non conformes au cycle de
vie (`GSIE-CON-005` à `GSIE-CON-010`, `PACT_FOR_AI_AGENTS.md`, `GSIE-DESIGN-PHILOSOPHY.md`) ;
traçabilité de `GSIE-DIR-0004` (GSIE Genesis Directive, ACTIVE) ajoutée à la
mémoire. Ouverture de **RFC-0002** « Unification du système d'articles
constitutionnels » (double système `ARTICLE_0xx` vides / `GSIE-CON-0xx` rédigés).
**Motivations** : l'audit révèle des écarts de traçabilité et de conformité. Le
double système d'articles crée une ambiguïté qu'il faut lever. Aucun document
`Locked` n'a été modifié.
**Impact** : `RFC-0003` à `RFC-0010` remplacés par des en-têtes « Réservé — non
ouvert » (traçabilité conservée). Livrables 011 et 012 amorcés (fichiers de
`GSIE/DOCUMENTATION/` rédigés en Draft ; `CONTEXT_SNAPSHOT_001.md` réservé).
ROADMAP mis à jour (livrable 010 repointé vers `GSIE-CON-0xx`, moteurs
requalifiés honnêtement).

---

## 2026-07-07 — RFC-0003 GSIE-Net et livrables 005-009 en Review
**Décisions** : ouverture de **RFC-0003** « Architecture distribuée GSIE-Net » —
capture la vision fondateur sur l'architecture offline-first, multi-couches,
distribuée et orientée données (activé en Phase 2). Passage des livrables 005 à
009 de `Draft` à `Review` (soumis à la validation du Fondateur).
**Motivations** : la vision d'architecture distribuée doit être capturée
formellement avant qu'elle ne se perde. Les cinq livrables constitutionnels
transverses (Pacte IA, Design Philosophy, Constitutions scientifique/technique/IA)
sont rédigés et prêts pour revue.
**Impact** : `PROJECT_MEMORY.md` mis à jour (avancement Review 5/12, RFC-0003
tracé) ; `ROADMAP.md` mis à jour (statuts livrables + RFC-0003 + prochaine
étape).

---

## 2026-07-11 — Ouverture de RFC-0004 Ignis
**Décisions** : ouverture de **RFC-0004** « Ignis : Système autonome de
surveillance et d'analyse des incendies » — nouvelle branche fonctionnelle
dédiée au risque incendie, positionnée comme application cliente des 14 moteurs
GSIE. Création de `apps/Ignis/REGISTRE.md` : registre vivant des idées
Ignis (60+ idées en 9 sections).
**Motivations** : le risque incendie est un domaine d'application à fort impact
pour GSIE. La proposition adopte une approche hybride — Ignis comme
application, extensions ciblées des moteurs existants, moteur dédié éventuel
réservé à un second RFC. Démonstrateur visé : incendie de Landiras (Gironde,
2022), sans drone.
**Impact** : `PROJECT_MEMORY.md` synchronisé (RFC-0004 référence le registre) ;
`02_RFC/RFC-0004.md` créé avec exigences (sourçage scientifique, métriques
domaine, cadre réglementaire EASA/SORA/BVLOS/DGAC/RGPD), écosystème
(Pyronear, ForeFire, SDIS/CODIS, Prométhée) et points de vigilance. Aucun
développement métier en Phase 1.

---

## 2026-07-12 — Adoption RFC-0004, validation 005-009 et articles CON-001 à 010
**Décisions** : **RFC-0004 ADOPTÉ** — `DEC-000003` tracée (Ignis devient
officiellement une branche fonctionnelle de GSIE, approche hybride Option C
retenue). Livrables 005 à 009 passent de `Review` à **Validated** après audit et
enrichissement par le Fondateur. Articles `GSIE-CON-001` à `GSIE-CON-010` mis en
conformité (template RFC-0001) et validés.
**Motivations** : les cinq livrables transverses étaient solides mais
nécessitaient les sections Objectif, Historique et Validation pour être
conformes au template. Les articles constitutionnels 001 à 010 devaient suivre
le même template (Références + Historique). L'adoption de RFC-0004 formalise
l'engagement de GSIE sur le risque incendie.
**Impact** : avancement Phase 1 — 7/12 Validated, 3/12 Locked, 2/12 Draft (010
désormais Validated, reste 011 et 012). Corrections de gouvernance Ignis
appliquées (statut ✅ redéfini, phases renommées « Jalon 0-6 » pour éviter la
collision avec les phases GSIE globales). Sous-dossier
`apps/Ignis/` créé pour les livrables du Jalon 0. Pack contexte
agent archivé (le code du banc vit hors dépôt, dans `~/Ignis/` WSL2).

---

> Chaque session ou décision significative ajoute une entrée datée.
