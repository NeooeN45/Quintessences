# 06 — Research

## Objectif

Regrouper les travaux scientifiques, bibliographiques et expérimentaux
qui fondent les choix de GSIE. Chaque règle, seuil ou corrélation doit
reposer sur une source identifiable.

## Responsabilités

- Documenter les sources scientifiques
- Répertorier les références (articles, thèses, guides sylvicoles)
- Soutenir la base de connaissances (`07_KNOWLEDGE`)

## Ce qui peut y être ajouté

- Études bibliographiques
- Notes de recherche
- Hypothèses et protocoles

## Ce qui est interdit

- Ajouter une connaissance sans source
- Implémenter du code

## Les cinq registres d'opportunités (depuis 2026-08-16)

À consulter avant tout : ces cinq registres classent et actualisent toutes les opportunités modèles, outils et architectures applicables à Quintessences.

| Registre | Cible | Opportunités | Lien |
|---|---|---|---|
| **GSIE Serveur** | API, RAG, orchestration, HPC | 23 actives + plateforme data | [REGISTRE_GSIE_SERVEUR.md](REGISTRE_GSIE_SERVEUR.md) |
| **Applications mobiles** | GeoSylva, Artemis (terrain, hors-ligne) | 10 actives | [REGISTRE_APPS_MOBILES.md](REGISTRE_APPS_MOBILES.md) |
| **GSIE PC** | Desktop, QGIS, traitement LiDAR lourd | 20 actives | [REGISTRE_GSIE_PC.md](REGISTRE_GSIE_PC.md) |
| **Hub Unreal Engine** | Centre de Commandement, GCS-Cinéma | 12 actives | [REGISTRE_HUB_UNREAL.md](REGISTRE_HUB_UNREAL.md) |
| **Applications clientes** | Ignis, Hydro, Flora, Terra, Aeris, Artemis, Atlas | 32 actives | [REGISTRE_APPS_CLIENTES.md](REGISTRE_APPS_CLIENTES.md) |

**À savoir :**
- Identifiants stables `OPP-xxx` : une opportunité entre une fois et n'en sort jamais — elle change de rang et de statut.
- Chaque registre a ses règles non négociables (voir §2 de chaque fichier).
- Les verrous ne sont pas des pénalités : un corpus manquant est une tâche, pas une raison de descendre le rang.
- Renvois croisés entre registres : les opportunités se connectent à travers les cibles.

---

## Mission WeatherNext 2 → Atmos (2026-08-18)

Cette étude évalue le dépôt officiel WeatherNext v0.3.0 et les équivalents
scientifiques utiles aux autres domaines Quintessences. Elle ne vaut pas
adoption de modèle : chaque candidat reste soumis à une licence qualifiée, un
benchmark territorial et une validation humaine.

- [WEATHERNEXT2_DEEP_DIVE.md](WEATHERNEXT2_DEEP_DIVE.md) — dépôt, architecture,
  données, inference, ensembles, matériel et limites.
- [QUINTESSENCES_SCIENTIFIC_TECHNOLOGY_HORIZON.md](QUINTESSENCES_SCIENTIFIC_TECHNOLOGY_HORIZON.md)
  — horizon multi-domaines et technologies pivots.
- [TOP_20_WEATHERNEXT_LIKE_TECHNOLOGIES.md](TOP_20_WEATHERNEXT_LIKE_TECHNOLOGIES.md)
  — classement initial et Top 5 à tester.
- [WEATHERNEXT_ATMOS_POC_PLAN.md](WEATHERNEXT_ATMOS_POC_PLAN.md) — POC flux,
  normalisation, stockage, API, downscaling et IGNIS.

Voir aussi les architectures :

- `../ARCHITECTURE/ATMOS_WEATHERNEXT_ARCHITECTURE.md`
- `../ARCHITECTURE/IGNIS_PROBABILISTIC_WEATHER_INTEGRATION.md`
- `../ARCHITECTURE/ADR_WEATHERNEXT_ATMOS.md`

---

## Archive des sources (depuis 2026-08-16)

Les documents sources ont été archivés dans [ARCHIVE/](ARCHIVE/) après consolidation dans les registres. Voir [ARCHIVE/README.md](ARCHIVE/README.md) pour détails et priorités de consultation.

---

## Liens

- **07_KNOWLEDGE** : les connaissances sont sourcées depuis ici
- **08_DATASETS** : les datasets sont validés par la recherche
- **21_EXPERIMENTS** : les bancs (EXP-xxxx) sont tracés depuis la recherche
