# Audit de conformité des exigences — Baseline globale

| Champ | Valeur |
|---|---|
| Date | 2026-09-29 |
| Auditeur | Devin (assistant IA) |
| Statut | Draft — en attente de validation Fondateur |
| Type | Audit documentaire et code — baseline de conformité des exigences |
| Périmètre | Projet Quintessences complet : GEO-001 à GEO-005, IDENTITE-001, SITE-001/002, HUB-001 à 003, IGNIS-001 à 003, HUB_AND_APPS_PLAN, Constitutions GSIE, exigences transverses (RGPD, sécurité, gouvernance) |
| Sources d'exigences | `05_SPECIFICATIONS/`, `00_CONSTITUTION/`, `03_DECISIONS/` (DEC-000083 à 000088), `02_RFC/` |
| Sources de preuves | `REGISTRE_CAMPAGNES_RECETTE.md`, audits `23_QUALITY_MANAGEMENT/AUDITS/`, `PROJECT_MEMORY.md`, code réel (`GSIE/API`, `apps/GeoSylva`, `apps/Ignis`, `site-quintessences`, `Forge`) |
| Livrable associé | `23_QUALITY_MANAGEMENT/REGISTRE_CONFORMITE_EXIGENCES.md` |
| Décision associée | DEC-000089 (proposée) |

---

## 1. Objet

Établir une baseline vérifiable et datée de la conformité de **toutes les exigences
du projet Quintessences** face aux preuves disponibles au 2026-09-29. Cet audit
croise chaque exigence identifiée avec les preuves existantes et produit une
classification honnête : une spécification validée ou un composant présent ne
constitue pas une preuve de conformité.

## 2. Méthode

