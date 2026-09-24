#!/usr/bin/env python3
"""Proposition 2's witnesses: exact values, and the released scorer on materialised scores.

    python scripts/prop2_witness.py            # prints every cell; writes build/prop2_witness.json
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from pooling_audit.witness import WITNESSES, check  # noqa: E402

out, ok = [], True
for name in sorted(WITNESSES):
    for dense in (False, True):
        r = check(name, 1, dense)
        out.append(r)
        ok &= r["worst_gap"] <= 1e-12
        print(f"{name:10s} {'dense ' if dense else 'sparse'}  {len(r['cells']):2d} cells  "
              f"worst gap {r['worst_gap']:.1e}  pooled vertices {r['pooled_vertices']}")
        for c in r["cells"]:
            if c["implementation"] == "baseline":
                print(f"    {c['curve']:4s} {c['metric']:17s} claimed {c['claimed']:>6s}   released {c['released']:.6f}")
(REPO / "build").mkdir(exist_ok=True)
(REPO / "build" / "prop2_witness.json").write_text(json.dumps(out, indent=2))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
