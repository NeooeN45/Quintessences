# Matrice de traçabilité EXP-0001

| Exigence | Interprétation dans EXP-0001 | Code/artefact | Test ou preuve |
|---|---|---|---|
| RFC-0003 — offline-first | aucun réseau requis pour construire, vérifier et calculer | CLI `demo`, fixtures locales | `make demo` |
| Technique T-8 | fonctions critiques disponibles hors-ligne | `capsule.py`, `bench.py` | suite unitaire |
| CON-002 — science | aucun cas non revu présenté comme validé | état `scientific_review` | rapport Golden Bench |
| CON-004 — explicabilité | attendu, obtenu, tolérance et écart exposés | `BenchCaseResult` | test du rapport |
| CON-005 — traçabilité | manifeste, empreintes, sources et ID stables | schéma + fixtures | vérification intégrité |
| CON-010 — historique | version de schéma, d'algorithme et de cas | JSON versionnés | validation des champs |
| GEO-F-18 / GEO-NF-02 | paquet exploitable sans connexion | `.gsiecap` | scénario démonstration |
| ADR-III-10 | paquet local géolocalisé signé | ADR-008 + `capsule.py` | signature Ed25519 valide |
| Sécurité Zip Slip | aucun chemin hors racine | validateur de chemins | `test_rejects_path_traversal` |
| Intégrité | aucune altération silencieuse | SHA-256 signé | `test_rejects_tampered_payload` |
| Confiance externe | la capsule ne s'auto-approuve pas | clé publique fournie séparément | `test_rejects_untrusted_key` |
| Reproductibilité | mêmes entrées, même calcul et même rapport sémantique | Golden Bench | cas nominaux et limites |

## Écarts assumés

| Exigence cible | État | Prochaine preuve |
|---|---|---|
| Téléchargement dans GeoSylva | non commencé | test E2E serveur local → WorkManager |
| Installation atomique Android | non commencé | coupure simulée pendant installation |
| Anti-rollback | non couvert | refus d'une version antérieure signée |
| Rotation/révocation | non couvert | fixtures à deux générations de clés |
| Double revue scientifique | en attente | signatures de deux experts par cas |
| Données territoriales officielles | volontairement absentes | capsule pilote sous licence vérifiée |
| Lecture Hub UE 5.8 | non commencé | import de la fixture et affichage couche |

