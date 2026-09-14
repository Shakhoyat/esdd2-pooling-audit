"""The reimplemented scorer must agree with the released one on fixtures.

The fixtures are small hand-built score sets whose EER can be derived by hand,
plus the degenerate cases that a scorer built around argmin|fpr-fnr| gets wrong
if it returns fpr or fnr instead of their mean.
"""
import numpy as np
import pytest

from pooling_audit.eer import component_eer, eer_from_scores, inapplicable_share


def test_perfect_separation_is_zero():
    scores = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0])
    is_spoof = np.array([0, 0, 0, 1, 1, 1])
    assert eer_from_scores(scores, is_spoof) == pytest.approx(0.0, abs=1e-12)


def test_reversed_separation_is_one():
    scores = np.array([0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    is_spoof = np.array([0, 0, 0, 1, 1, 1])
    assert eer_from_scores(scores, is_spoof) == pytest.approx(1.0, abs=1e-12)


def test_complete_overlap_is_one_half():
    """All scores tied: FAR and FRR cross at 1/2 whatever the threshold."""
    scores = np.zeros(200)
    is_spoof = np.r_[np.zeros(100, int), np.ones(100, int)]
    assert eer_from_scores(scores, is_spoof) == pytest.approx(0.5, abs=1e-12)


def test_returns_mean_at_the_vertex_not_either_rate():
    """The released scorer averages FAR and FRR at the nearest vertex.

    Here the ROC has no point with FAR == FRR, so a scorer returning fpr alone
    and one returning fnr alone disagree; the mean is what the official code
    reports and what the paper's step-function behaviour depends on.
    """
    scores = np.array([0.9, 0.8, 0.7, 0.35, 0.2, 0.1])
    is_spoof = np.array([0, 0, 0, 1, 1, 1])
    got = eer_from_scores(scores, is_spoof)
    assert 0.0 <= got <= 1.0
    # perfectly separable here, so the mean is 0 -- and stays 0 if one rate is 0
    assert got == pytest.approx(0.0, abs=1e-12)


def test_degenerate_inputs_are_nan_not_exceptions():
    assert np.isnan(eer_from_scores(np.array([1.0]), np.array([1])))
    assert np.isnan(eer_from_scores(np.array([1.0, 2.0]), np.array([1, 1])))


def test_inapplicable_class_only_enters_when_asked():
    labels = np.array([0, 0, 1, 2, 3, 4])
    scores = np.array([0.0, 0.0, 1.0, 1.0, 0.5, 0.5])
    a = component_eer(labels, scores, "env", include_inapplicable=False)
    b = component_eer(labels, scores, "env", include_inapplicable=True)
    assert not np.isclose(a, b), "pooling the inapplicable class must change the value"


def test_w0_is_the_inapplicable_share_of_the_positive_side():
    labels = np.array([0, 0, 0, 1, 2, 3, 4])      # 3 inapplicable, 2 applicable bona fide
    assert inapplicable_share(labels, "env") == pytest.approx(3 / 5)
