"""Interface en ligne de commande de la preuve exécutable GSIE."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

from gsie_execution_kit.bench import BenchError, run_bench
from gsie_execution_kit.capsule import (
    CapsuleError,
    build_capsule,
    generate_keypair,
    verify_capsule,
)
from gsie_execution_kit.json_utils import write_json_atomic


def _datetime_argument(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date ISO 8601 invalide") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("la date doit inclure un fuseau horaire")
    return parsed


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gsie-execution-kit",
        description="Capsule territoriale signée et Golden Bench GSIE",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    keygen = subparsers.add_parser("keygen", help="générer une paire Ed25519 de démonstration")
    keygen.add_argument("--private-key", type=Path, required=True)
    keygen.add_argument("--public-key", type=Path, required=True)
    keygen.add_argument("--overwrite", action="store_true")

    build = subparsers.add_parser("build", help="construire et signer une capsule")
    build.add_argument("--source", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--private-key", type=Path, required=True)
    build.add_argument("--created-at", type=_datetime_argument)
    build.add_argument("--valid-until", type=_datetime_argument)

    verify = subparsers.add_parser("verify", help="vérifier une capsule hors-ligne")
    verify.add_argument("--capsule", type=Path, required=True)
    verify.add_argument("--public-key", type=Path, required=True)
    verify.add_argument("--report", type=Path)

    bench = subparsers.add_parser("bench", help="exécuter le Golden Bench")
    bench.add_argument("--cases", type=Path, required=True)
    bench.add_argument("--report", type=Path)
    bench.add_argument("--require-reviewed", action="store_true")

    demo = subparsers.add_parser("demo", help="exécuter la tranche verticale complète")
    demo.add_argument("--source", type=Path, required=True)
    demo.add_argument("--cases", type=Path, required=True)
    demo.add_argument("--workdir", type=Path, required=True)
    return parser


def _run_demo(source: Path, cases: Path, workdir: Path) -> int:
    workdir.mkdir(parents=True, exist_ok=True)
    private_key = workdir / "demo-private.pem"
    public_key = workdir / "demo-public.pem"
    capsule = workdir / "demo-territoire.gsiecap"
    verification_report_path = workdir / "verification-report.json"
    bench_report_path = workdir / "golden-bench-report.json"
    demonstration_report_path = workdir / "demonstration-report.json"

    key_id = generate_keypair(private_key, public_key, overwrite=True)
    created_at = datetime.now(UTC).replace(microsecond=0)
    build_report = build_capsule(
        source,
        capsule,
        private_key,
        created_at=created_at,
        valid_until=created_at + timedelta(days=30),
    )
    verification_report = verify_capsule(capsule, public_key)
    bench_report = run_bench(cases, require_reviewed=False)
    write_json_atomic(verification_report_path, verification_report)
    write_json_atomic(bench_report_path, bench_report)

    success = bool(verification_report["valid"] and bench_report["numeric_success"])
    demonstration_report = {
        "demo_schema_version": "1.0.0",
        "success": success,
        "offline": True,
        "key_id": key_id,
        "build": build_report,
        "verification_report": str(verification_report_path),
        "golden_bench_report": str(bench_report_path),
        "scientific_review_pending": bench_report["summary"]["review_pending"],
        "production_ready": False,
        "production_blockers": [
            "validation scientifique indépendante",
            "rotation/révocation et protection anti-rollback",
            "tests contractuels Kotlin/Python",
            "benchmark sur appareil Android réel",
        ],
    }
    write_json_atomic(demonstration_report_path, demonstration_report)

    print("DÉMONSTRATION GSIE : SUCCÈS" if success else "DÉMONSTRATION GSIE : ÉCHEC")
    print(f"Capsule              : {capsule}")
    print(f"Signature            : {verification_report['signature']}")
    print(f"Fichiers vérifiés    : {verification_report['file_count']}")
    print(
        "Golden Bench         : "
        f"{bench_report['summary']['numeric_passed']}/{bench_report['summary']['case_count']}"
    )
    print(f"Revues en attente    : {bench_report['summary']['review_pending']}")
    print(f"Rapport de synthèse  : {demonstration_report_path}")
    return 0 if success else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "keygen":
            key_id = generate_keypair(
                args.private_key,
                args.public_key,
                overwrite=args.overwrite,
            )
            _print_json({"key_id": key_id, "public_key": str(args.public_key)})
            return 0
        if args.command == "build":
            _print_json(
                build_capsule(
                    args.source,
                    args.output,
                    args.private_key,
                    created_at=args.created_at,
                    valid_until=args.valid_until,
                )
            )
            return 0
        if args.command == "verify":
            report = verify_capsule(args.capsule, args.public_key)
            if args.report:
                write_json_atomic(args.report, report)
            _print_json(report)
            return 0
        if args.command == "bench":
            report = run_bench(args.cases, require_reviewed=args.require_reviewed)
            if args.report:
                write_json_atomic(args.report, report)
            _print_json(report)
            return 0 if report["success"] else 1
        if args.command == "demo":
            return _run_demo(args.source, args.cases, args.workdir)
    except (CapsuleError, BenchError) as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 2
    parser.error("commande inconnue")
    return 2
