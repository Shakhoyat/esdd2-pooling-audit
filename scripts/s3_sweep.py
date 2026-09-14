#!/usr/bin/env python3
"""Section 3.1: the declared constants, the gates, and the full constant sweep."""
import _common  # noqa: F401
from pooling_audit.recompute import s3_gates_and_sweep

g = s3_gates_and_sweep()
print("reference system, environmental axis, native score scale")
print(f"  published                 {g['published_env']:.4f}")
print(f"  component-only (target)   {g['component_only']:.4f}")
print(f"  c = 0                     {g['c0']:.4f}")
print(f"  c = 0.5, and oracle gate  {g['c05']:.4f}   (the Proposition 3 floor)")
print(f"  gate from original score  {g['free_gate']:.4f}")
print(f"  Proposition 3 fixed point {g['prop3_floor']:.4f}   w_a = {g['wa']:.4f}")
print(f"\nsweeping every constant: reported value ranges over "
      f"[{g['sweep_lo']:.4f}, {g['sweep_hi']:.4f}]")
print(f"  closest any constant comes to the target: {g['sweep_closest_value']:.4f} "
      f"at c = {g['sweep_closest_at_c']:.4f} (gap {g['sweep_closest_gap']:.4f})")
print(f"  largest step: at c = {g['sweep_step_at_c']:.4f}, "
      f"{g['sweep_step_from']:.4f} -> {g['sweep_step_to']:.4f}")
