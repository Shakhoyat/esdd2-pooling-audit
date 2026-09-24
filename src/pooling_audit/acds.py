"""ACDS: the applicability-conditioned detection score, Definitions 2 and 3 of the paper.

    AC_a(t; alpha0)      = ROC_a(t) - alpha0 * R0(t)
    ACDS_a(alpha0, tmax) = (1/tmax) * integral_0^tmax AC_a(t; alpha0) dt

Populations (Definition 1), per axis a, from the corpus label and the applicability
indicator A_a (A_a = 0 on class 0, 1 on classes 1-4):

    N   = {A_a = 1, spoofed}      env: classes 3,4      speech: classes 2,4
    P_a = {A_a = 1, genuine}      env: classes 1,2      speech: classes 1,3
    P_0 = {A_a = 0}               class 0 (structural zeros)

THREE CHOICES, FIXED AND DOCUMENTED

1. `t` is a rate on N ONLY. Scores are bona-fide-oriented (higher = more genuine) and a
   clip is accepted at s >= tau. For each threshold tau, t = FAR(tau) = |{n in N: s >= tau}|/|N|,
   and BOTH ROC_a and R0 are read at that same tau, on one grid built from the distinct
   scores of every clip. There is no second threshold grid: that is the whole point, and it is
   what the paragraph after Definition 2 states.  The endpoints tau = +inf (t = 0) and tau below
   the minimum (t = 1) are included, so t spans [0, 1] and the integral needs no extrapolation.

   ROC_a(t) = |{p in P_a: s >= tau}|/|P_a|      the applicable positives accepted
   R0(t)    = |{x in P_0: s <  tau}|/|P_0|      the structural zeros REJECTED, = 1 - ROC_0(t)

   R0 is the rejection rate because on this axis a structural zero has no component to be
   genuine: calling it spoofed is the alarm being priced. This orientation is what makes
   Proposition 2(ii) close: integral_0^1 R0 = 1 - AUC_0.

2. INTERPOLATION: trapezoid (linear between grid points), for ACDS and for every AUC it is
   compared against, so that ACDS(0,1) = AUC_a holds exactly rather than approximately. The
   step rule is computed as well and reported; the paper states the two differ by at most
   4e-4 on any system.  When tmax falls between grid points the curve is linearly interpolated
   at tmax and the partial trapezoid is added, so no grid point is snapped or dropped.

3. TIES: tied scores collapse grid points. The convention is the released scorer's
   (`pooling_audit.eer`, itself a reimplementation of ESDD2-Baseline/libs/eval_metrics.py):
   rates are counted at distinct score values with >= on the accept side, so a tie contributes
   one grid point carrying the whole block. tests/test_acds.py pins it.

Everything is computed from the released per-clip scores. Nothing retrains.
"""
from __future__ import annotations

import numpy as np

from .eer import AXES as _EER_AXES

# The score COLUMN each axis reads, alongside the class memberships eer.AXES already fixes.
# Column order in every released .npz and in baseline_scores.txt is [original, speech, env].
AXES = {a: dict(col=(2 if a == "env" else 1), pa=_EER_AXES[a]["bona"], neg=_EER_AXES[a]["spoof"])
        for a in _EER_AXES}


