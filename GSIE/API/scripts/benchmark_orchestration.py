#!/usr/bin/env python3
"""Mesure contrôlée de ``POST /api/v1/orchestration/analyse``.

Le script est réservé à une base de test explicitement cloisonnée. Il mesure
la latence de bout en bout, le débit, les erreurs HTTP et vérifie que chaque
réponse 200 possède bien une ligne ``analysis_run`` persistée dans PostgreSQL.
Il ne démarre ni ne migre Docker et refuse toute base qui n'est pas
explicitement déclarée comme environnement de test.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import ssl
import statistics
import time
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import asyncpg  # type: ignore[import-untyped]
import httpx
import jwt


def _jeton() -> str:
    """Signe un jeton de test avec la clé montée dans la stack Docker."""
    chemin = Path(os.environ.get("GSIE_JWT_PRIVATE_KEY_PATH", "keys/private.pem"))
    if not chemin.is_file():
        raise RuntimeError(f"clé JWT de test introuvable : {chemin}")
    maintenant = datetime.now(UTC)
    charge = {
        "sub": "benchmark-orchestration",
        "iss": os.environ.get("GSIE_JWT_ISSUER", "gsie-api"),
        "aud": os.environ.get("GSIE_JWT_AUDIENCE", "gsie-clients"),
        "iat": maintenant,
        "exp": maintenant + timedelta(minutes=10),
        "jti": str(uuid4()),
        "type": "access",
        "roles": ["writer"],
    }
    return jwt.encode(charge, chemin.read_text(encoding="utf-8"), algorithm="RS256")


def _corps() -> dict[str, Any]:
    """Construit une demande stationnelle complète et déterministe."""
    source = {
        "type_source": "referentiel_officiel",
        "auteur": "INRAE (2008)",
        "date_publication": "2008",
        "reference": "Référentiel pédologique français, édition 2008",
    }
    return {
        "requete_id": str(uuid4()),
        "station_id": str(uuid4()),
        "contexte": {
            "pedologie": {
                "source_moteur": "PEDOLOGY",
                "source": source,
                "evidence_level": "B",
                "valeurs": {"pH": 5.2, "profondeur_cm": 80},
            }
        },
        "regles": [
            {
                "identifiant": "regle-acidite-01",
                "condition": "pedologie_pH < 5.5",
                "enonce_conclusion": "Le sol est acide.",
                "source": source,
                "evidence_level": "B",
                "niveau_confiance": 0.85,
            },
            {
                "identifiant": "regle-profondeur-01",
                "condition": "pedologie_profondeur_cm > 50",
                "enonce_conclusion": "Le sol est profond.",
                "source": source,
                "evidence_level": "B",
                "niveau_confiance": 0.80,
            },
        ],
        "qualifications": [
            {
                "identifiant_regle": "regle-acidite-01",
                "role": "contrainte",
                "domaine_element": "pedologique",
            },
            {
                "identifiant_regle": "regle-profondeur-01",
                "role": "atout",
                "domaine_element": "pedologique",
            },
        ],
        "etat_global": {
            "etat": "vigueur_reduite",
            "justification": "Acidité marquée constatée sur la station",
            "source": source,
            "evidence_level": "B",
        },
        "question": "Quelles essences sont adaptées à cette station ?",
        "objectif_forestier": "production",
        "alternatives_demandees": True,
    }


async def _appel(
    client: httpx.AsyncClient, url: str, jeton: str, semaphore: asyncio.Semaphore
) -> dict[str, Any]:
    async with semaphore:
        debut = time.perf_counter()
        try:
            response = await client.post(
                url,
                json=_corps(),
                headers={"Authorization": f"Bearer {jeton}"},
            )
            duree_ms = (time.perf_counter() - debut) * 1000
            corps: dict[str, Any] = {}
            with suppress(ValueError):
                corps = response.json()
            return {
                "status": response.status_code,
                "duration_ms": duree_ms,
                "analysis_id": corps.get("analyse_id"),
                "error": None if response.status_code == 200 else response.text[:500],
            }
        except Exception as exc:  # le benchmark compte aussi les erreurs réseau
            return {
                "status": None,
                "duration_ms": (time.perf_counter() - debut) * 1000,
                "analysis_id": None,
                "error": f"{type(exc).__name__}: {exc}",
            }


async def _verifier_persistance(
    identifiants: list[str],
    expected_namespace: str,
    expected_database: str,
) -> int:
    """Vérifie les lignes de preuve dans la seule base de test autorisée."""
    role = os.environ.get("GSIE_DATABASE_ROLE")
    espace = os.environ.get("GSIE_DATA_NAMESPACE")
    base = os.environ.get("GSIE_DB_NAME", "")
    if role != "test" or espace != expected_namespace or base != expected_database:
        raise RuntimeError(
            "refus de vérification : GSIE_DATABASE_ROLE/GSIE_DATA_NAMESPACE/"
            "GSIE_DB_NAME ne désignent pas l'environnement de benchmark attendu"
        )
    connexion: Any = await asyncpg.connect(
        host=os.environ.get("GSIE_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("GSIE_DB_PORT", "5432")),
        user=os.environ.get("GSIE_API_DB_USER", "gsie_api"),
        password=os.environ.get("GSIE_API_DB_PASSWORD", ""),
        database=base,
    )
    try:
        valeur = await connexion.fetchval(
            "SELECT count(*) FROM analysis_run WHERE id = ANY($1::uuid[])",
            [UUID(identifiant) for identifiant in identifiants],
        )
        return int(valeur or 0)
    finally:
        await connexion.close()


async def _verifier_rejeu(
    requete_id: str,
    expected_namespace: str,
    expected_database: str,
) -> int:
    """Compte les lignes produites par un rejeu idempotent.

    Le contrôle est volontairement limité à ``requete_origine`` et à la base
    de test déclarée : il prouve qu'un même contrat n'a pas créé de doublon
    sans inspecter d'autres environnements.
    """
    role = os.environ.get("GSIE_DATABASE_ROLE")
    espace = os.environ.get("GSIE_DATA_NAMESPACE")
    base = os.environ.get("GSIE_DB_NAME", "")
    if role != "test" or espace != expected_namespace or base != expected_database:
        raise RuntimeError(
            "refus de vérification : GSIE_DATABASE_ROLE/GSIE_DATA_NAMESPACE/"
            "GSIE_DB_NAME ne désignent pas l'environnement de benchmark attendu"
        )
    connexion: Any = await asyncpg.connect(
        host=os.environ.get("GSIE_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("GSIE_DB_PORT", "5432")),
        user=os.environ.get("GSIE_API_DB_USER", "gsie_api"),
        password=os.environ.get("GSIE_API_DB_PASSWORD", ""),
        database=base,
    )
    try:
        valeur = await connexion.fetchval(
            "SELECT count(*) FROM analysis_run WHERE requete_origine = $1::uuid",
            UUID(requete_id),
        )
        return int(valeur or 0)
    finally:
        await connexion.close()


async def _rejouer(
    client: httpx.AsyncClient,
    url: str,
    jeton: str,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Soumet deux fois le même contrat et retourne les réponses observées."""
    corps = _corps()
    headers = {
        "Authorization": f"Bearer {jeton}",
        "Idempotency-Key": corps["requete_id"],
    }
    premiere = await client.post(url, json=corps, headers=headers)
    seconde = await client.post(url, json=corps, headers=headers)
    if premiere.status_code != 200 or seconde.status_code != 200:
        raise RuntimeError(
            "rejeu idempotent refusé : " f"statuts={premiere.status_code},{seconde.status_code}"
        )
    premiere_json = premiere.json()
    seconde_json = seconde.json()
    if premiere_json != seconde_json:
        raise RuntimeError("rejeu idempotent non déterministe : réponses différentes")
    analyse_id = premiere_json.get("analyse_id")
    if not isinstance(analyse_id, str) or not analyse_id:
        raise RuntimeError("rejeu idempotent invalide : analyse_id absent")
    return premiere_json, seconde_json, corps["requete_id"]


