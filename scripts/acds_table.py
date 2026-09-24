#!/usr/bin/env python3
"""Table 1: ACDS under four settings of (alpha_0, t_max), and Section 4.4's crossings.

    python scripts/acds_table.py

Environmental axis, evaluation split, means over the three seeds; the reference baseline is one
released submission and so has a single seed. Recomputed from the per-clip scores in scores/ --
nothing is read from a cached result and no model is retrained.
"""
import _common  # noqa: F401
from pooling_audit.acds_artefacts import SETTINGS, SYSTEMS, acds_table

NAMES = dict(SYSTEMS + [("reference", "reference")])

t = acds_table()
print(f"{'system':16s}" + "".join(f"{s:>12s}" for s in SETTINGS) + f"{'AUC_0':>10s}")
for key, label in NAMES.items():
    r, a = t["rows"][key], t["aucs"][key]
    print(f"  {label:14s}" + "".join(f"{r[s]:12.4f}" for s in SETTINGS) + f"{a['auc_0']:10.4f}")

print(f"\nw0 = {t['w0']:.5f}   wa = {t['wa']:.5f}   w0/wa = {t['w0_over_wa']:.4f}")
print("Proposition 2(i) ACDS(0,1) = AUC_a and 2(ii) wa*ACDS(w0/wa,1) = AUC_pub - w0:")
print(f"  worst residual over every system and seed: {t['worst_identity_residual']:.3e}")
print(f"  trapezoid vs step rule, worst gap:         {t['worst_step_gap']:.3e}")

print(f"\ndynamic ranges: ACDS(0,1) spans {t['span_acds01']:.4f}, "
      f"1 - AUC_0 spans {t['span_alarm']:.4f}")
print(f"{t['n_crossings']} pairwise crossings in alpha_0, all at or below "
      f"{t['last_crossing']:.4f}:")
for c in t["crossings"]:
    print(f"  {NAMES[c['pair'][0]]:16s} x {NAMES[c['pair'][1]]:16s}  alpha_0 = {c['alpha0']:.4f}")
print("\nranking by setting:")
for s in SETTINGS:
    print(f"  {s:>12s}  " + " > ".join(NAMES[n] for n in t["ranks"][s]))
