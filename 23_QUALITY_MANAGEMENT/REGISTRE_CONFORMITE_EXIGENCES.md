# Registre de conformité des exigences — Quintessences / GSIE

| Champ | Valeur |
|---|---|
| Statut | Draft — registre vivant, référence unique de conformité |
| Créé | 2026-09-29 |
| Responsable | Devin (assistant IA) — sous autorité du Fondateur |
| Baseline | `AUDITS/2026-09-29_CONFORMITE_EXIGENCES_BASELINE.md` |
| Décision | DEC-000089 (proposée) |

---

## 1. Rôle

Ce registre est la **source de vérité vivante** de l'état de conformité de
chaque exigence du projet. Il complète `REGISTRE_CAMPAGNES_RECETTE.md` (qui
trace les campagnes de recette, pas le statut par exigence). Une ligne ne
passe en `CONFORME` que sur preuve référencée ; une preuve locale n'est
jamais extrapolée en preuve de staging ou de production.

## 2. Statuts et niveaux de preuve

**Statut de conformité :**
`CONFORME` — critère satisfait par une preuve référencée ·
`PARTIEL` — sous-périmètre prouvé, portes ouvertes ·
`NON DÉMARRÉ` — aucune implémentation ni preuve ·
`NON MESURÉ` — métrique non instrumentée ·
`BLOQUÉ` — dépendance externe non levée ·
`DIFFÉRÉ` — hors périmètre V1 par décision (DEC-000083) ·
`NON CONFORME` — écart constaté ·
`NON CONCLUANT` — preuve insuffisante pour trancher.

**Niveau de preuve maximal :**
`N0` structurel (code/document existe) · `N1` local (tests ou recette locale)
· `N2` TEST (environnement `gsie-test` Docker) · `N3` terrain/production
(appareil réel ou déploiement).

**Maintenance :** mise à jour à chaque campagne de recette, décision ou
livraison majeure ; la colonne « Preuve » doit citer un rapport, un audit,
un test ou un commit daté — jamais une affirmation non traçable.

---

## 3. GEO-001 — GeoSylva fonctionnel (35 exigences)

