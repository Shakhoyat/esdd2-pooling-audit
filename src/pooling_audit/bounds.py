"""Theorem 2's interval (3), the ordering criterion, and the pairwise test.

    (3)  [ max(0, (EER_pub - w0)/wa),  min(1, EER_pub/wa) ]

Two published systems are separated by the table only if their intervals are
disjoint, which happens exactly when their published EERs differ by more than w0.
"""
from __future__ import annotations

import itertools


def interval(eer_pub: float, w0: float) -> tuple[float, float]:
    wa = 1.0 - w0
    return (max(0.0, (eer_pub - w0) / wa), min(1.0, eer_pub / wa))


def disjoint(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return a[1] < b[0] or b[1] < a[0]


def pairwise_determined(published: list[float], w0: float) -> dict:
    """How many of the C(n,2) comparisons the published table settles.

    Reports both the geometric test (disjoint intervals) and the closed-form
    criterion (|e_i - e_j| > w0), which must agree on every pair.
    """
    iv = [interval(e, w0) for e in published]
    pairs = list(itertools.combinations(range(len(published)), 2))
    geo = sum(1 for i, j in pairs if disjoint(iv[i], iv[j]))
    crit = sum(1 for i, j in pairs if abs(published[i] - published[j]) > w0)
    mism = sum(1 for i, j in pairs
               if disjoint(iv[i], iv[j]) != (abs(published[i] - published[j]) > w0))
    gaps = [abs(published[i] - published[j]) for i, j in pairs]
    return dict(n_systems=len(published), n_pairs=len(pairs), pair_size=2,
                determined_geometric=geo,
                determined_criterion=crit, mismatches=mism, max_gap=max(gaps), w0=w0,
                intervals=iv)
