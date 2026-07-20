# Veille technologique — Pl@ntNet et NVIDIA NIM pour Quintessences

| Champ | Valeur |
|---|---|
| **Type** | Veille technologique externe |
| **Date** | 2026-07-20 |
| **Origine** | Analyse conduite par le fondateur (Camille Perraudeau) via ChatGPT, versée telle quelle pour traçabilité, puis reprise dans `02_RFC/RFC-0017-veille-plantnet-nvidia-nim.md` |
| **Statut** | Matière première non validée scientifiquement — sert de base de discussion RFC, ne constitue pas une source GSIE au sens SCI-001 |

---

## 1. Pl@ntNet — identification botanique assistée

### 1.1 Évaluation de départ

- Aide à l'identification : 9/10.
- Identification professionnelle autonome : 4/10.
- Position retenue : **assistant botanique, jamais vérité automatique**.

### 1.2 Ce que l'API apporte

- Jusqu'à 5 photos par individu (feuille, fleur, fruit, écorce).
- Espèces candidates + scores de confiance, famille botanique, noms
  vernaculaires, identifiants GBIF/POWO, version du moteur.
- Cas d'usage GeoSylva : essences, régénération, plantes indicatrices,
  relevés floristiques/IBP, espèces invasives ou patrimoniales,
  diagnostic stationnel, préremplissage d'observation Flora, pistes de
  maladies/ravageurs (liste limitée).

### 1.3 Fonctionnement professionnel proposé

- Ne jamais écrire directement une essence après une seule photo.
- Afficher 3 hypothèses, confiance, écart entre résultats, organes
  photographiés, boutons Confirmer / Ajouter une photo / Identifier
  manuellement, avertissement si incertitude.
- Statut `SUGGESTION_IA` → `VALIDEE_UTILISATEUR` uniquement après
  confirmation d'un technicien. Tant que non validée : aucune valeur
  déclenchante (cubage, conseil sylvicole, conclusion écologique).
- Traçabilité à conserver : espèces candidates + scores, identifiants
  taxonomiques, version du moteur Pl@ntNet, date d'analyse, empreinte
  numérique des photos, décision + identité du validateur, niveau de
  preuve/incertitude.

### 1.4 Compatibilité offline-first

- Photos et observation enregistrées localement ; identification mise
  en file d'attente, envoyée au retour réseau, notification à
  réception ; recherche manuelle locale en secours.
- Piste long terme : petit modèle embarqué (essences forestières
  françaises), Pl@ntNet en vérification en ligne ensuite.

### 1.5 Architecture recommandée

`GeoSylva → serveur GSIE sécurisé → Pl@ntNet → normalisation
Quintessences → validation humaine`. Clé API jamais côté client
(extraction APK). Retrait des métadonnées GPS avant envoi.

### 1.6 Prix et licences (à confirmer par écrit avant usage commercial)

- Quota gratuit : 500 identifications/jour.
- Usage commercial : 1 000 € HT / 200 000 requêtes/an, puis 5 € HT par
  tranche de 1 000 requêtes.
- Attribution obligatoire des photos de référence (CC BY-SA) ;
  données d'observation CC BY.
- API multi-espèces par placette : en bêta, accès sur demande.

### 1.7 Piste — modèle embarqué français hors ligne

- Le mode hors ligne officiel Pl@ntNet est réservé à son app mobile ;
  l'API ne permet pas de récupérer ce modèle sans accord.
- Proposition : pack téléchargeable « Essences forestières — France
  métropolitaine » (TAXREF comme référentiel principal, GBIF/POWO en
  complément), modèle de vision léger (MobileNet/EfficientNet-Lite,
  ~100-250 taxons prioritaires, quantifié INT8, LiteRT sur Android).
- Le modèle doit savoir répondre « espèce inconnue / résultat
  insuffisant » plutôt que de forcer un taxon du catalogue.
- Données d'entraînement de départ : Pl@ntNet-300K (CC BY 4.0,
  ~306 000 images, 1 081 espèces) — insuffisant seul, nécessite un
  corpus forestier français dédié (saisons, organes, espèces proches,
  hybrides, introduites).