| ID | Exigence | Statut | Preuve / niveau | Écart résiduel |
|---|---|---|---|---|
| GEO-F-01 | Ingestion LiDAR HD IGN | NON DÉMARRÉ | — | Aucun téléchargement réel (DS-002) |
| GEO-F-02 | Segmentation arbres LiDAR | NON DÉMARRÉ | — | Pas de pipeline |
| GEO-F-03 | Attributs dendro par arbre | PARTIEL | 357 tests Android — N1 | Ambiguïté diamètre moyen/quadratique ; extraction LiDAR absente |
| GEO-F-04 | Essences (BD Forêt, Crown-BERT, TAXREF) | PARTIEL | TAXREF résolu (`resolve_taxref`) — N1 | Fusion BD Forêt / Crown-BERT absente |
| GEO-F-05 | Cartographie peuplements BD Forêt | NON DÉMARRÉ | — | DS-001 planifié |
| GEO-F-06 | Type/structure/composition peuplement | PARTIEL | Modèle local parcelles app — N1 | Caractérisation IGN non branchée |
| GEO-F-07 | Cartes dendro 700 m² exportables ONF | NON DÉMARRÉ | — | — |
| GEO-F-08 | Biomasse LiDAR | NON DÉMARRÉ | — | — |
| GEO-F-09 | Biomasse GEDI / ESA Biomass CCI | NON DÉMARRÉ | — | Datasets non qualifiés |
| GEO-F-10 | Suivi inter-annuel quantifié | NON DÉMARRÉ | — | Dépend F-01/F-08 |
| GEO-F-11 | Diagnostic sylvicole explicable | PARTIEL | DiagnosticEngine + tests chaîne — N1 | Jamais exécuté sur données réelles ; bench en revue experte |
| GEO-F-12 | Recommandations structurées | PARTIEL | RecommendationEngine + tests — N1 | Aucune recommandation réelle validée |
| GEO-F-13 | Validation forestier avec traçabilité | PARTIEL | Martelage humain par conception app — N1 | Versioning runs non branché (audit 2026-09-07) |
| GEO-F-14 | Couches `geosylva.*` dans le Hub | DIFFÉRÉ | — | DEC-000083 — Hub hors V1 |
| GEO-F-15 | Peuplements procéduraux PCG | DIFFÉRÉ | — | DEC-000083 |
| GEO-F-16 | Gradient de fidélité visuelle | DIFFÉRÉ | — | DEC-000083 |
| GEO-F-17 | Gaussian Splats | DIFFÉRÉ | — | DEC-000083 |
| GEO-F-18 | Offline-first 100 % | PARTIEL | App offline, file parcelles, packs territoriaux — N1 | Exhaustivité 100 % non démontrée |
| GEO-F-19 | Saisie inventaire mobile | PARTIEL | App v3.0 installée S25, parcours présent — N3 | Recette complète G1 non clôturée |
| GEO-F-20 | Sync différée avec gestion conflits | PARTIEL | ParcelSync + contrats testés — N1 | E2E appareil → API non prouvé |
| GEO-F-21 | GPS + cartographie terrain | PARTIEL | Présent app, filtre MAD — N1 | Non re-prouvé en phase 4 |
| GEO-F-22 | Basculer état réel ↔ simulé | PARTIEL | SimulationEngine existe — N0 | Séparation en usage non démontrée |
| GEO-F-23 | Convention `simulated.*` | PARTIEL | Convention HUB-002 — N0 | Hub absent |
| GEO-NF-01 | Android 8+, Kotlin, Compose | CONFORME | App existante — N0 | — |
| GEO-NF-02 | Fonctionnement hors ligne | PARTIEL | cf. F-18 — N1 | — |
| GEO-NF-03 | Synchronisation différée | PARTIEL | cf. F-20 — N1 | — |
| GEO-NF-04 | Sécurité mobile (SQLCipher, biométrie) | PARTIEL | SQLCipher actif déclaré — N1 | Biométrie/PIN à confirmer |
| GEO-NF-05 | GPS < 5 m terrain | PARTIEL | Filtre MAD déclaré — N1 | Précision non mesurée terrain |
| GEO-NF-06 | Performance app (temps réponse) | NON MESURÉ | — | Pas de benchmark |
| GEO-NF-07 | Rendu Hub fluide | DIFFÉRÉ | — | DEC-000083 |
| GEO-NF-08 | Latence API → Hub | DIFFÉRÉ | — | DEC-000083 |
| GEO-NF-09 | API REST/WebSocket | PARTIEL | Endpoints existent — N0 | WS Hub non branché |
| GEO-NF-10 | SRS Lambert-93 / WGS84 / 4978 | PARTIEL | SRID 2154 utilisé (préparation) — N1 | Chaîne complète multi-SRS non prouvée |
| GEO-NF-11 | Traçabilité couches/données | PARTIEL | Provenance dans moteurs — N0 | Journalisation bout-en-bout absente |
| GEO-NF-12 | Modularité app / moteur | CONFORME | Repos séparés, API client — N0 | — |

## 4. GEO-002 — GeoSylva non fonctionnel (31 exigences)

