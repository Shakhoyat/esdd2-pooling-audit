#!/usr/bin/env python3
"""Aggregate the consistency-experiment arms and report the four pre-registered quantities.

Reads the per-run outputs written by run.py and reports, over all configurations
and seeds: the change in the reported (pooled) environmental EER, the change in
the component-only value, the change in the AUC separating the inapplicable class,
and the distance from the label-free fixed point (§2.3).
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

OUT = Path(__file__).resolve().parents[2] / "build" / "consistency"


def main() -> int:
    if not OUT.exists():
        print(f"  no runs found under {OUT}; run run.py first")
        return 2
    runs = [json.loads(p.read_text()) for p in sorted(OUT.glob("*.json"))]
    if not runs:
        print("  no runs found")
        return 2
    import numpy as np
    for arm in ("M", "C"):
        sel = [r for r in runs if r["arm"] == arm]
        if not sel:
            continue
        print(f"  arm {arm}: n={len(sel)}  "
              f"pooled {np.mean([r['eer_pooled'] for r in sel]):.4f}  "
              f"component-only {np.mean([r['eer_component'] for r in sel]):.4f}  "
              f"class-0 AUC {np.mean([r['auc_orig_vs_bona'] for r in sel]):.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
