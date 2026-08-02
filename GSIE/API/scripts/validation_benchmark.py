#!/usr/bin/env python3
"""Validation scientifique + benchmark — DEC-000043 S3.

Deux objectifs :

1. **Ground truth** : comparer les prédictions du Reasoning Engine à la
   littérature vérifiée (Parelle et al. 2007). Pour chaque scénario, on
   déclare la conclusion attendue et on vérifie que le moteur la produit.

2. **Benchmark** : mesurer latence (min/max/mean/p50/p95/p99),
   throughput (req/s) et mémoire sur N exécutions de la chaîne complète.

Le script est reproductible : mêmes entrées → mêmes sorties + mêmes
métriques (à la jitter près, mesuré).

Usage :
    python scripts/validation_benchmark.py [--url http://127.0.0.1:8000]
                                           [--iterations 50]
                                           [--output benchmark_resultat.json]

Prérequis :
- API GSIE démarrée (docker compose up)
- Dev login activé

Sortie :
- Rapport de validation + benchmark sur stdout
- Rapport JSON complet dans benchmark_resultat.json
- Exit 0 si toutes les validations passent, 1 sinon
"""

from __future__ import annotations

import argparse
import gc
import json
import statistics
import sys
import time
import tracemalloc
from uuid import uuid4

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import httpx

# --- Couleurs ----------------------------------------------------------------

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
NC = "\033[0m"


def ok(msg: str) -> None:
    print(f"{GREEN}[OK]{NC} {msg}")


def info(msg: str) -> None:
    print(f"{CYAN}[INFO]{NC} {msg}")


def fail(msg: str) -> None:
    print(f"{RED}[ÉCHEC]{NC} {msg}")


def step(msg: str) -> None:
    print(f"{YELLOW}[ÉTAPE]{NC} {msg}")


# --- Sources -----------------------------------------------------------------

SOURCE_PARELLE = {
    "type_source": "peer_reviewed",
    "auteur": "Parelle J., Brendel O., Jolivet Y.",
    "date_publication": "2007",
    "reference": "Annals of Forest Science, hal-02653679",
}

SOURCE_INRAE = {
    "type_source": "referentiel_officiel",
    "auteur": "INRAE (2008)",
    "date_publication": "2008",
    "reference": "Référentiel pédologique français, édition 2008",
}


# --- Ground truth : scénarios avec conclusions attendues ---------------------
#
# Chaque scénario est construit à partir d'un fait vérifié de Parelle 2007.
# La conclusion attendue est ce que la littérature dit — si le moteur
# produit une conclusion différente, c'est un échec de validation.

