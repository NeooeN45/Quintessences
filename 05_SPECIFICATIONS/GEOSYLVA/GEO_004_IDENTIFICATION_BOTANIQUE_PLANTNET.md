# GEO-004 — Spécification fonctionnelle : identification botanique assistée (Pl@ntNet)

| Champ | Valeur |
|---|---|
| **Document** | GEO-004 |
| **Dossier** | 05_SPECIFICATIONS/GEOSYLVA/ |
| **Phase** | 4 — Implémentation |
| **Statut** | Draft |
| **Date de création** | 2026-07-20 |
| **Lois fondatrices** | GSIE-CON-001 (décideur humain), GSIE-CON-002 (science avant tout), GSIE-CON-005 (traçabilité), GSIE-CON-010 (versionnement) |
| **RFC de référence** | RFC-0018 (Identification botanique assistée Pl@ntNet et extension du Botanical Engine) — Draft |
| **RFC complémentaires** | RFC-0016 (schéma forestier — `AutecologyProfile`, TAXREF canonique), RFC-0015 (registre de modèles/licences), RFC-0017 (veille d'origine, adopté comme cadrage — DEC-000029) |
| **Spécification liée** | `GEO_001_SPECIFICATION.md` §3.1 (GEO-F-04 — identification des essences, déjà existante, complétée ici sur le canal photo assisté par IA) |
| **Documents connexes** | `GSIE/RESEARCH/VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20.md`, `engines/botanical/extraction_bridge.py` (pont existant, pattern réutilisé) |

> Cette spécification décrit **ce que le canal d'identification
> Pl@ntNet doit faire**, pas comment l'implémenter (rôle de
> `GSIE/ARCHITECTURE`). Aucun code métier n'est produit ici (CON-003
> tant que RFC-0018 n'est pas adopté). Elle complète GEO-F-04 sans le
> remplacer : GEO-F-04 couvre l'identification par fusion BD Forêt/
> Crown-BERT (télédétection) ; GEO-004 couvre l'identification par
> photo terrain (Pl@ntNet), un canal complémentaire déclenché par le
> forestier lui-même.

---

## 1. Objet et périmètre

### 1.1 Définition

Un canal d'identification botanique par photographie, disponible dans
l'app mobile GeoSylva, qui envoie jusqu'à 5 clichés d'un même individu
à l'API Pl@ntNet via un serveur GSIE, affiche les hypothèses retournées
sans jamais les présenter comme certaines, et n'écrit une essence dans
l'inventaire qu'après validation explicite du technicien.

### 1.2 Principe fondamental

> **Une identification par photo est une suggestion, jamais une
> mesure (CON-001, CON-002).**

Contrairement à GEO-F-04 (fusion BD Forêt + contexte, déjà une
inférence de peuplement), l'identification Pl@ntNet est une inférence
*par individu*, avec un niveau d'incertitude propre à chaque photo. Le
statut `SUGGESTION_IA` ne devient jamais `VALIDEE_UTILISATEUR`
automatiquement, quel que soit le score de confiance retourné.

### 1.3 Périmètre inclus

- Capture photo (1 à 5 clichés) par organe : feuille, fleur, fruit,
  écorce.
- Envoi via serveur GSIE (clé API jamais côté client), retrait des
  métadonnées GPS avant transmission à Pl@ntNet.
- Réception et affichage des 3 meilleures hypothèses (espèce, famille,
  score de confiance, identifiants GBIF/POWO).
- Décision du technicien : Confirmer / Ajouter une photo / Identifier
  manuellement.
- Sur confirmation : écriture d'un `AutecologyProfile` (RFC-0016) via
  un connecteur dédié, jamais d'écriture directe sur l'inventaire sans
  ce passage.
- File d'attente offline : capture et photo toujours enregistrées
  localement, requête Pl@ntNet différée si pas de réseau.
