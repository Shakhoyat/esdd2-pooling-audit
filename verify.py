#!/usr/bin/env python3
"""Recompute every number the paper prints, and compare at its printed precision.

    python verify.py                 # all tier-0 entries
    python verify.py --draws 200     # faster bootstrap, for a smoke run
    python verify.py --only t2       # entries whose id starts with t2

Exits non-zero if any checkable entry disagrees with the paper.

By design this reads ONLY per-clip scores, the evaluation index and the
published table that ships with the repository. It never reads a cached result
from the authors' working tree; if it did, it would be checking our bookkeeping
rather than our arithmetic.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


from pooling_audit import recompute  # noqa: E402

from pooling_audit.claims import CHECKABLE, compare, load_spec, resolve  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="evaluation", choices=["validation", "evaluation", "test"],
                    help="per-clip scores are released for the evaluation split only")
    ap.add_argument("--draws", type=int, default=2000,
                    help="bootstrap resamples for Table 2 (paper uses 2000)")
    ap.add_argument("--only", default=None, help="only ids starting with this prefix")
    args = ap.parse_args()
    if args.split != "evaluation":
        raise SystemExit(f"--split {args.split}: the paper reports the evaluation split, and "
                         "per-clip scores are released for that split only.")

    spec = load_spec()
    entries = spec["numbers"]
    if args.only:
        entries = [e for e in entries if e["id"].startswith(args.only)]

    t0 = time.time()
    print("recomputing from per-clip scores ...", flush=True)
    art = recompute.all_artefacts(n_draws=args.draws)
    print(f"  done in {time.time() - t0:.1f}s\n", flush=True)

    rows, npass, nfail, nskip = [], 0, 0, 0
    for e in entries:
        tier, key = e["tier"], e.get("key")
        if tier not in CHECKABLE or not key:
            rows.append((e["id"], e["value"], "-", "SKIP",
                         e.get("why", f"tier {tier}")))
            nskip += 1
            continue
        try:
            got = resolve(art, key)
        except Exception as exc:                       # noqa: BLE001
            rows.append((e["id"], e["value"], "-", "FAIL", f"key error: {exc}"))
            nfail += 1
            continue
        if got is None:
            rows.append((e["id"], e["value"], "-", "SKIP",
                         e.get("why", "input not present")))
            nskip += 1
            continue
        ok, shown, how = compare(e, got)
        note = e["location"] + ("" if how.startswith("equal") else f"  ({how})")
        rows.append((e["id"], e["value"], shown, "PASS" if ok else "FAIL", note))
        npass += ok
        nfail += (not ok)

    w = max(len(r[0]) for r in rows) + 1
    print(f"{'id':<{w}}{'paper':>10}{'recomputed':>13}  {'':6}note")
    print("-" * (w + 33))
    for rid, want, got, status, note in rows:
        mark = {"PASS": "ok  ", "FAIL": "FAIL", "SKIP": "skip"}[status]
        print(f"{rid:<{w}}{str(want):>10}{got:>13}  {mark}  {note}")

    total = len(entries)
    print(f"\n  {npass}/{total} verified   {nfail} failed   {nskip} not checked")
    print(f"  wall clock {time.time() - t0:.1f}s")
    if nfail:
        print("\n  FAILED. A recomputed value disagrees with the paper.")
    return 1 if nfail else 0


if __name__ == "__main__":
    raise SystemExit(main())
