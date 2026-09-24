"""The released ESDD2 scorer's equal error rate, reimplemented.

This is a REIMPLEMENTATION from the published description, not a copy. The
original is `libs/eval_metrics.py` in the ESDD2 baseline release
(https://github.com/XuepingZhang/ESDD2-Baseline), whose `compute_eer` builds an
ROC with `sklearn.metrics.roc_curve`, takes the index minimising |fpr - fnr|,
and returns the MEAN of fpr and fnr at that index rather than either one. That
"mean at the nearest ROC vertex" detail is what makes the reported value a step
function of the fill constant, so it matters and is preserved here.

Orientation, from the same file: `pos_label=1` is BONA FIDE and the submitted
component scores are bona-fide-oriented (higher = more genuine). We therefore
label SPOOF as 1 and negate the score, which is the equivalent framing and the
one under which FRR_pub = w0*FRR_0 + wa*FRR_a closes.

`tests/test_scorer_equivalence.py` pins this against fixtures.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_curve

# Component axes, as the ESDD2 evaluation plan defines them (its Table I).
# Class 0 (`original`) is INAPPLICABLE: it carries no component annotation.
AXES = {
    "env":    {"bona": (1, 2), "spoof": (3, 4)},
    "speech": {"bona": (1, 3), "spoof": (2, 4)},
}


def eer_from_scores(scores: np.ndarray, is_spoof: np.ndarray) -> float:
    """EER at the nearest ROC vertex, averaging FAR and FRR there."""
    scores = np.asarray(scores, dtype=float)
    is_spoof = np.asarray(is_spoof).astype(int)
    if scores.size < 2 or is_spoof.min() == is_spoof.max():
        return float("nan")
    fpr, tpr, _ = roc_curve(is_spoof, -scores, pos_label=1)
    fnr = 1.0 - tpr
    i = int(np.nanargmin(np.abs(fpr - fnr)))
    return float((fpr[i] + fnr[i]) / 2.0)


def component_eer(labels: np.ndarray, scores: np.ndarray, axis: str,
                  include_inapplicable: bool = False,
                  mask: np.ndarray | None = None) -> float:
    """EER on one component axis.

    include_inapplicable=False  the component-only value: class 0 is dropped.
    include_inapplicable=True   the published value: class 0 joins the BONA FIDE
                                side, which is the mapping the protocol mandates.
    """
    spec = AXES[axis]
    wanted = set(spec["bona"]) | set(spec["spoof"])
    if include_inapplicable:
        wanted |= {0}
    keep = np.isin(labels, list(wanted))
    if mask is not None:
        keep &= mask
    return eer_from_scores(scores[keep], np.isin(labels[keep], spec["spoof"]))


def inapplicable_share(labels: np.ndarray, axis: str) -> float:
    """w0: the inapplicable share of the positive side on this axis."""
    n0 = int((labels == 0).sum())
    na = int(np.isin(labels, AXES[axis]["bona"]).sum())
    return n0 / (n0 + na)


def declared_prior(labels: np.ndarray, axis: str) -> float:
    """The third declared constant: the bona fide share among APPLICABLE clips."""
    return float(np.isin(labels, AXES[axis]["bona"]).sum() / (labels != 0).sum())


def far_frr_at(scores: np.ndarray, labels: np.ndarray, axis: str, c: float):
    """FAR on the negatives and FRR on the applicable positives at threshold c."""
    spec = AXES[axis]
    spoof = np.isin(labels, spec["spoof"])
    bona = np.isin(labels, spec["bona"])
    return float((scores[spoof] >= c).mean()), float((scores[bona] < c).mean())