def curves(neg, pa, p0):
    """The three curves on one shared threshold grid. Returns (t, roc_a, r0, roc_0)."""
    neg = np.sort(np.asarray(neg, dtype=float))
    pa = np.sort(np.asarray(pa, dtype=float))
    p0 = np.sort(np.asarray(p0, dtype=float)) if len(p0) else np.zeros(0)
    tau = np.unique(np.concatenate([neg, pa, p0]))[::-1]          # descending distinct scores
    tau = np.r_[np.inf, tau]                                      # tau = +inf: t = 0
    ge = lambda arr: (arr.size - np.searchsorted(arr, tau, side="left")) / max(arr.size, 1)
    t = ge(neg)
    roc_a = ge(pa)
    roc_0 = ge(p0) if p0.size else np.zeros_like(t)
    # the lowest threshold accepts everything: close the curves at t = 1
    if t[-1] < 1.0:
        t = np.r_[t, 1.0]; roc_a = np.r_[roc_a, 1.0]; roc_0 = np.r_[roc_0, 1.0 if p0.size else 0.0]
    # With no structural zeros there is no alarm to price: R0 = 0, so ACDS(alpha0, .) = AUC_a for
    # every alpha0, which is the w0 = 0 degenerate case. Taking 1 - ROC_0 on an empty
    # population would instead charge the full penalty against nothing.
    r0 = (1.0 - roc_0) if p0.size else np.zeros_like(t)
    return t, roc_a, r0, roc_0


def _integrate(t, y, tmax, rule="trapezoid"):
    """Integral of y over [0, tmax] along t, with y linearly interpolated at tmax."""
    if tmax <= 0:
        raise ValueError("tmax must be positive")
    keep = t <= tmax
    tt, yy = t[keep], y[keep]
    # Drop points repeating the previous (t, y): they are zero-width trapezoids, but they
    # change the ORDER of summation, and a structural-zero score between two applicable
    # scores inserts exactly such a point. Without this, ACDS(0, .) moved by one ULP
    # (1.11e-16) when the fill constant changed: invariant mathematically, not bit-identically,
    # which Proposition 2(iv) requires. With it the grid is the same whatever P_0 contains.
    if tt.size > 1:
        same = np.r_[False, (np.diff(tt) == 0) & (np.diff(yy) == 0)]
        tt, yy = tt[~same], yy[~same]
    if tt.size == 0 or tt[-1] < tmax:                              # add the boundary point
        tt = np.r_[tt, tmax]
        yy = np.r_[yy, np.interp(tmax, t, y)]
    if rule == "trapezoid":
        return float(np.trapezoid(yy, tt)) if hasattr(np, "trapezoid") else float(np.trapz(yy, tt))
    if rule == "step":                                             # right-continuous step
        return float(np.sum(np.diff(tt) * yy[:-1]))
    raise ValueError(rule)


def acds(t, roc_a, r0, alpha0=0.0, tmax=1.0, rule="trapezoid"):
    """ACDS_a(alpha0, tmax) on precomputed curves."""
    return _integrate(t, roc_a - alpha0 * r0, tmax, rule) / tmax


def auc(t, roc, tmax=1.0, rule="trapezoid"):
    return _integrate(t, roc, tmax, rule) / 1.0


def populations(labels, scores, axis, fill=None):
    """(N, P_a, P_0) score vectors for one axis; `fill` replaces every structural-zero score."""
    a = AXES[axis]
    labels = np.asarray(labels)
    s = np.asarray(scores, dtype=float)
    if fill is not None:
        s = np.where(labels == 0, float(fill), s)
    return s[np.isin(labels, a["neg"])], s[np.isin(labels, a["pa"])], s[labels == 0]


def score_all(labels, scores, axis, settings, fill=None, rule="trapezoid"):
    """ACDS for a list of (alpha0, tmax) settings, plus the quantities the gates compare against."""
    neg, pa, p0 = populations(labels, scores, axis, fill)
    t, roc_a, r0, roc_0 = curves(neg, pa, p0)
    w0 = p0.size / (p0.size + pa.size)
    pooled = np.r_[pa, p0]
    tp, roc_pub, _, _ = curves(neg, pooled, np.zeros(0))
    return dict(
        w0=w0, wa=1.0 - w0,
        auc_a=auc(t, roc_a, rule=rule), auc_0=auc(t, roc_0, rule=rule),
        auc_pub=auc(tp, roc_pub, rule=rule),
        cells={(a0, tm): acds(t, roc_a, r0, a0, tm, rule) for a0, tm in settings},
        n=dict(neg=neg.size, pa=pa.size, p0=p0.size))