| ID | Exigence | Statut | Preuve / niveau | Écart résiduel |
|---|---|---|---|---|
| GEO-OFF-01 | Cache hors ligne < 2 Go | NON MESURÉ | — | Pas de mesure |
| GEO-OFF-02 | File de sync persistante | PARTIEL | File parcelles présente — N1 | Persistance après redémarrage non prouvée |
| GEO-OFF-03 | Gestion de conflits versionnée | PARTIEL | Contrats sync — N1 | Conflit réel non exercé |
| GEO-OFF-04 | GPS actif < 5 m | PARTIEL | Filtre MAD — N1 | Mesure terrain absente |
| GEO-RES-01 | Reprise session après coupure | PARTIEL | Refresh session prouvé 2026-08-29 — N2 | Cas limites ouverts |
| GEO-RES-02 | Mode dégradé ZICAD | NON DÉMARRÉ | — | Lié Hub |
| GEO-RES-03 | Reprise sync après réseau | PARTIEL | Queue + retry — N1 | Non prouvé E2E |
| GEO-SEC-01 | JWT RS256 (15 min / 7 j) | CONFORME | Implémenté et testé — N2 | — |
| GEO-SEC-02 | TLS 1.3 | PARTIEL | Build stricte — N0 | Production non déployée |
| GEO-SEC-03 | Rôles métier (forestier/ONF) | PARTIEL | RBAC API — N1 | Rôles métier non déployés |
| GEO-SEC-04 | Conformité RGPD | PARTIEL | Cycle compte en cours — N2 | G2 ouvert, conservation juridique à confirmer |
| GEO-SEC-05 | Aucun secret en dur | CONFORME | Audits + pentest 2026-08-07 — N1 | — |
| GEO-INT-01 | Export GeoJSON | PARTIEL | Format défini — N0 | Export réel non exercé |
| GEO-INT-02 | 3D Tiles 1.1 | NON DÉMARRÉ | — | Lié Hub |
| GEO-INT-03 | LAZ/LAS | NON DÉMARRÉ | — | Lié pipeline LiDAR |
| GEO-INT-04 | GeoTIFF COG | PARTIEL | SoilGrids GeoTIFF borné — N1 | Chaîne complète non démontrée |
| GEO-INT-05 | Conversions SRS | CONFORME | 2154/4326/4978 utilisés — N1 | — |
| GEO-INT-06 | Contrats API GSIE | PARTIEL | Contrats sync/existence — N1 | Couverture incomplète |
| GEO-INT-07 | Contrat Hub HUB-002 | DIFFÉRÉ | — | DEC-000083 |
| GEO-INT-08 | App cliente API | PARTIEL | ParcelSync fonctionnel — N1 | Inventaire API non exhaustif |
| GEO-EXP-01 | Provenance données | PARTIEL | Moteurs tracent provenance — N1 | Bout-en-bout non démontré |
| GEO-EXP-02 | Décision humaine contournable | CONFORME | Par conception (CON-001) — N0 | — |
| GEO-EXP-03 | Journalisation audit | PARTIEL | `audit_log` serveur — N1 | Couverture actions app à compléter |
| GEO-ACC-01 | Navigation ≤ 3 niveaux | PARTIEL | Passe UX — N0 | Non recetté |
| GEO-ACC-02 | Lisibilité extérieure | PARTIEL | Contrastes renforcés — N1 | Non mesuré terrain |
| GEO-ACC-03 | Gestes terrain simplifiés | NON MESURÉ | — | — |
| GEO-ACC-04 | Utilisation gant/pluie | NON MESURÉ | — | — |
| GEO-002 §2 | Performance appareil | NON MESURÉ | — | Pas de benchmark |
| GEO-002 §2.2 | Capacité volumétrique | NON MESURÉ | — | — |
| GEO-002 §7 | Licences et souveraineté données | CONFORME | Licences documentées 19_LEGAL — N0 | — |
| GEO-002 §9 | Scalabilité API/moteurs | NON DÉMARRÉ | — | Pas de test de charge |

## 5. GEO-004 — Identification botanique Pl@ntNet (22 exigences)

