#!/usr/bin/env python3
"""Figure 1: areas average, crossings do not. Writes build/fig_pooling.pdf."""
from pathlib import Path

import _common  # noqa: F401
import figure_style as S  # noqa: E402  -- the paper figure's exact rcParams
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from pooling_audit import data, pooling  # noqa: E402

idx = data.load_index()
labels = idx.label_id.to_numpy()
sysd = data.load_system("beats_linear", idx)
s_env = sysd["scores"][0, :, 2].astype(float)
r = pooling.pooling_residual(labels, s_env, "env", 0.0, n_grid=20001)

grid = np.linspace(0, 1, 20001)
neg = np.isin(labels, (3, 4))
app = np.isin(labels, (1, 2))
R_a = pooling.roc_on_grid(s_env[app], s_env[neg], grid)
tau = np.quantile(np.sort(s_env[neg]), 1 - grid)
R_0 = (0.0 >= tau).astype(float)
R_pub = r["w0"] * R_0 + r["wa"] * R_a

fig, ax = plt.subplots(figsize=(S.COL_IN, S.COL_IN * 0.86))
for key, R, lab in (("third", R_0, "inapplicable"),
                    ("mixture_only", R_a, "component"),
                    ("official", R_pub, "pooled")):
    col, ls, mk = S.SERIES[key]
    ax.plot(grid, R, color=col, ls=ls, lw=1.6, label=lab,
            marker=mk, markevery=(1250, 2500), markersize=3.2)
ax.plot([0, 1], [1, 0], color=S.RULE, lw=0.8, ls=(0, (1, 2)), zorder=0)
for e, key in ((r["eer_0"], "third"), (r["eer_a"], "mixture_only"), (r["eer_pub"], "official")):
    ax.plot([e], [1 - e], marker="o", ms=4.5, mfc="white", mec=S.SERIES[key][0], mew=1.2,
            zorder=6, clip_on=False)
ax.set_xlabel("false-acceptance rate")
ax.set_ylabel("true-positive rate")
ax.set_xlim(-0.03, 1.06); ax.set_ylim(-0.07, 1.03)
ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
leg = ax.legend(loc="center right", bbox_to_anchor=(1.005, 0.70),
                handletextpad=0.5, labelspacing=0.25, borderpad=0.3)
leg.get_frame().set_linewidth(0.8)
fig.subplots_adjust(bottom=0.30, left=0.155, right=0.985, top=0.985)
fig.text(0.02, 0.105, f"area  {r['area_pub']:.4f} = {r['w0']:.4f}({r['area_0']:.4f})"
                      f" + {r['wa']:.4f}({r['area_a']:.4f})",
         fontsize=S.FLOOR_PT, ha="left", va="center")
fig.text(0.02, 0.030, f"crossing  {r['eer_pub']:.3f}, weighted mean  "
                      f"{r['eer_weighted_mean']:.3f}", fontsize=S.FLOOR_PT, ha="left", va="center")
out = Path(__file__).resolve().parents[1] / "build"
out.mkdir(exist_ok=True)
fig.savefig(out / "fig_pooling.pdf")
print(f"wrote {out / 'fig_pooling.pdf'}")
print(f"  area identity residual {r['area_residual']:.2e}; crossing gap {r['crossing_gap']:.4f}")
