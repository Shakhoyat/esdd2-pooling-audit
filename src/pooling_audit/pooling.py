"""Identities (1) and (2), and the collapsibility residual of Theorem 1.

(1)  FRR_pub(tau) = w0 FRR_0(tau) + wa FRR_a(tau)
(2)  ROC_pub(t)   = w0 ROC_0(t)   + wa ROC_a(t)

Both are exact whenever the negative set is shared, which is what makes the
pooled AREA a weighted mean while the pooled CROSSING is not. Neither needs any
continuity assumption, which is why the paper's figure -- whose R_0 is a step --
is an instance of (2) rather than of Theorem 1's curve class.
"""
from __future__ import annotations

import numpy as np

from .eer import AXES, eer_from_scores


def roc_on_grid(scores_pos: np.ndarray, scores_neg: np.ndarray,
                grid: np.ndarray) -> np.ndarray:
    """TPR of one positive population against SHARED negatives, at each FAR in grid."""
    tau = np.quantile(np.sort(scores_neg), 1.0 - grid)
    return np.array([(scores_pos >= t).mean() for t in tau])


def pooling_residual(labels: np.ndarray, scores: np.ndarray, axis: str,
                     c: float, n_grid: int = 2001):
    """Return (area residual, crossing gap) for the pooled vs weighted-mean summaries.

    The area residual is Theorem 1's dividing line made numeric: it must vanish
    to machine precision. The crossing gap must not.
    """
    spec = AXES[axis]
    neg = np.isin(labels, spec["spoof"])
    app = np.isin(labels, spec["bona"])
    inap = labels == 0
    w0 = inap.sum() / (inap.sum() + app.sum())
    wa = 1.0 - w0

    grid = np.linspace(0.0, 1.0, n_grid)
    R_a = roc_on_grid(scores[app], scores[neg], grid)
    tau = np.quantile(np.sort(scores[neg]), 1.0 - grid)
    R_0 = (c >= tau).astype(float)          # a step: every inapplicable clip scores c
    R_pub = w0 * R_0 + wa * R_a

    def area(R):
        return float(np.trapezoid(R, grid))

    def crossing(R):
        i = int(np.nanargmin(np.abs(grid - (1.0 - R))))
        return float((grid[i] + (1.0 - R[i])) / 2.0)

    area_res = abs(area(R_pub) - (w0 * area(R_0) + wa * area(R_a)))
    cross_gap = abs(crossing(R_pub) - (w0 * crossing(R_0) + wa * crossing(R_a)))
    return dict(w0=float(w0), wa=float(wa), area_pub=area(R_pub), area_0=area(R_0),
                area_a=area(R_a), area_residual=area_res, eer_pub=crossing(R_pub),
                eer_0=crossing(R_0), eer_a=crossing(R_a),
                eer_weighted_mean=w0 * crossing(R_0) + wa * crossing(R_a),
                crossing_gap=cross_gap)


def frr_identity_residual(labels: np.ndarray, scores: np.ndarray, axis: str,
                          c: float, taus: np.ndarray) -> float:
    """Largest violation of (1) over the supplied thresholds. Must be ~0."""
    spec = AXES[axis]
    app = np.isin(labels, spec["bona"])
    inap = labels == 0
    w0 = inap.sum() / (inap.sum() + app.sum())
    wa = 1.0 - w0
    s = np.where(inap, c, scores)
    pooled_pos = inap | app
    worst = 0.0
    for t in taus:
        lhs = float((s[pooled_pos] < t).mean())
        rhs = w0 * float((s[inap] < t).mean()) + wa * float((s[app] < t).mean())
        worst = max(worst, abs(lhs - rhs))
    return worst


# --------------------------------------------------------------------------
# Theorem 1's dividing line on real systems.
#
# Note what R_0 is here. It is the ROC of the inapplicable clips under the
# SYSTEM'S OWN scores, not a step at some fill constant. The collapsibility
# question is about the protocol's pooling of two populations against shared
# negatives, which is a property of the system as submitted; the fill constant
# is a separate question and belongs to Section 4.2.

SUMMARIES_COLLAPSIBLE = ("AUC", "pAUC(FAR<=0.2)", "TPR@FAR=0.01",
                         "TPR@FAR=0.05", "TPR@FAR=0.10")
SUMMARIES_NOT = ("EER", "min-DCF", "Youden's J")


def _summaries(R: np.ndarray, grid: np.ndarray) -> dict:
    """Every summary the paper sorts, evaluated on one ROC curve."""
    at = lambda t: float(np.interp(t, grid, R))
    hi = grid <= 0.2
    crossing_i = int(np.nanargmin(np.abs(grid - (1.0 - R))))
    return {
        "AUC": float(np.trapezoid(R, grid)),
        "pAUC(FAR<=0.2)": float(np.trapezoid(R[hi], grid[hi])),
        "TPR@FAR=0.01": at(0.01),
        "TPR@FAR=0.05": at(0.05),
        "TPR@FAR=0.10": at(0.10),
        "EER": float((grid[crossing_i] + (1.0 - R[crossing_i])) / 2.0),
        "min-DCF": float(np.min(0.5 * grid + 0.5 * (1.0 - R))),
        "Youden's J": float(np.max(R - grid)),
    }


def collapsibility_residuals(labels: np.ndarray, scores: np.ndarray, axis: str,
                             n_grid: int = 20001) -> dict:
    """Residual |T(pooled) - (w0 T(R_0) + wa T(R_a))| for every summary."""
    from .eer import AXES
    spec = AXES[axis]
    neg = np.isin(labels, spec["spoof"])
    app = np.isin(labels, spec["bona"])
    inap = labels == 0
    w0 = inap.sum() / (inap.sum() + app.sum())
    wa = 1.0 - w0

    grid = np.linspace(0.0, 1.0, n_grid)
    R_0 = roc_on_grid(scores[inap], scores[neg], grid)
    R_a = roc_on_grid(scores[app], scores[neg], grid)
    R_pub = w0 * R_0 + wa * R_a

    s_pub, s_0, s_a = (_summaries(R, grid) for R in (R_pub, R_0, R_a))
    return {k: abs(s_pub[k] - (w0 * s_0[k] + wa * s_a[k])) for k in s_pub}