| ID | Exigence | Statut | Preuve / niveau | Écart résiduel |
|---|---|---|---|---|
| GEO-ID-01 | Capture photo guidée mobile | NON DÉMARRÉ | — | Tranche 2 |
| GEO-ID-02 | Appel API Pl@ntNet | BLOQUÉ | — | Conditions commerciales à confirmer (19_LEGAL) |
| GEO-ID-03 | Confidentialité GPS | BLOQUÉ | — | Tranche 2 bloquée |
| GEO-ID-04 | Rétention limitée serveur | BLOQUÉ | — | Tranche 2 bloquée |
| GEO-ID-05 | Affichage résultats + confiance | NON DÉMARRÉ | — | — |
| GEO-ID-06 | Association résultat → arbre | NON DÉMARRÉ | — | — |
| GEO-ID-07 | Correction manuelle essence | NON DÉMARRÉ | — | — |
| GEO-ID-08 | Historique identifications | NON DÉMARRÉ | — | — |
| GEO-ID-09 | Mode hors ligne file d'attente | NON DÉMARRÉ | — | — |
| GEO-ID-10 | Schéma données identifications | PARTIEL | Tables request/result livrées — N0 | Tranche 1 |
| GEO-ID-11 | Quotas et rate limiting | BLOQUÉ | — | Dépend de l'accord commercial |
| GEO-ID-12 | Traçabilité requêtes | PARTIEL | Schéma prévu — N0 | Exécution absente |
| GEO-ID-13 | Journalisation décisions | PARTIEL | Table decision — N0 | — |
| GEO-ID-14 | Fallback essence inconnue | NON DÉMARRÉ | — | — |
| GEO-ID-15 | Intégration workflow inventaire | NON DÉMARRÉ | — | — |
| GEO-ID-16 | Consentement utilisateur | NON DÉMARRÉ | — | — |
| GEO-ID-NF-01 | Quota mensuel respecté | BLOQUÉ | — | Accord commercial absent |
| GEO-ID-NF-02 | Latence API < seuil | BLOQUÉ | — | Non mesurable sans accord |
| GEO-ID-NF-03 | Clé serveur non embarquée | NON DÉMARRÉ | — | Design acté, code absent |
| GEO-ID-NF-04 | Taille photo optimisée | NON DÉMARRÉ | — | — |
| GEO-ID-NF-05 | Précision identification | NON DÉMARRÉ | — | Nécessite benchmark terrain |
| GEO-ID-NF-06 | Coût maîtrisé | NON DÉMARRÉ | — | Dépend accord |

## 6. GEO-005 — Pilotage et recette (35 exigences)

| ID | Exigence | Statut | Preuve / niveau | Écart résiduel |
|---|---|---|---|---|
| GEO-G0 | Gate 0 réconciliation | CONFORME | Clôturé — N2 | — |
| GEO-G1 | Gate 1 interface 3.0 | PARTIEL | En cours, 357 tests — N1 | Recette non clôturée |
| GEO-G2 | Gate 2 identité/RGPD | PARTIEL | Preuves API substantielles — N2 | Google, purge, isolation, worker ouverts |
| GEO-G3 | Gate 3 acquisition données | PARTIEL | Handoff IFN testé — N1 | Aucun téléchargement réel |
| GEO-G4 | Gate 4 façade GSIE | NON DÉMARRÉ | — | Subordonné RFC-0041/DEC-000073 |
| GEO-G5 | Gate 5 lancement | NON DÉMARRÉ | — | — |
| GEO-CPT-01 | Inscription | CONFORME | Validée API + UI — N2 | — |
| GEO-CPT-02 | Erreurs bornées | PARTIEL | Cas partiels — N1 | Couverture exhaustive à prouver |
| GEO-CPT-03 | Connexion/déconnexion | CONFORME | Prouvée S25 + API — N2 | — |
| GEO-CPT-04 | Rotation refresh | PARTIEL | Refresh invalide → purge prouvée — N2 | Rotation acceptée une fois non formalisée |
| GEO-CPT-05 | Vérification e-mail | CONFORME | Mailpit + code — N2 | — |
| GEO-CPT-06 | Récupération mot de passe | CONFORME | Anti-énumération + révocation — N2 | — |
| GEO-CPT-07 | Google réel | NON DÉMARRÉ | — | Config Google Cloud absente |
| GEO-CPT-08 | Liaison Google | NON DÉMARRÉ | — | Dépend CPT-07 |
| GEO-CPT-09 | Google non configuré refusé | CONFORME | `not_configured` retourné — N2 | — |
| GEO-CPT-10 | Profil consultable/modifiable | CONFORME | Profil relu, nom rectifié — N2 | — |
| GEO-CPT-11 | Consentements | CONFORME | Acceptés/révoqués, historisés — N2 | — |
| GEO-CPT-12 | Sessions consultables/révocables | CONFORME | Liste + isolation B — N2 | Révocation inter-compte à formaliser |
| GEO-CPT-13 | Export données | CONFORME | Export lisible sans secret — N2 | Comparaison inventaire non formalisée |
| GEO-CPT-14 | Demande suppression | CONFORME | pending_deletion + révocation — N2 | — |
| GEO-CPT-15 | Annulation suppression | CONFORME | Prouvée — N2 | — |
| GEO-CPT-16 | Finalisation suppression | PARTIEL | Compte synthétique PASS PARTIEL — N2 | Smoke test worker destructeur ouvert |
| GEO-CPT-17 | Purge locale | NON DÉMARRÉ | — | Recette appareil ouverte |
| GEO-CPT-18 | Isolation 2 comptes appareil | NON DÉMARRÉ | — | Isolation Room/fichiers à prouver |
| GEO-CPT-19 | Sauvegarde/restauration | NON DÉMARRÉ | — | — |
| GEO-CPT-20 | Hors ligne/reconnexion | PARTIEL | Saisie locale continue — N1 | Reprise sync non prouvée |
| GEO-CPT-21 | MFA | NON DÉMARRÉ | — | Non implémenté |
| GEO-CPT-22 | Désinstall/réinstall | NON DÉMARRÉ | — | — |
| GEO-L0 | Lot 0 synchronisation | PARTIEL | En cours — N1 | — |
| GEO-L1 | Lot 1 interface | PARTIEL | En cours — N1 | — |
| GEO-L2 | Lot 2 navigation | NON DÉMARRÉ | — | À prouver |
| GEO-L3 | Lot 3 création forêt | PARTIEL | WIP — N1 | — |
| GEO-L4 | Lot 4 carte/recherche | PARTIEL | API + client présents — N1 | E2E non prouvé |
| GEO-L5 | Lot 5 staging | PARTIEL | TEST local déclaré — N2 | Staging distant à préparer |
| GEO-L6 | Lot 6 haptique/mémoire | NON DÉMARRÉ | — | — |

