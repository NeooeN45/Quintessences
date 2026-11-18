# DRAFT — PROJECT_MEMORY en tableau de bord (proposition de format)

| Champ | Valeur |
|---|---|
| **Statut** | Draft — proposition de remplacement du corps de `PROJECT_MEMORY.md` racine |
| **Date** | 2026-09-02 |
| **Origine** | Audit `23_QUALITY_MANAGEMENT/AUDITS/2026-09-02_ANALYSE_ETAT_ET_VISION.md` §7.5 (constat C-02) |
| **Règle d'adoption** | Si validé : ce contenu devient `PROJECT_MEMORY.md` ; le journal chronologique actuel est déplacé intégralement vers `22_PROJECT_MEMORY/JOURNAL_2026-07_2026-08.md` sans réécriture. Tant qu'il n'est pas validé, `PROJECT_MEMORY.md` racine reste la seule mémoire canonique. |

> Principe : une page, lisible en deux minutes par un humain ou un agent avant
> toute tâche. **L'état, pas l'historique.** Chaque ligne porte son niveau de
> preuve. L'historique vit dans le journal et dans `CHANGELOG.md`.

---

## Niveaux de preuve (vocabulaire imposé)

| Niveau | Signification | Ne vaut pas |
|---|---|---|
| **N0 — structurel** | Module, schémas, routeur et tests de contrat existent | fonctionnement sur donnée réelle |
| **N1 — prouvé local** | Tests unitaires/mutation verts sur le poste, sans réseau ni base réelle | persistance, intégration |
| **N2 — prouvé sur TEST** | Vérifié sur PostgreSQL/PostGIS/MinIO réels (`database_role=test`) et/ou sur données fournisseur réelles bornées | SLO de production, validation métier |
| **N3 — prouvé terrain** | Utilisé par un forestier sur une parcelle réelle, résultat relu par un expert | rien de plus : c'est l'objectif V1 |

---

## 1. Où en est le projet

| Champ | Valeur |
|---|---|
| Phase | 4 — Implémentation (DEC-000017, GSIE-DIR-0011) |
| Pilote V1 | GeoSylva 3.0 → 3.1 (DEC-000074) ; document d'exécution GEO-005 |
| Gel Horizon 2 | DEC-000083 (Proposé) — Hub Unreal, Mesh, LLM, LoRa, WeatherNext, apps secondaires, Orchestre |
| Dernière décision | DEC-000083 (2026-09-02, Proposé) ; dernière Validée : DEC-000082 (cubage offline-first, 2026-08-31) |
| Mise à jour | 2026-09-02 |

## 2. Gates V1 (GEO-005)

| Gate | Objet | Statut | Preuve | Bloqueur principal |
|---|---|---|---|---|
| G0 | Réconciliation et gel du périmètre | **Clos** (réconciliation uniquement) | `AUDITS/2026-08-29_G0_RECONCILIATION_GEOSYLVA.md` | — |
| G1 | GeoSylva 3.1 utilisable localement | Ouvert | Parcours natif compte/consentements N2 ; cubage offline-first en cours (RFC-0042 Review) | Recette martelage complet sur S25 ; suite Android non rejouée en entier |
| G2 | Compte Quintessences + RGPD | Ouvert | Création, connexion, export, sessions, e-mail, récupération, consentements, finalisation serveur (CPT-16) : N2 | Google OAuth non configuré ; purge locale complète ; isolation multi-compte in-app ; smoke worker |
| G3 | Data Acquisition Fabric | Non démarré | Handoff Forge → Registry N2 ; SoilGrids WCS qualifié (DEC-000078) ; FETCH fermé | Aucune acquisition réelle exécutée |
| G4 | Verticale GeoSylva ↔ GSIE | Non démarré | Préparation serveur N2 (`StationPreparationService`) | RFC-0041 / DEC-000073 non validées ; `station-link` absent ; client Kotlin absent |
| G5 | Boucle d'amélioration | Non démarré | GSIE-Bench Open/Silver N1 ; runner durci | 30 scénarios Gold `pending_expert_review` ; aucun expert nommé |

## 3. Les 14 moteurs — niveau de preuve courant

