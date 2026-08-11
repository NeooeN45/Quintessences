# Pack de développement GeoSylva - Quintessences

## Objectif

Ce dossier transforme les décisions fonctionnelles et architecturales prises autour de GeoSylva et de l'écosystème Quintessences en documents directement exploitables par Devin, GLM-5.2, Claude Code, Codex ou une équipe humaine.

GeoSylva est défini comme le client forestier mobile, professionnel et offline-first de Quintessences. Il ne s'agit plus d'une application Android isolée : il communique avec le serveur GSIE, partage une identité unique avec les autres applications, reçoit des packs préparés par le serveur et exécute localement les moteurs indispensables au terrain.

## Ordre de lecture recommandé

1. `01_VISION_PRODUIT.md`
2. `02_ARCHITECTURE_GSIE_GEOSYLVA.md`
3. `03_IDENTITE_AUTHENTIFICATION.md`
4. `04_SYSTEME_DE_PACKS_QPIS.md`
5. `05_NOYAU_SCIENTIFIQUE_FORESTIER.md`
6. `06_METIERS_MISSIONS_PROTOCOLS.md`
7. `07_MOTEUR_GEOSPATIAL.md`
8. `08_TREEVISION.md`
9. `09_DONNEES_SYNCHRONISATION_SECURITE.md`
10. `10_ROADMAP_IMPLEMENTATION.md`
11. `11_PROMPT_DEVIN_GLM52.md`
12. `12_MODELES_RFC_ADR.md`

## Règles non négociables

- Offline-first réel.
- Une donnée commune n'existe qu'une seule fois dans Quintessences.
- UUID global pour toute entité synchronisable.
- Aucun calcul scientifique important sans méthode, version, source, domaine de validité et trace.
- L'IA assiste, explique et structure ; elle ne remplace pas les moteurs déterministes.
- Le serveur prépare les packs et absorbe la complexité des API externes.
- Les données non synchronisées ne doivent jamais être supprimées automatiquement.
- GeoSylva reste utilisable sans réseau pendant une durée définie par la politique du compte ou de l'organisation.
- Les fonctionnalités doivent être adaptées au métier, à la mission et au contexte, pas seulement au rôle statique.
- Les évolutions doivent être livrées par étapes testables, avec migrations et possibilité de retour arrière.

## Livrables inclus

- Un document maître DOCX.
- Les spécifications Markdown modulaires.
- Un prompt maître pour Devin + GLM-5.2.
- Une feuille de route technique.
- Des modèles RFC et ADR.
