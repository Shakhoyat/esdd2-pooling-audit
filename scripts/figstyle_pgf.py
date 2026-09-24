r"""Shared conventions for the figures that ship inside paper/main.tex.

`scripts/figure_style.py` is the Agg/Nimbus-Roman style used by the retired `fig_pooling` figure.
The three figures the current paper includes go through
pdflatex instead (`matplotlib.use("pgf")`, `\renewcommand{\rmdefault}{ptm}`), which is what makes their glyphs the same URW Times Type 1 faces the body
text uses -- no Type 3, no second font family, no CID TrueType. This module is that style, factored
out so the three figure scripts cannot drift from it.

Four rules it enforces rather than documents:

  * 9 pt floor. `text()` refuses a smaller size, and `verify_floor()` re-checks the GLYPHS THAT
    SHIPPED, because mathtext and LaTeX script levels are invisible to the call site.
  * exactly \columnwidth. `COLW` is spconf.sty's 86 mm, so \includegraphics[width=\columnwidth]
    places the PDF at scale 1.00 and 9 pt in the figure is 9 pt on the page.
  * no tight bbox anywhere. `savefig(bbox_inches="tight")` silently changes the width and with it
    the scale factor, which is how a 9 pt label becomes 7.9 pt (it is how a 9 pt label became 7.9 pt in an earlier draft).
  * no legend or label over a plotted curve. `assert_clear()` measures the artist's rendered
    bounding box against every sampled point of every curve, so "it does not sit on the data" is
    checked at generation time rather than eyeballed after the fact.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("pgf")
import matplotlib.pyplot as plt  # noqa: E402

FLOOR_PT = 9.0
COLW = 86.0 / 25.4                       # spconf \columnwidth, inches

# Okabe-Ito, each series additionally carrying its own dash pattern, so the figures read in
# greyscale and under the common colour-vision deficiencies.
BLUE, ORANGE, INK, GREY, RULE = "#0072B2", "#D55E00", "#1a1a1a", "#595959", "#B8B8B8"
GREEN, PINK = "#009E73", "#CC79A7"       # the fourth and fifth series of Fig. 3
POS, NEG = "#cfe0ee", "#f2ddcc"          # the two lobes of a signed integral
FILL = "#c8d4dd"                         # interval body, Fig. 1

# One line weight and one marker size across all three figures, so a curve in Fig. 2 and an
# interval in Fig. 1 read as the same kind of object. Quoted, not repeated, in each script.
LW, LW_THIN, MS = 1.15, 0.6, 3.0

# Legend geometry, also shared: three figures, three legends, one set of paddings. The numbers
# are in em at 9 pt, so a legend is about 10.4 pt per row plus 3.6 pt of border.
LEGEND = dict(frameon=False, handlelength=1.5, handletextpad=0.4, labelspacing=0.22,
              columnspacing=0.9, borderpad=0.2, borderaxespad=0.0)

plt.rcParams.update({
    "pgf.texsystem": "pdflatex", "pgf.rcfonts": False,
    "pgf.preamble": r"\usepackage[T1]{fontenc}\renewcommand{\rmdefault}{ptm}\usepackage{amsmath}",
    "font.family": "serif", "font.size": FLOOR_PT,
    "axes.labelsize": FLOOR_PT, "xtick.labelsize": FLOOR_PT, "ytick.labelsize": FLOOR_PT,
    "legend.fontsize": FLOOR_PT,
    "axes.linewidth": 0.7, "xtick.major.width": 0.7, "ytick.major.width": 0.7,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
})

_REQUESTED: list[float] = []


def text(ax, x, y, s, size=FLOOR_PT, **kw):
    """ax.text with the floor enforced, not asserted in a docstring."""
    if size < FLOOR_PT:
        raise ValueError(f"{s!r} at {size} pt is below the {FLOOR_PT} pt floor")
    _REQUESTED.append(size)
    return ax.text(x, y, s, fontsize=size, **kw)


# TeX's script and scriptscript levels for a 9 pt base, as pdfTeX rounds them. A subscript in a
# figure label is the same size as a subscript in the body text -- the paper prints $t_{\max}$ and
# $\mathrm{ROC}_{\mathrm{a}}$ on every other line -- so these are permitted, counted and reported.
# Everything BETWEEN them and the floor is a fault: that band is where a mis-scaled figure lands
# (7.9 pt after \includegraphics rescaling) and where Agg's mathtext lands (0.7 x 9 =
# 6.3 pt, the fragment scripts/figure_style.py was written to catch).
SCRIPT_PT = (5.98, 4.98)
SCRIPT_TOL = 0.06


def verify_floor(pdf_path: Path | str) -> None:
    """Every glyph in the emitted PDF at or above the floor, or at an exact TeX script level.

    Rotated glyphs are MEASURED, not excused: pdfplumber reports their `size` as the rotated
    bounding-box width, so the true unrotated height is the box width (pdfplumber does not undo the CTM). The y-axis
    label is the only rotated text these figures carry and it is the one that has been missed
    before.
    """
    import pdfplumber
    bad, rotated, script, n = [], 0, 0, 0
    with pdfplumber.open(str(pdf_path)) as pdf:
        for c in pdf.pages[0].chars:
            if not c["text"].strip():
                continue
            n += 1
            if not c.get("upright", True):
                rotated += 1
                size = c["x1"] - c["x0"]
            else:
                size = c["size"]
            if size >= FLOOR_PT - 0.05:      # 8.97 pt is 9 pt as pdfTeX rounds it
                continue
            if any(abs(size - s) <= SCRIPT_TOL for s in SCRIPT_PT):
                script += 1
                continue
            bad.append((c["text"], round(size, 2)))
    if bad:
        raise ValueError(f"{len(bad)} glyph(s) below {FLOOR_PT} pt in {pdf_path}, and not at a "
                         f"TeX script level: {sorted(set(bad))[:12]}")
    smallest = f"{min(_REQUESTED):.1f} pt" if _REQUESTED else "n/a (text() not called)"
    print(f"  floor OK: {n - script} glyphs >= {FLOOR_PT} pt ({rotated} rotated, measured by box "
          f"width), {script} math script-level glyphs at {SCRIPT_PT} pt; {len(_REQUESTED)} "
          f"text() calls, smallest requested {smallest}")


def verify_width(pdf_path: Path | str) -> None:
    """The emitted page must be exactly \\columnwidth, or LaTeX rescales the type."""
    import pdfplumber
    with pdfplumber.open(str(pdf_path)) as pdf:
        w, h = pdf.pages[0].width, pdf.pages[0].height
    want = COLW * 72.0
    if abs(w - want) > 0.5:
        raise ValueError(f"{pdf_path} is {w:.2f} pt wide, not {want:.2f} pt (86 mm): "
                         "\\includegraphics would rescale it and the 9 pt floor with it")
    print(f"  width OK: {w:.2f} pt = 86 mm, so width=\\columnwidth scales at 1.00 "
          f"(height {h:.1f} pt)")


def _renderer(fig):
    """A renderer the pgf canvas may not carry. Agg's metrics are the same ones pgf lays out."""
    try:
        return fig.canvas.get_renderer()
    except AttributeError:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        keep = fig.canvas
        r = FigureCanvasAgg(fig).get_renderer()
        fig.canvas = keep
        return r


