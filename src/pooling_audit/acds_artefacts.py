"""The ACDS artefacts: Table 1's cells, Section 4.4's crossings, Section 4.5's gate.

`recompute.all_artefacts` imports these, so `verify.py`, `scripts/acds_table.py`,
`scripts/acds_gate.py` and the three figure scripts all read one implementation and cannot
drift from one another. Kept out of `recompute.py` because that file is already long and the
house rule is no file over ~300 lines.

Everything here is a re-scoring of the released per-clip scores on the evaluation split. No
model is retrained and no threshold is fitted.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np

from . import acds, data

SYSTEMS = [("beats_linear", "BEATs probe"), ("eat_linear", "EAT probe"),
           ("beats_attentive", "attentive head"), ("two_encoder", "two-encoder")]
SETTINGS = ["(0,1)", "(1,1)", "(0,0.2)", "(w0/wa,1)"]
GATE_THRESHOLD = 0.5          # gate an axis at gamma_a >= 1/2


def _score_matrix(idx):
    """Per-system (seeds, n, 3) score blocks, the reference baseline last with one seed."""
    out = []
    for name, _label in SYSTEMS:
        out.append((name, data.load_system(name, idx)["scores"].astype(float)))
    base = data.load_baseline(idx)
    out.append(("reference", base[["s_original", "s_speech", "s_env"]].to_numpy(float)[None]))
    return out


def _cells(labels, s, axis):
    neg, pa, p0 = acds.populations(labels, s, axis)
    t, roc_a, r0, roc_0 = acds.curves(neg, pa, p0)
    w0 = p0.size / (p0.size + pa.size)
    wa = 1.0 - w0
    pooled = np.r_[pa, p0]
    tp, roc_pub, _, _ = acds.curves(neg, pooled, np.zeros(0))
    v = {"(0,1)": acds.acds(t, roc_a, r0, 0.0, 1.0),
         "(1,1)": acds.acds(t, roc_a, r0, 1.0, 1.0),
         "(0,0.2)": acds.acds(t, roc_a, r0, 0.0, 0.2),
         "(w0/wa,1)": acds.acds(t, roc_a, r0, w0 / wa, 1.0)}
    step = {"(0,1)": acds.acds(t, roc_a, r0, 0.0, 1.0, rule="step")}
    return dict(cells=v, auc_a=acds.auc(t, roc_a), auc_0=acds.auc(t, roc_0),
                auc_pub=acds.auc(tp, roc_pub), w0=w0, wa=wa,
                step_gap=abs(step["(0,1)"] - v["(0,1)"]))


def acds_table(axis: str = "env") -> dict:
    """Table 1: four settings x five systems, three-seed means, plus the two exact identities.

    Proposition 2(i) and (ii) are checked here rather than asserted in prose: the (0,1) column
    must equal AUC_a and w_a times the (w0/wa,1) column must equal AUC_pub - w0. The paper says
    both hold to 1e-15 and that is what `worst_identity_residual` reports.
    """
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    rows, aucs, resid, steps = {}, {}, [], []
    for name, block in _score_matrix(idx):
        per = [_cells(labels, block[k, :, acds.AXES[axis]["col"]], axis)
               for k in range(block.shape[0])]
        rows[name] = {s: float(np.mean([p["cells"][s] for p in per])) for s in SETTINGS}
        rows[name]["n_seeds"] = block.shape[0]
        aucs[name] = dict(auc_a=float(np.mean([p["auc_a"] for p in per])),
                          auc_0=float(np.mean([p["auc_0"] for p in per])),
                          auc_pub=float(np.mean([p["auc_pub"] for p in per])),
                          w0=float(np.mean([p["w0"] for p in per])))
        aucs[name]["alarm_area"] = 1.0 - aucs[name]["auc_0"]   # integral of R_0, Prop 9(ii)
        steps += [p["step_gap"] for p in per]
        for p in per:
            resid.append(abs(p["cells"]["(0,1)"] - p["auc_a"]))
            resid.append(abs(p["wa"] * p["cells"]["(w0/wa,1)"] - (p["auc_pub"] - p["w0"])))

    w0 = aucs["reference"]["w0"]
    out = dict(rows=rows, aucs=aucs, w0=w0, wa=1.0 - w0, w0_over_wa=w0 / (1.0 - w0),
               worst_identity_residual=float(max(resid)),
               worst_step_gap=float(max(steps)),
               worst_step_gap_e4=float(max(steps)) * 1e4,
               # the two the paper prints as bounds or as a header rather than as a measurement
               identity_residual_e15=float(max(resid)) * 1e15,
               tmax_short=0.2,
               span_acds01=float(max(r["(0,1)"] for r in rows.values())
                                 - min(r["(0,1)"] for r in rows.values())),
               span_alarm=float(max(1 - a["auc_0"] for a in aucs.values())
                                - min(1 - a["auc_0"] for a in aucs.values())))
    # At t_max = 1 the score is AUC_a - alpha_0 (1 - AUC_0), affine in alpha_0, so every
    # pairwise crossing is exact rather than searched for.
    cross = []
    for a, b in combinations(aucs, 2):
        da, db = 1 - aucs[a]["auc_0"], 1 - aucs[b]["auc_0"]
        if abs(da - db) < 1e-15:
            continue
        x = (aucs[a]["auc_a"] - aucs[b]["auc_a"]) / (da - db)
        if 0 <= x <= 2:
            cross.append(dict(pair=[a, b], alpha0=float(x)))
    cross.sort(key=lambda c: c["alpha0"])
    out["crossings"] = cross
    out["last_crossing"] = float(cross[-1]["alpha0"]) if cross else 0.0
    out["n_crossings"] = len(cross)
    out["ranks"] = {s: sorted(rows, key=lambda n: -rows[n][s]) for s in SETTINGS}
    return out


def acds_gate() -> dict:
    """Section 4.5: what a gate read off the submission alone costs, on both axes.

    gamma_a = 1 - sigma(score_original), the probability the axis applies. lambda is the share
    of the gated positive set that is a structural zero; rho is the share of the applicable
    positives the gate drops, which is what makes Proposition 3's hypothesis fail here.
    """
    from .eer import component_eer
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    base = data.load_baseline(idx)
    ref = base[["s_original", "s_speech", "s_env"]].to_numpy(float)
    gamma = 1.0 - 1.0 / (1.0 + np.exp(-ref[:, 0]))
    keep = gamma >= GATE_THRESHOLD
    out = {}
    for axis in ("env", "speech"):
        a = acds.AXES[axis]
        s = ref[:, a["col"]]
        pa = np.isin(labels, a["pa"])
        p0 = labels == 0
        kept_pa, kept_p0 = keep & pa, keep & p0
        lam = kept_p0.sum() / max(kept_pa.sum() + kept_p0.sum(), 1)
        rho = 1.0 - kept_pa.sum() / max(pa.sum(), 1)
        # annotated partition
        n_a, p_a, z_a = acds.populations(labels, s, axis)
        t, roc_a, r0, roc_0 = acds.curves(n_a, p_a, z_a)
        ann = acds.acds(t, roc_a, r0, 0.0, 1.0)
        auc0 = acds.auc(t, roc_0)
        # Predicted partition: the gate's positive set, structural zeros and all. The NEGATIVE
        # set is NOT gated -- the axis is the false-acceptance rate on N, which is what fixes
        # the operating point, and a gate that moved it would be answering a different
        # question. Only the positive side is the gate's to predict.
        tg, rg, r0g, _ = acds.curves(s[np.isin(labels, a["neg"])],
                                     s[kept_pa | kept_p0], np.zeros(0))
        gated = acds.acds(tg, rg, r0g, 0.0, 1.0)
        corrected = (gated - lam * auc0) / (1.0 - lam)
        out[axis] = dict(
            lam=float(lam), rho=float(rho), auc_0=float(auc0),
            acds_annotated=float(ann), acds_gated=float(gated),
            abs_error_gated=float(abs(gated - ann)),
            leak_corrected=float(corrected),
            abs_error_corrected=float(abs(corrected - ann)),
            eer_gated=float(component_eer(labels[keep], s[keep], axis,
                                          include_inapplicable=True)),
            eer_annotated=float(component_eer(labels, s, axis)),
            eer_pooled=float(component_eer(labels, s, axis, include_inapplicable=True)))
        out[axis]["err_gated_eer"] = abs(out[axis]["eer_gated"] - out[axis]["eer_annotated"])
        out[axis]["err_pooled_eer"] = abs(out[axis]["eer_pooled"] - out[axis]["eer_annotated"])
        # err_gated_eer against err_pooled_eer, NOT recompute.table2()'s bootstrap-point-estimate
        # reduction_pct (a different, older computation over a different pair of quantities that
        # gives 78% for speech rather than 85%; the two must not be conflated). Neither reduction
        # percentage is printed in the submitted paper; this field is kept as a checked, internally
        # consistent quantity, not because either digit is currently a paper claim.
        out[axis]["reduction_pct_eer"] = 100 * (1 - out[axis]["err_gated_eer"]
                                                 / out[axis]["err_pooled_eer"])
    out["gate_threshold"] = GATE_THRESHOLD
    return out
