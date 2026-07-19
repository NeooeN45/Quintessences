"""Preuve exécutable GSIE pour les capsules territoriales hors-ligne."""

from gsie_execution_kit.bench import BenchError, run_bench
from gsie_execution_kit.capsule import (
    CapsuleError,
    CapsuleLimits,
    build_capsule,
    generate_keypair,
    verify_capsule,
)

__all__ = [
    "BenchError",
    "CapsuleError",
    "CapsuleLimits",
    "build_capsule",
    "generate_keypair",
    "run_bench",
    "verify_capsule",
]

__version__ = "0.1.0"
