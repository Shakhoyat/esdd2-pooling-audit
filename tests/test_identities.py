"""Identities (1) and (2) are exact whenever the negative set is shared.

They are algebra, not approximations, so these run on synthetic data and assert
machine precision. If either ever fails, Theorem 1's premise has gone.
"""
import numpy as np
import pytest

from pooling_audit.pooling import frr_identity_residual, pooling_residual


def synthetic(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    labels = np.r_[np.zeros(n // 4, int), np.full(n // 4, 1),
                   np.full(n // 4, 3), np.full(n // 4, 4)]
    scores = np.r_[rng.normal(0.2, 0.3, n // 4),      # inapplicable
                   rng.normal(1.0, 0.4, n // 4),      # applicable bona fide
                   rng.normal(-1.0, 0.4, n // 4),     # spoof env
                   rng.normal(-1.2, 0.4, n // 4)]
    return labels, scores


def test_frr_identity_1_is_exact():
    labels, scores = synthetic()
    taus = np.linspace(scores.min() - 1, scores.max() + 1, 200)
    assert frr_identity_residual(labels, scores, "env", 0.0, taus) < 1e-12


def test_roc_identity_2_makes_areas_average_exactly():
    labels, scores = synthetic(seed=1)
    r = pooling_residual(labels, scores, "env", 0.0, n_grid=4001)
    assert r["area_residual"] < 1e-12, "areas must aggregate exactly"


def _pl(points, grid):
    """Piecewise-linear ROC through the given (FAR, TPR) points."""
    xs, ys = zip(*points)
    return np.interp(grid, xs, ys)


def _crossing(R, grid):
    i = int(np.nanargmin(np.abs(grid - (1.0 - R))))
    return float((grid[i] + (1.0 - R[i])) / 2.0)


def test_no_aggregation_rule_exists_for_the_crossing():
    """The necessity direction, as a witness rather than a per-instance gap.

    Theorem 1 does NOT say the pooled crossing always differs from the weighted
    mean -- on easy data it can coincide, and it does for some random draws.
    It says no function phi(T_0, T_a, w0) reproduces the pooled value for ALL
    curves. Two component pairs with IDENTICAL (EER_0, EER_a) at the same w0 but
    DIFFERENT pooled EER settle that: no function of those three arguments can
    return both. Areas, by contrast, aggregate on the very same pairs.
    """
    grid = np.linspace(0.0, 1.0, 200001)
    w0 = 0.5
    e0, ea = 0.30, 0.20

    # Pair A: the plain piecewise-linear curves through each crossing.
    A0 = _pl([(0, 0), (e0, 1 - e0), (1, 1)], grid)
    Aa = _pl([(0, 0), (ea, 1 - ea), (1, 1)], grid)
    # Pair B: same crossings, different shape either side of them.
    B0 = _pl([(0, 0), (0.05, 0.50), (e0, 1 - e0), (1, 1)], grid)
    Ba = _pl([(0, 0), (ea, 1 - ea), (0.90, 0.99), (1, 1)], grid)

    for R0, Ra in ((A0, Aa), (B0, Ba)):
        assert _crossing(R0, grid) == pytest.approx(e0, abs=1e-4)
        assert _crossing(Ra, grid) == pytest.approx(ea, abs=1e-4)

    pooled_A = _crossing(w0 * A0 + (1 - w0) * Aa, grid)
    pooled_B = _crossing(w0 * B0 + (1 - w0) * Ba, grid)
    assert abs(pooled_A - pooled_B) > 1e-3, (
        "identical component crossings must be able to give different pooled "
        "crossings, or an aggregation rule would exist")

    # control: the AREA does aggregate, on these same two pairs
    for R0, Ra in ((A0, Aa), (B0, Ba)):
        pooled_area = np.trapezoid(w0 * R0 + (1 - w0) * Ra, grid)
        mean_area = w0 * np.trapezoid(R0, grid) + (1 - w0) * np.trapezoid(Ra, grid)
        assert abs(pooled_area - mean_area) < 1e-12


@pytest.mark.parametrize("c", [-2.0, 0.0, 0.5, 2.0])
def test_identity_holds_for_any_fill_constant(c):
    labels, scores = synthetic(seed=3)
    r = pooling_residual(labels, scores, "env", c, n_grid=2001)
    assert r["area_residual"] < 1e-12
