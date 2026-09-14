"""One function per paper artefact. Every value is recomputed from per-clip data.

`verify.py` and everything in `scripts/` call these, so there is exactly one
implementation of each number and no way for a script and the verifier to drift.

Tier 0 (CPU, no training) covers everything except the consistency experiment of
Section 4.3, which requires retraining two heads and is tier 1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import bounds, data, pooling, regimes, sharpness, sweep
from .consistency import consistency
from .bootstrap import clustered_ci
from .eer import (AXES, component_eer, declared_prior, eer_from_scores,
                  inapplicable_share)

SYSTEMS_TABLE1 = ["beats_linear", "eat_linear", "beats_attentive", "two_encoder"]
COLLAPSIBILITY_SYSTEMS = SYSTEMS_TABLE1 + ["sslam_linear", "xlsr_linear"]  # + baseline = 7
CONSTANTS = ("0", "0.5", "prior")
GATE_THRESHOLD = 0.5            # score an axis over {x : gamma(x) >= 1/2}
SWEEP_THRESHOLDS = (0.1, 0.9)   # the gate-threshold sweep the paper reports


def _constants(labels, axis):
    return {"0": 0.0, "0.5": 0.5, "prior": declared_prior(labels, axis)}


# --------------------------------------------------------------------------- §4.1
def dataset_counts() -> dict:
    idx = data.load_index()
    return {"eval_clips": len(idx),
            "inapplicable_rows": int((idx.label_id == 0).sum()),
            "format_matched_applicable": int(((idx.native_sr == 16000) &
                                              (idx.native_channels == 1) &
                                              (idx.label_id != 0)).sum()),
            "format_matched_inapplicable": int(((idx.native_sr == 16000) &
                                                (idx.native_channels == 1) &
                                                (idx.label_id == 0)).sum()),
            "inapplicable_not_16k_mono_pct": float(
                ((idx.label_id == 0) & ~((idx.native_sr == 16000) &
                                         (idx.native_channels == 1))).sum()
                / (idx.label_id == 0).sum() * 100)}


# --------------------------------------------------------------------------- Table 1
def table1() -> dict:
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    consts = _constants(labels, "env")
    out, census = {}, []

    for name in SYSTEMS_TABLE1:
        sysd = data.load_system(name, idx)
        per = {c: [] for c in CONSTANTS}
        comp = []
        for k in range(sysd["scores"].shape[0]):
            s_env = sysd["scores"][k, :, 2].astype(float)
            comp.append(component_eer(labels, s_env, "env"))
            for c in CONSTANTS:
                filled = np.where(labels == 0, consts[c], s_env)
                per[c].append(component_eer(labels, filled, "env",
                                            include_inapplicable=True))
                census.append(regimes.classify(labels, s_env, "env", consts[c]))
        means = {c: float(np.mean(per[c])) for c in CONSTANTS}
        out[name] = dict(mean=means,
                         sd={c: float(np.std(per[c], ddof=1)) for c in CONSTANTS},
                         per_seed=per,
                         spread=max(means.values()) - min(means.values()),
                         component_only=float(np.mean(comp)),
                         component_only_per_seed=comp)

    base = data.load_baseline(idx)
    s_env = base.s_env.to_numpy(float)
    bm = {}
    for c in CONSTANTS:
        bm[c] = component_eer(labels, np.where(labels == 0, consts[c], s_env), "env",
                              include_inapplicable=True)
        census.append(regimes.classify(labels, s_env, "env", consts[c]))
    out["reference"] = dict(mean=bm, sd=None, per_seed=None,
                            spread=max(bm.values()) - min(bm.values()),
                            component_only=component_eer(labels, s_env, "env"),
                            component_only_per_seed=None)

    spreads = [r["spread"] for r in out.values()]
    sds = [max(r["sd"].values()) for n, r in out.items()
           if r["sd"] and n != "beats_attentive"]
    cap = [c for c in census if c["regime"] == "captured"]
    return dict(rows=out, spread_min=min(spreads), spread_max=max(spreads),
                max_seed_sd_excl_attentive=max(sds),
                prior_env=consts["prior"],
                census_captured=len(cap), census_cells=len(census),
                census_max_deviation=max(c["deviation"] for c in cap))


# --------------------------------------------------------------------------- Table 2
def table2(n_draws: int = 2000, seed: int = 1337) -> dict:
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    base = data.load_baseline(idx)
    gamma = sweep.applicability_gate(base.s_original.to_numpy(float))
    gate = gamma >= GATE_THRESHOLD
    score = {"env": base.s_env.to_numpy(float), "speech": base.s_speech.to_numpy(float)}
    z = (labels != 0).astype(int)

    res = {}
    for axis in ("env", "speech"):
        def cells(rows):
            lab, sc = labels[rows], score[axis][rows]
            g = gate[rows]
            pooled = component_eer(lab, sc, axis, include_inapplicable=True)
            cond = component_eer(lab[g], sc[g], axis)
            comp = component_eer(lab, sc, axis)
            return np.array([pooled, cond, comp, abs(pooled - comp), abs(cond - comp)])

        ci = clustered_ci(cells, data.cluster_ids(idx, axis), n_draws=n_draws, seed=seed)
        p = ci["point"]
        res[axis] = dict(pooled=p[0], cond=p[1], comp=p[2],
                         err_pooled=p[3], err_cond=p[4],
                         ci_err_pooled=(ci["lo"][3], ci["hi"][3]),
                         ci_err_cond=(ci["lo"][4], ci["hi"][4]),
                         ci_pooled=(ci["lo"][0], ci["hi"][0]),
                         reduction_pct=100 * (1 - p[4] / p[3]),
                         n_clusters=ci["n_clusters"], n_draws=ci["n_draws"])
    tp = int((gate & (z == 1)).sum()); fp = int((gate & (z == 0)).sum())
    fn = int((~gate & (z == 1)).sum())
    res["gate"] = dict(precision=tp / (tp + fp), recall=tp / (tp + fn),
                       n_selected=int(gate.sum()), n_applicable=int((z == 1).sum()))
    res["threshold_sweep"] = {
        t: abs(component_eer(labels[gamma >= t], score["env"][gamma >= t], "env")
               - component_eer(labels, score["env"], "env")) for t in SWEEP_THRESHOLDS}
    return res


# --------------------------------------------------------------------------- §2
def s2_bounds() -> dict:
    tab = data.load_published_table()
    # Test-split shares. Properties of the corpus split, carried with the table;
    # see data/published/README.md for why they are not recomputed here.
    W0 = {"env": 0.5282467763767187, "speech": 0.39605811344941777}
    out = {}
    for axis, col in (("env", "eer_env_test"), ("speech", "eer_speech_test")):
        out[axis] = bounds.pairwise_determined(tab[col].tolist(), W0[axis])
    out["max_lower_endpoint"] = max(lo for axis in ("env", "speech") for lo, _ in out[axis]["intervals"])
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    base = data.load_baseline(idx)
    w0_eval = inapplicable_share(labels, "env")
    pub_exact = component_eer(labels, base.s_env.to_numpy(float), "env",
                              include_inapplicable=True)
    # Theorem 2 bounds what a reader can infer from a PUBLISHED table, so the
    # interval is computed from the published value at its printed precision,
    # not from our unrounded recomputation of it. Using the unrounded value
    # gives 0.9272 and answers a question nobody can ask.
    pub = round(pub_exact, 4)
    lo, hi = bounds.interval(pub, w0_eval)
    # Both directions of Theorem 2, and the lower-endpoint witness under the
    # stronger conditioning on the reference submission's other published cells.
    out["sharpness"] = dict(attainment=sharpness.attainment_grid(),
                            containment=sharpness.containment(),
                            witness=sharpness.lower_endpoint_witness(labels, pub))
    out["baseline_eval"] = dict(w0=w0_eval, published=pub, published_exact=pub_exact,
                                lo=lo, hi=hi,
                                width_pct=100 * (hi - lo),
                                component_only=component_eer(
                                    labels, base.s_env.to_numpy(float), "env"))
    return out


def s2_collapsibility() -> dict:
    """Theorem 1's dividing line, measured on every system and both axes.

    Collapsible summaries must vanish to machine precision in every cell. The
    ones the theorem excludes must not -- but note that a single cell can still
    be small when a system's two curves nearly coincide, so the claim the paper
    makes is about the SMALLEST such residual, which is the honest bound.
    """
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    coll, noncoll, area, cells = [], [], [], 0
    def add(sc, axis):
        nonlocal cells
        r = pooling.collapsibility_residuals(labels, sc, axis)
        area.append(r["AUC"])
        coll.extend(r[k] for k in pooling.SUMMARIES_COLLAPSIBLE)
        noncoll.extend(r[k] for k in pooling.SUMMARIES_NOT)
        cells += 1
    for name in COLLAPSIBILITY_SYSTEMS:
        sysd = data.load_system(name, idx)
        for axis, col in (("env", 2), ("speech", 1)):
            add(sysd["scores"][0, :, col].astype(float), axis)
    base = data.load_baseline(idx)
    for axis, c in (("env", "s_env"), ("speech", "s_speech")):
        add(base[c].to_numpy(float), axis)
    return dict(n_systems=len(COLLAPSIBILITY_SYSTEMS) + 1, n_checks=cells,
                worst_collapsible_residual=max(coll),
                worst_area_residual=max(area),
                smallest_non_collapsible_residual=min(noncoll),
                median_non_collapsible_residual=float(np.median(noncoll)))


# --------------------------------------------------------------------------- §3
def s3_gates_and_sweep() -> dict:
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    base = data.load_baseline(idx)
    s_env = base.s_env.to_numpy(float)
    gamma = sweep.applicability_gate(base.s_original.to_numpy(float))
    fill = lambda c: component_eer(labels, np.where(labels == 0, c, s_env), "env",
                                   include_inapplicable=True)
    gated = gamma * s_env + (1 - gamma) * 0.5
    out = dict(c0=fill(0.0), c05=fill(0.5), oracle=fill(0.5),
               rank_above=fill(float(s_env.max()) + 1.0),
               free_gate=component_eer(labels, gated, "env", include_inapplicable=True),
               component_only=component_eer(labels, s_env, "env"),
               prop3_floor=sweep.prop3_floor(labels, s_env, "env"),
               wa=1.0 - inapplicable_share(labels, "env"))
    out.update({f"sweep_{k}": v for k, v in
                sweep.sweep_constant(labels, s_env, "env").items()})
    return out


# --------------------------------------------------------------------------- §4.3
def s4_ablation() -> dict:
    """The pooling/head decomposition. Tier 0: no retraining, reference system only."""
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    base = data.load_baseline(idx)
    out = {}
    for axis, col in (("env", "s_env"), ("speech", "s_speech")):
        s = base[col].to_numpy(float)
        comp = component_eer(labels, s, axis)
        pub = component_eer(labels, s, axis, include_inapplicable=True)
        w0 = inapplicable_share(labels, axis)
        # weighted false-rejection gap at the published operating threshold
        spec = AXES[axis]
        is_spoof = np.isin(labels, spec["spoof"])
        keep = np.isin(labels, list(set(spec["bona"]) | set(spec["spoof"]) | {0}))
        from sklearn.metrics import roc_curve
        fpr, tpr, thr = roc_curve(np.isin(labels[keep], spec["spoof"]).astype(int),
                                  -s[keep], pos_label=1)
        i = int(np.nanargmin(np.abs(fpr - (1 - tpr))))
        tau = float(thr[i])
        frr0 = float((-s[labels == 0] >= tau).mean())
        frra = float((-s[np.isin(labels, spec["bona"])] >= tau).mean())
        out[axis] = dict(component_only=comp, published=pub, distortion=pub - comp,
                         w0=w0, frr_gap=frr0 - frra, weighted_frr_gap=w0 * (frr0 - frra))
    head_diff = out["env"]["component_only"] - out["speech"]["component_only"]
    total = out["env"]["published"] - out["speech"]["published"]
    pooling_net = out["env"]["distortion"] - out["speech"]["distortion"]
    out["decomposition"] = dict(total=total, head_difference=head_diff,
                                pooling_net=pooling_net,
                                pooling_pct=100 * pooling_net / total,
                                closes=abs(total - (head_diff + pooling_net)))
    return out


def s4_format_confound() -> dict:
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    base = data.load_baseline(idx)
    gamma = sweep.applicability_gate(base.s_original.to_numpy(float))
    z = (labels != 0).astype(int)
    fm = ((idx.native_sr == 16000) & (idx.native_channels == 1)).to_numpy()
    from sklearn.metrics import roc_auc_score, f1_score
    header_rule = ~fm                      # "not 16 kHz mono" predicts inapplicable
    out = dict(
        header_rule_f1=f1_score(1 - z, header_rule.astype(int)),
        gate_auc_full=roc_auc_score(z, gamma),
        gate_auc_format_matched=roc_auc_score(z[fm], gamma[fm]),
        header_auc_format_matched=0.5,     # constant on the subset, by construction
        n_fm_inapplicable=int((fm & (z == 0)).sum()),
        n_fm_applicable=int((fm & (z == 1)).sum()),
    )
    return out


# --------------------------------------------------------------------------- Fig. 1
def fig1_values(seed_index: int = 0) -> dict:
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    sysd = data.load_system("beats_linear", idx)
    s_env = sysd["scores"][seed_index, :, 2].astype(float)
    r = pooling.pooling_residual(labels, s_env, "env", 0.0, n_grid=20001)
    r["seed"] = int(sysd["seeds"][seed_index])
    return r


# --------------------------------------------------------------- assembly
def _train_val_counts() -> dict:
    """Training and validation clip counts, if those indices are present.

    They are not redistributed (see data/README.md), so this returns None when
    absent and verify.py reports those two literals as not checked rather than
    silently passing them.
    """
    out = {}
    for split in ("train", "val"):
        # Either a slim index we built, or the corpus CSV itself.
        for cand in (data.data_root() / f"{split}_index.csv",
                     data.data_root() / "development" / "metadata" / f"{split}.csv"):
            if cand.exists():
                out[f"{split}_clips"] = int(len(pd.read_csv(cand, low_memory=False)))
                break
        else:
            out[f"{split}_clips"] = None
    return out


def all_artefacts(n_draws: int = 2000, seed: int = 1337) -> dict:
    """Every recomputed value, flattened into the namespace paper_numbers.yaml uses."""
    counts = dataset_counts()
    counts.update(_train_val_counts())
    t1 = table1()
    t2 = table2(n_draws=n_draws, seed=seed)
    s2 = s2_bounds()
    collap = s2_collapsibility()
    s3 = s3_gates_and_sweep()
    abl = s4_ablation()
    fmt = s4_format_confound()
    fig = fig1_values()
    cons = consistency()
    plan = plan_values()
    cfg = configs()
    refstep = reference_c0_step()

    # derived views the paper prints directly
    for name, row in t1["rows"].items():
        m = row["mean"]
        disp = [round(m[c], 4) for c in CONSTANTS]
        row["displayed_difference"] = max(disp) - min(disp)
    t1["max_seed_sd_excl_attentive_ceil"] = _ceil_to(t1["max_seed_sd_excl_attentive"], 4)
    t1["census_max_deviation_e4"] = _ceil_to(t1["census_max_deviation"] * 1e4, 1)
    t1["half_w0"] = abl["env"]["w0"] / 2
    attn = t1["rows"]["beats_attentive"]
    t1["attn_c05_min"] = min(attn["per_seed"]["0.5"])
    t1["attn_c05_max"] = max(attn["per_seed"]["0.5"])
    t1["attn_comp_min"] = min(attn["component_only_per_seed"])
    t1["attn_comp_max"] = max(attn["component_only_per_seed"])
    t1.update(_two_encoder_geometry())

    collap["worst_collapsible_e15"] = collap["worst_collapsible_residual"] * 1e15
    collap["worst_area_e16"] = collap["worst_area_residual"] * 1e16
    s2["sharpness"]["attainment"]["worst_e12"] = s2["sharpness"]["attainment"]["worst_residual"] * 1e12
    s2["baseline_eval"]["w0_pct"] = s2["baseline_eval"]["w0"] * 100
    t1.update(_logit_ranges())
    collap["smallest_non_collapsible_e4"] = collap["smallest_non_collapsible_residual"] * 1e4
    s2["env"]["w0_pct"] = s2["env"]["w0"] * 100
    s3["published_env"] = t2["env"]["pooled"]
    for axis in ("env", "speech"):
        t2[axis]["n_shared_rows"] = counts["eval_clips"] - t2[axis]["n_clusters"]
    t2["ci_level"] = 95
    settings = dict(c_mid=float(_constants(np.array([0, 1, 3]), "env")["0.5"]),
                    gate_threshold=GATE_THRESHOLD,
                    sweep_lo=SWEEP_THRESHOLDS[0], sweep_hi=SWEEP_THRESHOLDS[1],
                    n_seeds=len(data.load_system("beats_linear", data.load_index())["seeds"]))

    return dict(counts=counts, t1=t1, t2=t2, s2=s2, collap=collap, s3=s3,
                abl=abl, fmt=fmt, fig1=fig, cons=cons, plan=plan, cfg=cfg, refstep=refstep,
                settings=settings)


def _ceil_to(x: float, nd: int) -> float:
    """Round half-up at nd places; used where the paper states a BOUND, not a value."""
    import math
    f = 10 ** nd
    return math.ceil(x * f - 1e-9) / f


def _two_encoder_geometry() -> dict:
    """How close the two-encoder sits to the capture/accept boundary and to the floor."""
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    consts = _constants(labels, "env")
    sysd = data.load_system("two_encoder", idx)
    bnd, flo = [], []
    means = {c: [] for c in CONSTANTS}
    for k in range(sysd["scores"].shape[0]):
        s = sysd["scores"][k, :, 2].astype(float)
        floor = sweep.prop3_floor(labels, s, "env")
        for c in CONSTANTS:
            r = regimes.classify(labels, s, "env", consts[c])
            bnd.append(abs(r["far"] - r["jump_lo"]))
            means[c].append(r["reported"])
        flo.append(floor)
    m = {c: float(np.mean(v)) for c, v in means.items()}
    f = float(np.mean(flo))
    # Both are stated in the paper as BOUNDS ("within x"), so they are rounded up.
    return dict(twoenc_boundary_distance=_ceil_to(float(max(bnd)), 3),
                twoenc_floor_distance=_ceil_to(max(abs(v - f) for v in m.values()), 4))


def _logit_ranges() -> dict:
    """Environmental score range of the two logit-valued systems, applicable and
    spoofed clips only (the inapplicable rows are replaced by c), over all seeds."""
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    out = {}
    for tag, name in (("attn", "beats_attentive"), ("twoenc", "two_encoder")):
        sc = data.load_system(name, idx)["scores"][:, labels != 0, 2].astype(float)
        out[f"range_{tag}_lo"], out[f"range_{tag}_hi"] = float(sc.min()), float(sc.max())
    return out


def reference_c0_step(n_draws: int = 1000, seed: int = 1337) -> dict:
    """Table 1 caption: the reference row's c=0 cell sits near a step.

    Class-stratified clip bootstrap: each draw resamples clips with replacement
    within each of the five classes, so every draw keeps the class counts and w0.
    The draws fall into two groups with nothing between them, so the caption
    reports the share of draws in the lower group and where that group sits,
    rather than a percentile interval, which would misdescribe a two-point mixture.
    """
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    s = data.load_baseline(idx).s_env.to_numpy(float)
    consts = _constants(labels, "env")
    by = [np.flatnonzero(labels == c) for c in np.unique(labels)]
    rng = np.random.default_rng(seed)
    c0, spread = [], []
    for _ in range(n_draws):
        r = np.concatenate([rng.choice(v, size=len(v), replace=True) for v in by])
        lab = labels[r]
        v = {c: component_eer(lab, np.where(lab == 0, cv, s[r]), "env", include_inapplicable=True)
             for c, cv in consts.items()}
        c0.append(v["0"])
        spread.append(max(v.values()) - min(v.values()))
    c0, spread = np.asarray(c0), np.asarray(spread)
    low = c0 < 0.3
    return dict(n_draws=n_draws, seed=seed,
                low_share_pct=float(low.mean() * 100),
                low_median=float(np.median(c0[low])) if low.any() else None,
                low_range=[float(c0[low].min()), float(c0[low].max())] if low.any() else None,
                high_median=float(np.median(c0[~low])),
                low_spread_median=float(np.median(spread[low])) if low.any() else None,
                gap_between_groups=float(c0[~low].min() - c0[low].max()) if low.any() else None)


def plan_values() -> dict:
    """The plan's worked-example logits, if the cached plan text is present.

    scripts/check_plan_values.py downloads and extracts it. Without that cache
    these three literals stay unchecked rather than silently passing.
    """
    import re
    txt = data.REPO / "build" / "esdd2_plan.txt"
    if not txt.exists():
        return {k: None for k in ("logit_a", "logit_b", "logit_c")}
    flat = re.sub(r"\s+", " ", txt.read_text(errors="replace"))
    found = lambda v: float(v) if re.search(re.escape(v) + r"(?![0-9])", flat) else None
    return dict(logit_a=found("1.22"), logit_b=found("-1.54"), logit_c=found("-1.89"))


def configs() -> dict:
    """Layer sets and audio conventions, read from the committed configs/."""
    import yaml
    c = yaml.safe_load(open(data.REPO / "configs" / "systems.yaml"))
    l7 = c["consistency_configs"]["layer7"]["layers"]
    l710 = c["consistency_configs"]["layers7to10"]["layers"]
    return dict(sample_rate_khz=c["audio"]["sample_rate_khz"],
                layer_single=l7[0], layer_lo=l710[0], layer_hi=l710[-1])
