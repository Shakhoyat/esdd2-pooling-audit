#!/usr/bin/env python3
r"""Fig. 3 -- ACDS against the price of an alarm on an inapplicable input.

    python scripts/fig_accurve.py       -> build/fig_accurve.pdf

One panel, because the finding is that the crossings cluster: every pairwise crossing on the
environmental axis falls at or below alpha_0 = 0.125, and nothing changes from there to
alpha_0 = 2. At t_max = 1 the score is exactly affine in alpha_0,

    ACDS_a(alpha_0, 1) = AUC_a - alpha_0 (1 - AUC_0),

so each system is a straight line and the axis can be truncated at 0.15 without hiding anything.
Values are the three-seed means recomputed by pooling_audit.acds_artefacts from the per-clip
scores. No randomness, so no seed.

The previous version labelled each line at its right-hand edge. Three of the five labels had to
be pushed apart and given leader lines because the curves end within 0.009 of one another, and
the labels themselves were abbreviated to "atten.", "two-enc." and "ref." to fit the gutter that
cost. Both are gone: the five series are named in full in a compact two-column legend inside the
plotting region, in the lower-left wedge the reference curve leaves empty, and the right-hand
gutter is given back to the data. The legend's box is checked against every plotted point
(figstyle_pgf.assert_clear), so "it does not sit on a curve" is measured, not asserted.
"""
from pathlib import Path

import _common  # noqa: F401
import numpy as np  # noqa: E402
import figstyle_pgf as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from pooling_audit.acds_artefacts import acds_table  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "build" / "fig_accurve.pdf"
AXIS = "env"
XMAX = 0.15                        # displayed range; the caption states the truncation
TMAX = 1                           # ACDS(alpha_0, 1), the setting that is affine in alpha_0

# Full names, never abbreviated: these are the labels the reader matches against Table 1.
LABEL = {"beats_linear": "BEATs linear", "eat_linear": "EAT linear",
         "beats_attentive": "BEATs attentive", "two_encoder": "BEATs + XLS-R",
         "reference": "ESDD2 baseline"}
# Okabe-Ito plus a dash pattern each, so the five read apart in greyscale as well as in colour.
STYLE = {"BEATs linear":    (S.BLUE,   (0, ())),
         "EAT linear":      (S.ORANGE, (0, (4, 1.5))),
         "BEATs attentive": (S.GREEN,  (0, (1, 1.2))),
         "BEATs + XLS-R":   (S.PINK,   (0, (5, 1.5, 1, 1.5))),
         "ESDD2 baseline":  (S.INK,    (0, (3, 1, 1, 1, 1, 1)))}


def main() -> int:
    rec = acds_table(AXIS)
    aucs, crossings = rec["aucs"], rec["crossings"]
    last = max(c["alpha0"] for c in crossings)
    if last > XMAX:
        raise SystemExit(f"a crossing at alpha_0 = {last:.4f} lies outside the displayed axis")

    # right=0.96, not 1.0: the last tick label is centred on the last tick, so half of "0.15"
    # hangs past the axis and the fixed (never "tight") bbox clips it.
    fig, ax = plt.subplots(figsize=(S.COLW, 1.44))
    fig.subplots_adjust(left=0.135, right=0.96, top=0.985, bottom=0.215)

    x = np.array([0.0, XMAX])                  # the line is affine: two points draw it exactly
    dense = np.linspace(0.0, XMAX, 400)        # but the overlap check needs the segment, not its
    curves = []                                # endpoints, or a legend could sit mid-line
    for system in LABEL:                       # Table 1's column order, so the legend matches it
        lab = LABEL[system]
        colour, dash = STYLE[lab]
        a = aucs[system]
        slope = 1 - a["auc_0"]
        ax.plot(x, a["auc_a"] - x * slope, color=colour, linestyle=dash, linewidth=S.LW,
                label=lab, zorder=4)
        curves.append((lab, dense, a["auc_a"] - dense * slope))

    # The last crossing. A subtle dotted vertical, labelled above the curves rather than on them.
    ax.axvline(last, color=S.GREY, linewidth=S.LW_THIN, linestyle=(0, (1, 2)), zorder=2)
    S.text(ax, last - 0.006, 0.9515, rf"last crossing, $\alpha_0={last:.3f}$",
           color=S.GREY, ha="right", va="center", zorder=8)

    # Lower left: the wedge under the reference line, the only region no curve enters. Two
    # columns, so five full names fit in three rows instead of five. Tighter spacing than
    # S.LEGEND's shared default: "ESDD2 baseline" and "BEATs attentive" are long enough that
    # the shared columnspacing/handletextpad push the box into the ESDD2 baseline curve itself
    # (assert_clear below caught this after the ESDD2-baseline rename widened the legend).
    leg = ax.legend(loc="lower left", ncol=2,
                    **{**S.LEGEND, "columnspacing": 0.5, "handletextpad": 0.25})
    leg.set_zorder(9)

    ax.set_xlim(0, XMAX)
    # the bottom of the range is the legend's room: the wedge under the reference line has to be
    # tall enough to hold three rows, and assert_clear below is what decides whether it is
    ax.set_ylim(0.66, 0.975)
    ax.set_xticks([0, 0.05, 0.10, 0.15])
    ax.set_yticks([0.70, 0.80, 0.90])
    ax.set_xlabel(r"price of an alarm on an inapplicable input, $\alpha_0$", labelpad=1.5)
    ax.set_ylabel(r"$\mathrm{ACDS}$", labelpad=3)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    S.assert_clear(fig, ax, leg, curves)
    S.finish(fig, OUT)
    print(f"  {len(curves)} systems, {len(crossings)} pairwise crossings, all in "
          f"[{min(c['alpha0'] for c in crossings):.4f}, {last:.4f}]; axis truncated at {XMAX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
