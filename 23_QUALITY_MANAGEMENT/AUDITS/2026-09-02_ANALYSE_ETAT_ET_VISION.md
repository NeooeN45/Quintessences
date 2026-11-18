# Analyse d'état et de vision — Quintessences / GSIE

| Champ | Valeur |
|---|---|
| **Identifiant** | ETAT-VISION-20260902 |
| **Statut** | Draft — en attente de relecture du Fondateur |
| **Date** | 2026-09-02 |
| **Périmètre** | Dépôt racine Quintessences, `GSIE/API`, `apps/GeoSylva` (repo externe, lecture seule), `Forge` (repo externe, lecture seule), gouvernance, mémoire, roadmap |
| **Références** | DEC-000074, GEO-005, DEC-000070, DEC-000078, DEC-000081, DEC-000082, RFC-0039, RFC-0041, RFC-0042 |
| **Type de contrôle** | Lecture documentaire + inventaire technique non destructif (comptages, `git log`, `git status`, structure des dossiers). Aucun test exécuté, aucune base touchée. |
| **Auteur** | Agent Devin CLI (GLM 5.2 High), sur demande du Fondateur |

## 1. Objet

Répondre à trois questions : où en est réellement le projet, quels problèmes
structurels ou d'hygiène il porte, et comment orienter sa vision pour le
trimestre suivant. Cet audit ne valide aucun gate GEO-005, aucun livrable et
aucune décision ; il produit des constats et des propositions.

## 2. Méthode et limites

Éléments inspectés : `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md`,
`CLAUDE.md`, `AGENTS.md`, `GSIE/API/AGENTS.md`, `03_DECISIONS/` (DEC-000068 à
DEC-000081), `02_RFC/` (RFC-0031 à RFC-0042), GEO-005, structure de
`GSIE/API/src` et `tests`, `.github/workflows/`, état git des trois dépôts.

Limites : les chiffres de tests et de couverture sont **repris de la mémoire
projet**, non rejoués dans cette session. Les lignes de code sont comptées
brutes (`Measure-Object -Line`), commentaires inclus. Aucun expert métier n'a
été consulté.

## 3. État mesuré

| Dimension | Mesure au 2026-09-02 |
|---|---|
| Âge du dépôt racine | 2 mois (2026-07-03 → 2026-08-31) |
| Gouvernance | 388 fichiers `.md` dans les dossiers de gouvernance/architecture/recherche ; 81 DEC ; 42 RFC ; 28 prompts versionnés |
| API GSIE | 272 fichiers Python source (~50 000 lignes), 268 fichiers de tests (~58 000 lignes), 29 routeurs montés, 14 packages moteurs + orchestration, 56 migrations Alembic, 68 dépendances |
| Qualité déclarée | 3 116 tests passants, 371 ignorés, couverture combinée ~98 %, 70 mutations tuées, mypy strict + Ruff |
| GeoSylva (Android) | 515 fichiers Kotlin, 66 fichiers de tests, 3.0.0 installé sur S25 Ultra, 67 fichiers modifiés non commités |
| Forge | Repo séparé, 251 tests, contrat `forge_analysis_bundle.v1` |
| Données réelles dans le Registry | 1 `DataAsset` RAW de 569 octets ; FETCH fermé pour toutes les sources ; 36 ressources de catalogue `metadata_only` |
| Validation scientifique | 30 scénarios GSIE-Bench candidats, tous `pending_expert_review` ; aucun manifeste Closed ; aucun expert externe nommé |
| Pilotage V1 (DEC-000074) | G0 clos ; G1 (GeoSylva 3.1) et G2 (compte/RGPD) ouverts ; G3, G4, G5 non démarrés |
| État git racine | Branche `feat/schemas-de-domaine` ; 46 fichiers modifiés (+1 666 / −173) ; **83 fichiers non suivis**, dont DEC-000074 à DEC-000082, RFC-0042, GEO-005, 6 migrations Alembic (0052 → 0057), le package `gsie_api/geosylva/`, trois audits |
| Branches | 15, dont 6 dependabot non fusionnées (cryptography, bcrypt, python-multipart, slowapi, eccodeslib, opentelemetry) |
| Cadence | Par rafales : 18 commits le 30/08, 17 le 11/08, 11 le 15/08 ; silence du 25 au 30/08 |

Synthèse : une infrastructure logicielle et documentaire de niveau
industriel, construite en deux mois, sans utilisateur réel, sans donnée réelle
et sans validation scientifique externe.

## 4. Points forts à préserver

- Discipline **fail-closed** cohérente et effective : quarantaine, promotion
  explicite, RLS, tables append-only, empreintes SHA-256, refus nommés.
- La mémoire projet formule elle-même la règle d'honnêteté : ne jamais
  annoncer un moteur ou une source « connecté » sur la seule présence d'un
  module ou d'un test de contrat.
- Le recentrage DEC-000074 (GeoSylva pilote, ordre G1 → G5 bloquant) est la
  décision structurante la plus saine des deux mois.
- Frontière Forge → Registry par contrat versionné, sans duplication de
  connecteurs.
