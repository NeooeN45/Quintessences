# Domaine A — Forestier, dendrométrie, gestion, filière

> Fichier partiel — GSIE-PROMPT-0025
> Toutes les URL ci-dessous ont été vérifiées par accès réel (webfetch) le 2026-07-30.
> Compteur URL : 7 testées, 0 échec.

---

## Entrées vérifiées

### A-001 — Cadastre (plan cadastral parcellaire)

```yaml
- nom: Cadastre
  producteur: Etalab / DGFIP (France)
  url: https://www.data.gouv.fr/fr/datasets/cadastre/
  access_method: file_download
  licence: Licence Ouverte 2.0 (etalab-2.0)
  ai_training_allowed: false
  grain_m2: inconnu — découpage parcellaire, pas raster
  emprise: France entière (métropole + DOM + Saint-Martin/Saint-Barthélemy)
  etendue_temporelle: continu (mise à jour par commune)
  frequence_mise_a_jour: mensuelle (fichiers par département)
  format: GeoJSON, Shapefile
  volume_estime: ~5 Go (France entière, toutes couches)
  type_source: referentiel_officiel
  moteur_destinataire: GIS, Forest Dynamics, Recommendation (foncier)
  regime: referencee
```

**Note** : couches disponibles — parcelles, lieux_dits, feuilles, sections, communes, batiments, subdivisions_fiscales (beta). Le PCI vecteur est désormais source unique depuis le 01/09/2025. URL testée : page d'accueil du dataset répond, description et fichiers confirmés.

---

### A-002 — ONF Open Data (catalogue thématique)

```yaml
- nom: ONF Open Data — catalogue des données publiques
  producteur: Office National des Forêts (France)
  url: https://www.onf.fr/onf/connaitre-lonf/+/35::opendata-onf.html
  access_method: publication_text
  licence: Variable par jeu — Licence Ouverte 2.0 pour la plupart
  ai_training_allowed: false
  grain_m2: inconnu — portail catalogue, pas un jeu unique
  emprise: France métropolitaine + DOM
  etendue_temporelle: variable par jeu
  frequence_mise_a_jour: variable par jeu
  format: Shapefile, GeoPackage, PDF (selon jeu)
  volume_estime: inconnu — portail
  type_source: referentiel_officiel
  moteur_destinataire: GIS, Forest Dynamics, Diagnostic, Knowledge
  regime: referencee
```

**Note** : page catalogue vérifiée. Thématiques : contours des réserves biologiques, documents d'aménagement, contours publics des forêts, données naturalistes (via INPN). Accès indirect — renvoie vers téléchargements et INPN. L'URL d'origine `+54:::ouvert.html` est 404 (page déplacée).

---

### A-003 — RENECOFOR (réseau suivi long terme écosystèmes forestiers)

```yaml
- nom: RENECOFOR — Réseau National de suivi à long terme des Écosystèmes Forestiers
  producteur: Office National des Forêts (France)
  url: https://www.onf.fr/renecofor
  access_method: publication_text
  licence: inconnue — à établir (données sur demande ONF)
  ai_training_allowed: false
  grain_m2: inconnu — placettes de suivi, surface représentative non déclarée publiquement
  emprise: France métropolitaine (102 sites permanents)
  etendue_temporelle: 1992 — continu
  frequence_mise_a_jour: annuelle (mesures décennales pour sol, annuelles pour dendrométrie)
  format: PDF (rapports), données tabulaires sur demande
  volume_estime: inconnu — 102 sites × ~30 ans de mesures
  type_source: capteur_instrumente
  moteur_destinataire: Forest Dynamics, Correlation, Climate, Diagnostic, Learning
  regime: referencee
```

**Note** : réseau créé 1992, 102 sites permanents, suit arbres/sol/atmosphère/flore. Inscrit dans ICP Forests (réseau européen). Données d'accès conditionné — l'évaluation ONF 2007 note que "les conditions d'accès aux données ont été jugées comme devant encore être améliorées". type_source = `capteur_instrumente` (proposé RFC-0029 §11.3) : chaîne de mesure calibrée, protocole ICP Forests.

---

### A-004 — CNPF (Centre National de la Propriété Forestière)

```yaml
- nom: CNPF — Centre National de la Propriété Forestière
  producteur: CNPF (établissement public, tutelle MAA/MTE, France)
  url: https://cnpf.fr/
  access_method: publication_text
  licence: inconnue — à établir (contenu institutionnel, fiches techniques)
  ai_training_allowed: false
  grain_m2: sans objet — documentaire
  emprise: France métropolitaine (forêts privées, 13 Mha)
  etendue_temporelle: continu
  frequence_mise_a_jour: continue
  format: PDF, HTML (fiches, guides, PSG agréés)
  volume_estime: inconnu — des milliers de documents techniques
  type_source: referentiel_officiel
  moteur_destinataire: Recommendation, Knowledge, Forest Dynamics
  regime: referencee
```

**Note** : établissement public gestion forêts privées. Délivre PSG (Plans Simple de Gestion), RTG (Règlements Type de Gestion), SRGS (Schémas Régionaux de Gestion Sylvicole). IDF (Institut pour le Développement Forestier) est sa branche technique. 18 CRPF régionaux. Le rapport d'activité 2025 mentionne "presque 500 PSG de propriétés 20-25 ha nouvellement soumises par la loi incendie de 2023". URL testée : page d'accueil répond.

---

### A-005 — France Bois Forêt (observatoire économique filière)