def assert_clear(fig, ax, artist, curves, what="legend") -> None:
    """No sampled point of any curve inside the artist's box.

    A legend that sits on a line is the defect this pass exists to remove, and "it looked fine in
    the render" is how it came back last time. The box is MEASURED and the curves are the arrays
    that were plotted, so the check fails at generation time, not at a reviewer's desk.
    `curves` is [(name, xs, ys), ...] in data coordinates.
    """
    fig.canvas.draw() if hasattr(fig.canvas, "draw") else None
    bb = artist.get_window_extent(_renderer(fig))
    inv = ax.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    lo_x, hi_x = min(x0, x1), max(x0, x1)
    lo_y, hi_y = min(y0, y1), max(y0, y1)
    hits = []
    for name, xs, ys in curves:
        for x, y in zip(xs, ys):
            if lo_x <= x <= hi_x and lo_y <= y <= hi_y:
                hits.append((name, round(float(x), 4), round(float(y), 4)))
                break
    if hits:
        raise ValueError(f"{what} box x[{lo_x:.4f},{hi_x:.4f}] y[{lo_y:.4f},{hi_y:.4f}] "
                         f"covers plotted data: {hits}")
    print(f"  {what} clear of every curve: x[{lo_x:.3f},{hi_x:.3f}] y[{lo_y:.3f},{hi_y:.3f}]")


def finish(fig, out: Path) -> None:
    """Save, then run both artefact checks. No bbox_inches: the width is the contract."""
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    print(f"wrote {out}")
    verify_width(out)
    verify_floor(out)
