# EXP-0001 — Capsule territoriale et Golden Bench

| Champ | Valeur |
|---|---|
| **Statut** | Draft expérimental |
| **Date de départ** | 2026-07-18 |
| **Décision** | DEC-000028 (Proposé — renumeroté depuis DEC-000025 du pack d'origine, collision d'ID) |
| **Architecture** | ADR-008 (Proposé) |
| **Cible** | GSIE backend → GeoSylva Android → Hub UE 5.8 |

## Résultat attendu

Cette expérience fournit un premier objet GSIE **démontrable de bout en
bout**. Une commande construit un paquet territorial, le signe, le vérifie
hors-ligne, exécute des calculs de référence et produit un rapport JSON.

Elle prouve le mécanisme, pas la validité opérationnelle des données. Le
territoire et les observations sont synthétiques ; les cas scientifiques sont
marqués « revue experte requise » tant qu'ils ne sont pas contresignés.

## Démarrage rapide

Prérequis : Python 3.12. L'installation initiale peut nécessiter le réseau ;
la démonstration elle-même n'en utilise pas.

```bash
cd 21_EXPERIMENTS/EXP-0001_CAPSULE_TERRITORIALE
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make check
make demo
```

La démonstration écrit uniquement dans `build/` :

- `demo-territoire.gsiecap` — capsule signée ;
- `demo-public.pem` — clé publique à approuver côté client ;
- `verification-report.json` — contrôle cryptographique et fichiers ;
- `golden-bench-report.json` — résultats numériques et état de revue ;
- `demonstration-report.json` — synthèse exploitable par la CI.

Le scénario détaillé et les résultats attendus sont dans
[`DEMONSTRATION.md`](DEMONSTRATION.md).

## Commandes unitaires

```bash
PYTHONPATH=src python -m gsie_execution_kit keygen \
  --private-key build/private.pem --public-key build/public.pem

PYTHONPATH=src python -m gsie_execution_kit build \
  --source fixtures/territoire-reference \
  --output build/territoire.gsiecap \
  --private-key build/private.pem

PYTHONPATH=src python -m gsie_execution_kit verify \
  --capsule build/territoire.gsiecap \
  --public-key build/public.pem

PYTHONPATH=src python -m gsie_execution_kit bench \
  --cases fixtures/golden-bench \
  --report build/golden-bench-report.json
```

## Contenu

| Élément | Rôle |
|---|---|
| `src/gsie_execution_kit/` | constructeur, vérificateur, CLI et banc numérique |
| `schemas/` | contrat JSON du manifeste v1 |
| `fixtures/territoire-reference/` | petit territoire entièrement synthétique |
| `fixtures/golden-bench/` | cas numériques traçables et état de revue |
| `tests/` | succès, altération, mauvaise clé, archive hostile, tolérances |
| `ORGANISATION.md` | rôles, backlog, gates et définition de terminé |
| `SECURITY.md` | modèle de menace et passage vers la production |
| `GOLDEN_BENCH_CHARTER.md` | règles de gouvernance scientifique |
| `TRACEABILITY.md` | exigences GSIE reliées au code et aux tests |

## Hors périmètre de cette version

- téléchargement HTTP et reprise de transfert ;
- registre central de capsules ;
- chiffrement des données ;
- rotation/révocation des clés et protection anti-rollback ;
- rasters ou nuages de points réels ;
- API FastAPI, SDK Kotlin et interface GeoSylva ;
- validation scientifique par un expert indépendant.

## Condition de promotion

L'expérience ne passe vers le code de production qu'après validation de
DEC-000028 et ADR-008, revue scientifique, revue de sécurité, benchmark
Android et tests contractuels multi-langages.
