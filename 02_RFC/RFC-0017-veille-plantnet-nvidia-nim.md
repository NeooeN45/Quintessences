# RFC-0017 — Veille technologique : Pl@ntNet (identification botanique) et NVIDIA NIM (couche IA serveur)

| Champ | Valeur |
|---|---|
| **ID** | RFC-0017 |
| **Statut** | Adopté (2026-07-20, DEC-000029) — scindé en RFC-0018 et RFC-0019 |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-20 |
| **Auteur** | Camille Perraudeau (Fondateur) — proposition rédigée à partir de la veille externe versée en `GSIE/RESEARCH/VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20.md` |
| **Impact potentiel** | Botanical Engine, GeoSylva (module identification + offline-first), futur `gsie-ai-gateway` (nouveau composant transverse), Flora, Ignis (détection/vidéo), Hydro/Atmos (Earth2Studio), Hub UE5.8 (OpenUSD, sans dépendance runtime) |
| **Lois fondatrices** | GSIE-CON-000 (primauté Constitution), GSIE-CON-001 (l'IA assiste, ne décide jamais), GSIE-CON-002 (science sourcée), GSIE-CON-005 (traçabilité) |
| **RFC liées** | RFC-0014 (garde-fou anti-invention), RFC-0015 (Environmental Model Fabric — registre de modèles, licences, domaine de validité), RFC-0016 (schéma forestier — `AutecologyProfile` pertinent pour l'identification d'essences) |
| **Décision liée** | Aucune — RFC en discussion, aucune décision `03_DECISIONS/` n'est encore prise |

---

## 1. Objet

Ce RFC ne propose **pas** une implémentation. Il formalise deux pistes
d'évolution technique repérées par veille externe, afin qu'elles soient
débattues et, le cas échéant, scindées en RFC d'exécution distincts :

1. **Identification botanique assistée par IA** (Pl@ntNet en ligne +
   piste d'un modèle embarqué offline pour les essences forestières
   françaises), rattachable au Botanical Engine et à GeoSylva.
2. **Couche IA serveur optionnelle via NVIDIA NIM/Blueprints** (RAG
   scientifique, recherche sémantique, vision, météo, voix,
   optimisation), transverse à plusieurs moteurs et applications.

Le détail complet de l'analyse (avantages, architecture, tarifs,
limites) est conservé dans le document de veille cité ci-dessus et
n'est pas dupliqué ici.

## 2. Ce que ce RFC ne couvre pas

- Le choix définitif d'un fournisseur commercial (Pl@ntNet, NVIDIA) —
  nécessite validation contractuelle/juridique séparée (`19_LEGAL/`).
- L'implémentation de code métier — interdite sans RFC adopté
  (règle §2.3 de `CLAUDE.md`).
- La création du composant `gsie-ai-gateway` — s'il est retenu, il
  fera l'objet de sa propre spécification (`05_SPECIFICATIONS/`) une
  fois ce RFC adopté.

## 3. Piste 1 — Identification botanique (Pl@ntNet)

### 3.1 Principe retenu si adopté

Toute identification automatique est une **suggestion**, jamais une
vérité. Statut `SUGGESTION_IA` → `VALIDEE_UTILISATEUR` uniquement après
confirmation humaine (cohérent avec GSIE-CON-001). Aucune valeur
`SUGGESTION_IA` ne doit alimenter un cubage, un conseil sylvicole ou
une conclusion écologique.

### 3.2 Architecture si adoptée

`GeoSylva → serveur GSIE sécurisé → Pl@ntNet → normalisation
Quintessences → validation humaine`. Clé API jamais embarquée côté
client. Compatible offline-first : capture locale, file d'attente,
synchronisation au retour réseau.

### 3.3 Préalables avant toute implémentation

- Confirmation écrite de Pl@ntNet/CIRAD sur les conditions d'usage
  commercial (au-delà du quota gratuit de 500/jour) avant mise en
  production.
- Respect des licences CC BY-SA (photos de référence) et CC BY
  (observations) — attribution à intégrer dans l'UI GeoSylva.
- Schéma de traçabilité à spécifier formellement (champs listés en
  §1.3 du document de veille) — probable extension satellite au
  schéma forestier RFC-0016, pas une nouvelle ontologie.