- Attribution des photos de référence Pl@ntNet (CC BY-SA) si affichées
  dans l'UI.

### 1.4 Périmètre exclu

- **Entraînement d'un modèle embarqué offline** — étude de faisabilité
  seulement (RFC-0018 §6), non spécifié ici.
- **Négociation contractuelle avec Pl@ntNet** — relève de `19_LEGAL/`.
- **Composant `gsie-ai-gateway` générique** — RFC-0019 ; ce canal peut
  fonctionner en service autonome dans l'intervalle (§6.2).
- **Identification par télédétection (LiDAR/hyperspectral)** — déjà
  couverte par GEO-F-04, hors périmètre de ce document.
- **Diagnostic sanitaire/maladies** — l'API Pl@ntNet des maladies
  existe mais ne couvre qu'une liste limitée d'espèces/pathologies ;
  non retenue dans ce périmètre, à réévaluer séparément si un besoin
  terrain est confirmé.

---

## 2. Acteurs et rôles

| Acteur | Rôle | Niveau d'interaction |
|---|---|---|
| **Forestier / technicien terrain** | Photographie l'individu, consulte les hypothèses, valide/rejette | Saisie + lecture + validation (CON-001) |
| **App mobile GeoSylva** | Capture, file d'attente offline, affichage des hypothèses | Producteur + consommateur |
| **Serveur GSIE (canal identification)** | Retire les métadonnées GPS, appelle Pl@ntNet avec la clé côté serveur, normalise la réponse (GBIF/POWO/TAXREF) | Intermédiaire sécurisé |
| **API Pl@ntNet** | Retourne les espèces candidates + scores | Fournisseur externe |
| **Botanical Engine** | Reçoit la décision validée, alimente `AutecologyProfile` | Consommateur de la décision humaine |

---

## 3. Exigences fonctionnelles

### 3.1 Capture et envoi (GEO-ID-01 à GEO-ID-04)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-ID-01 | GeoSylva doit permettre la capture de 1 à 5 photographies d'un même individu, avec sélection de l'organe photographié (feuille, fleur, fruit, écorce) pour chaque cliché | P0 | Doc. API Pl@ntNet, RFC-0018 §5.1 |
| GEO-ID-02 | GeoSylva doit enregistrer localement la capture et l'observation associée avant tout envoi réseau (offline-first) | P0 | RFC-0018 §5.4, RFC-0003 (T-8/T-10) |
| GEO-ID-03 | Le serveur GSIE doit retirer les métadonnées EXIF GPS des photographies avant transmission à Pl@ntNet | P0 | RFC-0018 §5.2, veille §1.5 |
| GEO-ID-04 | La clé API Pl@ntNet ne doit jamais être présente dans l'APK ou tout artefact client — exclusivement côté serveur | P0 | RFC-0018 §5.2 |

### 3.2 Restitution et décision (GEO-ID-05 à GEO-ID-09)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-ID-05 | GeoSylva doit afficher systématiquement les 3 meilleures hypothèses retournées, jamais une seule espèce présentée comme certaine | P0 | RFC-0018 §5.3, GSIE-CON-001 |
| GEO-ID-06 | GeoSylva doit afficher pour chaque hypothèse : nom scientifique, famille, score de confiance, identifiants GBIF/POWO | P0 | RFC-0018 §5.1 |
| GEO-ID-07 | GeoSylva doit afficher un avertissement visuel explicite quand l'écart de confiance entre la 1ʳᵉ et la 2ᵉ hypothèse est faible (seuil à calibrer en phase pilote) | P1 | RFC-0018 §5.3 |
| GEO-ID-08 | GeoSylva doit proposer trois actions explicites au technicien : Confirmer, Ajouter une photo, Identifier manuellement — aucune action par défaut ne doit valider automatiquement | P0 | GSIE-CON-001, RFC-0018 §5.2 |
| GEO-ID-09 | GeoSylva doit afficher l'attribution (auteur, licence CC BY-SA) de toute photographie de référence Pl@ntNet montrée à l'utilisateur | P0 | Licences Pl@ntNet, RFC-0018 §5.3 |