## 7. IDENTITE-001 — Authentification (52 exigences)

| ID | Exigence | Statut | Preuve / niveau | Écart résiduel |
|---|---|---|---|---|
| ID-F-001 | UUID canonique | CONFORME | Identité en base — N2 | — |
| ID-F-002 | Création compte | CONFORME | API réelle + UI — N2 | — |
| ID-F-003 | Connexion locale | CONFORME | S25 + API — N2 | — |
| ID-F-004 | Providers annoncés | CONFORME | `not_configured` retourné — N2 | — |
| ID-F-005 | Connexion Google | PARTIEL | Refus faux jeton 503 — N2 | Config Google Cloud réelle absente |
| ID-F-006 | 1ʳᵉ connexion Google crée compte | PARTIEL | Code présent — N0 | Non testé réel |
| ID-F-007 | Pas de fusion auto comptes | CONFORME | ACCOUNT_LINK_REQUIRED — N1 | — |
| ID-F-008 | Rattachement Google explicite | PARTIEL | Endpoint présent — N0 | Recette réelle absente |
| ID-F-009 | Refresh/verify/logout partagés | CONFORME | Rotation prouvée — N2 | — |
| ID-F-010 | Pro conditionnel providers | CONFORME | Aucun contrôle inactif — N1 | — |
| ID-F-011 | Rôles émis par GSIE | CONFORME | `app,role` scoped — N1 | — |
| ID-F-012 | Même compte multi-apps | PARTIEL | GeoSylva + API — N2 | Autres apps absentes |
| ID-F-013 | Espace compte app | CONFORME | S25 : profil + déconnexion — N3 | — |
| ID-F-014 | Erreurs identité non bloquantes offline | PARTIEL | Session expirée → refresh/purge — N2 | Cas limites ouverts |
| ID-F-015 | 8 pressions options dev | PARTIEL | Déclaré — N0 | Non re-prouvé |
| ID-F-016 | Diagnostic dev read-only | PARTIEL | Déclaré — N0 | — |
| ID-F-017 | Profil modifiable | CONFORME | Nom affiché rectifié — N2 | — |
| ID-F-018 | Vérification e-mail | CONFORME | Mailpit code prouvé — N2 | — |
| ID-F-019 | Récupération anti-énumération | CONFORME | Même réponse, 401 ancien mdp — N2 | — |
| ID-F-020 | Récupération révoque sessions | CONFORME | Prouvée — N2 | — |
| ID-F-021 | Sessions consultables/révocables | CONFORME | Liste validée — N2 | Révocation inter-appareil à formaliser |
| ID-F-022 | Export données | CONFORME | Lisible, daté, sans secret — N2 | Inventaire comparatif non formalisé |
| ID-F-023 | Consentements versionnés | CONFORME | Acceptés/révoqués/historisés — N2 | — |
| ID-F-024 | Suppression différée | CONFORME | pending_deletion + sessions — N2 | — |
| ID-F-025 | Annulation suppression | CONFORME | Prouvée — N2 | — |
| ID-F-026 | Finalisation suppression | PARTIEL | Fonction SQL compte synthétique — N2 | Smoke test worker destructeur ouvert |
| ID-F-027 | Restauration distincte | PARTIEL | Reset + annulation prouvés — N2 | Restauration sauvegarde locale ouverte |
| ID-F-028 | Isolation multi-compte | PARTIEL | B ne voit pas A (API) — N2 | Isolation Room/fichiers locale ouverte |
| ID-S-001 | Argon2id | CONFORME | Implémenté — N2 | — |
| ID-S-002 | Bornes mot de passe | CONFORME | Politique appliquée — N2 | — |
| ID-S-003 | Anti-énumération | CONFORME | Réponses uniformes — N2 | — |
| ID-S-004 | Vérif Google côté serveur | CONFORME | Faux jeton refusé — N2 | Réel non testé |
| ID-S-005 | Codes vérification hachés 15 min | CONFORME | Implémenté — N2 | — |
| ID-S-006 | Nonce usage unique | CONFORME | Implémenté — N2 | — |
| ID-S-007 | Rate limiting auth | CONFORME | Implémenté — N2 | — |
| ID-S-008 | Pas de secret dans logs | PARTIEL | Audit events — N1 | Contrôle logcat appareil à faire |
| ID-S-009 | Comptes désactivés bloqués | CONFORME | Implémenté — N2 | — |
| ID-S-010 | RLS, pas de DELETE | CONFORME | Migrations — N2 | — |
| ID-S-011 | Stockage chiffré mobile | CONFORME | SQLCipher — N1 | — |
| ID-S-012 | Sessions révocables | CONFORME | Implémenté — N2 | — |
| ID-S-013 | Audit événements auth | CONFORME | auth_events — N2 | — |
| ID-S-014 | Commande Fondateur future | PARTIEL | Conçue — N0 | Non implémentée |
| ID-S-015 | Jetons opaques | CONFORME | Implémenté — N2 | — |
| ID-S-016 | Expirations bornées | CONFORME | 15 min/7 j — N2 | — |
| ID-S-017 | SMTP chiffré prod | PARTIEL | Config documentée — N0 | Prod non déployée |
| ID-D-001 | Schéma `gsie_rgpd_identites` | CONFORME | Migrations appliquées — N2 | — |
| ID-D-002 | Contrainte unicité | CONFORME | Migrations — N2 | — |
| ID-D-003 | Normalisation e-mail | CONFORME | Implémenté — N2 | — |
| ID-D-004 | Horodatage UTC | CONFORME | Implémenté — N2 | — |
| ID-D-005 | Horodatage événements | CONFORME | auth_events — N2 | — |
| ID-D-006 | Rôles périmètre app | CONFORME | `app,role` — N1 | — |
| ID-D-007 | Actions sensibles minimisées | CONFORME | Design RGPD — N1 | — |

