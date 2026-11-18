# Avenant Phase 4 — état actif du contrat Data Registry

**Contrat parent :** `GSIE_DATA_ADAPTER_CONTRACT_PHASE3.md`
**Statut de l'avenant :** actif
**Date :** 2026-08-30

## Mise au clair documentaire

Le document Phase 3 conserve son historique de rédaction, mais son contenu
est désormais la référence active de l'implémentation Phase 4. Le bootstrap
standard enregistre six factories lazy : GBIF, IGN, Indigénat Bellifa,
Météo-France, SoilGrids et TAXREF.

« Enregistré » signifie que la factory est connue du registre et peut être
instanciée à la demande. Cela ne signifie pas que le fournisseur est contacté,
qu'un fetch est autorisé ou qu'une source est promue. Ces décisions restent
portées par SCI-001, `source_coverage`, le contexte opérateur et les manifests.

## Capacités actuelles

| Adapter | Capacités opérationnelles | Limite explicite |
|---|---|---|
| GBIF | santé, requête, normalisation | résolution d'espèce ; pas d'occurrences en masse |
| TAXREF | santé, requête, normalisation | miroir GBIF déclaré ; pas de service INPN implicite |
| Bellifa | santé, requête, normalisation | fichier local versionné, sans réseau |
| SoilGrids | santé, requête, fetch borné, normalisation | WCS uniquement ; FETCH de production fermé par défaut |
| IGN | santé, requête, normalisation | cadastre et altitude ; pas de couche WFS arbitraire |
| Météo-France | santé, requête, normalisation | Météo des forêts seulement |

## Contrôles obligatoires

```powershell
python scripts/audit_source_coverage.py
python scripts/audit_engine_source_matrix.py
python scripts/audit_research_source_inventory.py
```

Les trois contrôles sont sans réseau et sans base. Ils doivent rester dans la
CI. Les tests fournisseurs simulés prouvent le contrat et la normalisation,
pas la disponibilité d'un service externe ; les tests de santé réels et les
campagnes de quota sont des preuves séparées, datées et révocables.

## Compatibilité décennale

Les moteurs dépendent d'identifiants SCI-001 et de capacités, pas d'URLs
fournisseur. Une évolution doit ajouter une nouvelle distribution ou un
successeur, conserver l'ancienne identité historique et rejouer la matrice,
les tests de contrat et les preuves de provenance.
