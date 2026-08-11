# IDEA_BACKLOG — Idées non encore transformées en décisions

| Champ | Valeur |
|---|---|
| **Créé le** | 2026-07-01 |
| **Source de vérité** | Ce fichier uniquement pour les idées non décidées |
| **Processus** | `/ingestion-idee` puis qualification Fondateur |

---

## Format

Chaque idée suit le modèle :

```
### IDEA-XXXX — [Titre]
- **Date** : YYYY-MM-JJ
- **Origine** : [Discussion / Directive / Observation / Veille]
- **Produit** : [Quintessences / GSIE / GeoSylva / IGNIS / autre]
- **Type** : [produit / recherche / architecture / donnée / UX / commercial]
- **Description** : [Résumé de l'idée et problème traité]
- **Valeur potentielle** : faible / moyenne / élevée / inconnue
- **Maturité** : brute / qualifiée / recherche / prototype / validée
- **Horizon** : actif / phase courante / phase future / spéculatif
- **Dépendances** : [RFC, moteur, dataset, app ou décision]
- **Risques** : [scientifiques, techniques, juridiques, commerciaux]
- **Prochaine action** : [action minimale vérifiable]
- **Statut** : PROPOSÉE / ÉTUDIÉE / TRANSFORMÉE EN RFC / TRANSFORMÉE EN DEC / REJETÉE
- **Sources** : [DOI, URL, fichier ou conversation]
- **Lien** : [RFC ou DEC si transformée]
```

Une idée enregistrée n'est pas une priorité de développement. Toute écriture
automatique doit rester explicitement demandée par le Fondateur. Les RFC et DEC
restent dans leurs dossiers canoniques respectifs.

---

### IDEA-0001 — GSIE comme moteur générique d'intelligence environnementale
- **Date** : 2026-07-06
- **Origine** : Discussion (échange fondateur, prolongée d'une discussion externe ChatGPT)
- **Description** : La chaîne de raisonnement de GSIE (Evidence → Knowledge →
  Correlation → Reasoning → Diagnostic → Recommendation → Validation) ne
  contient aucune logique spécifiquement forestière ; seuls les moteurs
  domaine (GIS, Climate, Pedology, Botanical, Forest Dynamics) le sont.
  L'idée : documenter explicitement GSIE comme un moteur générique de
  systèmes experts environnementaux, dont la foresterie constitue la
  première spécialisation officielle — sans que cela change l'architecture
  actuelle, qui valide déjà ce principe par construction. Piste de
  formulation : « GSIE est conçu comme une plateforme générique d'intelligence
  environnementale ; la spécialisation forestière constitue son premier domaine
  d'application officiel. »
- **Statut** : PROPOSÉE
- **Lien** : —

### IDEA-0002 — Écosystème de produits dérivés (GeoSylva Mobile/Web/Desktop/Enterprise/Education/Research/Climate/Carbon/…, marques sœurs AquaSylva/AgroSylva/BioSylva/TerraSylva/…)
- **Date** : 2026-07-06
- **Origine** : Discussion (échange fondateur, prolongée d'une discussion externe ChatGPT)
- **Description** : Vision étendue à ~20 déclinaisons produit de GeoSylva et
  une dizaine de marques dérivées par domaine environnemental (eau,
  agriculture, biodiversité, sols, climat, faune, flore…), avec un
  renommage possible GeoSylva → GSIE Forest une fois GSIE établi comme
  marque plateforme. Catalogue explicitement spéculatif à ce stade :
  aucun de ces produits n'a de justification issue d'un besoin utilisateur
  validé, et figer des noms/périmètres maintenant risquerait de contraindre
  artificiellement l'architecture avant la Phase 2. À ne pas transformer en
  RFC avant qu'au moins un cas d'usage réel (Phase 3/4) ne le justifie.
- **Statut** : PROPOSÉE
- **Lien** : —

### IDEA-0003 — IGNIS-FOLD : guidage d'urgence inspiré de G-FOLD
- **Date** : 2026-08-05
- **Origine** : Brainstorming externe du Fondateur avec ChatGPT
- **Produit** : IGNIS
- **Type** : recherche
- **Description** : Étudier une architecture de guidage de trajectoire pour les
  dérivations urgentes, le retour avec énergie limitée et l'atterrissage sûr
  d'un drone autonome opérant dans un environnement d'incendie. Le concept
  s'inspire de G-FOLD, méthode de guidage de descente propulsée par
  optimisation convexe de type SOCP, mais ne constitue pas une adaptation
  validée pour un drone. Le planificateur de mission, le guidage, le
  Safety Supervisor et l'autopilote doivent rester séparés.
- **Valeur potentielle** : élevée
- **Maturité** : recherche
- **Horizon** : phase future
- **Dépendances** : modèle dynamique, classe de drone, météo, terrain 3D,
  énergie, PX4/ArduPilot SITL et HIL
- **Risques** : validité de l'adaptation mathématique, sécurité aérienne,
  incertitudes thermiques et aérologiques, certification, licence des
  implémentations, validation terrain
- **Prochaine action** : définir les classes de drones candidates et produire
  une étude de faisabilité hors vol avec modèle dynamique et critères de
  sécurité
- **Statut** : PROPOSÉE
- **Sources** : Açıkmeşe & Ploen, DOI 10.2514/1.27553 ; Scharf et al.,
  DOI 10.2514/1.g000399 ; conversation externe du 2026-08-05
- **Lien** : —

> Prochaine idée : IDEA-0004.
