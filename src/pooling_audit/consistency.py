"""The supplementary train/score consistency experiment, recomputed from saved scores.

Not reported in the paper; it backs the remark in Section 4.3 that the baseline masks
Class 0 in both component losses.

Two arms, identical but for the loss mask:

    M   the inapplicable clips are masked out of both component losses, as the
        released baseline's trainer does. Nothing supervises the heads there, so
        the value they emit is unspecified and the fill constant is free.
    C   both heads are supervised on the inapplicable clips, consistent with the
        mapping the scorer mandates.

Retraining is tier 1. The per-clip scores of all twelve runs (2 feature
configurations x 2 arms x 3 seeds) ship in scores/consistency/, so its four
numbers are recomputable on CPU.

Score convention, carried over from the training script: columns are
[speech, env], each a sigmoid output in [0, 1] and bona-fide-oriented.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score

from . import data
from .eer import AXES, eer_from_scores

CONFIGS = ("layer7", "layers7to10")
ARMS = ("M", "C")
SEEDS = (1337, 1338, 1339)
COL = {"speech": 0, "env": 1}


def _run(labels: np.ndarray, s: np.ndarray, axis: str) -> dict:
    spec = AXES[axis]
    spoof = np.isin(labels, spec["spoof"])
    bona = np.isin(labels, spec["bona"])
    inap = labels == 0
    w0 = inap.sum() / (inap.sum() + bona.sum())
    wa = 1.0 - w0

    pooled = eer_from_scores(s[inap | bona | spoof],
                             np.isin(labels[inap | bona | spoof], spec["spoof"]))
    comp = eer_from_scores(s[bona | spoof], np.isin(labels[bona | spoof], spec["spoof"]))

    # How well the environmental score alone separates the inapplicable class from
    # the applicable bona fide clips. Higher score = more "original" here, so the
    # raw score is used, not its negation.
    auc = roc_auc_score(np.r_[np.ones(inap.sum()), np.zeros(bona.sum())],
                        np.r_[s[inap], s[bona]])

    # The label-free fixed point (§2.3, "Post-hoc correction"), FAR = wa * FRR_a, on this arm's own curves.
    grid = np.unique(-s)
    far = np.array([(-s[spoof] < t).mean() for t in grid])
    frr = np.array([(-s[bona] >= t).mean() for t in grid])
    floor = float(far[int(np.nanargmin(np.abs(far - wa * frr)))])

    return dict(eer_pooled=pooled, eer_component=comp, auc_inapplicable=float(auc),
                prop3_floor=floor, distance_to_floor=abs(pooled - floor))


def consistency() -> dict:
    """Aggregate both arms over every configuration and seed."""
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    root = data.repo_scores_dir() / "consistency"

    runs = {arm: [] for arm in ARMS}
    for cfg in CONFIGS:
        for arm in ARMS:
            for sd in SEEDS:
                p = root / f"{cfg}_{arm}_{sd}.npz"
                if not p.exists():
                    raise SystemExit(f"missing consistency scores: {p}")
                z = np.load(p)
                order = data.align(z["filename"], idx)
                s = z["scores"][order, COL["env"]].astype(float)
                r = _run(labels, s, "env")
                r.update(config=cfg, arm=arm, seed=sd)
                runs[arm].append(r)

    agg = {arm: {k: float(np.mean([r[k] for r in runs[arm]]))
                 for k in ("eer_pooled", "eer_component", "auc_inapplicable")}
           for arm in ARMS}
    return dict(
        runs=runs,
        pooled_drop=agg["M"]["eer_pooled"] - agg["C"]["eer_pooled"],
        component_change=agg["C"]["eer_component"] - agg["M"]["eer_component"],
        auc_masked=agg["M"]["auc_inapplicable"],
        auc_consistent=agg["C"]["auc_inapplicable"],
        max_distance_to_floor=max(r["distance_to_floor"] for r in runs["C"]),
        n_runs=sum(len(v) for v in runs.values()),
        **{f"agg_{a}": agg[a] for a in ARMS})
