#!/usr/bin/env python3
r"""Fig. 2 -- what ACDS is: Definitions 2 and 3, drawn.

    python scripts/fig_acds_mechanism.py    -> build/fig_acds_mechanism.pdf

Fig. 3 (fig_accurve) is a RESULTS figure: it sweeps alpha_0 and shows how the score behaves.
This one shows what the score IS, on measured curves rather than a schematic, because the one
thing a schematic cannot show here is that the two terms are read at the SAME operating point --
the crux stated in the paragraph after Definition 2.

    AC_a(t; alpha_0) = ROC_a(t) - alpha_0 R_0(t)          Definition 2
    ACDS_a           = mean of AC_a over [0, t_max]       Definition 3

One panel, three curves on one shared false-acceptance axis:

  ROC_a(t)          acceptance rate of the applicable positives  (= AC_a at alpha_0 = 0)
  R_0(t)            alarm rate on the structural zeros, at the same threshold; at the alpha_0 = 1
                    drawn here this curve is also alpha_0 R_0(t), the priced term itself
  AC_a(t; 1)        the priced curve; the signed area under it is ACDS_a(1, 1)

The legend's top edge sits pinned on the zero rule, in the lower-right quadrant no curve enters,
and the placement is CHECKED against the plotted arrays rather than eyeballed
(figstyle_pgf.assert_clear). The subtraction is a measured length: a two-headed arrow between
AC_a and ROC_a at one t, on a guide that runs down to the axis, so "same operating point,
vertical difference" is the first thing the panel says.

The system is the released reference baseline on the environmental axis, the row of Table 1 whose
price term is larger than its detection term (AUC_0 = 0.2870 < 1/2), so both lobes of the signed
integral are visible at 86 mm. The curves are the full empirical grid, resampled to 1001 uniform
points for drawing only; the three areas in the legend are computed on the FULL grid by
pooling_audit.acds and the resampling error is asserted below 1e-4 before any area is drawn.
"""
from pathlib import Path

import _common  # noqa: F401
import figstyle_pgf as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from pooling_audit import acds, data  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "build" / "fig_acds_mechanism.pdf"
ALPHA0 = 1.0                       # the alpha_0 of Table 1's second row
T_STAR = 0.42                      # where the one-threshold reading is marked
YLO, YHI = -1.12, 1.12            # symmetric, so the legend clears the bottom spine
NGRID = 1001


