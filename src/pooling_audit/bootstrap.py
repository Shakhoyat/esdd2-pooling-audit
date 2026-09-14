"""Clustered bootstrap. The cluster is the SOURCE COMPONENT CLIP, not the mixture.

One source component appears in several mixtures, so those rows are not
independent. On the evaluation split this is close to a no-op -- almost every row
is its own cluster -- and it is reported because it is the correct estimator,
not because it changes the interval.

The EER is not a mean, and neither is the absolute error between two EERs, so
both are recomputed inside every resample rather than averaged.
"""
from __future__ import annotations

import numpy as np


def clustered_ci(stat_fn, clusters: np.ndarray, n_draws: int = 2000,
                 seed: int = 1337, alpha: float = 0.05) -> dict:
    """Percentile CI for any statistic of a row set, resampling whole clusters."""
    uniq, inverse = np.unique(clusters, return_inverse=True)
    rows_by_cluster = [np.flatnonzero(inverse == i) for i in range(len(uniq))]
    rng = np.random.default_rng(seed)
    point = stat_fn(np.arange(len(clusters)))
    draws = []
    for _ in range(n_draws):
        picked = rng.integers(0, len(uniq), len(uniq))
        rows = np.concatenate([rows_by_cluster[i] for i in picked])
        v = stat_fn(rows)
        if v is not None and np.isfinite(np.asarray(v, dtype=float)).all():
            draws.append(v)
    a = np.asarray(draws, dtype=float)
    lo, hi = np.percentile(a, [100 * alpha / 2, 100 * (1 - alpha / 2)], axis=0)
    # stat_fn may return a scalar or a vector of statistics; keep whichever shape
    # it gave, so a caller can bootstrap several quantities jointly in one pass.
    scalar = np.ndim(point) == 0
    return dict(point=point,
                lo=float(lo) if scalar else lo,
                hi=float(hi) if scalar else hi,
                n_draws=int(a.shape[0]), n_clusters=int(len(uniq)))