1. Inventaire des sources normatives (constitutions, spécifications, décisions,
   RFC, plan d'exécution).
2. Inventaire des preuves (registre de campagnes de recette, audits internes,
   rapports de tests, mémoire projet, inspections du code).
3. Croisement exigence ↔ preuve et classification selon la grille du registre vivant :
   `CONFORME`, `PARTIEL`, `NON DÉMARRÉ`, `NON MESURÉ`, `BLOQUÉ`, `DIFFÉRÉ`,
   `NON CONFORME`, `NON CONCLUANT`.
4. Niveau de preuve maximal atteint : N0 structurel (code/document existe),
   N1 local (tests unitaires/intégration ou recette locale), N2 TEST
   (environnement `gsie-test` Docker), N3 terrain/production (appareil réel
   ou environnement déployé).

Principe de prudence appliqué : une preuve locale n'est jamais extrapolée en
preuve de staging ou de production ; un critère coché dans une spécification
`Draft` n'est pas traité comme une validation.

## 3. Synthèse par domaine

| Domaine | Exigences | CONFORME | PARTIEL | NON DÉMARRÉ | NON MESURÉ | BLOQUÉ | DIFFÉRÉ |
|---|---|---|---|---|---|---|---|
| GEO-001 fonctionnel | 35 | 2 | 19 | 7 | 1 | 0 | 6 |
| GEO-002 non fonctionnel | 31 | 5 | 16 | 4 | 5 | 0 | 1 |
| GEO-004 Pl@ntNet | 22 | 0 | 3 | 15 | 0 | 4 | 0 |
| GEO-005 pilotage (G/L/CPT) | 35 | 12 | 8 | 15 | 0 | 0 | 0 |
| IDENTITE-001 | 52 | 37 | 15 | 0 | 0 | 0 | 0 |
| SITE-001 | 43 | 16 | 18 | 6 | 3 | 0 | 0 |
| HUB-001 | 44 | 2 | 0 | 0 | 0 | 0 | 42 |
| IGNIS-001/002 | 61 | 0 | 4 | 0 | 0 | 0 | 57 |
| Transverses (CON, RGPD, sécurité, gouvernance) | 14 | 5 | 8 | 0 | 0 | 1 | 0 |
| **Total** | **337** | **79** | **91** | **47** | **9** | **5** | **106** |

Lecture : hors périmètre différé (DEC-000083), le cœur V1 compte
**79 exigences conformes**, **91 partielles** et **47 non démarrées**.
Les 42 exigences Hub et 57 exigences Ignis sont majoritairement différées de la
phase 4, pas abandonnées.

## 4. Constatations majeures

### 4.1 Non-conformités et écarts critiques

1. **Pipeline scientifique GeoSylva non démarré.** GEO-F-01 à F-10 (ingestion
   LiDAR HD IGN, segmentation, cartes dendrométriques ONF, biomasse
   GEDI/ESA, suivi inter-annuel) n'ont aucune implémentation ni preuve. Les
   datasets correspondants sont planifiés (DS-001, DS-002, DS-003) mais aucun
   n'est téléchargé réellement.
2. **Chaîne de calcul climatique absente.** Les routes de cubage ne sont pas
   trouvées dans l'API (audit du 2026-09-07) ; aucune formule n'est branchée
   côté serveur. Les 357 tests Android réussis couvrent la couche app, pas la
   chaîne GSIE.
3. **Hub et Ignis hors chemin critique V1** (DEC-000083). Toute exigence de
   visualisation temps réel, PCG, Gaussian Splats, affichage incendie ou drone
   est reportée. Ne pas les présenter comme en implémentation.
4. **Pl@ntNet bloqué juridiquement.** Le schéma de données est livré (tranche 1)
   mais aucune intégration réelle n'est possible sans confirmation des
   conditions commerciales (19_LEGAL). Quatre exigences sont `BLOQUÉ`.
5. **Zone Compte et galerie du site public fermées par décision.** Les exigences
   correspondantes (F-010 à F-017) ne sont pas démarrées ; le blocage est
   volontaire jusqu'à validation juridique et autorisation Cloudflare.
6. **Goulots scientifiques et experts.** 30 scénarios GSIE-Bench sont
   `pending_expert_review` ; aucun dataset n'est promu production ; la
   qualification scientifique est le goulot majeur, pas le code.

### 4.2 Conformités substantielles établies

1. **Identité et RGPD compte.** IDENTITE-001 est le domaine le plus avancé :
   37 exigences `CONFORME` dont le cycle complet compte → export → suppression
   différée → finalisation (compte synthétique, CPT-16 PASS PARTIEL). Limites :
   Google réel non recetté (retourne `not_configured`), isolation deux comptes
   sur même appareil et purge locale ouvertes.
2. **Socle API sécurisé.** JWT RS256, Argon2id, rate limiting, anti-énumération,
   RLS sans DELETE, audit logs, migrations appliquées jusqu'à `20260826_0055`
   (env `gsie-test`). Aucune preuve de déploiement staging distant.
3. **Site public structuré et vérifiable.** 13 routes Astro, `verify:public`
   automatisé, Turnstile serveur, mentions légales présentes mais placeholders
   bloquants ; la zone Compte et la galerie sont fermées conformément aux
   décisions.
4. **Forge et acquisition.** Handoff IFN livré et testé (251/251 tests),
   contrat `forge_analysis_bundle.v1` validé, quarantaine TEST fonctionnelle ;
   aucun téléchargement réel ni promotion production.

### 4.3 Exigences partielles représentatives

| Exigence | État | Écart résiduel |
|---|---|---|
| GEO-F-03 attributs dendro | PARTIEL | Ambiguïté diamètre moyen/quadratique non résolue ; extraction LiDAR par arbre absente |
| GEO-F-18 offline-first | PARTIEL | Fonctionnalités hors ligne non exhaustives ; file d'attente et packs présents |
| GEO-F-20 sync différée | PARTIEL | Contrats sync testés ; E2E appareil → API non prouvé |
| ID-F-005/006 Google | PARTIEL | Refus faux jeton prouvé ; configuration Google Cloud réelle absente |
| ID-F-026 finalisation | PARTIEL | Fonction SQL prouvée sur compte synthétique ; smoke test worker destructeur ouvert |
| SITE-F-006 indicateurs | NON DÉMARRÉ | Endpoint public absent ; remplacé par repères éditoriaux |
| SEC-* transverse | PARTIEL | 24 CVE connus (6 HIGH) ; escalade pyjwt en attente |

## 5. Exigences hors périmètre V1

Les décisions DEC-000083 et suivantes retirent du chemin critique de la phase 4 :
- **Hub** (visualisation, PCG, Splats, couches multi-domaines) : 42 exigences
  `DIFFÉRÉ`. L'environnement UE 5.8 + Cesium est configuré (N0), aucune
  implémentation n'est revendiquée.
- **Ignis** (détection, propagation, drones, simulation) : 57 exigences
  `DIFFÉRÉ`. Les seules preuves sont de banc : ForeFire compilé, PX4 SITL 5 vols,
  lawnmower exécuté, RTH partiel.
- **Aeris, Atlas, Terra, QGISIA** : scaffolding activé (DEC-000056) sans
  spécification propre d'exigences à auditer dans cette baseline.

## 6. Recommandations

1. **Priorité P1 — Clôturer G1 GeoSylva.** Finir l'interface 3.0 et la recette
   G1 (saisie → synchronisation → affichage) avant toute expansion scientifique.
2. **Priorité P1 — Lever le blocage Pl@ntNet.** Trancher la confirmation
   commerciale ou décider d'un retrait explicite de GEO-004.
3. **Priorité P2 — Finir G2 identité/RGPD.** Recetter Google réel, la purge
   locale, l'isolation deux comptes et le smoke test du worker de suppression.
4. **Priorité P2 — Documenter les choix de staging.** Choisir le fournisseur
   (CON-008) et préparer l'environnement `gsie-staging` pour les preuves N2→N3.
5. **Priorité P3 — Scientifique.** Lancer la revue experte GSIE-Bench et
   télécharger au moins un dataset réel (DS-001 ou DS-003) pour sortir le
   pipeline scientifique du `NON DÉMARRÉ`.
6. **Ne pas présenter les exigences `DIFFÉRÉ` comme en retard.** Elles sont
   explicitement hors périmètre V1 ; les réintégrer nécessitera une décision.

## 7. Limites de l'audit

- Audit documentaire et code au 2026-09-29 ; ne constitue pas une recette.
- Les statuts `CONFORME` reflètent le niveau de preuve indiqué (colonne
  `Niveau` du registre vivant) ; aucun ne vaut validation scientifique ou
  production sauf mention explicite.
- Les applications `apps/GeoSylva`, `apps/QGISIA` et `Forge` ont leur propre
  Git ; l'audit s'appuie sur les états remontés dans la mémoire et les
  audits internes, pas sur une inspection systématique de chaque commit.
- Les exigences `NON MESURÉ` n'ont pas de métrique instrumentée ; ce n'est ni
  une conformité ni une non-conformité.

## 8. Registre vivant

Le détail par exigence (337 lignes) est maintenu dans
`23_QUALITY_MANAGEMENT/REGISTRE_CONFORMITE_EXIGENCES.md`. Ce registre sera
mis à jour à chaque campagne de recette, décision ou livraison majeure ;
la présente baseline sert de point de comparaison daté.