## 8. SITE-001 — Site public (43 exigences)

| ID | Exigence | Statut | Preuve / niveau | Écart résiduel |
|---|---|---|---|---|
| SITE-F-001 | Hero + proposition | CONFORME | Build 13 routes — N1 | — |
| SITE-F-002 | Chaîne de valeur | CONFORME | Contenu présent — N1 | — |
| SITE-F-003 | 9 applications | CONFORME | Icônes présentes — N1 | — |
| SITE-F-004 | Domaines couverts | CONFORME | Contenu présent — N1 | — |
| SITE-F-005 | Principes | CONFORME | Contenu présent — N1 | — |
| SITE-F-006 | Indicateurs live réels | NON DÉMARRÉ | — | Endpoint public absent ; remplacé par repères éditoriaux |
| SITE-F-007 | État dégradé sans données | CONFORME | Repères non dynamiques — N1 | — |
| SITE-F-008 | Liens docs/api/status | PARTIEL | Liens internes vérifiés — N1 | `api.` renvoie 530 |
| SITE-F-009 | Lien zone Compte | PARTIEL | Retiré du build fermé — N1 | Zone à rouvrir après décision |
| SITE-F-010 | Écrans compte web | NON DÉMARRÉ | — | PUBLIC_ACCOUNT_ENABLED=false |
| SITE-F-011 | Identité visuelle compte | NON DÉMARRÉ | — | — |
| SITE-F-012 | État connexion persistant web | NON DÉMARRÉ | — | — |
| SITE-F-013 | Fil actualités structuré | PARTIEL | Entrées versionnées — N1 | Contenu à enrichir |
| SITE-F-014 | Éditorialité maîtrisée | NON MESURÉ | — | Jugement humain requis |
| SITE-F-015 | Filtres/catégories actus | PARTIEL | Structure — N1 | — |
| SITE-F-016 | URL stable par actu | PARTIEL | Routes Astro — N1 | — |
| SITE-F-017 | Actualités sans backend | CONFORME | Fichiers versionnés — N1 | — |
| SITE-F-018 | Galerie sans média non publié | CONFORME | Fermée, collection vide — N1 | Par fermeture |
| SITE-F-019 | Process vérification galerie | PARTIEL | Page statique — N0 | Processus publication à définir |
| SITE-F-020 | Attribution médias | PARTIEL | Structure — N0 | — |
| SITE-F-021 | Consentement publication | BLOQUÉ | — | Process vie privée non défini |
| SITE-F-022 | Retrait média | PARTIEL | Structure — N0 | — |
| SITE-F-023 | Formulaire contact Turnstile | CONFORME | Vérif serveur — N1 | — |
| SITE-F-024 | Catégories contact | CONFORME | Transmises — N1 | — |
| SITE-F-025 | Canal sécurité distingué | PARTIEL | Catégorie transmise — N1 | Distinction visuelle à confirmer |
| SITE-X-001 | LCP/INP/CLS budgets | NON MESURÉ | — | Pas de mesure labo |
| SITE-X-002 | prefers-reduced-motion | NON MESURÉ | — | À vérifier |
| SITE-X-003 | Navigation clavier | PARTIEL | Focus visible — N1 | Audit complet à faire |
| SITE-X-004 | WCAG AA | NON MESURÉ | — | Audit à faire |
| SITE-X-005 | Lisible sans JS | PARTIEL | Astro statique — N1 | Contact nécessite JS |
| SITE-X-006 | Responsive | PARTIEL | Déclaré — N1 | — |
| SITE-X-007 | Thème clair | CONFORME | Présent — N1 | — |
| SITE-X-008 | SEO (robots, sitemap, OG) | CONFORME | Fichiers présents — N1 | `robots.txt` servi HTML sur ancien domaine |
| SITE-X-009 | Fonctionne si API down | CONFORME | Statique — N1 | — |
| SITE-S-001 | CSP stricte | PARTIEL | Headers définis — N0 | CSP absente sur domaine actuel (verify:live) |
| SITE-S-002 | Turnstile | CONFORME | Vérifié serveur — N1 | — |
| SITE-S-003 | Endpoints read-only | CONFORME | Pas de persistance publique — N1 | — |
| SITE-S-004 | Sessions web | PARTIEL | Zone fermée — N0 | — |
| SITE-S-005 | HTTPS/HSTS | PARTIEL | Config Cloudflare — N0 | Domaine non basculé |
| SITE-D-001 | Contenu versionné | CONFORME | Git — N0 | — |
| SITE-D-002 | Médias optimisés | PARTIEL | Pas encore de médias — N0 | — |
| SITE-D-003 | Endpoint indicateurs | NON DÉMARRÉ | — | — |
| SITE-D-004 | Données compte isolées | CONFORME | Zone fermée — N1 | Par fermeture |