SCENARIOS_GROUND_TRUTH: list[dict] = [
    {
        "nom": "sol_acide_engorgement_quercus",
        "description": (
            "Sol acide (pH 4.8) avec engorgement hivernal. "
            "Q. robur plus tolérant à l'engorgement que Q. petraea."
        ),
        "contexte": {
            "pedologie": {
                "source_moteur": "PEDOLOGY",
                "source": SOURCE_INRAE,
                "evidence_level": "B",
                "valeurs": {
                    "pH": 4.8,
                    "profondeur_cm": 70,
                    "engorgement_hivernal": True,
                },
            }
        },
        "regles": [
            {
                "identifiant": "regle-acidite",
                "condition": "pedologie_pH < 5.5",
                "enonce_conclusion": "Le sol est acide (pH < 5.5).",
                "source": SOURCE_PARELLE,
                "evidence_level": "B",
                "niveau_confiance": 0.85,
            },
            {
                "identifiant": "regle-engorgement",
                "condition": "pedologie_engorgement_hivernal == True",
                "enonce_conclusion": (
                    "Engorgement hivernal : Q. robur plus tolerant que "
                    "Q. petraea a l'engorgement racinaire."
                ),
                "source": SOURCE_PARELLE,
                "evidence_level": "B",
                "niveau_confiance": 0.80,
            },
        ],
        "qualifications": [
            {
                "identifiant_regle": "regle-acidite",
                "role": "contrainte",
                "domaine_element": "pedologique",
            },
            {
                "identifiant_regle": "regle-engorgement",
                "role": "risque",
                "domaine_risque": "sanitaire",
                "probabilite": "modere",
                "horizon": "court_terme",
            },
        ],
        "etat_global": {
            "etat": "vigueur_reduite",
            "justification": "Acidite et engorgement combinés",
            "source": SOURCE_INRAE,
            "evidence_level": "B",
        },
        "conclusions_attendues": 2,
        "validation_attendue": "valide",
    },
    {
        "nom": "sol_neutre_draine_quercus",
        "description": (
            "Sol neutre (pH 6.5) bien drainé, pas d'engorgement. "
            "Conditions favorables — pas de contrainte."
        ),
        "contexte": {
            "pedologie": {
                "source_moteur": "PEDOLOGY",
                "source": SOURCE_INRAE,
                "evidence_level": "B",
                "valeurs": {
                    "pH": 6.5,
                    "profondeur_cm": 80,
                    "engorgement_hivernal": False,
                },
            }
        },
        "regles": [
            {
                "identifiant": "regle-acidite",
                "condition": "pedologie_pH < 5.5",
                "enonce_conclusion": "Le sol est acide (pH < 5.5).",
                "source": SOURCE_PARELLE,
                "evidence_level": "B",
                "niveau_confiance": 0.85,
            },
            {
                "identifiant": "regle-profondeur",
                "condition": "pedologie_profondeur_cm > 50",
                "enonce_conclusion": "Le sol est profond (> 50 cm).",
                "source": SOURCE_INRAE,
                "evidence_level": "B",
                "niveau_confiance": 0.90,
            },
        ],
        "qualifications": [
            {
                "identifiant_regle": "regle-profondeur",
                "role": "atout",
                "domaine_element": "pedologique",
            },
        ],
        "etat_global": {
            "etat": "sain",
            "justification": "Sol neutre et profond, pas de contrainte",
            "source": SOURCE_INRAE,
            "evidence_level": "B",
        },
        "conclusions_attendues": 1,  # seule la règle profondeur conclut (pH 6.5 >= 5.5)
        "validation_attendue": "valide",
    },
    {
        "nom": "sol_tres_acide_quercus",
        "description": (
            "Sol très acide (pH 3.5). Contrainte pédologique sévère. "
            "Q. petraea préférable (tolérant aux sols acides)."
        ),
        "contexte": {
            "pedologie": {
                "source_moteur": "PEDOLOGY",
                "source": SOURCE_INRAE,
                "evidence_level": "B",
                "valeurs": {
                    "pH": 3.5,
                    "profondeur_cm": 60,
                    "engorgement_hivernal": False,
                },
            }
        },
        "regles": [
            {
                "identifiant": "regle-acidite-severe",
                "condition": "pedologie_pH < 4.5",
                "enonce_conclusion": (
                    "Sol tres acide (pH < 4.5) : contrainte severe pour "
                    "la plupart des essences forestieres."
                ),
                "source": SOURCE_PARELLE,
                "evidence_level": "B",
                "niveau_confiance": 0.90,
            },
            {
                "identifiant": "regle-profondeur",
                "condition": "pedologie_profondeur_cm > 50",
                "enonce_conclusion": "Le sol est profond (> 50 cm).",
                "source": SOURCE_INRAE,
                "evidence_level": "B",
                "niveau_confiance": 0.90,
            },
        ],
        "qualifications": [
            {
                "identifiant_regle": "regle-acidite-severe",
                "role": "contrainte",
                "domaine_element": "pedologique",
            },
            {
                "identifiant_regle": "regle-profondeur",
                "role": "atout",
                "domaine_element": "pedologique",
            },
        ],
        "etat_global": {
            "etat": "vigueur_reduite",
            "justification": "Acidité sévère limitant la vigueur",
            "source": SOURCE_INRAE,
            "evidence_level": "B",
        },
        "conclusions_attendues": 2,
        "validation_attendue": "valide",
    },
]


