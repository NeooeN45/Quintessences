# Leçon 003 — Repos externes

- **Date** : 2026-08-08
- **Source** : AGENTS.md
- **Contexte** : GeoSylva, QGISIA, Forge sont des repos git indépendants

## Règle

Ne JAMAIS committer dans le repo parent les fichiers de :
- `apps/GeoSylva/` (GitHub: NeooeN45/GeoSylva)
- `apps/QGISIA/` (GitHub: NeooeN45/QGISIAPRO)
- `Forge/` (GitHub: NeooeN45/Forge)

Ces dossiers sont ignorés par `.gitignore` du repo parent.
Pour travailler dessus : `cd` dans le dossier, utiliser son propre git.
