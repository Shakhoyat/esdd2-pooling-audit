"""The three regimes, and what the released scorer returns inside the capture one.

Every inapplicable clip receives the same constant c, so FRR_pub jumps by w0 at
c. Relative to that jump the false-acceptance rate at c can sit above it (the
atom is rejected), below it (accepted), or inside it (the atom captures the
operating point). In the capture regime the scorer, which averages FAR and FRR
at the nearest ROC vertex, returns the mean of FAR(c) and the NEARER end of the
jump.
"""
from __future__ import annotations

import numpy as np

from .eer import AXES, component_eer


def classify(labels: np.ndarray, scores: np.ndarray, axis: str, c: float) -> dict:
    spec = AXES[axis]
    spoof = np.isin(labels, spec["spoof"])
    bona = np.isin(labels, spec["bona"])
    inap = labels == 0
    w0 = inap.sum() / (inap.sum() + bona.sum())
    wa = 1.0 - w0

    far = float((scores[spoof] >= c).mean())
    frr_a = float((scores[bona] < c).mean())
    lo, hi = wa * frr_a, w0 + wa * frr_a
    if lo - 1e-12 <= far <= hi + 1e-12:
        regime = "captured"
    elif far < lo:
        regime = "accepted"
    else:
        regime = "rejected"

    nearer = lo if abs(far - lo) <= abs(far - hi) else hi
    predicted = (far + nearer) / 2.0
    reported = component_eer(labels, np.where(inap, c, scores), axis,
                             include_inapplicable=True)
    return dict(regime=regime, far=far, jump_lo=lo, jump_hi=hi, w0=float(w0),
                predicted_in_capture=float(predicted), reported=float(reported),
                deviation=abs(reported - predicted))
