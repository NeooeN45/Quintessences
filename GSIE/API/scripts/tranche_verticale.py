#!/usr/bin/env python3
"""Tranche verticale réelle — DEC-000043 S2.

Prouve que la chaîne complète GSIE fonctionne de bout en bout sur un cas
forestier réel : un massif de chênes (Quercus robur / Quercus petraea)
sur sol acide avec risque d'engorgement.

Données réelles utilisées :
- Pilote Parelle et al. (2007) — tolérance à l'engorgement et à la
  sécheresse de Q. robur vs Q. petraea (Annals of Forest Science,
  hal-02653679, 29 faits vérifiés)
- Référentiel pédologique français (INRAE 2008) — règles d'acidité

Chaîne testée :
    Reasoning → Diagnostic → Recommendation → Validation

L'endpoint /api/v1/orchestration/analyse enchaîne les quatre moteurs
sur une session unique et retourne chaque étape.

Usage :
    python scripts/tranche_verticale.py [--url http://127.0.0.1:8000]

Prérequis :
- API GSIE démarrée (docker compose up)
- Dev login activé (GSIE_AUTH_DEV_LOGIN_ENABLED=true)
- Base de données initialisée (alembic upgrade head)

Sortie :
- Trace de chaque étape sur stdout
- Rapport JSON complet dans tranche_verticale_resultat.json
- Exit 0 si la chaîne complète aboutit, 1 sinon
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from uuid import uuid4

# Forcer UTF-8 sur stdout — Windows utilise cp1252 par défaut
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


# --- Données réelles du pilote Parelle 2007 ----------------------------------
# Source : Parelle J., Brendel O., Jolivet Y. (2007), Annals of Forest Science,
# hal-02653679. 29 faits vérifiés sur Q. robur et Q. petraea.
#
# Le scénario : une station forestière sur sol acide (pH 4.8) avec risque
# d'engorgement hydrique. Deux règles s'appliquent :
# 1. Acidité → contrainte pédologique (pH < 5.5)
# 2. Engorgement → risque pour Q. petraea (moins tolérant que Q. robur)
#
# L'objectif forestier est la production. La question : quelles essences
# sont adaptées à cette station ?

SOURCE_INRAE_2008 = {
    "type_source": "referentiel_officiel",
    "auteur": "INRAE (2008)",
    "date_publication": "2008",
    "reference": "Référentiel pédologique français, édition 2008",
}

SOURCE_PARELLE_2007 = {
    "type_source": "peer_reviewed",
    "auteur": "Parelle J., Brendel O., Jolivet Y.",
    "date_publication": "2007",
    "reference": "Annals of Forest Science, hal-02653679",
}


def _corps_analyse() -> dict:
    """Construit la requête d'analyse avec données réelles du pilote Quercus.

    Scénario : station acide avec engorgement → Q. robur préféré à Q. petraea.
    """
    return {
        "requete_id": str(uuid4()),
        "station_id": str(uuid4()),
        "contexte": {
            "pedologie": {
                "source_moteur": "PEDOLOGY",
                "source": SOURCE_INRAE_2008,
                "evidence_level": "B",
                "valeurs": {
                    "pH": 4.8,
                    "profondeur_cm": 70,
                    "engorgement_hivernal": True,
                },
            },
        },
        "regles": [
            {
                "identifiant": "regle-acidite-quercus",
                "condition": "pedologie_pH < 5.5",
                "enonce_conclusion": (
                    "Le sol est acide (pH < 5.5) : Quercus petraea est "
                    "préférable à Quercus robur sur sol acide profond."
                ),
                "source": SOURCE_PARELLE_2007,
                "evidence_level": "B",
                "niveau_confiance": 0.85,
            },
            {
                "identifiant": "regle-engorgement-quercus",
                "condition": "pedologie_engorgement_hivernal == True",
                "enonce_conclusion": (
                    "Engorgement hivernal détecté : Quercus robur est plus "
                    "tolérant à l'engorgement racinaire que Quercus petraea."
                ),
                "source": SOURCE_PARELLE_2007,
                "evidence_level": "B",
                "niveau_confiance": 0.80,
            },
        ],
        "qualifications": [
            {
                "identifiant_regle": "regle-acidite-quercus",
                "role": "contrainte",
                "domaine_element": "pedologique",
            },
            {
                "identifiant_regle": "regle-engorgement-quercus",
                "role": "risque",
                "domaine_risque": "sanitaire",
                "probabilite": "modere",
                "horizon": "court_terme",
            },
        ],
        "etat_global": {
            "etat": "vigueur_reduite",
            "justification": (
                "Station acide avec engorgement hivernal — contraintes "
                "pédologiques combinées pour Quercus petraea"
            ),
            "source": SOURCE_INRAE_2008,
            "evidence_level": "B",
        },
        "question": (
            "Quelles essences (Quercus robur vs Quercus petraea) sont "
            "adaptées à cette station acide avec engorgement hivernal ?"
        ),
        "objectif_forestier": "production",
        "alternatives_demandees": True,
    }


# --- Exécution ---------------------------------------------------------------


def _login(client: httpx.Client, base_url: str) -> str:
    """Authentifie via dev login et retourne le token JWT."""
    step("Authentification (dev login)")
    resp = client.post(
        f"{base_url}/api/v1/auth/login",
        json={"username": "admin", "password": "dev-test-only-not-secret"},
    )
    if resp.status_code != 200:
        fail(f"Login échoué : {resp.status_code} {resp.text}")
        sys.exit(1)
    token = resp.json().get("access_token", "")
    if not token:
        fail("Pas de token dans la réponse")
        sys.exit(1)
    ok("Token JWT obtenu")
    return token


def _verifier_sante(client: httpx.Client, base_url: str) -> None:
    """Vérifie que l'API et la DB sont opérationnelles."""
    step("Vérification santé API + DB")
    resp = client.get(f"{base_url}/health")
    if resp.status_code != 200:
        fail(f"/health échoué : {resp.status_code}")
        sys.exit(1)
    ok(f"/health : {resp.json().get('status', 'ok')}")

    resp = client.get(f"{base_url}/ready")
    if resp.status_code != 200:
        fail(f"/ready échoué : {resp.status_code}")
        sys.exit(1)
    ok(f"/ready : {resp.json().get('status', 'ok')}")


