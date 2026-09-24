#!/usr/bin/env python3
"""Table 1: environmental EER under three declared constants, and the regime census."""
import _common  # noqa: F401
from pooling_audit.recompute import CONSTANTS, table1

NAMES = {"beats_linear": "BEATs probe", "eat_linear": "EAT probe",
         "beats_attentive": "attentive head", "two_encoder": "two-encoder",
         "reference": "reference"}

t = table1()
print(f"prior (third declared constant) = {t['prior_env']:.5f}\n")
print(f"{'system':16s}{'c=0':>9s}{'c=0.5':>9s}{'prior':>9s}{'spread':>9s}{'comp-only':>11s}")
for k, label in NAMES.items():
    r = t["rows"][k]
    m = r["mean"]
    print(f"  {label:14s}{m['0']:9.4f}{m['0.5']:9.4f}{m['prior']:9.4f}"
          f"{r['spread']:9.4f}{r['component_only']:11.4f}")
print(f"\nspread across the five rows: {t['spread_min']:.4f} to {t['spread_max']:.4f}")
print(f"max seed s.d. excluding the attentive head: {t['max_seed_sd_excl_attentive']:.5f}")
print(f"regime census: {t['census_captured']} of {t['census_cells']} cells captured, "
      f"max deviation from (FAR(c)+F)/2 = {t['census_max_deviation']:.3e}")
