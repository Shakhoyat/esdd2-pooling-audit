#!/usr/bin/env python3
"""Section 2: Theorem 1's dividing line, measured on every system and both axes."""
import _common  # noqa: F401
from pooling_audit.recompute import s2_collapsibility

c = s2_collapsibility()
print(f"systems: {c['n_systems']}   checks (systems x axes): {c['n_checks']}")
print(f"  worst area residual (must vanish):      {c['worst_area_residual']:.3e}")
print(f"  smallest crossing gap (must not):       {c['smallest_crossing_gap']:.3e}")