def _executer_analyse(client: httpx.Client, base_url: str, token: str) -> dict:
    """Exécute la chaîne complète via /orchestration/analyse."""
    step("Exécution chaîne : Reasoning → Diagnostic → Recommendation → Validation")
    corps = _corps_analyse()
    info(
        f"Station : pH={corps['contexte']['pedologie']['valeurs']['pH']}, "
        f"profondeur={corps['contexte']['pedologie']['valeurs']['profondeur_cm']}cm, "
        f"engorgement={corps['contexte']['pedologie']['valeurs']['engorgement_hivernal']}"
    )
    info(f"Règles : {len(corps['regles'])} (acidité Quercus, engorgement Quercus)")
    info(f"Objectif : {corps['objectif_forestier']}")

    start = time.perf_counter()
    resp = client.post(
        f"{base_url}/api/v1/orchestration/analyse",
        json=corps,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )
    elapsed = time.perf_counter() - start

    if resp.status_code != 200:
        fail(f"Analyse échouée : {resp.status_code} {resp.text}")
        sys.exit(1)

    resultat = resp.json()
    ok(f"Chaîne complète en {elapsed:.2f}s")
    return resultat


def _tracer_etapes(resultat: dict) -> None:
    """Affiche la trace de chaque étape de la chaîne."""
    print()
    print("=" * 72)
    print("  TRACE DE LA CHAÎNE — chaque moteur")
    print("=" * 72)

    # 1. Reasoning
    inference = resultat.get("inference", {})
    conclusions = inference.get("conclusions", [])
    step(f"1. Reasoning Engine — {len(conclusions)} conclusion(s)")
    for c in conclusions:
        print(f"   • {c.get('conclusion_id', '?')[:8]}... : " f"{c.get('enonce', '?')[:80]}")
        print(
            f"     Confiance : {c.get('niveau_confiance', '?')}, "
            f"Preuve : {c.get('evidence_level', '?')}"
        )
    if not conclusions:
        fail("Aucune conclusion — le raisonnement n'a rien produit")
    else:
        ok(f"{len(conclusions)} conclusion(s) produite(s)")

    # 2. Diagnostic
    diagnostic = resultat.get("diagnostic", {})
    step(f"2. Diagnostic Engine — état : {diagnostic.get('etat_global', '?')}")
    print(f"   Diagnostic ID : {diagnostic.get('diagnostic_id', '?')[:12]}...")
    print(f"   Plancher preuve : {diagnostic.get('evidence_level_plancher', '?')}")
    print(f"   Conclusions source : {len(diagnostic.get('conclusions_source', []))}")
    qualifications = diagnostic.get("qualifications", [])
    print(f"   Qualifications : {len(qualifications)}")
    for q in qualifications[:3]:
        domaine = q.get("domaine_element", q.get("domaine_risque", "?"))
        print(f"     • {q.get('role', '?')} — {domaine}")
    ok(f"Diagnostic persisté : {diagnostic.get('diagnostic_id', '?')[:12]}...")

    # 3. Recommendation
    recommandations = resultat.get("recommandations", {})
    recs = recommandations.get("recommandations", [])
    step(f"3. Recommendation Engine — {len(recs)} recommandation(s)")
    print(f"   Diagnostic source : {recommandations.get('diagnostic_source', '?')[:12]}...")
    for r in recs[:3]:
        print(
            f"   • {r.get('essence', r.get('titre', '?'))} — "
            f"{r.get('action', r.get('recommendation', '?'))[:60]}"
        )
        print(
            f"     Priorité : {r.get('priorite', '?')}, "
            f"Contournable : {r.get('contournable', '?')}"
        )
    if not recs:
        fail("Aucune recommandation produite")
    else:
        ok(f"{len(recs)} recommandation(s) produite(s)")

    # 4. Validation
    validation = resultat.get("validation", {})
    step(f"4. Validation Engine — statut : {validation.get('statut', '?')}")
    causes_blocage = validation.get("causes_blocage", [])
    if causes_blocage:
        print(f"   Causes blocage : {causes_blocage}")
    ok(f"Validation : {validation.get('statut', '?')}")

    print()
    print("=" * 72)
    print(
        f"  RÉSUMÉ : {len(conclusions)} conclusions → "
        f"état {diagnostic.get('etat_global', '?')} → "
        f"{len(recs)} recommandations → "
        f"validation {validation.get('statut', '?')}"
    )
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Tranche verticale réelle GSIE")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="URL de base de l'API GSIE",
    )
    parser.add_argument(
        "--output",
        default="tranche_verticale_resultat.json",
        help="Fichier de sortie pour le rapport JSON complet",
    )
    args = parser.parse_args()
    base_url = args.url

    print()
    print("=" * 72)
    print("  TRANCHE VERTICALE RÉELLE — DEC-000043 S2")
    print("  Pilote : Quercus robur vs Quercus petraea (Parelle 2007)")
    print("  Chaîne : Reasoning → Diagnostic → Recommendation → Validation")
    print("=" * 72)
    print()

    with httpx.Client(timeout=30.0) as client:
        _verifier_sante(client, base_url)
        token = _login(client, base_url)
        resultat = _executer_analyse(client, base_url, token)

    _tracer_etapes(resultat)

    # Sauvegarder le rapport complet
    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(resultat, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    info(f"Rapport complet sauvegardé : {output_path}")

    # Vérifier le critère de succès
    conclusions = resultat.get("inference", {}).get("conclusions", [])
    recs = resultat.get("recommandations", {}).get("recommandations", [])
    validation_statut = resultat.get("validation", {}).get("statut", "")

    if not conclusions:
        fail("ÉCHEC : aucune conclusion produite par le Reasoning Engine")
        return 1
    if not recs:
        fail("ÉCHEC : aucune recommandation produite")
        return 1
    if validation_statut == "bloque":
        fail("ÉCHEC : la validation a bloqué la chaîne")
        return 1

    ok("SUCCÈS : la chaîne complète a produit un diagnostic et des recommandations")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
