"""Exhaustive exact-arithmetic check of the AC-EER properties on small score sets with ties.
Convention: accept (bona fide) iff s >= tau. FAR over negatives N, FRR over positives."""
from fractions import Fraction as Fr
from itertools import product
import sys
nN, nA, n0 = map(int, sys.argv[1:4]); G = int(sys.argv[4])
grid = range(G)
def rates(neg, pos, t):
    F = Fr(sum(s >= t for s in neg), len(neg)); R = Fr(sum(s < t for s in pos), len(pos)); return F, R
def thresholds(*sets):
    u = sorted(set(x for S in sets for x in S)); return u + [u[-1] + 1]
def eer_mm(neg, pos):
    ts = thresholds(neg, pos); vals = [(max(*rates(neg, pos, t)), t) for t in ts]
    m = min(v for v, _ in vals); return m, [t for v, t in vals if v == m]
def eer_mid(neg, pos):
    ts = thresholds(neg, pos); g = [(abs(F - R), (F + R) / 2, t) for t in ts for F, R in [rates(neg, pos, t)]]
    m = min(x[0] for x in g); return [(x[1], x[2], x[0]) for x in g if x[0] == m]
def auc(neg, pos):
    return Fr(sum((p > n) + Fr(1, 2) * (p == n) for p in pos for n in neg), len(pos) * len(neg))
viol = dict(lemma=0, bound_mm=0, naive_mm=0, bound_mid=0, naive_mid=0, auc=0); worst = {}
for neg in product(grid, repeat=nN):
  for pa in product(grid, repeat=nA):
    ea, _ = eer_mm(neg, pa)
    for t in thresholds(neg, pa):                      # sandwich lemma at every tau
        F, R = rates(neg, pa, t)
        if not (min(F, R) <= ea <= max(F, R)): viol['lemma'] += 1
    mids_a = eer_mid(neg, pa)
    for p0 in product(grid, repeat=n0):
        P = pa + p0; w0 = Fr(n0, n0 + nA)
        ep, taus = eer_mm(neg, P)
        for t in taus:
            F, Rp = rates(neg, P, t); _, Ra = rates(neg, pa, t); _, R0 = rates(neg, p0, t)
            d0 = w0 * (R0 - Ra)
            assert Rp == Ra + d0
            if abs(ep - ea) > abs(d0) + abs(F - Rp): viol['bound_mm'] += 1
            if abs(ep - ea) > abs(d0):
                viol['naive_mm'] += 1; worst.setdefault('naive_mm', (neg, pa, p0, ep, ea, d0))
        for (vp, t, gp) in eer_mid(neg, P):
            _, Ra = rates(neg, pa, t); _, R0 = rates(neg, p0, t); d0 = w0 * (R0 - Ra)
            for (va, ta, ga) in mids_a:
                if abs(vp - va) > abs(d0) + (gp + ga) / 2: viol['bound_mid'] += 1
                if abs(vp - va) > abs(d0): viol['naive_mid'] += 1
        if auc(neg, P) != w0 * auc(neg, p0) + (1 - w0) * auc(neg, pa): viol['auc'] += 1
print({k: v for k, v in viol.items()})
print('naive counterexample (neg, P_a, P_0, EER_pub, EER_a, Delta0):', worst.get('naive_mm'))

# EXPECTED (reference run, sizes 3 3 2, grid 4): lemma 0, bound_mm 0, bound_mid 0, auc 0,
# naive_mm 147, naive_mid 8424. Any nonzero lemma/bound/auc count is a FAILURE.
