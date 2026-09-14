#!/usr/bin/env python3
"""Section 4.3: is the asymmetry acoustic difficulty, or pooling?"""
import _common  # noqa: F401
from pooling_audit.recompute import s4_ablation

a = s4_ablation()
for axis in ("env", "speech"):
    r = a[axis]
    print(f"{axis:8s} component-only {r['component_only']:.4f}   published {r['published']:.4f}"
          f"   distortion {r['distortion']:+.4f}   w0 {r['w0']:.4f}"
          f"   weighted FRR gap {r['weighted_frr_gap']:.4f}")
d = a["decomposition"]
print(f"\ndecomposition of the {d['total']:.4f} between the two published values:")
print(f"  pooling contributes {d['pooling_net']:.4f} ({d['pooling_pct']:.0f}%)")
print(f"  the heads differ by {d['head_difference']:.4f}")
print(f"  the two terms close to {d['closes']:.2e}")