- Outillage qualité réel : couverture par couche, harnais de mutation, CI HA,
  scans de sécurité, vérificateur d'environnements.

## 5. Constats

### 5.1 Gouvernance et traçabilité

| # | Constat | Preuve | Gravité | Traitement |
|---|---|---|---|---|
| C-01 | Collision d'identifiant : deux décisions `DEC-000078` (SoilGrids WCS, 30/08 ; cubage offline-first, 31/08) | `03_DECISIONS/` | Haute — CON-005 | **Corrigé le 2026-09-02** : seconde décision renumérotée `DEC-000082`, note de traçabilité ajoutée ; aucune autre référence n'existait |
| C-02 | `PROJECT_MEMORY.md` est un journal chronologique de plus de 1 000 lignes intitulé « vue courante » ; sa section « État » (l. 953 et suivantes) contredit le haut du fichier (Terra/Aeris/Atlas « non développement » vs DEC-000056) | fichier racine | Moyenne | Proposition §7.5 ; Draft de tableau de bord déposé dans `22_PROJECT_MEMORY/` |
| C-03 | `GSIE/API/AGENTS.md` annonçait « score de mutation 14/14 » alors que le harnais en compte 70+ | règle always-on | Faible | **Corrigé** : formulation « 100 % des mutations tuées », sans chiffre figé |
| C-04 | 83 fichiers non suivis dont neuf décisions/RFC/spécifications et six migrations ; une semaine de travail de gouvernance et de schéma n'existe que sur le poste | `git status` | Haute — risque de perte ; contredit « aucune décision perdue » | À traiter par le Fondateur : commits scindés par sujet (voir §7.6) |
| C-05 | Branche `feat/schemas-de-domaine` portant du WIP identité, consentements, site public, cubage et handoff Forge | `git status`, `git branch` | Moyenne | Idem C-04 |

### 5.2 Hygiène du dépôt

| # | Constat | Traitement |
|---|---|---|
| C-06 | 20 captures d'écran, un fichier HTML et un document personnel `.docx` à la racine (non suivis) | **Corrigé** : déplacés dans `tmp/` (ignoré par git) ; règle `.gitignore` ajoutée pour `/*.png`, `/*.jpg`, `/*.html`, `/*.docx`, `/*.pdf` |
| C-07 | Trois rapports de sécurité/pentest versionnés à la racine | **Corrigé** : `git mv` vers `23_QUALITY_MANAGEMENT/AUDITS/` ; liens du bilan hebdomadaire mis à jour ; les références par nom de fichier dans le code restent valides |
| C-08 | `.claude/skills/` contient plusieurs centaines de skills sans rapport (DOCA, Jetson, TAO, NeMo…) ; chaque session d'agent paie ce contexte | Non traité — élagage à décider (skill `skill-management`) |
| C-09 | Espace de travail Devin configuré sur `a:/Quintessences`, chemin inexistant | Non traité — configuration de poste |

### 5.3 Goulot structurel : validation humaine et données

C'est le constat principal de cet audit.

- **Validation scientifique.** Les 30 scénarios GSIE-Bench sont bloqués en
  `pending_expert_review` depuis mi-août. RFC-0039 et DEC-000067 exigent deux
  avis experts indépendants avant tout manifeste Closed. Aucun expert n'est
  identifié, aucune démarche de recrutement n'est planifiée dans la roadmap.
  La thèse « la connaissance est le produit » repose sur une porte que seuls
  des humains extérieurs peuvent ouvrir.
- **Données.** Après la construction d'un pipeline complet (adapters, santé,
  resolver, QualityAssessment, promotion Silver, object storage, handoff
  Forge), le Registry contient un seul actif de 569 octets. SoilGrids WCS est
  qualifié (DEC-000078) mais FETCH reste fermé : la porte est prête, personne
  ne l'a franchie.
- **Terrain.** Aucun forestier n'a utilisé GeoSylva en conditions réelles.
  Toutes les recettes sont faites par ADB sur un appareil avec des comptes
  synthétiques.

### 5.4 Périmètre vs capacité

Le portefeuille documenté comprend neuf applications, un Hub Unreal 5.8 +
Cesium, un maillage territorial (RFC-0035/0036), une cascade LLM T1/T2/T3, une
synchronisation LoRa/Meshtastic, WeatherNext → Atmos, un jumeau numérique
fédéré (RFC-0037) et un orchestrateur d'agents auto-évolutif — pour un
fondateur seul assisté d'agents. DEC-000074 a recentré la V1 mais
`ROADMAP.md` présente encore tous ces chantiers au même niveau ; un lecteur ne
distingue pas ce qui est gelé de ce qui est actif.

### 5.5 Signaux techniques secondaires

- 371 tests ignorés (~11 %) : dette masquée, non catégorisée (Docker absent,
  réseau, obsolètes ?).
- `/ready` exige environ deux minutes de démarrage des moteurs.
- Six branches dependabot ouvertes ; l'audit CVE d'août est fait mais les
  mises à jour ne sont pas fusionnées.
