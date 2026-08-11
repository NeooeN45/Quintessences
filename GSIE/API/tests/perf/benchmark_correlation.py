"""Benchmark Correlation Engine — scipy (baseline CPU) vs nvmath-python (GPU).

Ce module mesure les performances du calcul de corrélation Pearson sur
des matrices de variables de tailles croissées, pour établir un baseline
scipy et préparer l'évaluation de nvmath-python comme backend optionnel.

Contexte : veille NVIDIA Developer Blog du 2026-08-08, article
nvmath-python v1.0. Voir GSIE/RESEARCH/VEILLE_NVIDIA_DEV_BLOG_2026-08-08.md §2.

Exécution :
    # Baseline scipy uniquement (CPU, pas de GPU requis)
    python tests/perf/benchmark_correlation.py

    # Avec nvmath-python (requiert GPU NVIDIA + nvmath installé)
    python tests/perf/benchmark_correlation.py --backend nvmath

Le benchmark génère un rapport JSON dans tests/perf/results/ et un
résumé Markdown sur stdout.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np
from scipy import stats as scipy_stats

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Tailles de matrices testées : (n_variables, n_observations)
# n_variables simule le nombre de variables GSIE (120+ tables, météo, sol, etc.)
# n_observations simule le nombre de relevés terrain
MATRIX_SIZES: list[tuple[int, int]] = [
    (10, 100),
    (10, 1_000),
    (10, 10_000),
    (50, 1_000),
    (50, 10_000),
    (120, 1_000),
    (120, 10_000),
]

N_REPETITIONS = 5  # répétitions pour stabiliser les mesures
WARMUP_RUNS = 1  # runs d'échauffement (cache, JIT, etc.)


# ---------------------------------------------------------------------------
# Dataclasses pour les résultats
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    """Configuration d'un run de benchmark."""

    backend: Literal["scipy", "nvmath"]
    matrix_sizes: list[tuple[int, int]]
    n_repetitions: int
    warmup_runs: int
    platform: str
    python_version: str
    scipy_version: str
    numpy_version: str
    nvmath_version: str | None = None
    gpu_name: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True, slots=True)
class MatrixResult:
    """Résultat pour une taille de matrice donnée."""

    n_variables: int
    n_observations: int
    n_pairs: int  # n_variables * (n_variables - 1) / 2
    times_ms: list[float]  # une mesure par répétition
    mean_ms: float
    median_ms: float
    std_ms: float
    min_ms: float
    max_ms: float
    throughput_pairs_per_sec: float


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    """Rapport complet d'un benchmark."""

    config: BenchmarkConfig
    results: list[MatrixResult]
    summary: str


# ---------------------------------------------------------------------------
# Génération de données synthétiques
# ---------------------------------------------------------------------------