def main() -> int:
    idx = data.load_index()
    labels = idx.label_id.to_numpy()
    base = data.load_baseline(idx)
    s = base.s_env.to_numpy(float)
    neg, pa, p0 = acds.populations(labels, s, "env")
    tf, roc_af, r0f, roc_0f = acds.curves(neg, pa, p0)

    e = {"acds_0_1": acds.acds(tf, roc_af, r0f, 0.0, 1.0),
         "int_r0": acds.auc(tf, r0f),
         "acds_1_1": acds.acds(tf, roc_af, r0f, ALPHA0, 1.0),
         "auc_0": acds.auc(tf, roc_0f)}
    # Proposition 2(i)/(ii), asserted so the figure cannot label an area the definitions do not
    # produce, and so a future change to acds.py cannot silently move what the legend prints.
    assert abs(e["acds_0_1"] - acds.auc(tf, roc_af)) < 1e-12, "ACDS(0,1) != AUC_a"
    assert abs(e["int_r0"] - (1.0 - e["auc_0"])) < 1e-12, "int R_0 != 1 - AUC_0"
    assert abs(e["acds_1_1"] - (e["acds_0_1"] - e["int_r0"])) < 1e-12, "AC is not affine"

    t = np.linspace(0.0, 1.0, NGRID)
    roc_a, r0 = np.interp(t, tf, roc_af), np.interp(t, tf, r0f)
    trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    err = max(abs(float(trap(roc_a, t)) - e["acds_0_1"]),
              abs(float(trap(roc_a - r0, t)) - e["acds_1_1"]))
    if err > 1e-4:
        raise SystemExit("the drawn grid is too coarse for the areas it is annotated with")
    ac = roc_a - ALPHA0 * r0

    fig, ax = plt.subplots(figsize=(S.COLW, 1.34))
    fig.subplots_adjust(left=0.125, right=0.995, top=0.97, bottom=0.235)

    # the signed integral of Definition 3, in its two lobes: charged, then earned
    ax.fill_between(t, ac, 0, where=ac < 0, color=S.NEG, lw=0, zorder=0, interpolate=True)
    ax.fill_between(t, ac, 0, where=ac >= 0, color=S.POS, lw=0, zorder=0, interpolate=True)
    ax.axhline(0, color=S.RULE, lw=0.7, zorder=1)

    # The three areas are the three terms of Definition 3 at t_max = 1, so the legend carries the
    # arithmetic: 0.8740 - 0.7130 = 0.1611, read straight down.
    ax.plot(t, roc_a, color=S.BLUE, lw=S.LW, zorder=4,
            label=r"$\mathrm{ROC}_{\mathrm{a}}(t)$, area $" + f"{e['acds_0_1']:.4f}$")
    ax.plot(t, r0, color=S.ORANGE, lw=S.LW, ls=(0, (4, 1.5)), zorder=4,
            label=r"$\alpha_0R_0(t)$, area $" + f"{e['int_r0']:.4f}$")
    ax.plot(t, ac, color=S.INK, lw=S.LW, ls=(0, (3, 1, 1, 1)), zorder=5,
            label=r"$\mathrm{AC}_a(t;1)$, area $" + f"{e['acds_1_1']:.4f}$")

    # THE CRUX: one threshold, three readings, and the price as a LENGTH between two of them.
    ya, y0, yc = (float(np.interp(T_STAR, t, v)) for v in (roc_a, r0, ac))
    ax.plot([T_STAR, T_STAR], [YLO, ya], color=S.GREY, lw=S.LW_THIN, ls=(0, (1, 1.6)), zorder=3)
    for y, col in ((ya, S.BLUE), (y0, S.ORANGE), (yc, S.INK)):
        ax.plot([T_STAR], [y], marker="o", ms=2.6, color=col, zorder=7)
    ax.annotate("", xy=(T_STAR + 0.035, ya), xytext=(T_STAR + 0.035, yc),
                arrowprops=dict(arrowstyle="<->,head_width=0.11,head_length=0.28",
                                color=S.GREY, lw=S.LW_THIN, shrinkA=0, shrinkB=0), zorder=6)
    price = S.text(ax, T_STAR + 0.065, 0.36 * ya + 0.64 * yc, r"$\alpha_0R_0(t)$",
                   color=S.GREY, ha="left", va="center", zorder=8)

    ax.set_xlim(0, 1.0)
    ax.set_ylim(YLO, YHI)
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xticklabels(["0", "0.5", "1"])
    ax.set_yticks([-1, 0, 1])
    ax.set_yticklabels(["$-1$", "0", "1"])
    ax.set_xlabel(r"false acceptance rate on $\mathcal{N}$, $t$", labelpad=1.0)
    ax.set_ylabel("rate", labelpad=1.0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    # Top edge of the legend on the zero rule: below it, right of t = 0.3, no curve goes.
    leg = ax.legend(loc="upper right", bbox_to_anchor=(1.0, -YLO / (YHI - YLO)),
                    bbox_transform=ax.transAxes, **S.LEGEND)
    leg.set_zorder(9)

    curves = [("ROC_a", t, roc_a), ("R_0", t, r0), ("AC_a", t, ac)]
    S.assert_clear(fig, ax, leg, curves)
    S.assert_clear(fig, ax, price, curves, what="price label")
    S.finish(fig, OUT)
    print(f"  resampling error on the drawn grid: {err:.2e} at {NGRID} points")
    print(f"  at t = {T_STAR}:  ROC_a {ya:.4f}  R_0 {y0:.4f}  AC {yc:.4f}")
    print(f"  ACDS(0,1) {e['acds_0_1']:.4f}   ACDS(1,1) {e['acds_1_1']:.4f}   "
          f"int R_0 {e['int_r0']:.4f}   AUC_0 {e['auc_0']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