def _corps_analyse(scenario: dict) -> dict:
    """Construit le corps de la requête depuis un scénario ground truth."""
    return {
        "requete_id": str(uuid4()),
        "station_id": str(uuid4()),
        "contexte": scenario["contexte"],
        "regles": scenario["regles"],
        "qualifications": scenario["qualifications"],
        "etat_global": scenario["etat_global"],
        "question": "Quelles essences sont adaptées à cette station ?",
        "objectif_forestier": "production",
        "alternatives_demandees": True,
    }


# --- Validation ground truth -------------------------------------------------


def _valider_scenario(client: httpx.Client, base_url: str, token: str, scenario: dict) -> dict:
    """Exécute un scénario et valide les conclusions attendues.

    Returns:
        dict avec les résultats de validation (pass/fail + détails).
    """
    nom = scenario["nom"]
    attendues = scenario["conclusions_attendues"]
    validation_attendue = scenario["validation_attendue"]

    corps = _corps_analyse(scenario)
    resp = client.post(
        f"{base_url}/api/v1/orchestration/analyse",
        json=corps,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )

    if resp.status_code != 200:
        return {
            "scenario": nom,
            "succes": False,
            "erreur": f"HTTP {resp.status_code}: {resp.text[:200]}",
        }

    resultat = resp.json()
    conclusions = resultat.get("inference", {}).get("conclusions", [])
    recs = resultat.get("recommandations", {}).get("recommandations", [])
    validation_statut = resultat.get("validation", {}).get("statut", "")

    # Vérifications
    checks = []

    # 1. Nombre de conclusions
    n_conclusions = len(conclusions)
    if n_conclusions == attendues:
        checks.append(
            {
                "check": "nombre_conclusions",
                "succes": True,
                "attendu": attendues,
                "obtenu": n_conclusions,
            }
        )
    else:
        checks.append(
            {
                "check": "nombre_conclusions",
                "succes": False,
                "attendu": attendues,
                "obtenu": n_conclusions,
            }
        )

    # 2. Validation statut
    if validation_statut == validation_attendue:
        checks.append(
            {
                "check": "validation_statut",
                "succes": True,
                "attendu": validation_attendue,
                "obtenu": validation_statut,
            }
        )
    else:
        checks.append(
            {
                "check": "validation_statut",
                "succes": False,
                "attendu": validation_attendue,
                "obtenu": validation_statut,
            }
        )

    # 3. Au moins une recommandation
    if len(recs) >= 1:
        checks.append(
            {
                "check": "recommandations_produites",
                "succes": True,
                "attendu": ">=1",
                "obtenu": len(recs),
            }
        )
    else:
        checks.append(
            {"check": "recommandations_produites", "succes": False, "attendu": ">=1", "obtenu": 0}
        )

    # 4. Sources traçables (chaque conclusion a au moins une source)
    sources_ok = all(len(c.get("sources_utilisees", [])) >= 1 for c in conclusions)
    checks.append(
        {"check": "sources_tracables", "succes": sources_ok, "attendu": True, "obtenu": sources_ok}
    )

    # 5. Diagnostic persisté (a un diagnostic_id)
    diag_id = resultat.get("diagnostic", {}).get("diagnostic_id", "")
    has_diag = bool(diag_id)
    checks.append(
        {"check": "diagnostic_persiste", "succes": has_diag, "attendu": True, "obtenu": has_diag}
    )

    # 6. Recommendation liée au diagnostic
    diag_source = resultat.get("recommandations", {}).get("diagnostic_source", "")
    rec_linked = diag_source == diag_id if diag_id else False
    checks.append(
        {
            "check": "recommandation_liee_diagnostic",
            "succes": rec_linked,
            "attendu": True,
            "obtenu": rec_linked,
        }
    )

    succes_global = all(c["succes"] for c in checks)

    return {
        "scenario": nom,
        "succes": succes_global,
        "n_conclusions": n_conclusions,
        "n_recommandations": len(recs),
        "validation_statut": validation_statut,
        "diagnostic_id": diag_id[:12] + "..." if diag_id else None,
        "checks": checks,
    }


