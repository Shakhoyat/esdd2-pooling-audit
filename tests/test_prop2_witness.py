"""Proposition 2's witnesses, exactly and under the released scorer. No data needed.

Every claimed cell is asserted in exact arithmetic and then under both released-scorer
orientations and both materialisations of the same exact ROC. The sparse materialisation
leaves only breakpoints; a witness whose crossing sat inside a segment would fail there,
which is why every printed crossing and optimum is a genuine vertex.
"""
from fractions import Fraction as F

import pytest

from pooling_audit.witness import HALF, WITNESSES, check, exact, mix

TOL = 1e-12           # the released scorer reproduces these exactly; this is float round-off


@pytest.mark.parametrize("name", sorted(WITNESSES))
def test_witness_holds_in_exact_arithmetic(name):
    w = WITNESSES[name]
    a, b, s = w["curves"]
    assert a.p != b.p, "A and B must be different curves"
    assert all(c.is_valid() for c in (a, b, s, mix(a, s, HALF), mix(b, s, HALF))), "curves must be concave ROCs"
    got = exact(name)
    for side in ("component", "pooled"):
        for tag, claims in w[side].items():
            for metric, want in claims.items():
                assert got[(tag, metric)] == want, (name, tag, metric, got[(tag, metric)], want)
    metric = next(iter(w["pooled"]["A|S"]))
    if metric != "AUC":
        assert got[("A", next(iter(w["component"]["A"])))] == got[("B", next(iter(w["component"]["B"])))]
        assert got[("A|S", metric)] != got[("B|S", metric)], "pooled values must differ"


@pytest.mark.parametrize("dense", [False, True], ids=["sparse", "dense"])
@pytest.mark.parametrize("name", sorted(WITNESSES))
def test_released_scorer_reproduces_every_cell(name, dense):
    r = check(name, 1, dense)
    bad = [c for c in r["cells"] if c["gap"] > TOL]
    assert not bad, bad
    assert {c["implementation"] for c in r["cells"]} == {"baseline", "audit"}
    if not dense:
        assert max(r["pooled_vertices"].values()) <= 6, "sparse must leave only breakpoints"


def test_equal_prior_triple_does_not_separate_at_asvspoof5_costs():
    """Why a third triple exists: at beta = 1.9 the equal-prior curves pool to the same 97/120."""
    from pooling_audit.witness import BETA_ASVSPOOF5
    a, b, s = WITNESSES["dcf_j"]["curves"]
    va = mix(a, s, HALF).mindcf(BETA_ASVSPOOF5, F(1))
    vb = mix(b, s, HALF).mindcf(BETA_ASVSPOOF5, F(1))
    assert va == vb == F(97, 120)
