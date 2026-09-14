#!/usr/bin/env python3
"""Table 2: what a third party recovers, what the organiser recovers, with CIs."""
import argparse

import _common  # noqa: F401
from pooling_audit.recompute import table2

ap = argparse.ArgumentParser()
ap.add_argument("--draws", type=int, default=2000)
a = ap.parse_args()

t = table2(n_draws=a.draws)
print(f"{'axis':12s}{'pooled':>9s}{'cond.':>9s}{'comp-only':>11s}"
      f"{'err pooled':>12s}{'err cond.':>11s}{'reduction':>11s}")
for axis in ("env", "speech"):
    d = t[axis]
    print(f"  {axis:10s}{d['pooled']:9.4f}{d['cond']:9.4f}{d['comp']:11.4f}"
          f"{d['err_pooled']:12.4f}{d['err_cond']:11.4f}{d['reduction_pct']:10.0f}%")
print(f"\n95% clustered bootstrap, {t['env']['n_draws']} resamples:")
for axis in ("env", "speech"):
    d = t[axis]
    print(f"  {axis:8s} pooled error [{d['ci_err_pooled'][0]:.4f}, {d['ci_err_pooled'][1]:.4f}]"
          f"   conditioned error [{d['ci_err_cond'][0]:.4f}, {d['ci_err_cond'][1]:.4f}]"
          f"   clusters {d['n_clusters']}")
g = t["gate"]
print(f"\ngate at 1/2: precision {g['precision']:.3f}  recall {g['recall']:.3f}  "
      f"selected {g['n_selected']} of {g['n_applicable']} applicable")
print("threshold sweep (absolute error on the environmental axis): "
      + "  ".join(f"{k}: {v:.4f}" for k, v in t["threshold_sweep"].items()))
