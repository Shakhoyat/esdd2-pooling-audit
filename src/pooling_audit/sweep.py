"""Sweeping the fill constant, and the gates a participant could build.

The reported EER is a STEP function of the constant: the inapplicable clips all
share one score, so the value only moves as c crosses a score held by some other
clip. Sweeping therefore means evaluating at every distinct applicable score,
not on a uniform grid.
"""
from __future__ import annotations

import numpy as np

from .eer import AXES, component_eer


def sweep_constant(labels: np.ndarray, scores: np.ndarray, axis: str,
                   extra: int = 2001) -> dict:
    inap = labels == 0
    grid = np.unique(np.concatenate([
        np.linspace(scores.min() - 0.1, scores.max() + 0.1, extra),
        np.sort(scores[~inap]),
    ]))
    vals = np.array([component_eer(labels, np.where(inap, c, scores), axis,
                                   include_inapplicable=True) for c in grid])
    target = component_eer(labels, scores, axis, include_inapplicable=False)
    best = int(np.nanargmin(np.abs(vals - target)))
    steps = [(float(grid[i]), float(vals[i - 1]), float(vals[i]))
             for i in range(1, len(grid)) if abs(vals[i] - vals[i - 1]) > 1e-4]
    big = max(steps, key=lambda s: abs(s[2] - s[1])) if steps else (float("nan"),) * 3
    return dict(target=float(target), lo=float(np.nanmin(vals)), hi=float(np.nanmax(vals)),
                closest_value=float(vals[best]), closest_at_c=float(grid[best]),
                closest_gap=float(abs(vals[best] - target)),
                step_at_c=big[0], step_from=big[1], step_to=big[2], n_steps=len(steps))


def prop3_floor(labels: np.ndarray, scores: np.ndarray, axis: str) -> float:
    """The label-free fixed point (§2.3, "Post-hoc correction"): FAR = wa * FRR_a, not FAR = FRR_a."""
    spec = AXES[axis]
    spoof = np.isin(labels, spec["spoof"])
    bona = np.isin(labels, spec["bona"])
    inap = labels == 0
    wa = 1.0 - inap.sum() / (inap.sum() + bona.sum())
    grid = np.unique(scores)
    far = np.array([(scores[spoof] >= t).mean() for t in grid])
    frr = np.array([(scores[bona] < t).mean() for t in grid])
    i = int(np.argmin(np.abs(far - wa * frr)))
    return float((far[i] + wa * frr[i]) / 2.0)


def applicability_gate(score_original: np.ndarray) -> np.ndarray:
    """gamma = 1 - sigmoid(score_original): the posterior the format already carries."""
    return 1.0 / (1.0 + np.exp(np.asarray(score_original, dtype=float)))