- Surface publique périmée : le domaine sert l'ancienne landing,
  `api.quintessences-platform.com/health` renvoie 530, Google OAuth
  `not_configured`.

## 6. Ce que cet audit ne conclut pas

Il ne mesure ni la qualité scientifique des règles ingérées, ni la robustesse
réelle des moteurs sur des données non synthétiques, ni la sécurité effective
du déploiement. Il ne remplace pas la recette GEO-005 et ne modifie aucun
statut de livrable.

## 7. Propositions de vision

### 7.1 Redéfinir la V1 par son utilisateur

> V1 = un forestier réel, une forêt réelle, une semaine de terrain, avec
> GeoSylva 3.1 seule (hors ligne), puis une analyse GSIE rejouable sur ses
> données.

Un seul critère de sortie pour G1 → G5. Structure partenaire à identifier :
ONF, CRPF, coopérative ou lycée forestier (les dossiers BTS déjà exploités
pour GSIE-Bench sont une piste naturelle).

### 7.2 Gel explicite « Horizon 2 »

Une décision unique plaçant hors chemin critique, avec date de réexamen :
Hub Unreal, Territorial Mesh, cascade LLM, LoRa, WeatherNext/Atmos,
Aeris/Atlas/Terra, Orchestre auto-évolutif. Les documents restent ; la
roadmap ne montre plus que G1 → G5 en tête. Proposition déposée : DEC-000083
(statut Proposé).

### 7.3 Recruter deux experts maintenant

Seule action qu'aucun agent ne peut accomplir. Publier la suite Open/Silver de
GSIE-Bench (déjà exécutable) comme benchmark forestier ouvert est un moyen
d'attirer ce profil.

### 7.4 Une donnée réelle de bout en bout

Ouvrir FETCH pour une seule distribution (SoilGrids WCS, déjà qualifiée) sur
une emprise limitée, jusqu'à Silver. Valide le pipeline avec des octets réels
et donne au Pedology Engine son premier contexte non synthétique.

### 7.5 Réparer la mémoire

- `PROJECT_MEMORY.md` → tableau de bord d'une page (phase, gates, moteurs et
  niveau de preuve, cinq dernières DEC, blockers). Draft déposé :
  `22_PROJECT_MEMORY/DRAFT_PROJECT_MEMORY_TABLEAU_DE_BORD.md`.
- Journal chronologique actuel → `22_PROJECT_MEMORY/JOURNAL_2026-08.md`.
- Formaliser trois niveaux de preuve : **prouvé local**, **prouvé sur TEST**,
  **prouvé terrain**. Aucune case de roadmap cochée sans indiquer lequel.

### 7.6 Actions mécaniques restantes

1. Scinder le WIP courant en commits par sujet : identité/consentements ;
   cubage offline-first (RFC-0042, DEC-000082, migrations 0056-0057,
   `gsie_api/geosylva/`) ; handoff Forge ; site public ; spécifications et
   audits. Renommer ou fermer `feat/schemas-de-domaine`.
2. Inventorier les 371 tests ignorés et les classer (environnement / obsolète
   / à réactiver).
3. Fusionner ou fermer les six branches dependabot.
4. Élaguer `.claude/skills/`.

### 7.7 Positionnement à long terme

Le différenciateur n'est ni l'application mobile ni le Hub 3D : c'est la
chaîne Evidence → Knowledge → … → Validation, traçable et benchmarkée,
appliquée à la forêt. Si la V1 prouve qu'un diagnostic stationnel GSIE est
explicable, sourcé et rejouable sur une vraie parcelle, GeoSylva devient le
canal de collecte, GSIE-Bench la preuve publique, et les autres applications
des projections légitimes. Le rythme de construction d'infrastructure n'est
soutenable que si le trimestre suivant est celui de la preuve terrain.

## 8. Modifications effectuées dans cette session

| Fichier | Action |
|---|---|
| `03_DECISIONS/DEC-000078-offline-first-cubage-geosylva.md` → `03_DECISIONS/DEC-000082.md` | Renommage + note de traçabilité |
| `GSIE/API/AGENTS.md` | Score de mutation reformulé |
| `PENTEST_AUTH_CONNEXION_2026-08-07.md`, `SECURITY_AUDIT_2026-08-07.md`, `PROMPT_PENTEST_CLAUDE.md` | `git mv` vers `23_QUALITY_MANAGEMENT/AUDITS/` |
| `GSIE/DOCUMENTATION/BILAN_HEBDOMADAIRE_2026-08-03_2026-08-10.md` | Liens relatifs mis à jour |
| `.gitignore` | Règle contre les binaires à la racine |
| Captures, `bing1.html`, `.docx` | Déplacés dans `tmp/` (non versionné) |
| `03_DECISIONS/DEC-000083.md` | Créé — Proposé |
| `22_PROJECT_MEMORY/DRAFT_PROJECT_MEMORY_TABLEAU_DE_BORD.md` | Créé — Draft |
| `CHANGELOG.md`, `PROJECT_MEMORY.md`, `ROADMAP.md` | Entrées de synchronisation |

Aucun document `Locked` n'a été modifié. Aucun push, aucune fusion.