- Stratégie hybride recommandée : offline (catalogue + IA
  spécialisée) / online (vérification Pl@ntNet) / Quintessences
  (normalisation taxonomique, contexte écologique, preuve) /
  validation humaine (seule habilitée à rendre l'essence exploitable).
- Contact CIRAD/Pl@ntNet à envisager pour licence du modèle embarqué
  ou partenariat.

---

## 2. NVIDIA NIM / Blueprints / Skills / Brev

### 2.1 Cadrage

Recherche datée du 20/07/2026 : ~42 Blueprints, ~299 Skills, ~139
modèles disponibles. Recommandation : ne pas généraliser NIM, l'utiliser
comme **couche serveur optionnelle** pour RAG scientifique, recherche,
vision, météo, voix, optimisation — les moteurs GSIE restent
déterministes, l'offline-first est préservé.

| Offre | Nature | Usage recommandé |
|---|---|---|
| NIM Models | API / conteneurs optimisés | Prototyper, éventuellement héberger |
| Blueprints | Architectures de référence | Récupérer les idées, pas tout déployer |
| NVIDIA Skills | Instructions pour Codex/Claude Code | Gain immédiat pour développer Quintessences |
| Brev | GPU cloud temporaire | Tests lourds, benchmarks, entraînements courts |

### 2.2 Priorisation proposée

- **P0** — NeMo Retriever + RAG Blueprint (base documentaire
  scientifique), Nemotron Embed + Rerank (recherche sémantique FR),
  NeMo Evaluator (banc d'essai GSIE-Eval-FR), NeMo Guardrails
  (garde-fou), NVIDIA Skills (aide au développement).
- **P1** — AI-Q Blueprint (chercheur scientifique avec citations),
  Earth2Studio (Atmos/Hydro/météo incendie), cuOpt (affectation de
  moyens/itinéraires), Parakeet ASR (saisie vocale terrain, français
  supporté).
- **P2** — DeepStream + TAO (détection fumée/feu/objets), VSS
  (recherche vidéo), Streaming Data to RAG (flux radio/capteurs),
  RAPIDS/cuDF/cuSpatial (géospatial accéléré), OpenUSD (pipeline
  assets vers le Hub Unreal).
- **P3** — PhysicsNeMo (modèles de substitution crues/propagation),
  Jetson (passerelle IA embarquée terrain).

### 2.3 Points de vigilance identifiés

- Config locale de référence du Blueprint RAG : ≥3 GPU H100/B200/RTX
  Pro 6000 — récupérer l'architecture, pas le déploiement complet.
  Vérité canonique = PostgreSQL/PostGIS/Apache AGE ; index NVIDIA =
  projection reconstruisible, jamais autoritaire.
- Nemotron Parse : langue annoncée = anglais, ne pas supposer une
  bonne performance sur documents scientifiques français sans
  benchmark.
- Earth2Studio agrège des modèles/données à licences propres ; une
  prévision Earth-2 doit être présentée comme scénario, pas comme
  alerte réglementaire.
- Un VLM (DeepStream/TAO/VSS) ne doit jamais déclencher seul une
  alerte incendie : chaîne détecteur déterministe → fusion capteurs →
  vérification VLM → opérateur humain.
- Connecteur Omniverse actuel : documenté pour Unreal Engine 5.3, non
  garanti en runtime packagé — ne pas en faire une dépendance du Hub
  UE5.8 ; utiliser OpenUSD comme format d'échange seulement.
- NIM documenté comme supporté sous Linux, non testé sous
  Windows/WSL — auto-hébergement non réaliste sur le poste actuel
  (RTX 3050 Laptop 4 Go, Windows 11). Passer par les endpoints hébergés
  et Brev pour prototyper.
- Programme développeur gratuit : prototypage via endpoints, et
  auto-hébergement NIM pour recherche/dev/test jusqu'à 16 GPU. Servir
  de vrais utilisateurs = usage de production nécessitant une licence
  NVIDIA AI Enterprise ou un endpoint partenaire.
- Tarifs indiqués : 4 500 $/GPU/an (plein tarif), 1 125 $/GPU/an
  (Inception/établissements éligibles), ~1 $/GPU/heure en cloud.
- Piste : candidater à NVIDIA Inception après immatriculation de la
  micro-entreprise et mise en ligne d'un site — programme gratuit,
  sans prise de participation, exclut le conseil pur (positionner
  Quintessences comme éditeur logiciel).

### 2.4 Architecture recommandée (gateway)

`GSIE AI Gateway` exposant `/ai/chat`, `/ai/embed`, `/ai/rerank`,
`/ai/research`, `/ai/transcribe`, `/ai/vision`, journalisant modèle,
version, prompt, paramètres, citations, coût, durée, confiance,
utilisateur. Clés NVIDIA exclusivement côté serveur. Permet de comparer
Nemotron / Mistral / OpenAI / autres sans verrouillage fournisseur.

### 2.5 Explicitement déconseillé (à ce stade)

- Auto-héberger le Blueprint RAG complet.
- Acheter un GPU de production immédiatement.
- Faire dépendre GeoSylva du réseau.
- Entraîner un LLM directement sur tous les PDF.
- Remplacer PostgreSQL/PostGIS/AGE par Milvus ou Elasticsearch.
- Utiliser un LLM pour les calculs dendrométriques.
- Laisser un VLM déclencher seul une alerte incendie.
- Faire du connecteur Omniverse une dépendance du runtime UE5.8.
- Utiliser les Blueprints actuellement dépréciés (ex. Flood
  Intelligence, CorrDiff).
- Payer une licence NIM de production avant clients/charge mesurée.

### 2.6 Feuille de route à 90 jours proposée (non engagée)

1. **J1-30** — `gsie-ai-gateway`, Skills ciblées, clés sécurisées,
   `GSIE-Eval-FR` (100 questions), 100-300 documents FR autorisés,
   test Nemotron Embed/Rerank, journalisation systématique.
2. **J31-60** — recherche hybride + citations exactes, filtres
   géo/climat/taxonomie, comparaison multi-modèles, premier agent
   AI-Q adapté GSIE, NeMo Evaluator en CI, NeMo Guardrails. Seuils
   proposés : Recall@10 ≥ 85 %, précision citations ≥ 95 %, aucune
   valeur calculée sans moteur déterministe ou source, abstention si
   preuve insuffisante.
3. **J61-90** — Parakeet (50 scénarios terrain), Earth2Studio
   (territoire pilote), cuOpt (scénario Ignis), VSS (petit corpus
   drone via Brev), bilan coût/latence/gain, décision de poursuite ou
   abandon par prototype.

---

## 3. Ce que cette veille n'est pas

- Ce n'est pas une décision (`03_DECISIONS/`) ni un RFC adopté.
- Aucune donnée scientifique ci-dessus n'est sourcée au niveau exigé
  par `GSIE-CON-005` — elle documente une opportunité, pas une
  connaissance validée.
- Aucun code métier ne doit être écrit sur cette base avant RFC dédié
  et, pour Pl@ntNet, confirmation écrite des conditions commerciales.
