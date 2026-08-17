# Reconstruction forensique du livrable 309 — Schéma de l'Encyclopédie

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-ARCH-309-R1 |
| **Statut** | Draft |
| **Date** | 2026-08-14 |
| **Nature** | Dossier de reconstruction non normatif |
| **Document historique** | [ENCYCLOPEDIA_DATABASE_SCHEMA.md](ENCYCLOPEDIA_DATABASE_SCHEMA.md) |
| **Décision de supersession** | [DEC-000022](../../03_DECISIONS/DEC-000022.md) |

---

## 1. Objet et limites

Ce dossier établit ce qui peut être prouvé au sujet du livrable 309 et relie
son intention historique au schéma GSIE v6.2 réellement présent. Il ne complète
pas le SQL ancien, ne restaure aucune section par conjecture et ne remplace
aucune source canonique.

Le livrable historique reste **Supersédé**. Le présent document reste **Draft**
tant que sa synthèse n'a pas suivi le cycle Review → Validated.

## 2. Preuve de la troncature

- Le fichier apparaît déjà tronqué dans son commit de création `990ae63`.
- Le fragment original correspond au blob Git
  `f1a68789752fe7751b20aa99fbdec0df587d6f96`.
- Il se termine dans la table `utilisateurs`, immédiatement après
  `nom_utilisateur`, sans type SQL, parenthèse de fermeture ni fin de fence.
- La référence interne au §10 montre que des sections prévues ne sont pas
  disponibles, mais ne permet pas d'en reconstituer le contenu exact.

Le scellement ajouté le 2026-08-14 ferme uniquement la fence Markdown et
marque explicitement l'interruption. Le fragment antérieur au marqueur est
contrôlé automatiquement par son empreinte de blob.

## 3. Contenu historique récupérable

La partie conservée décrit une architecture répartie entre PostgreSQL/PostGIS,
Neo4j, Elasticsearch et Jena. Les tables PostgreSQL 3.1.1 à 3.1.15 sont
présentes ; la table 3.1.16 `utilisateurs` est partielle. Aucun élément du dépôt
ne prouve la définition exacte de la suite.

Cette architecture à quatre stockages est historique. RFC-0011 et DEC-000022
l'ont remplacée par un métamodèle unifié et une persistance canonique
PostgreSQL/PostGIS ; les projections spécialisées restent optionnelles ou
différées.

## 4. Correspondance avec le schéma effectif v6.2

Cette table est une correspondance fonctionnelle, pas une migration automatique
ni une reconstitution du DDL manquant.

| Intention historique | Représentation effective ou canonique actuelle |
|---|---|
| Sources et provenance | `resource`, `source` |
| Datasets et leurs fichiers | `dataset`, `dataset_version`, `distribution`, `data_asset` |
| Connaissances et preuves | `assertion`, `evidence_assessment` et ressources associées |
| Versions et différences | `revision`, `snapshot`, `resource_diff` |
| Conflits | `conflict_cluster` |
| Relations du graphe | assertions, participants, prédicats et qualificateurs du métamodèle |
| Domaines de validité | contextes et qualificateurs typés du métamodèle |
| Utilisateurs | `user_account` et tables d'identité associées |
| Neo4j | non canonique ; AGE demeure soumis aux décisions et preuves dédiées |
| Elasticsearch | recherche PostgreSQL privilégiée ; projection externe non requise par ce dossier |
| Jena/RDF | projection régénérable, non source de vérité primaire |

Les noms ci-dessus servent à orienter la lecture. Le DDL généré et les modèles
restent la preuve technique détaillée.

## 5. Sources de vérité actuelles

- [ECOSYSTEM_METAMODEL.md](ECOSYSTEM_METAMODEL.md) : métamodèle de
  l'Encyclopédie.
- [RFC-0011](../../02_RFC/RFC-0011-metamodele-encyclopedie-v6.1.md),
  son [annexe 309](../../02_RFC/annexes/annexe-309.md) et
  [DEC-000022](../../03_DECISIONS/DEC-000022.md) : supersession et règles de
  conservation.
- [SCHEMA_DB.md](../DOCUMENTATION/SCHEMA_DB.md) : vue générée du schéma
  actuellement documenté.
- [Migration de référence v6.2](../API/alembic/versions/20260726_0001_baseline_gsie_v6_2.py) :
  baseline Alembic immuable.
- [Modèles SQLAlchemy](../API/src/gsie_api/) : implémentation répartie par
  contexte métier.

## 6. Vérifications et critères de clôture

- Le préfixe historique conserve l'empreinte Git
  `f1a68789752fe7751b20aa99fbdec0df587d6f96`.
- Les fences Markdown du livrable 309 sont équilibrées.
- Aucun DDL manquant n'est présenté comme retrouvé.
- Le statut du livrable historique reste **Supersédé**.
- Le garde de gouvernance ne doit plus signaler le fichier comme tronqué.

## 7. Limites de la reconstruction

Le schéma généré reflète l'état courant et peut évoluer avec de nouvelles
migrations. La baseline v6.2 demeure la référence immuable de son jalon. Toute
promotion du présent dossier exige une revue documentaire distincte ; elle ne
peut pas rétroactivement rendre complet ou Validated le livrable historique.

## 8. Historique

| Date | Évolution | Statut |
|---|---|---|
| 2026-08-14 | Création du dossier, scellement append-only et correspondance avec le schéma v6.2 | Draft |
