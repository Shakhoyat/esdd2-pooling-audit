"""Degenerate cases for pooling_audit.acds, and the tie convention.

Eleven unit tests with hand-derivable answers, not experiments: they need no data and run on a
clean clone. They pin the three choices the module's docstring fixes -- that t is a rate on the
negatives alone, that the rule is trapezoid, and that ties collapse to one grid point -- plus the
five degenerate cases the score has to survive (no structural zeros, a chance system, an alarm on
every structural zero, the range and monotonicity in alpha_0, and a t_max between grid points).
"""
import numpy as np
import pytest

from pooling_audit import acds as A


def _c(neg, pa, p0=()):
    return A.curves(np.asarray(neg, float), np.asarray(pa, float), np.asarray(p0, float))


@pytest.mark.parametrize("alpha0", [0.0, 1.0, 2.0])
def test_w0_zero_reduces_to_auc_a(alpha0):
    """No structural zeros: ACDS(alpha0, tmax) = AUC_a for every alpha0."""
    t, roc_a, r0, _ = _c([0, 1, 2, 3], [1, 2, 3, 4])
    auc_a = A.auc(t, roc_a)
    assert A.acds(t, roc_a, r0, alpha0, 1.0) == pytest.approx(auc_a, abs=1e-15)
    assert A.acds(t, roc_a, r0, alpha0, 0.2) == pytest.approx(A.acds(t, roc_a, r0, 0.0, 0.2), abs=1e-15)


def test_chance_system_returns_one_half():
    """AUC_a = 0.5 must come back as 0.5. The populations must be IDENTICAL: interleaving them
    ([0,2,4,6] against [1,3,5,7]) gives 0.625, because each positive beats every lower negative."""
    t, roc_a, r0, _ = _c([0, 1, 2, 3], [0, 1, 2, 3])
    assert A.acds(t, roc_a, r0, 0.0, 1.0) == pytest.approx(0.5, abs=1e-12)


@pytest.mark.parametrize("alpha0", [0.0, 0.5, 1.0])
def test_alarms_on_every_structural_zero(alpha0):
    """R0 == 1 everywhere: the score is AUC_a - alpha0."""
    t, roc_a, r0, _ = _c([0, 1, 2], [3, 4, 5], p0=[-10, -10, -10])
    assert A.acds(t, roc_a, r0, alpha0, 1.0) == pytest.approx(A.auc(t, roc_a) - alpha0, abs=1e-12)


def test_range_and_monotonicity_in_alpha0():
    rng = np.random.default_rng(0)
    t, roc_a, r0, _ = _c(rng.normal(0, 1, 200), rng.normal(1, 1, 200), rng.normal(0.2, 1, 150))
    vals = [A.acds(t, roc_a, r0, a, 1.0) for a in (0, 0.5, 1, 1.5, 2)]
    for a, v in zip((0, 0.5, 1, 1.5, 2), vals):
        assert -a - 1e-12 <= v <= 1 + 1e-12
    assert all(x >= y - 1e-12 for x, y in zip(vals, vals[1:]))


def test_fill_constant_invariance_is_bit_identical():
    """ACDS(0, .) must not move when the structural-zero score changes -- exactly, not nearly."""
    rng = np.random.default_rng(1)
    neg, pa = rng.normal(0, 1, 300), rng.normal(1, 1, 300)
    vals = set()
    for c in (0.0, 0.5, 0.3251, -1e6, 1e6):
        t, roc_a, r0, _ = _c(neg, pa, np.full(200, c))
        vals.add(A.acds(t, roc_a, r0, 0.0, 1.0))
    assert len(vals) == 1


def test_tie_convention_matches_the_pinned_scorer():
    """All scores tied: every rate is 0 or 1 at the two thresholds, so AUC_a = 1/2."""
    t, roc_a, r0, _ = _c([1, 1, 1], [1, 1, 1])
    assert A.auc(t, roc_a) == pytest.approx(0.5, abs=1e-12)


def test_tmax_interpolates_rather_than_snapping():
    """A tmax between grid points adds the partial trapezoid, so the score is continuous in tmax."""
    t, roc_a, r0, _ = _c([0, 1, 2, 3], [1, 2, 3, 4])
    a = A.acds(t, roc_a, r0, 0.0, 0.30)
    b = A.acds(t, roc_a, r0, 0.0, 0.3001)
    assert abs(a - b) < 1e-3
