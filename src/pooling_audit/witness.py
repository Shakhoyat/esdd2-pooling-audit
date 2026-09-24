"""Proposition 2's witnesses: exact rational ROC curves, and the released scorer on them.

Lemma 1 says a summary T with an aggregation rule phi must give equal pooled values whenever
two components have equal T. A witness breaks that: curves A != B with T(A) = T(B), pooled
with the same S at w = 1/2, and T(A|S) != T(B|S). Three triples are checked here:

  eer      A (2/5,3/5); B (3/11,1/2),(2/5,3/5); S (2/7,1).   EER 2/5 -> 2/7 vs 3/11.
  dcf_j    A (1/3,2/3); B (1/6,1/2),(1/3,2/3); S (1/5,4/5).  minDCF at equal priors and unit
           costs 1/3 -> 7/24 vs 4/15; Youden J 1/3 -> 5/12 vs 7/15.
  asvspoof5 A (1/2,6/7); B (1/8,5/8),(1/2,6/7); S (1/8,3/4). minDCF at ASVspoof 5's costs,
           beta P_miss + P_fa with beta = (C_miss/C_fa)(1-pi_spf)/pi_spf = 1.9:
           27/35 -> 27/35 vs 23/32.

The fractions are exact (Fraction arithmetic). The released scorer is checked separately:
`materialise` builds score arrays with one shared negative set whose empirical ROC is each curve
exactly, either with one tied score per linear segment (sparse: sklearn's drop_intermediate
leaves only breakpoints) or with vertices kept everywhere (dense). Every printed crossing and
optimum sits on a genuine vertex, so the scorer reproduces the fractions in both.
"""
from __future__ import annotations

from fractions import Fraction as F

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

from .eer import eer_from_scores

HALF = F(1, 2)
BETA_ASVSPOOF5 = F(1, 10) * F(95, 5)          # (C_miss / C_fa) * (1 - pi_spf) / pi_spf = 19/10


class ROC:
    """Piecewise-linear ROC: TPR as a function of FAR through (0,0), the breakpoints, (1,1)."""

    def __init__(self, pts, name=""):
        self.name = name
        self.p = [(F(0), F(0))] + [(F(a), F(b)) for a, b in pts] + [(F(1), F(1))]
        xs = [x for x, _ in self.p]
        assert all(b > a for a, b in zip(xs, xs[1:])), "breakpoints must increase"
        assert all(F(0) <= y <= F(1) for _, y in self.p)

    @property
    def slopes(self):
        return [(y2 - y1) / (x2 - x1) for (x1, y1), (x2, y2) in zip(self.p, self.p[1:])]

    def is_valid(self):
        s = self.slopes
        return all(v >= 0 for v in s) and all(b <= a for a, b in zip(s, s[1:]))

    def tpr(self, t):
        t = F(t)
        for (x1, y1), (x2, y2) in zip(self.p, self.p[1:]):
            if x1 <= t <= x2:
                return y1 + (y2 - y1) * (t - x1) / (x2 - x1)
        raise ValueError(t)

    def eer(self):
        for (x1, y1), (x2, y2) in zip(self.p, self.p[1:]):
            m = (y2 - y1) / (x2 - x1)
            t = (1 - y1 + m * x1) / (m + 1)
            if x1 <= t <= x2:
                return t
        raise ValueError("no crossing")

    def auc(self):
        return sum((y1 + y2) * (x2 - x1) / 2 for (x1, y1), (x2, y2) in zip(self.p, self.p[1:]))

    def youden(self):
        return max(y - x for x, y in self.p)

    def mindcf(self, a_miss=HALF, a_fa=HALF):
        """min over the curve of a_miss * P_miss + a_fa * P_fa (attained at a breakpoint)."""
        return min(a_miss * (1 - y) + a_fa * x for x, y in self.p)


def mix(c1: ROC, c2: ROC, w) -> ROC:
    w = F(w)
    xs = sorted({x for x, _ in c1.p} | {x for x, _ in c2.p})
    return ROC([(x, w * c1.tpr(x) + (1 - w) * c2.tpr(x)) for x in xs][1:-1], f"{c1.name}|{c2.name}")


WITNESSES = {
    "eer": dict(
        curves=(ROC([(F(2, 5), F(3, 5))], "A"), ROC([(F(3, 11), F(1, 2)), (F(2, 5), F(3, 5))], "B"),
                ROC([(F(2, 7), F(1))], "S")),
        grid=(42, 48510),
        component={"A": {"EER": F(2, 5), "AUC": F(3, 5)}, "B": {"EER": F(2, 5), "AUC": F(34, 55)}},
        pooled={"A|S": {"EER": F(2, 7)}, "B|S": {"EER": F(3, 11)}}),
    "dcf_j": dict(
        curves=(ROC([(F(1, 3), F(2, 3))], "A"), ROC([(F(1, 6), F(1, 2)), (F(1, 3), F(2, 3))], "B"),
                ROC([(F(1, 5), F(4, 5))], "S")),
        grid=(4, 360),
        component={"A": {"minDCF": F(1, 3), "J": F(1, 3)}, "B": {"minDCF": F(1, 3), "J": F(1, 3)}},
        pooled={"A|S": {"minDCF": F(7, 24), "J": F(5, 12)}, "B|S": {"minDCF": F(4, 15), "J": F(7, 15)}}),
    "asvspoof5": dict(
        curves=(ROC([(F(1, 2), F(6, 7))], "A"), ROC([(F(1, 8), F(5, 8)), (F(1, 2), F(6, 7))], "B"),
                ROC([(F(1, 8), F(3, 4))], "S")),
        grid=(21, 504),
        component={"A": {"minDCF_asvspoof5": F(27, 35)}, "B": {"minDCF_asvspoof5": F(27, 35)}},
        pooled={"A|S": {"minDCF_asvspoof5": F(27, 35)}, "B|S": {"minDCF_asvspoof5": F(23, 32)}}),
}