## 9. HUB-001 — Centre de Commandement (44 exigences)

Environnement UE 5.8 + Cesium configuré (N0). Toutes les autres exigences
sont `DIFFÉRÉ` par DEC-000083 (Hub hors chemin critique V1).

| ID | Exigence | Statut | Preuve / niveau | Écart résiduel |
|---|---|---|---|---|
| HUB-NF-01 | Unreal Engine 5.8 | CONFORME | Environnement configuré — N0 | Aucun code Hub |
| HUB-NF-02 | Cesium for Unreal | CONFORME | Plugin présent — N0 | — |
| HUB-F-01 → F-28 | Visualisation, couches, provenance, fraîcheur, incertitude, réel/simulé, PCG, Splats, contrôle | DIFFÉRÉ | — | DEC-000083 |
| HUB-NF-03 → NF-16 | Performance, latence, formats 3D Tiles/COG/LAZ, interop | DIFFÉRÉ | — | DEC-000083 |

## 10. IGNIS-001/002 — Incendies (61 exigences)

`DIFFÉRÉ` par DEC-000083 ; seules preuves de banc disponibles (N1).

| ID | Exigence | Statut | Preuve / niveau | Écart résiduel |
|---|---|---|---|---|
| IGNIS-F-11 | Propagation ForeFire | PARTIEL | ForeFire compilé, banc validé — N1 | Pas d'intégration opérationnelle |
| IGNIS-F-14 | Drones PX4 | PARTIEL | SITL 5 vols — N1 | Banc uniquement |
| IGNIS-F-15 | Trajectoires lawnmower | PARTIEL | Vol exécuté — N1 | — |
| IGNIS-F-16 | RTH (return-to-home) | PARTIEL | RTH partiel — N1 | Cas complets à couvrir |
| IGNIS-F-01 → F-10, F-12-13, F-17 → F-26 | Détection, alertes, météo, coordination, audit | DIFFÉRÉ | — | DEC-000083 |
| IGNIS-NF/RES/SEC/INT/EXP/OPS | Toutes | DIFFÉRÉ | — | DEC-000083 |

