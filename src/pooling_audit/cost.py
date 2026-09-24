"""Section 4.2's cost-metric sentence: minDCF at ASVspoof 5's cost parameters.

ASVspoof 5 (Wang et al., 2024, Sec. 3.1, eqs. 1-2) ranks Track 1 on
    minDCF = min_t [ beta * P_miss(t) + P_fa(t) ],   beta = (C_miss / C_fa) * (1 - pi_spf) / pi_spf,
with C_miss = 1, C_fa = 10, pi_spf = 0.05, so beta = 1.9. P_miss is the false rejection rate of
bona fide trials and P_fa the false acceptance rate of spoofed trials.

Here it is applied to the environmental component's decision of the reference submission, as
submitted: pooled (class 0 on the bona fide side, per the protocol) against component-only
(class 0 dropped). The residual is the pooled value minus w0 T(R_0) + w_a T(R_a), the quantity
Theorem 1 says vanishes exactly for a weighted area and not for a minimum over thresholds.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

from . import data
from .eer import AXES, inapplicable_share

C_MISS, C_FA, PI_SPF = 1.0, 10.0, 0.05
BETA = (C_MISS / C_FA) * (1 - PI_SPF) / PI_SPF


def _summaries(bona: np.ndarray, spoof: np.ndarray) -> dict:
    scores = np.r_[bona, spoof]
    lab = np.r_[np.ones(bona.size, int), np.zeros(spoof.size, int)]
    fpr, tpr, _ = roc_curve(lab, scores, pos_label=1)
    return dict(minDCF=float(np.min(BETA * (1 - tpr) + fpr)), AUC=float(roc_auc_score(lab, scores)))


def asvspoof5_mindcf() -> dict:
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    s = data.load_baseline(idx).s_env.to_numpy(float)
    spec = AXES["env"]
    spoof = s[np.isin(labels, spec["spoof"])]
    app, zero = s[np.isin(labels, spec["bona"])], s[labels == 0]
    w0 = inapplicable_share(labels, "env")
    pooled, comp, r0 = _summaries(np.r_[zero, app], spoof), _summaries(app, spoof), _summaries(zero, spoof)
    resid = {k: pooled[k] - (w0 * r0[k] + (1 - w0) * comp[k]) for k in pooled}
    return dict(beta=BETA, pooled_minDCF=pooled["minDCF"], component_minDCF=comp["minDCF"],
                residual_minDCF=resid["minDCF"], residual_auc=resid["AUC"],
                residual_auc_abs_e15=abs(resid["AUC"]) * 1e15)
