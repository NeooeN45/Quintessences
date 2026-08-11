"""Script de benchmark rapide — scipy vs numpy pour Pearson pairwise."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from benchmark_correlation import (
    MATRIX_SIZES,
    compute_pairwise_pearson_numpy,
    compute_pairwise_pearson_scipy,
    generate_correlated_data,
)

print("# Benchmark Correlation Engine — scipy vs numpy (CPU baseline)")
print(f"# Matrices: {MATRIX_SIZES}")
print()

results = []
for n_vars, n_obs in MATRIX_SIZES:
    data = generate_correlated_data(n_vars, n_obs)
    n_pairs = n_vars * (n_vars - 1) // 2

    # scipy
    t0 = time.perf_counter()
    compute_pairwise_pearson_scipy(data)
    scipy_ms = (time.perf_counter() - t0) * 1000

    # numpy
    t0 = time.perf_counter()
    compute_pairwise_pearson_numpy(data)
    numpy_ms = (time.perf_counter() - t0) * 1000

    speedup = scipy_ms / numpy_ms if numpy_ms > 0 else 0
    print(
        f"{n_vars:>4} vars x {n_obs:>7} obs | {n_pairs:>8} paires | "
        f"scipy={scipy_ms:>10.2f} ms | numpy={numpy_ms:>10.2f} ms | "
        f"speedup={speedup:>6.1f}x"
    )
    results.append(
        {
            "n_vars": n_vars,
            "n_obs": n_obs,
            "n_pairs": n_pairs,
            "scipy_ms": round(scipy_ms, 2),
            "numpy_ms": round(numpy_ms, 2),
            "speedup": round(speedup, 1),
        }
    )

print()
print("## Resume")
print("| Vars x Obs | Paires | scipy (ms) | numpy (ms) | Speedup |")
print("|---|---|---|---|---|")
for r in results:
    v = r["n_vars"]
    o = r["n_obs"]
    p = r["n_pairs"]
    s = r["scipy_ms"]
    n = r["numpy_ms"]
    su = r["speedup"]
    print(f"| {v} x {o} | {p} | {s} | {n} | {su}x |")