### 3.3 Traçabilité et statuts (GEO-ID-10 à GEO-ID-13)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-ID-10 | Chaque identification doit porter un statut explicite parmi `SUGGESTION_IA`, `VALIDEE_UTILISATEUR`, `REJETEE`, jamais fusionné avec une observation directe | P0 | RFC-0016 §3.4 (passeport de décision), RFC-0018 §4 |
| GEO-ID-11 | Une identification au statut `SUGGESTION_IA` ne doit déclencher aucun calcul de cubage, aucune recommandation sylvicole, aucune conclusion écologique | P0 | GSIE-CON-001, RFC-0018 §4 |
| GEO-ID-12 | Chaque résultat doit conserver : espèces candidates + scores, identifiants taxonomiques, version du moteur Pl@ntNet, date d'analyse, empreinte numérique des photos, identité du validateur et date de décision | P0 | GSIE-CON-005, RFC-0018 §5.1 |
| GEO-ID-13 | Sur validation (`VALIDEE_UTILISATEUR`), le résultat doit alimenter `AutecologyProfile` via un connecteur dédié — jamais d'écriture directe sur une table d'inventaire sans ce passage | P0 | RFC-0016 (`AutecologyProfile`), pattern `extraction_bridge.py` existant |

### 3.4 Offline-first (GEO-ID-14 à GEO-ID-16)

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| GEO-ID-14 | La requête d'identification doit être placée en file d'attente locale si le réseau est indisponible, sans bloquer la poursuite du travail terrain | P0 | RFC-0018 §5.4, RFC-0003 |
| GEO-ID-15 | GeoSylva doit envoyer automatiquement les requêtes en attente au retour du réseau et notifier l'utilisateur quand un résultat est disponible | P0 | RFC-0018 §5.4 |
| GEO-ID-16 | Une recherche manuelle locale (clé de détermination texte, catalogue TAXREF déjà intégré) doit rester disponible sans réseau, indépendamment de ce canal | P1 | Catalogue TAXREF existant (`BotanicalEngine.resolve_taxref`) |

---

## 4. Exigences non fonctionnelles

| ID | Exigence | Cible | Source |
|---|---|---|---|
| GEO-ID-NF-01 | Quota | Respect du quota gratuit (500 identifications/jour) en phase prototype ; alerte avant dépassement | Conditions Pl@ntNet |
| GEO-ID-NF-02 | Licences | Attribution CC BY-SA (photos de référence) et CC BY (données d'observation) affichées correctement | Règles de licence Pl@ntNet |
| GEO-ID-NF-03 | Sécurité | Clé API exclusivement côté serveur, retrait GPS avant envoi, chiffrement en transit (TLS) | RFC-0018 §5.2, GEO-NF-04 (GEO-001) |
| GEO-ID-NF-04 | Traçabilité | Chaque appel journalisé (date, version moteur, coût si applicable) — cohérent avec GSIE-CON-005 | RFC-0018 §5.1 |
| GEO-ID-NF-05 | Offline | 100 % de la capture disponible sans réseau ; aucune fonctionnalité de saisie terrain bloquée par l'indisponibilité de Pl@ntNet | GEO-NF-02 (GEO-001) |
| GEO-ID-NF-06 | Performance perçue | Notification de résultat disponible en tâche de fond, sans bloquer l'app pendant l'attente réseau | — |

---

## 5. Cas d'usage prioritaire

### 5.1 CU-ID-01 — Identification d'un individu incertain sur le terrain

**Acteur :** Forestier / technicien terrain, avec ou sans réseau
**Scénario :**
1. Le technicien rencontre un individu dont il n'est pas certain de
   l'essence (régénération, essence introduite, individu atypique).
2. Il photographie 2 à 5 organes (feuille, écorce si disponible).
3. Sans réseau : la capture est enregistrée localement et mise en file
   d'attente ; le technicien poursuit son inventaire normalement.
4. Au retour du réseau, la requête part automatiquement vers le
   serveur GSIE, qui retire les métadonnées GPS et interroge Pl@ntNet.
5. Le technicien reçoit une notification, ouvre le résultat : 3
   hypothèses avec scores, écart affiché, avertissement si incertain.
6. Le technicien confirme l'hypothèse correcte (ou identifie
   manuellement s'il reconnaît l'espèce entre-temps, ou rejette).