def exact(name: str) -> dict:
    """Every claimed value of one witness, in exact arithmetic."""
    a, b, s = WITNESSES[name]["curves"]
    curves = {"A": a, "B": b, "S": s, "A|S": mix(a, s, HALF), "B|S": mix(b, s, HALF)}
    f = {"EER": lambda c: c.eer(), "AUC": lambda c: c.auc(), "J": lambda c: c.youden(),
         "minDCF": lambda c: c.mindcf(), "minDCF_asvspoof5": lambda c: c.mindcf(BETA_ASVSPOOF5, F(1))}
    out = {}
    for side in ("component", "pooled"):
        for tag, claims in WITNESSES[name][side].items():
            for metric in claims:
                out[(tag, metric)] = f[metric](curves[tag])
    return out


def materialise(curves, grid, k: int, dense: bool):
    """Shared negatives, one positive array per curve; period * k negatives, as many positives."""
    q, period = grid
    m = period * k
    sizes = ([q, 2 * q] * (m // (3 * q))) if dense else [q] * (m // q)
    assert sum(sizes) == m
    neg, pos = [], {c.name: [] for c in curves}
    far = F(0)
    for b, size in enumerate(sizes):
        s = -float(b)
        neg.append(np.full(size, s))
        nxt = far + F(size, m)
        for c in curves:
            n_pos = (c.tpr(nxt) - c.tpr(far)) * m
            assert n_pos.denominator == 1, (c.name, far, n_pos)
            pos[c.name].append(np.full(int(n_pos), s))
        far = nxt
    return np.concatenate(neg), {n: np.concatenate(v) for n, v in pos.items()}


def released(pos: np.ndarray, neg: np.ndarray) -> dict:
    """Every summary under both released-scorer orientations.

    baseline: bona fide positive, as ESDD2-Baseline's eval_metrics.py (mean of FPR and FNR at
              argmin |FPR - FNR| over roc_curve's vertices);
    audit:    spoof positive with negated scores, as eer.eer_from_scores.
    """
    scores = np.r_[pos, neg]
    bona = np.r_[np.ones(pos.size, int), np.zeros(neg.size, int)]
    fpr, tpr, _ = roc_curve(bona, scores, pos_label=1)
    fnr = 1 - tpr
    i = int(np.nanargmin(np.abs(fpr - fnr)))
    beta = float(BETA_ASVSPOOF5)
    baseline = dict(EER=float((fpr[i] + fnr[i]) / 2), AUC=float(roc_auc_score(bona, scores)),
                    J=float(np.max(tpr - fpr)), minDCF=float(np.min(0.5 * fnr + 0.5 * fpr)),
                    minDCF_asvspoof5=float(np.min(beta * fnr + fpr)))
    fp2, tp2, _ = roc_curve(1 - bona, -scores, pos_label=1)       # fp2 = P_miss, 1 - tp2 = P_fa
    audit = dict(EER=eer_from_scores(scores, 1 - bona), AUC=float(roc_auc_score(1 - bona, -scores)),
                 J=float(np.max(tp2 - fp2)), minDCF=float(np.min(0.5 * fp2 + 0.5 * (1 - tp2))),
                 minDCF_asvspoof5=float(np.min(beta * fp2 + (1 - tp2))))
    return dict(baseline=baseline, audit=audit, n_vertices=int(fpr.size))


def check(name: str, k: int, dense: bool) -> dict:
    """Released-scorer value of every claimed cell, both orientations, with its gap."""
    w = WITNESSES[name]
    neg, pos = materialise(w["curves"], w["grid"], k, dense)
    sets = {"A": pos["A"], "B": pos["B"], "A|S": np.r_[pos["A"], pos["S"]], "B|S": np.r_[pos["B"], pos["S"]]}
    got = {t: released(p, neg) for t, p in sets.items()}
    cells = []
    for (tag, metric), want in exact(name).items():
        for impl in ("baseline", "audit"):
            v = got[tag][impl][metric]
            cells.append(dict(curve=tag, metric=metric, implementation=impl, claimed=str(want),
                              released=v, gap=abs(v - float(want))))
    return dict(witness=name, k=k, dense=dense, n_negatives=int(neg.size),
                pooled_vertices={t: got[t]["n_vertices"] for t in ("A|S", "B|S")},
                cells=cells, worst_gap=max(c["gap"] for c in cells))


def artefacts() -> dict:
    """Every printed fraction of the witnesses, exact, as strings: the paper's §2 literals."""
    out = {}
    for name, w in WITNESSES.items():
        a, b, s = w["curves"]
        curves = {"A": a, "B": b, "S": s, "A|S": mix(a, s, HALF), "B|S": mix(b, s, HALF)}
        out[name] = {
            "breakpoints": {n: [[str(x), str(y)] for x, y in c.p[1:-1]] for n, c in (("A", a), ("B", b), ("S", s))},
            "values": {n: dict(EER=str(c.eer()), AUC=str(c.auc()), J=str(c.youden()), minDCF=str(c.mindcf()),
                               minDCF_asvspoof5=str(c.mindcf(BETA_ASVSPOOF5, F(1))))
                       for n, c in curves.items()},
            "concave": all(c.is_valid() for c in curves.values()),
        }
    return out