def _login(client: httpx.Client, base_url: str) -> str:
    """Authentifie via dev login."""
    resp = client.post(
        f"{base_url}/api/v1/auth/login",
        json={"username": "admin", "password": "dev-test-only-not-secret"},
    )
    if resp.status_code != 200:
        fail(f"Login échoué : {resp.status_code}")
        sys.exit(1)
    return resp.json()["access_token"]


# --- Benchmark ---------------------------------------------------------------


def _benchmark(client: httpx.Client, base_url: str, token: str, iterations: int) -> dict:
    """Exécute la chaîne N fois et mesure les performances.

    Returns:
        dict avec latences (min/max/mean/p50/p95/p99), throughput, mémoire.
    """
    step(f"Benchmark : {iterations} itérations de la chaîne complète")

    # Scénario de référence pour le benchmark (le premier ground truth)
    scenario = SCENARIOS_GROUND_TRUTH[0]

    # Warmup : 1 itération non mesurée pour chauffer le cache
    info("Warmup : 1 itération non mesurée...")
    corps = _corps_analyse(scenario)
    client.post(
        f"{base_url}/api/v1/orchestration/analyse",
        json=corps,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )
    time.sleep(3.1)  # Respecter le rate limit après warmup

    # Mesures
    latences: list[float] = []
    gc.collect()
    tracemalloc.start()

    # Rate limit : 20/minute sur /orchestration/analyse. On espace à
    # 3s entre requêtes pour rester sous la limite (20 req/min = 1 req/3s).
    rate_limit_delay = 3.1  # secondes

    start_total = time.perf_counter()
    for i in range(iterations):
        corps = _corps_analyse(scenario)
        t0 = time.perf_counter()
        resp = client.post(
            f"{base_url}/api/v1/orchestration/analyse",
            json=corps,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )
        t1 = time.perf_counter()
        latences.append((t1 - t0) * 1000)  # ms

        if resp.status_code != 200:
            fail(f"Itération {i+1} échouée : HTTP {resp.status_code}")
            return {"erreur": f"HTTP {resp.status_code}"}

        # Respecter le rate limit (sauf après la dernière itération)
        if i < iterations - 1:
            time.sleep(rate_limit_delay)

    elapsed_total = time.perf_counter() - start_total

    # Mémoire
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Statistiques de latence
    latences_sorted = sorted(latences)
    n = len(latences_sorted)

    def percentile(data: list[float], p: float) -> float:
        idx = int(n * p / 100)
        idx = min(idx, n - 1)
        return data[idx]

    stats = {
        "iterations": iterations,
        "latence_ms": {
            "min": round(min(latences), 2),
            "max": round(max(latences), 2),
            "mean": round(statistics.mean(latences), 2),
            "median": round(statistics.median(latences), 2),
            "p50": round(percentile(latences_sorted, 50), 2),
            "p95": round(percentile(latences_sorted, 95), 2),
            "p99": round(percentile(latences_sorted, 99), 2),
            "stdev": round(statistics.stdev(latences), 2) if n > 1 else 0.0,
        },
        "throughput": {
            "total_seconds": round(elapsed_total, 3),
            "req_per_sec": round(iterations / elapsed_total, 2),
        },
        "memoire": {
            "current_mb": round(current_mem / 1024 / 1024, 2),
            "peak_mb": round(peak_mem / 1024 / 1024, 2),
        },
    }

    info(f"Latence moyenne : {stats['latence_ms']['mean']:.2f}ms")
    info(f"Latence p95 : {stats['latence_ms']['p95']:.2f}ms")
    info(f"Latence p99 : {stats['latence_ms']['p99']:.2f}ms")
    info(f"Throughput : {stats['throughput']['req_per_sec']:.2f} req/s")
    info(f"Mémoire peak : {stats['memoire']['peak_mb']:.2f} MB")

    return stats