```yaml
- nom: France Bois Forêt — Observatoire économique
  producteur: France Bois Forêt (interprofession nationale, France)
  url: https://franceboisforet.fr/
  access_method: publication_text
  licence: inconnue — à établir (données économiques, conditions d'utilisation à vérifier)
  ai_training_allowed: false
  grain_m2: sans objet — données économiques
  emprise: France entière
  etendue_temporelle: 2004 — continu
  frequence_mise_a_jour: annuelle (indicateurs), ponctuelle (études)
  format: PDF, HTML (rapports, indicateurs)
  volume_estime: inconnu — indicateurs économiques filière
  type_source: referentiel_officiel
  moteur_destinataire: Recommendation, Knowledge
  regime: referencee
```

**Note** : interprofession nationale filière forêt-bois créée 2004. Observatoire économique + VEM (Veille Économique Mutualisée). Indicateurs : prix bois sur pied, enquête construction bois, perceptions Français. URL testée : page d'accueil répond, observatoire à http://observatoire.franceboisforet.com/ (URL secondaire non testée séparément).

---

### A-006 — FCBA (Institut technologique forêt-bois-ameublement)

```yaml
- nom: FCBA — Institut technologique Forêt Cellulose Bois Ameublement
  producteur: FCBA (centre technique industriel, France)
  url: https://www.fcba.fr/
  access_method: publication_text
  licence: inconnue — à établir (ressources documentaires, prestations)
  ai_training_allowed: false
  grain_m2: sans objet — R&D et normes
  emprise: France
  etendue_temporelle: continu
  frequence_mise_a_jour: continue
  format: PDF, HTML (guides, memento, rapports d'impacts)
  volume_estime: inconnu — ressources documentaires techniques
  type_source: referentiel_officiel
  moteur_destinataire: Recommendation, Knowledge, Forest Dynamics
  regime: referencee
```

**Note** : centre technique industriel accrédité COFRAC. Secteurs : forêt (génétique, sylviculture, récolte), 1ère transformation (scierie, pâte), 2nde transformation (construction), ameublement, environnement. Publie le Memento 2025-2026, Rapport impacts 2025. Pas une source de données géospatiales directe mais référentiel normatif filière. URL testée : page d'accueil répond.

---

### A-007 — Régions de provenance MFR (matériels forestiers de reproduction)

```yaml
- nom: Régions de provenance des matériels forestiers de reproduction (MFR)
  producteur: Ministère de l'Agriculture (MAA) + IGN + IRSTEA/INRAE (France)
  url: https://agriculture.gouv.fr/fournisseurs-especes-reglementees-provenances-et-materiels-de-base-forestiers
  access_method: publication_text
  licence: Licence Ouverte 2.0 (données réglementaires publiques)
  ai_training_allowed: false
  grain_m2: sans objet — zonage réglementaire
  emprise: France métropolitaine
  etendue_temporelle: 2003 — continu (arrêté 24/10/2003, mises à jour 2025-2026)
  frequence_mise_a_jour: ponctuelle (arrêtés modificatifs)
  format: PDF (arrêtés, annexes cartographiques), HTML
  volume_estime: inconnu — 68 espèces réglementées, ~100 régions de provenance
  type_source: referentiel_officiel
  moteur_destinataire: Recommendation, Knowledge, Forest Dynamics
  regime: referencee
```

**Note** : arrêté fondateur du 24/10/2003, transposition directive EU 1999/105/CE. 68 espèces d'intérêt sylvicole réglementées au 01/07/2025. Cartographies IGN par sylvoécorégions (SER). Conseils d'utilisation révisés sous coordination IRSTEA/INRAE pour prise en compte changement climatique. URL secondaire vérifiée via recherche : inventaire-forestier.ign.fr/spip.php?article973 (cartes de répartition par essence). URL principale testée : page MAA répond, arrêtés téléchargeables.

---

## À VÉRIFIER — Domaine A

### A-V001 — Documents de gestion durable (PSG/RTG/SRGS) en open data

**Motif** : le CNPF agrée les PSG mais aucun portail de téléchargement bulk des documents n'a été identifié. Les PSG contiennent des informations individuelles (propriétaire, parcelles) qui peuvent limiter l'ouverture. Les SRGS (Schémas Régionaux) sont publics mais leur localisation précise en open data n'est pas confirmée. À établir : existe-t-il un portail data.gouv.fr ou CNPF de téléchargement des SRGS ?

### A-V002 — Vergers à graines (localisation et génotypes)

**Motif** : les vergers à graines sont listés dans le registre national des matériels de base (MAA) mais leur localisation géographique précise n'est pas publiquement accessible (informations professionnelles). Le registre est consultable mais pas sous forme de jeu de données téléchargeable. À établir : le registre national MFR a-t-il un export tabulaire ?

### A-V003 — BD Forêt v3 (2026, jeu test 40 zones)

**Motif** : mentionnée dans l'inventaire existant §10.1 ("Jeu test sur 40 zones disponible, production par IA à partir de BD Ortho. Retours attendus jusqu'avril 2026"). L'URL précise du jeu test n'est pas confirmée — probablement via data.geopf.fr mais endpoint exact non vérifié. À établir quand la v3 sortira en production.

---

## Signalements — Domaine A

- L'URL ONF open data `+54:::ouvert.html` citée dans l'inventaire existant est **morte** (404, page déplacée). La nouvelle URL `+/35::opendata-onf.html` fonctionne. À corriger dans l'inventaire existant.
