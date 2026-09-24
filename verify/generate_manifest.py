#!/usr/bin/env python3
"""Regenerate numbers_manifest.csv and numbers_recomputed.csv from paper_numbers.yaml.

    python verify/generate_manifest.py

Both CSVs used to be hand-maintained, and the script that originally produced them was lost in an
earlier audit round (see reproduce.py's STEP 5 comment) -- a change to paper_numbers.yaml or to
results/artefacts.json could then drift from the CSVs without anything catching it. This closes
that gap: both files are derived, every run, from the same paper_numbers.yaml and
results/artefacts.json that tests/test_claims.py and verify.py already check against, using the
same pooling_audit.claims.resolve/compare so the three can never disagree about what counts as a
match.
"""
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from pooling_audit.claims import compare, load_spec, resolve  # noqa: E402

MANIFEST_FIELDS = ["id", "file", "location", "printed_value", "precision", "tier", "key",
                   "printed_as_digit", "why"]
RECOMPUTED_FIELDS = ["id", "printed", "recomputed_unrounded", "recomputed_rounded", "match", "note"]


def printed_str(entry: dict) -> str:
    v = entry["value"]
    if isinstance(v, str):
        return v
    p = entry["precision"]
    return f"{v:.{p}f}" if isinstance(v, float) else str(v)


def main() -> int:
    spec = load_spec()
    entries = spec["numbers"]
    artefacts_path = REPO / "results" / "artefacts.json"
    artefacts = json.loads(artefacts_path.read_text()) if artefacts_path.exists() else None

    with open(REPO / "verify" / "numbers_manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        for e in entries:
            w.writerow(dict(
                id=e["id"], file="paper/main.tex", location=e["location"],
                printed_value=printed_str(e), precision=e["precision"], tier=e["tier"],
                key=e.get("key", ""), printed_as_digit=str(e.get("printed", True) is not False),
                why=e.get("why", "")))

    with open(REPO / "verify" / "numbers_recomputed.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RECOMPUTED_FIELDS)
        w.writeheader()
        for e in entries:
            printed = printed_str(e)
            if artefacts is None or not e.get("key"):
                w.writerow(dict(id=e["id"], printed=printed, recomputed_unrounded="",
                                recomputed_rounded="", match="not checked",
                                note="results/artefacts.json absent; run `make all`"
                                     if artefacts is None else "no key to recompute from"))
                continue
            try:
                got = resolve(artefacts, e["key"])
            except KeyError as exc:
                w.writerow(dict(id=e["id"], printed=printed, recomputed_unrounded="",
                                recomputed_rounded="", match="not checked", note=str(exc)))
                continue
            if got is None:
                w.writerow(dict(id=e["id"], printed=printed, recomputed_unrounded="",
                                recomputed_rounded="", match="not checked",
                                note=e.get("why", "input not present when results were built")))
                continue
            ok, shown, how = compare(e, got)
            unrounded = str(got) if isinstance(e["value"], str) else repr(float(got))
            w.writerow(dict(id=e["id"], printed=printed, recomputed_unrounded=unrounded,
                            recomputed_rounded=shown, match="yes" if ok else "no", note=how))

    print(f"  wrote {len(entries)} rows to verify/numbers_manifest.csv and "
          f"verify/numbers_recomputed.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