7. Sur confirmation, un `AutecologyProfile` est créé/complété avec le
   statut `VALIDEE_UTILISATEUR`, traçant scores, identifiants, version
   du moteur et identité du validateur.

---

## 6. Points ouverts pour la Review

- **§6.1** — Seuil exact de l'écart de confiance déclenchant
  l'avertissement (GEO-ID-07) : à calibrer sur un premier lot de cas
  réels, pas de valeur figée dans cette spécification.
- **§6.2** — Ce canal peut être implémenté comme service autonome
  (endpoint dédié) avant que `gsie-ai-gateway` (RFC-0019) existe ; si
  RFC-0019 est adopté plus tard, ce canal devra migrer vers ses routes
  (`/ai/vision` ou équivalent) sans changement de contrat côté
  GeoSylva.
- **§6.3** — Le module Pl@ntNet des maladies (liste limitée
  d'espèces/pathologies) est explicitement exclu du périmètre initial
  (§1.4) ; à réévaluer si un besoin terrain concret est documenté.

---

## 7. Critères d'acceptation

La spécification GEO-004 est considérée **complète** quand :

- [x] Toutes les exigences fonctionnelles (GEO-ID-01 à GEO-ID-16) sont
  tracées vers une source (RFC-0018, RFC-0016, doc. Pl@ntNet).
- [x] Le principe `SUGGESTION_IA` → `VALIDEE_UTILISATEUR` est explicite
  et non contournable par défaut.
- [x] Les exigences non fonctionnelles (quota, licences, sécurité,
  traçabilité, offline, performance) sont quantifiées.
- [x] Le cas d'usage terrain (avec et sans réseau) est couvert.
- [x] Les garde-fous constitutionnels sont respectés (CON-001, CON-002,
  CON-005, CON-010).
- [x] Le périmètre exclu (modèle embarqué, gateway générique,
  diagnostic maladies) est explicite pour éviter toute dérive de
  portée.
- [ ] Seuil d'avertissement (GEO-ID-07) calibré sur cas réels — **à
  faire en phase pilote**.
- [ ] Confirmation écrite de Pl@ntNet sur les conditions commerciales
  — **préalable bloquant avant production**, hors périmètre technique
  de cette spécification (`19_LEGAL/`).

---

## 8. Glossaire

| Terme | Définition |
|---|---|
| **Pl@ntNet** | Service d'identification botanique par photographie (API CIRAD/Pl@ntNet) |
| **`SUGGESTION_IA`** | Statut d'une identification produite par un modèle, non encore validée par un humain |
| **`VALIDEE_UTILISATEUR`** | Statut d'une identification confirmée explicitement par un technicien |
| **`AutecologyProfile`** | Entité du schéma forestier (RFC-0016) que ce canal alimente sur validation |
| **Empreinte numérique** | Hash de la photographie conservé pour traçabilité, sans conserver nécessairement le fichier source |
| **Offline-first** | Architecture où toute la capture fonctionne sans réseau, la requête IA est différée (RFC-0003) |

---

> Statut : *Draft — spécification fonctionnelle Phase 4, préparant la
> Review de RFC-0018. À valider par le Fondateur. Aucun code métier
> produit (CON-003 tant que RFC-0018 n'est pas adopté).*