| Moteur | Niveau | Détail |
|---|---|---|
| Evidence | N1 | Cœur Rust + PyO3, 122 tests Python + 41 Rust |
| Knowledge | N2 | Ingestion `accepted`, versionnement CON-010, qualificateurs/versions persistés sur PostgreSQL |
| Correlation | N1 | Tests cœur |
| Reasoning | N1 | Tests cœur |
| Diagnostic | N1 | Propagation du niveau de preuve vers Recommendation |
| Recommendation | N1 | Tests cœur |
| Validation | N2 | Reçoit la session DB via l'orchestration ; sorties bloquées/partielles persistées |
| GIS | N1 | Client IGN résilient ; aucune donnée persistée |
| Climate | N1 | Clients Météo-France (AROME, DPClim, SYNOP, Vigilance, PaquetObs) ; aucune donnée persistée |
| Pedology | N1 → N2 partiel | `SoilGridsWcsClient` avec GeoTIFF borné ; un actif RAW de 569 octets rejoué (DEC-000061) ; FETCH fermé |
| Botanical | N1 | GBIF / TAXREF ; adapters Registry qualifiés, FETCH fermé |
| Forest Dynamics | N1 | Tests cœur |
| Learning | N0/N1 | Aucun modèle, aucun entraînement autorisé (RFC-0039) |
| Simulation | N1 | Tests cœur |
| **Orchestration** (transverse) | **N2** | `analysis_run` append-only, hydratation stationnelle fail-closed, préparation serveur, couverture 100 % du package |

**Aucun moteur n'est N3.** Contrat structurel automatisé : 14/14 (N0).

## 4. Données et connaissance

| Élément | État | Niveau |
|---|---|---|
| Data Registry | 36 ressources catalogue `metadata_only`, 4 datasets `discovered`, 1 DataAsset RAW | N2 |
| FETCH | Fermé pour toutes les sources ; SoilGrids WCS qualifié et prêt | — |
| Handoff Forge → Registry | `gsie_acquisition_handoff.v1`, `forge_analysis_bundle.v1` importé en quarantaine TEST (DEC-000081) | N2 |
| Connaissances validées | 25 (Phase 3) ; règles `accepted` avec qualificateurs | N2 |
| GSIE-Bench | 30 scénarios candidats Gold `pending_expert_review` ; 3 Silver synthétiques exécutables ; baseline déterministe `GO` | N1 |
| Ressources locales `E:\Documents` | 3 077 ressources logiques inventoriées, aucune ingérée | metadata |

## 5. Applications

| App | État | Niveau |
|---|---|---|
| GeoSylva | 3.0.0 sur S25 Ultra ; compte natif relié ; cubage offline-first en implémentation | N2 (recette ADB, comptes synthétiques) |
| API GSIE | 29 routeurs, 56 migrations, HA prouvée en CI (6 000/6 000, p95 ~165 ms) | N2 |
| Site public Astro | Build vert 13 routes ; `verify:public` bloque (mentions légales) ; domaine sert encore l'ancienne landing ; API publique 530 | N1 |
| Admin web | `/data` lit le catalogue réel | N2 |
| Forge | 251 tests ; exporteurs de bundles | N1 |
| Ignis, QGISIA, Hydro, Flora, Artemis, Aeris, Atlas, Terra | Gelées Horizon 2 (DEC-000083 Proposé) | — |

## 6. Blockers actifs (par ordre d'impact)

1. **Aucun expert forestier externe** identifié pour la relecture GSIE-Bench Gold (bloque G5 et la thèse scientifique).
2. **Aucune donnée réelle** dans le Registry (bloque G3 et tout N2 « donnée fournisseur » des moteurs domaine).
3. **Aucun usage terrain** de GeoSylva (bloque tout N3).
4. RFC-0041 / DEC-000073 non validées (bloque G4).
5. Google OAuth non configuré ; mentions légales incomplètes (bloque G2 et la mise en ligne publique).
6. 83 fichiers non suivis dont neuf documents de gouvernance et six migrations (risque de perte).

## 7. Cinq dernières décisions

| DEC | Date | Objet | Statut |
|---|---|---|---|
| DEC-000083 | 2026-09-02 | Gel Horizon 2 | Proposé |
| DEC-000082 | 2026-08-31 | Cubage offline-first GeoSylva (ex-DEC-000078 renuméroté) | Validé |
| DEC-000081 | 2026-08-31 | Import persistant des bundles Forge en quarantaine TEST | Implémenté |
| DEC-000080 | 2026-08-31 | Contrat extensible des paramètres Forge → GSIE | Validé |
| DEC-000079 | 2026-08-30 | Matrice durable des dépendances moteurs et sources | Validé |

## 8. Prochaine action unique

> Scinder et committer le WIP courant, puis lancer la recette G1 martelage sur
> S25 Ultra. Aucune nouvelle couche avant.

## 9. Règles de maintenance de cette page

- Mettre à jour **l'état**, ne jamais ajouter de paragraphe narratif : le
  récit va dans `22_PROJECT_MEMORY/JOURNAL_*.md` et `CHANGELOG.md`.
- Toute cellule « Niveau » cite implicitement une preuve reproductible ; en
  cas de doute, rétrograder d'un niveau.
- Une ligne ne monte de niveau que par une DEC ou un audit déposé dans
  `23_QUALITY_MANAGEMENT/AUDITS/`.
- Longueur cible : ≤ 150 lignes.
