"""Plotting conventions for Figure 1, ported from the script that produced the paper's figure.

  * vector PDF, fonts embedded, no Type 3 (pdf.fonttype = 42)
  * every upright glyph at least 9 pt at final scale
  * three redundant channels per series: marker, line style and hue
  * a single orange/blue pair plus neutrals, so no colour-vision-deficient pair carries meaning
"""
import matplotlib

matplotlib.use("Agg")

FLOOR_PT = 9.0
COL_IN = 3.386                           # one IEEE column, 86 mm

for k in ("font.size", "axes.labelsize", "xtick.labelsize", "ytick.labelsize",
          "legend.fontsize", "axes.titlesize"):
    matplotlib.rcParams[k] = FLOOR_PT
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["font.family"] = "serif"
# Liberation Serif is a real TrueType face metric-compatible with Times, so it embeds
# cleanly under fonttype 42 and matches the body text.
matplotlib.rcParams["font.serif"] = ["Liberation Serif", "DejaVu Serif"]
matplotlib.rcParams["lines.linewidth"] = 1.6
matplotlib.rcParams["axes.linewidth"] = 0.8
matplotlib.rcParams["legend.frameon"] = True
matplotlib.rcParams["legend.edgecolor"] = "#4d4d4d"
matplotlib.rcParams["legend.framealpha"] = 1.0
matplotlib.rcParams["legend.borderpad"] = 0.35
matplotlib.rcParams["legend.handlelength"] = 2.4

INK, MUTE, RULE = "#1a1a1a", "#6b6b6b", "#B8B8B8"
BAD, GOOD = "#C1741C", "#14477A"
SERIES = {"official": (BAD, "-", "o"), "mixture_only": (GOOD, "--", "s"),
          "third": (INK, ":", "^")}
