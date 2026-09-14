"""Theorem 2 in both directions, and the lower-endpoint witness on a real submission.

The paper says three things about the interval (3) that are checked here rather
than proved here:

  attainment    for every sampled value v in (3), endpoints included, an admissible
                system exists whose pooled crossing is EER_pub and whose component
                crossing is v. `attainment_grid` builds one explicitly, with exact
                discrete score masses, and reports the worst residual in either
                crossing. The paper states this as "to 1e-12".
  containment   no admissible system lands OUTSIDE (3). `containment` draws random
                systems and brackets each crossing between the two step functions,
                so the check does not depend on a tie-breaking convention.
  witness       conditioning also on a submission's OTHER published cells constrains
                the construction further. `lower_endpoint_witness` reassigns only the
                reference system's environmental score -- every other published cell
                is computed from other columns and cannot move -- and reproduces its
                published 0.4336 under the released scorer while the component-only
                value sits at the lower endpoint, 0. No witness is built, or claimed,
                for the upper endpoint.

Both constructions are ports of the authors' proof checks; see README, "Provenance".
"""
from __future__ import annotations

import numpy as np

from .bounds import interval
from .eer import component_eer, inapplicable_share


# ------------------------------------------------------------------ attainment
def build_system(E: float, w0: float, v: float):
    """Discrete score masses realising pooled crossing E and component crossing v.

    Scores are integers; a clip is accepted as bona fide when its score >= t.
    Returns (neg, P_a, P_0, t_component, t_pooled), each P a {score: mass} dict.
    """
    wa = 1.0 - w0
    a = (E - wa * v) / w0                       # mass of P_0 below the pooled threshold
    if v >= E:
        neg = {0: 1 - v, 1: v - E, 2: E}
        return neg, {0: v, 3: 1 - v}, {0: a, 3: 1 - a}, 1, 2
    neg = {0: 1 - E, 2: E - v, 3: v}
    return neg, {1: v, 4: 1 - v}, {1: a, 4: 1 - a}, 3, 2


def _far(d, t):
    return sum(m for s, m in d.items() if s >= t)


def _frr(d, t):
    return sum(m for s, m in d.items() if s < t)


SETTINGS = ((0.4336, 0.532310), (0.4279, 0.528247), (0.1993, 0.399090),
            (0.0869, 0.528247), (0.3000, 0.500000), (0.6000, 0.250000))


def attainment_grid(n_points: int = 25) -> dict:
    """Worst residual over every construction, endpoints of each interval included."""
    worst, n, infeasible = 0.0, 0, 0
    for E, w0 in SETTINGS:
        lo, hi = interval(E, w0)
        for v in np.linspace(lo, hi, n_points):
            v = float(v)
            neg, Pa, P0, tc, tp = build_system(E, w0, v)
            if min(list(P0.values()) + list(neg.values())) < -1e-12:
                infeasible += 1
                continue
            pooled_far, pooled_frr = _far(neg, tp), w0 * _frr(P0, tp) + (1 - w0) * _frr(Pa, tp)
            comp_far, comp_frr = _far(neg, tc), _frr(Pa, tc)
            worst = max(worst, abs(pooled_far - E), abs(pooled_frr - E),
                        abs(comp_far - v), abs(comp_frr - v))
            n += 1
    return dict(n_constructions=n, n_infeasible=infeasible, worst_residual=worst,
                n_settings=len(SETTINGS), points_per_interval=n_points)


# ----------------------------------------------------------------- containment
def containment(trials: int = 5000, seed: int = 11, bins: int = 4096,
                published_scale: float = 1.0) -> dict:
    """Random admissible systems: does any component crossing escape (3)?

    `published_scale` misreports the pooled crossing by that factor before the
    interval is built. It exists so a test can show the check is able to fail;
    the paper's claim is the default, 1.0.
    """
    rng = np.random.default_rng(seed)
    g = np.arange(bins)

    def mass(concentrated: bool) -> np.ndarray:
        m = np.zeros(bins)
        for _ in range(int(rng.integers(1, 4))):      # up to three modes: non-concave ROCs
            c = rng.uniform(0, bins)
            s = rng.uniform(bins / 400, bins / 40) if concentrated else rng.uniform(bins / 60, bins / 6)
            m += rng.uniform(0.2, 1.0) * np.exp(-0.5 * ((g - c) / s) ** 2)
        return m / m.sum()

    def bracket(pos, neg):
        far = np.concatenate(([1.0], 1.0 - np.cumsum(neg)))
        frr = np.concatenate(([0.0], np.cumsum(pos)))
        i = int(np.argmax(frr >= far))
        return float(min(far[i], frr[i])), float(max(far[i], frr[i]))

    worst = 0.0
    for k in range(trials):
        w0 = float(rng.uniform(0.02, 0.98))
        neg, P0, Pa = mass(False), mass(k % 4 == 0), mass(False)
        e_lo, e_hi = (published_scale * x for x in bracket(w0 * P0 + (1 - w0) * Pa, neg))
        v_lo, v_hi = bracket(Pa, neg)
        lo, hi = max(0.0, (e_lo - w0) / (1 - w0)), min(1.0, e_hi / (1 - w0))
        worst = max(worst, lo - v_hi, v_lo - hi, 0.0)
    return dict(trials=trials, seed=seed, worst_violation=worst)


# ------------------------------------------------------------------- witness
def lower_endpoint_witness(labels: np.ndarray, published: float) -> dict:
    """Reassign the environmental score only, and hold the published cell.

    Negatives are spread uniformly on [0, 1) and every applicable bona fide clip is
    placed above all of them, so the component-only EER is 0, the lower endpoint.
    The inapplicable clips are spread uniformly on [0, u): the pooled false-rejection
    rate is then w0 * t / u, which crosses FAR(t) = 1 - t at EER = w0 / (u + w0).
    u is the single free parameter, solved from the published cell and then nudged
    so the released scorer's value prints as `published` at four decimals.
    """
    neg = np.isin(labels, [3, 4])
    bona = np.isin(labels, [1, 2])
    inap = labels == 0
    w0 = inapplicable_share(labels, "env")
    s = np.zeros(len(labels))
    s[neg] = (np.arange(int(neg.sum())) + 0.5) / neg.sum()
    s[bona] = 1.1 + np.arange(int(bona.sum())) / bona.sum()
    n0 = int(inap.sum())
    target = round(published, 4)

    def pooled(u: float):
        e = s.copy()
        e[inap] = (np.arange(n0) + 0.5) / n0 * u
        return component_eer(labels, e, "env", include_inapplicable=True), e

    u0 = w0 * (1 - target) / target
    for du in sorted(np.linspace(-0.01, 0.01, 2001), key=abs):
        val, e = pooled(u0 + du)
        if round(val, 4) == target:
            comp = component_eer(labels, e, "env")
            lo, hi = interval(target, w0)
            return dict(found=True, u=float(u0 + du), pooled=val, component_only=comp,
                        interval_lo=lo, interval_hi=hi, at_lower=bool(abs(comp - lo) < 1e-12),
                        upper_claimed=False)
    return dict(found=False, upper_claimed=False)
