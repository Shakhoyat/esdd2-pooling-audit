"""Theorem 2 in both directions, on constructed systems. No data needed.

The paper says both directions are checked numerically in the released code and
that every sampled value in the interval is realised to 1e-12. These are those
checks. They are numerical, not a proof -- see README, "A numerical check is not
a proof".
"""
import numpy as np
import pytest

from pooling_audit.bounds import interval
from pooling_audit.sharpness import (_far, _frr, attainment_grid, build_system,
                                     containment, lower_endpoint_witness)


def test_every_sampled_value_is_attained_to_1e12():
    r = attainment_grid(n_points=25)
    assert r["n_infeasible"] == 0
    assert r["n_constructions"] == 6 * 25
    assert r["worst_residual"] < 1e-12


@pytest.mark.parametrize("E,w0", [(0.4336, 0.532310), (0.6, 0.25)])
def test_both_endpoints_are_constructed(E, w0):
    for v in interval(E, w0):
        neg, Pa, P0, tc, tp = build_system(E, w0, v)
        assert min(P0.values()) >= -1e-12 and min(neg.values()) >= -1e-12
        assert _far(neg, tp) == pytest.approx(E, abs=1e-12)
        assert w0 * _frr(P0, tp) + (1 - w0) * _frr(Pa, tp) == pytest.approx(E, abs=1e-12)
        assert _far(neg, tc) == pytest.approx(v, abs=1e-12)
        assert _frr(Pa, tc) == pytest.approx(v, abs=1e-12)


def test_no_random_admissible_system_escapes_the_interval():
    assert containment(trials=2000, seed=11)["worst_violation"] == 0.0


def test_containment_check_can_fail():
    """A check that cannot fail checks nothing: misreport the pooled value and it must object."""
    assert containment(trials=500, seed=11, published_scale=0.8)["worst_violation"] > 0.0


def test_lower_endpoint_witness_on_synthetic_labels():
    rng = np.random.default_rng(3)
    labels = rng.choice([0, 1, 2, 3, 4], size=30000, p=[0.27, 0.13, 0.11, 0.28, 0.21])
    w = lower_endpoint_witness(labels, 0.4336)
    assert w["found"] and w["at_lower"] and w["component_only"] == 0.0
    assert round(w["pooled"], 4) == 0.4336
    assert w["upper_claimed"] is False