def generate_correlated_data(
    n_variables: int,
    n_observations: int,
    seed: int = 42,
) -> np.ndarray:
    """Génère une matrice (n_variables, n_observations) avec corrélations.

    Les variables sont générées avec une structure de corrélation
    réaliste : quelques clusters de variables corrélées + bruit.
    """
    rng = np.random.default_rng(seed)
    # 3 clusters de variables corrélées
    cluster_size = max(1, n_variables // 3)
    data = np.empty((n_variables, n_observations), dtype=np.float64)

    for i in range(n_variables):
        cluster = i // cluster_size
        # Chaque cluster partage un facteur latent
        latent = rng.standard_normal(n_observations) * (1.0 + cluster * 0.3)
        noise = rng.standard_normal(n_observations) * 0.5
        data[i] = latent + noise

    return data


# ---------------------------------------------------------------------------
# Backend scipy (baseline CPU)
# ---------------------------------------------------------------------------


def compute_pairwise_pearson_scipy(data: np.ndarray) -> np.ndarray:
    """Calcule la matrice de corrélation Pearson pairwise avec scipy.

    Args:
        data: matrice (n_variables, n_observations)

    Returns:
        Matrice (n_variables, n_variables) de coefficients Pearson.
    """
    n_vars = data.shape[0]
    result = np.ones((n_vars, n_vars), dtype=np.float64)

    for i in range(n_vars):
        for j in range(i + 1, n_vars):
            r, _ = scipy_stats.pearsonr(data[i], data[j])
            result[i, j] = r
            result[j, i] = r

    return result


# ---------------------------------------------------------------------------
# Backend numpy vectorisé (alternative CPU, plus rapide que scipy pairwise)
# ---------------------------------------------------------------------------


def compute_pairwise_pearson_numpy(data: np.ndarray) -> np.ndarray:
    """Calcule la matrice de corrélation Pearson avec numpy vectorisé.

    Utilise np.corrcoef qui est largement plus rapide que scipy pairwise
    pour les matrices N×N. Cette fonction sert de référence CPU haute
    performance (sans GPU).

    Args:
        data: matrice (n_variables, n_observations)

    Returns:
        Matrice (n_variables, n_variables) de coefficients Pearson.
    """
    # np.corrcoef attend (observations, variables) par défaut avec rowvar=False
    return np.corrcoef(data)


# ---------------------------------------------------------------------------
# Backend nvmath-python (GPU — requiert nvmath installé + GPU NVIDIA)
# ---------------------------------------------------------------------------


def compute_pairwise_pearson_nvmath(data: np.ndarray) -> np.ndarray:
    """Calcule la matrice de corrélation Pearson avec nvmath-python (GPU).

    Utilise nvmath.linalg.advanced.matmul pour le produit matriciel
    accéléré GPU, puis normalise pour obtenir les coefficients Pearson.

    Principe :
        1. Centrer et réduire chaque variable (z-score)
        2. Calculer la matrice de covariance C = X @ X^T / (n-1)
        3. Normaliser par les écarts-types : R = C / (sigma_i * sigma_j)

    Avec nvmath, l'étape 2 utilise cuBLAS sur GPU.

    Raises:
        ImportError: si nvmath n'est pas installé ou pas de GPU disponible.
    """
    try:
        import cupy as cp
        import nvmath
    except ImportError as exc:
        raise ImportError(
            "nvmath-python et cupy sont requis pour le backend GPU. "
            "Installez avec : pip install nvmath-python cupy-cuda12x"
        ) from exc

    n_vars, n_obs = data.shape

    # Transférer vers GPU
    data_gpu = cp.asarray(data, dtype=cp.float64)

    # Z-score : centrer et réduire
    mean = cp.mean(data_gpu, axis=1, keepdims=True)
    std = cp.std(data_gpu, axis=1, keepdims=True)
    z_gpu = (data_gpu - mean) / (std + 1e-10)  # epsilon pour éviter division par zéro

    # Produit matriciel accéléré GPU via nvmath
    # R = (Z @ Z^T) / (n_obs - 1)
    covariance_gpu = nvmath.linalg.advanced.matmul(z_gpu, z_gpu.T)

    # Normalisation : les z-scores ont std=1, donc covariance = corrélation
    correlation_gpu = covariance_gpu / (n_obs - 1)

    # Clip pour gérer les erreurs numériques
    correlation_gpu = cp.clip(correlation_gpu, -1.0, 1.0)

    # Transférer vers CPU
    return cp.asnumpy(correlation_gpu)


# ---------------------------------------------------------------------------
# Benchmark engine
# ---------------------------------------------------------------------------


def _time_function(func: callable, *args: object, **kwargs: object) -> float:
    """Mesure le temps d'exécution d'une fonction en millisecondes."""
    start = time.perf_counter()
    func(*args, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000.0
    return elapsed


def benchmark_matrix(
    data: np.ndarray,
    compute_func: callable,
    n_repetitions: int,
    warmup_runs: int,
) -> MatrixResult:
    """Benchmark une fonction de calcul pour une matrice donnée."""
    n_vars, n_obs = data.shape
    n_pairs = n_vars * (n_vars - 1) // 2

    # Warmup
    for _ in range(warmup_runs):
        compute_func(data)

    # Mesures
    times: list[float] = []
    for _ in range(n_repetitions):
        t = _time_function(compute_func, data)
        times.append(t)

    arr = np.array(times)
    return MatrixResult(
        n_variables=n_vars,
        n_observations=n_obs,
        n_pairs=n_pairs,
        times_ms=[round(t, 3) for t in times],
        mean_ms=round(float(np.mean(arr)), 3),
        median_ms=round(float(np.median(arr)), 3),
        std_ms=round(float(np.std(arr)), 3),
        min_ms=round(float(np.min(arr)), 3),
        max_ms=round(float(np.max(arr)), 3),
        throughput_pairs_per_sec=round(n_pairs / (float(np.median(arr)) / 1000.0), 1),
    )


def run_benchmark(
    backend: Literal["scipy", "nvmath", "numpy"],
    matrix_sizes: list[tuple[int, int]],
    n_repetitions: int,
    warmup_runs: int,
) -> BenchmarkReport:
    """Exécute un benchmark complet pour un backend donné."""
    import platform

    import scipy

    compute_func: callable
    nvmath_version: str | None = None
    gpu_name: str | None = None

    if backend == "scipy":
        compute_func = compute_pairwise_pearson_scipy
    elif backend == "numpy":
        compute_func = compute_pairwise_pearson_numpy
    elif backend == "nvmath":
        compute_func = compute_pairwise_pearson_nvmath
        try:
            import nvmath

            nvmath_version = nvmath.__version__
        except ImportError:
            nvmath_version = "not installed"
        try:
            import cupy as cp

            gpu_name = cp.cuda.runtime.getDeviceProperties(0)["name"]
        except Exception:
            gpu_name = "not available"
    else:
        raise ValueError(f"Backend inconnu : {backend}")

    config = BenchmarkConfig(
        backend=backend,
        matrix_sizes=matrix_sizes,
        n_repetitions=n_repetitions,
        warmup_runs=warmup_runs,
        platform=f"{platform.system()} {platform.machine()}",
        python_version=platform.python_version(),
        scipy_version=scipy.__version__,
        numpy_version=np.__version__,
        nvmath_version=nvmath_version,
        gpu_name=gpu_name,
    )

    results: list[MatrixResult] = []
    for n_vars, n_obs in matrix_sizes:
        data = generate_correlated_data(n_vars, n_obs)
        result = benchmark_matrix(data, compute_func, n_repetitions, warmup_runs)
        results.append(result)
        print(
            f"  [{backend}] {n_vars:>4} vars × {n_obs:>7} obs "
            f"({result.n_pairs:>10} paires) : "
            f"médiane={result.median_ms:>10.3f} ms, "
            f"throughput={result.throughput_pairs_per_sec:>12.1f} paires/s"
        )

    # Résumé
    fastest = min(results, key=lambda r: r.throughput_pairs_per_sec)
    slowest = max(results, key=lambda r: r.throughput_pairs_per_sec)
    summary = (
        f"Backend {backend} : "
        f"throughput min={fastest.throughput_pairs_per_sec:.1f} paires/s "
        f"({fastest.n_variables}×{fastest.n_observations}), "
        f"max={slowest.throughput_pairs_per_sec:.1f} paires/s "
        f"({slowest.n_variables}×{slowest.n_observations})"
    )

    return BenchmarkReport(config=config, results=results, summary=summary)


# ---------------------------------------------------------------------------
# Rapport et sortie
# ---------------------------------------------------------------------------


def save_report(report: BenchmarkReport, output_dir: Path) -> Path:
    """Sauvegarde le rapport en JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_{report.config.backend}_{timestamp}.json"
    filepath = output_dir / filename

    report_dict = {
        "config": asdict(report.config),
        "results": [asdict(r) for r in report.results],
        "summary": report.summary,
    }

    with filepath.open("w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    return filepath


def print_markdown_summary(reports: list[BenchmarkReport]) -> None:
    """Affiche un résumé comparatif en Markdown."""
    print("\n## Résumé comparatif\n")
    print("| Backend | Vars × Obs | Paires | Médiane (ms) | Throughput (paires/s) |")
    print("|---|---|---|---|---|")

    for report in reports:
        for r in report.results:
            print(
                f"| {report.config.backend} | "
                f"{r.n_variables} × {r.n_observations} | "
                f"{r.n_pairs} | "
                f"{r.median_ms} | "
                f"{r.throughput_pairs_per_sec} |"
            )

    print("\n### Configurations testées\n")
    for report in reports:
        c = report.config
        print(
            f"- **{c.backend}** : {c.platform}, Python {c.python_version}, "
            f"numpy {c.numpy_version}, scipy {c.scipy_version}",
            end="",
        )
        if c.nvmath_version:
            print(f", nvmath {c.nvmath_version}", end="")
        if c.gpu_name:
            print(f", GPU {c.gpu_name}", end="")
        print()


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark Correlation Engine — scipy vs nvmath-python"
    )
    parser.add_argument(
        "--backend",
        choices=["scipy", "numpy", "nvmath", "all"],
        default="all",
        help="Backend à tester (default: all = scipy + numpy)",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=N_REPETITIONS,
        help=f"Nombre de répétitions par matrice (default: {N_REPETITIONS})",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=WARMUP_RUNS,
        help=f"Runs d'échauffement (default: {WARMUP_RUNS})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "results",
        help="Dossier de sortie pour les rapports JSON",
    )
    args = parser.parse_args()

    # Déterminer les backends à tester
    if args.backend == "all":
        backends: list[Literal["scipy", "nvmath", "numpy"]] = ["scipy", "numpy"]
        # Tenter nvmath si disponible
        try:
            import nvmath  # noqa: F401

            backends.append("nvmath")
        except ImportError:
            print("nvmath-python non installé — backend GPU ignoré.")
            print("Pour tester nvmath : pip install nvmath-python cupy-cuda12x")
    else:
        backends = [args.backend]

    print(f"# Benchmark Correlation Engine — {datetime.now(UTC).isoformat()}")
    print(f"# Backends : {backends}")
    print(f"# Répétitions : {args.repetitions}, Warmup : {args.warmup}\n")

    reports: list[BenchmarkReport] = []
    for backend in backends:
        print(f"\n### Backend : {backend}\n")
        try:
            report = run_benchmark(
                backend=backend,
                matrix_sizes=MATRIX_SIZES,
                n_repetitions=args.repetitions,
                warmup_runs=args.warmup,
            )
            reports.append(report)
            filepath = save_report(report, args.output_dir)
            print(f"  → Rapport sauvegardé : {filepath}")
        except ImportError as exc:
            print(f"  ✗ Backend {backend} indisponible : {exc}")
        except Exception as exc:
            print(f"  ✗ Erreur backend {backend} : {exc}")

    if len(reports) > 1:
        print_markdown_summary(reports)

    print("\n# Résumé :")
    for report in reports:
        print(f"  - {report.summary}")


if __name__ == "__main__":
    main()