## 11. Exigences transverses (14 exigences)

| ID | Exigence | Statut | Preuve / niveau | Écart résiduel |
|---|---|---|---|---|
| TRV-CON-001 | L'humain décide (CON-001) | CONFORME | Par conception + garde-fous — N0 | — |
| TRV-CON-002 | Science validée avant usage (CON-002) | PARTIEL | GSIE-Bench pending_expert_review — N0 | 30 scénarios en attente |
| TRV-CON-003 | Connaissance avant code (CON-003) | CONFORME | Processus respecté — N0 | — |
| TRV-CON-004 | Explicabilité (CON-004) | PARTIEL | Provenance moteurs — N1 | Bout-en-bout à démontrer |
| TRV-CON-005 | Traçabilité décisions (CON-005) | CONFORME | DEC/RFC tracés — N0 | — |
| TRV-CON-006 | Documentation à jour (CON-006) | CONFORME | Memory/CHANGELOG sync — N0 | — |
| TRV-CON-007 | Modularité (CON-007) | CONFORME | Repos/engines séparés — N0 | — |
| TRV-CON-008 | Souveraineté choix fournisseurs (CON-008) | PARTIEL | Options documentées — N0 | Fournisseur staging non choisi |
| TRV-CON-009 | Patrimoine données (CON-009) | CONFORME | DATASETS catalogués — N0 | — |
| TRV-CON-010 | Versionnement (CON-010) | PARTIEL | Contrats versionnés — N1 | Couverture incomplète |
| TRV-RGPD | Conformité RGPD globale | PARTIEL | Registre données + cycle compte — N2 | Mentions légales placeholders ; conservation juridique à confirmer |
| TRV-SEC | Sécurité transverse | PARTIEL | Audits + pentest 08-07/10 — N1 | 24 CVE connus (6 HIGH) ; escalade pyjwt en attente |
| TRV-DOC | Hiérarchie documentaire | CONFORME | Structure respectée — N0 | — |
| TRV-WIP | Limite WIP / diffs séparés | PARTIEL | Registre WIP — N0 | Plusieurs WIP concurrents à suivre |

---

## 12. Historique du registre

| Date | Événement | Modification |
|---|---|---|
| 2026-09-29 | Baseline | Création du registre — audit `2026-09-29_CONFORMITE_EXIGENCES_BASELINE.md` |