### 3.4 Piste secondaire — modèle embarqué offline

Non retenue à ce stade comme prioritaire : nécessite (a) un corpus
d'entraînement forestier français dédié à constituer, (b) une
vérification que le mode offline officiel Pl@ntNet ne peut être
réutilisé sans accord, (c) une capacité de calcul d'entraînement hors
du poste actuel du fondateur. À rouvrir après un premier retour
d'usage sur l'intégration en ligne.

## 4. Piste 2 — Couche IA serveur (NVIDIA NIM)

### 4.1 Principe retenu si adopté

NIM/Blueprints n'est **jamais** l'autorité de vérité. PostgreSQL/
PostGIS/Apache AGE restent la vérité canonique ; tout index ou
résultat NVIDIA est une projection reconstruisible. Les moteurs GSIE
déterministes (Forest Dynamics, calculs dendrométriques, etc.) ne sont
jamais remplacés par un LLM. Un VLM ne déclenche jamais seul une
alerte incendie.

### 4.2 Composant proposé si adopté

Un `gsie-ai-gateway` unique exposant des routes stables (`/ai/chat`,
`/ai/embed`, `/ai/rerank`, `/ai/research`, `/ai/transcribe`,
`/ai/vision`), journalisant systématiquement modèle, version, prompt,
coût, latence et confiance — cohérent avec l'exigence de traçabilité
GSIE-CON-005 et avec le registre de modèles déjà posé par RFC-0015
(`ModelRegistry`/`ModelArtifact`/`LicenseRecord`).

### 4.3 Priorisation proposée si adopté

P0 : RAG scientifique (recherche documentaire GSIE), garde-fou
(NeMo Guardrails), banc d'essai (`GSIE-Eval-FR`). P1 : agent de
recherche AI-Q, météo/climat (Earth2Studio), voix terrain (Parakeet),
optimisation de moyens (cuOpt). P2+ : vision/vidéo (DeepStream/TAO/
VSS), géospatial accéléré, pipeline Hub UE5.8. Détail complet §2.2 du
document de veille.

### 4.4 Préalables avant toute implémentation

- Aucun auto-hébergement NIM en production sur le matériel actuel
  (non supporté sous Windows, GPU insuffisant) — prototypage par
  endpoints hébergés et Brev uniquement, avec plafond d'heures GPU
  défini avant chaque expérience.
- Vérification de licence par actif NVIDIA utilisé (modèles,
  Blueprints, jeux de données Earth2Studio) avant toute intégration,
  conformément à RFC-0015 (registre de modèles/licences).
- Benchmark français obligatoire avant adoption d'un modèle
  (Nemotron Embed/Rerank, Nemotron Parse) — pas de présomption de
  bonne performance en français sans test sur corpus GSIE.
- Candidature NVIDIA Inception à envisager seulement après
  immatriculation de la micro-entreprise et mise en ligne d'un site,
  en la positionnant comme éditeur logiciel.

## 5. Alternatives considérées

- **Ne rien faire / statu quo** : reste possible sans risque, mais
  prive GeoSylva d'une aide à l'identification et prive GSIE d'un RAG
  scientifique performant. Rejeté comme option par défaut à long
  terme, mais acceptable comme position actuelle tant que ce RFC n'est
  pas débattu plus avant.
- **Construire un RAG et un module d'identification 100 % maison**
  (sans NVIDIA ni Pl@ntNet) : plus long, plus coûteux à court terme,
  mais élimine toute dépendance externe. À comparer explicitement lors
  du débat du RFC.

## 6. Suite donnée

Le fondateur a validé ce RFC le 2026-07-20 (DEC-000029) en tant que
**cadrage**, avec scission immédiate en deux RFC d'exécution
autonomes, chacun repartant en `Draft` et devant suivre son propre
cycle Review → Décision avant toute implémentation :

- **RFC-0018** — Identification botanique assistée (Pl@ntNet) et
  extension du Botanical Engine.
- **RFC-0019** — `gsie-ai-gateway` et intégration NVIDIA NIM.

Ce document (RFC-0017) reste la référence de veille et de priorisation
(§2.2, §5) ; il n'autorise par lui-même aucun code métier — seuls
RFC-0018 et RFC-0019, une fois adoptés à leur tour, le pourront.
