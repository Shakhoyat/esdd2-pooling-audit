#!/usr/bin/env python3
"""Section 2: the interval, the ordering criterion, and the 0-of-55 result."""
import _common  # noqa: F401
from pooling_audit.recompute import s2_bounds

b = s2_bounds()
e = b["baseline_eval"]
print("reference baseline, evaluation split")
print(f"  w0 {e['w0']:.4f}   published {e['published']:.4f}   "
      f"interval [{e['lo']:.4f}, {e['hi']:.4f}] = {e['width_pct']:.0f}% of the range")
print(f"  true component-only {e['component_only']:.4f}, which the interval contains: "
      f"{e['lo'] <= e['component_only'] <= e['hi']}")
print("\neleven published systems, test split")
for axis in ("env", "speech"):
    r = b[axis]
    print(f"  {axis:7s} {r['determined_geometric']} of {r['n_pairs']} pairs determined "
          f"(criterion agrees on {r['n_pairs'] - r['mismatches']}/{r['n_pairs']}); "
          f"largest published gap {r['max_gap']:.4f} against w0 {r['w0']:.4f}")
