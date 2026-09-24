#!/usr/bin/env python3
r"""Fig. 1 -- Theorem 2's identified set, drawn for the systems it applies to.

    python scripts/fig_identified.py    -> build/fig_identified.pdf

What a published component EER leaves of the quantity a reader wants. Each row is one system's
sharp identified set for the component-only EER, i.e. the interval

    [ max(0, (EER_pub - w_0)/w_a),  min(1, EER_pub/w_a) ]

evaluated at that system's own split. Two things the prose states and a reader has to take on
trust are here as a picture:

  * the reference baseline's evaluation-split row -- the only row whose true value is known --
    is pinned to [0, 0.9271] while the truth is 0.2090, so the interval contains the answer and
    almost everything else with it;
  * every one of the eleven challenge systems publishing a component EER has lower endpoint 0, so
    the intervals are nested, every pair overlaps, and none of the 55 comparisons is determined.

Drawn as an identified-set plot rather than a bar chart: a bar reads as a magnitude from zero,
which is the wrong reading of an interval whose left endpoint happens to be zero. Each row is a
segment with a cap at each end, the shared lower endpoint is a column of caps standing off the
axis at x = 0, and the explanatory sentences live in the caption, leaving a compact legend in the
wedge the narrow rows leave free. The legend's box is checked against every plotted point
(figstyle_pgf.assert_clear), so "it does not sit on a segment" is measured, not asserted.

Systems are not named. The claim is about the protocol, not about any team, and the manuscript
makes the same choice.

Every plotted value comes from pooling_audit.recompute.s2_bounds: the eleven test-split
intervals from data/published/esdd2_overview_table.csv, the evaluation row from the released
baseline submission and the evaluation index.
"""
from pathlib import Path

import _common  # noqa: F401
import figstyle_pgf as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from pooling_audit.recompute import s2_bounds  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "build" / "fig_identified.pdf"
AXIS = "env"
GAP = 2.0                          # blank rows between the test group and the reference row
CAP = 0.30                         # half-height of an end cap, in row units


def interval(ax, y, lo, hi, colour, lw, cap):
    """One identified set: the segment, and a cap at each endpoint."""
    ax.plot([lo, hi], [y, y], color=colour, lw=lw, solid_capstyle="butt", zorder=4)
    for x in (lo, hi):
        ax.plot([x, x], [y - cap, y + cap], color=colour, lw=lw, zorder=5)


def main() -> int:
    s2 = s2_bounds()
    env, be = s2[AXIS], s2["baseline_eval"]
    if max(lo for lo, _ in env["intervals"]) != 0.0:
        raise SystemExit("a published interval no longer starts at 0; the figure's claim moved")
    if not be["lo"] <= be["component_only"] <= be["hi"]:
        raise SystemExit("the validated interval no longer contains the true value")
    mv = {"interval": [be["lo"], be["hi"]], "true_corrected": be["component_only"],
          "official": be["published"]}
    n_systems = env["n_systems"]

    # widest at the bottom, narrowest at the top: the staircase then leaves the upper right free,
    # which is where the legend goes and where nothing is ever plotted.
    rows = sorted(({"lo": lo, "hi": hi} for lo, hi in env["intervals"]), key=lambda r: -r["hi"])
    fig, ax = plt.subplots(figsize=(S.COLW, 1.19))
    fig.subplots_adjust(left=0.035, right=0.985, top=0.98, bottom=0.275)

    y_ref = -GAP
    # the shared lower endpoint, as one rule rather than eleven coincident caps on the spine
    ax.plot([0, 0], [y_ref - 0.6, len(rows) - 0.4], color=S.RULE, lw=S.LW_THIN,
            linestyle=(0, (1, 1.6)), zorder=1)
    for i, r in enumerate(rows):
        interval(ax, i, r["lo"], r["hi"], S.BLUE, 0.9, CAP)
    interval(ax, y_ref, mv["interval"][0], mv["interval"][1], S.ORANGE, 1.2, 0.45)
    ax.plot([mv["true_corrected"]], [y_ref], marker="D", ms=S.MS, color=S.INK,
            markeredgewidth=0, zorder=7)

    # The diamond is named in the legend, not annotated in place: a 9 pt label in the gap between
    # the two groups needs more clear height than the gap leaves, and would overprint the longest
    # interval, which is what assert_clear below now measures. The value itself belongs to the
    # caption and to the body text, where it already is.
    handles = [Line2D([], [], color=S.BLUE, lw=0.9,
                      label="challenge systems (test split)"),
               Line2D([], [], color=S.ORANGE, lw=1.2,
                      label="ESDD2 baseline (evaluation split)"),
               Line2D([], [], color=S.INK, lw=0, marker="D", ms=S.MS,
                      label=r"EER$_{\mathrm{a}}$ of the ESDD2 baseline")]
    leg = ax.legend(handles=handles, loc="upper right", **S.LEGEND)
    leg.set_zorder(9)

    ax.set_xlim(-0.028, 1.0)
    ax.set_ylim(y_ref - 1.0, len(rows) + 2.3)
    ax.set_yticks([])
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"])
    ax.set_xlabel("component-only EER, environmental axis", labelpad=1.0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0)

    # the legend must not reach a segment: every row is [lo, hi] at its own y
    drawn = [(f"row {i}", [r["lo"], r["hi"]], [i, i]) for i, r in enumerate(rows)]
    drawn.append(("reference", list(mv["interval"]), [y_ref, y_ref]))
    S.assert_clear(fig, ax, leg, drawn)
    S.finish(fig, OUT)
    print(f"  eval reference: [{mv['interval'][0]:.4f}, {mv['interval'][1]:.4f}] from "
          f"EER_pub {mv['official']:.4f}; true {mv['true_corrected']:.4f}")
    print(f"  {n_systems} test systems, w0 {env['w0']:.4f}, widths "
          f"{rows[-1]['hi']:.4f} to {rows[0]['hi']:.4f}, all lower endpoints 0; "
          f"{env['determined_geometric']} of {env['n_pairs']} pairs determined")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
