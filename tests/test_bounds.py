"""Theorem 2's interval and the ordering criterion."""
import pytest

from pooling_audit.bounds import disjoint, interval, pairwise_determined


def test_interval_formula():
    lo, hi = interval(eer_pub=0.4336, w0=0.5323)
    assert lo == pytest.approx(0.0)                    # clipped at 0
    assert hi == pytest.approx(0.4336 / (1 - 0.5323), rel=1e-12)


def test_interval_is_clipped_to_the_unit_square():
    lo, hi = interval(eer_pub=0.9, w0=0.1)
    assert 0.0 <= lo <= hi <= 1.0


def test_lower_endpoint_is_zero_whenever_published_is_below_the_share():
    for e in (0.05, 0.2, 0.4336, 0.53):
        lo, _ = interval(e, 0.5323)
        assert lo == pytest.approx(0.0)


def test_disjointness_matches_the_gap_criterion():
    """Two intervals are disjoint exactly when the published values differ by > w0."""
    w0 = 0.3
    for a in [0.05, 0.2, 0.35, 0.5, 0.7]:
        for b in [0.05, 0.2, 0.35, 0.5, 0.7]:
            geo = disjoint(interval(a, w0), interval(b, w0))
            crit = abs(a - b) > w0
            assert geo == crit, (a, b)


def test_pairwise_determined_agrees_both_ways():
    pub = [0.0869, 0.0926, 0.11, 0.1126, 0.1228, 0.1263,
           0.1594, 0.1703, 0.1883, 0.2853, 0.4279]
    r = pairwise_determined(pub, w0=0.5282467763767187)
    assert r["n_pairs"] == 55
    assert r["mismatches"] == 0
    assert r["determined_geometric"] == r["determined_criterion"] == 0