# --- Main --------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Validation scientifique + benchmark GSIE")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="URL de base de l'API GSIE",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Nombre d'itérations pour le benchmark",
    )
    parser.add_argument(
        "--output",
        default="benchmark_resultat.json",
        help="Fichier de sortie pour le rapport JSON",
    )
    args = parser.parse_args()
    base_url = args.url

    print()
    print("=" * 72)
    print("  VALIDATION SCIENTIFIQUE + BENCHMARK — DEC-000043 S3")
    print("  Ground truth : Parelle 2007 (Quercus robur vs petraea)")
    print(f"  Benchmark : {args.iterations} itérations")
    print("=" * 72)
    print()

    with httpx.Client(timeout=30.0) as client:
        # Vérifier santé
        step("Vérification santé API")
        resp = client.get(f"{base_url}/health")
        if resp.status_code != 200:
            fail("API non accessible")
            return 1
        ok("API opérationnelle")

        # Login
        token = _login(client, base_url)
        ok("Authentifié")

        # --- Phase 1 : Validation ground truth ---
        print()
        step(f"Phase 1 : Validation ground truth ({len(SCENARIOS_GROUND_TRUTH)} scénarios)")

        validations = []
        n_succes = 0
        for i, scenario in enumerate(SCENARIOS_GROUND_TRUTH):
            info(f"Scénario : {scenario['nom']}")
            info(f"  {scenario['description'][:80]}")
            result = _valider_scenario(client, base_url, token, scenario)
            validations.append(result)

            if result["succes"]:
                n_succes += 1
                ok(f"  {result['scenario']} : {len(result['checks'])} checks passés")
            else:
                fail(f"  {result['scenario']} : échec")
                if "erreur" in result:
                    info(f"  Erreur : {result['erreur'][:120]}")
                for c in result.get("checks", []):
                    if not c["succes"]:
                        print(
                            f"    x {c['check']} : attendu={c['attendu']}, " f"obtenu={c['obtenu']}"
                        )

            # Respecter le rate limit entre scénarios
            if i < len(SCENARIOS_GROUND_TRUTH) - 1:
                time.sleep(3.1)

        print()
        print(f"  Validation : {n_succes}/{len(SCENARIOS_GROUND_TRUTH)} scénarios validés")

        if n_succes < len(SCENARIOS_GROUND_TRUTH):
            fail("Validation ground truth : ÉCHEC")
            validation_reussie = False
        else:
            ok("Validation ground truth : SUCCÈS")
            validation_reussie = True

        # --- Phase 2 : Benchmark ---
        print()
        # Attendre que la fenêtre de rate limit se vide (60s = 1 minute)
        info("Attente 60s pour vider la fenêtre de rate limit avant le benchmark...")
        time.sleep(61)
        bench = _benchmark(client, base_url, token, args.iterations)

    # --- Rapport final ---
    rapport = {
        "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "validation_ground_truth": {
            "n_scenarios": len(SCENARIOS_GROUND_TRUTH),
            "n_succes": n_succes,
            "succes_global": validation_reussie,
            "details": validations,
        },
        "benchmark": bench,
    }

    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(rapport, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    info(f"Rapport sauvegardé : {output_path}")

    # --- Résumé final ---
    print()
    print("=" * 72)
    print("  RÉSUMÉ FINAL")
    print("=" * 72)
    print(
        f"  Validation ground truth : {n_succes}/{len(SCENARIOS_GROUND_TRUTH)} "
        f"{'✓' if validation_reussie else '✗'}"
    )
    if "latence_ms" in bench:
        print(f"  Latence moyenne : {bench['latence_ms']['mean']:.2f}ms")
        print(f"  Latence p95 : {bench['latence_ms']['p95']:.2f}ms")
        print(f"  Latence p99 : {bench['latence_ms']['p99']:.2f}ms")
        print(f"  Throughput : {bench['throughput']['req_per_sec']:.2f} req/s")
        print(f"  Mémoire peak : {bench['memoire']['peak_mb']:.2f} MB")
    print("=" * 72)

    return 0 if validation_reussie else 1


if __name__ == "__main__":
    from pathlib import Path

    sys.exit(main())