async def _executer(args: argparse.Namespace) -> dict[str, Any]:
    jeton = _jeton()
    semaphore = asyncio.Semaphore(args.concurrency)
    limites = httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=args.concurrency,
    )
    debut_global = time.perf_counter()
    verification_tls: bool | ssl.SSLContext
    if args.ca_file is not None:
        verification_tls = ssl.create_default_context(cafile=str(args.ca_file))
    else:
        verification_tls = True
    async with httpx.AsyncClient(
        timeout=args.timeout,
        limits=limites,
        verify=verification_tls,
        trust_env=False,
    ) as client:
        if args.replay:
            premiere, seconde, requete_id = await _rejouer(client, args.url, jeton)
            nombre_lignes = await _verifier_rejeu(
                requete_id,
                args.expected_namespace,
                args.expected_database,
            )
            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "url": args.url,
                "requests": 2,
                "concurrency": 1,
                "timeout_seconds": args.timeout,
                "successes": 2,
                "errors": 0,
                "persisted_analysis_runs": nombre_lignes,
                "persistence_ratio": 1.0 if nombre_lignes == 1 else 0.0,
                "idempotency": {
                    "requete_id": requete_id,
                    "same_response": premiere == seconde,
                    "same_analysis_id": premiere.get("analyse_id") == seconde.get("analyse_id"),
                    "expected_rows": 1,
                },
            }
        resultats = await asyncio.gather(
            *(_appel(client, args.url, jeton, semaphore) for _ in range(args.requests))
        )
    duree_totale_s = time.perf_counter() - debut_global
    latences = sorted(float(r["duration_ms"]) for r in resultats)
    succes = [r for r in resultats if r["status"] == 200 and r["analysis_id"]]
    ids = [str(r["analysis_id"]) for r in succes]
    persistes = (
        await _verifier_persistance(
            ids,
            args.expected_namespace,
            args.expected_database,
        )
        if ids
        else 0
    )

    def percentile(fraction: float) -> float:
        return latences[min(len(latences) - 1, int(len(latences) * fraction))]

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "url": args.url,
        "requests": args.requests,
        "concurrency": args.concurrency,
        "timeout_seconds": args.timeout,
        "elapsed_seconds": round(duree_totale_s, 6),
        "successes": len(succes),
        "errors": args.requests - len(succes),
        "persisted_analysis_runs": persistes,
        "persistence_ratio": round(persistes / len(succes), 6) if succes else 0.0,
        "throughput_requests_per_second": round(args.requests / duree_totale_s, 3),
        "latency_ms": {
            "min": round(latences[0], 3),
            "p50": round(percentile(0.50), 3),
            "p95": round(percentile(0.95), 3),
            "p99": round(percentile(0.99), 3),
            "max": round(latences[-1], 3),
            "mean": round(statistics.mean(latences), 3),
        },
        "status_counts": {
            str(code): sum(1 for r in resultats if r["status"] == code)
            for code in sorted({r["status"] for r in resultats}, key=str)
        },
        "errors_detail": [r["error"] for r in resultats if r["error"]][:10],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/orchestration/analyse")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument(
        "--ca-file",
        type=Path,
        default=None,
        help="CA PEM à utiliser pour une cible HTTPS locale ou de test",
    )
    parser.add_argument(
        "--replay",
        action="store_true",
        help="soumet deux fois le même contrat et vérifie l'absence de doublon",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("tests/perf/results/orchestration.json")
    )
    parser.add_argument(
        "--expected-namespace",
        default="gsie-test",
        help="Namespace de test attendu pour la vérification de persistance",
    )
    parser.add_argument(
        "--expected-database",
        default="gsie_test",
        help="Nom de base attendu pour la vérification de persistance",
    )
    args = parser.parse_args()
    if args.requests <= 0 or args.concurrency <= 0 or args.concurrency > args.requests:
        parser.error("requests doit être positif et concurrency compris entre 1 et requests")
    rapport = asyncio.run(_executer(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(rapport, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(rapport, indent=2, ensure_ascii=False))
    return 0 if rapport["errors"] == 0 and rapport["persistence_ratio"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
