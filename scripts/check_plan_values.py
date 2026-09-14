#!/usr/bin/env python3
"""Check the three logits and the baseline table we quote from the ESDD2 plan.

The paper quotes the evaluation plan's worked example (1.22, -1.54, -1.89) as
evidence that unbounded logits are within the rules, and quotes the baseline's
published EERs. Both are other people's numbers, so this downloads the plan and
checks we transcribed them correctly rather than asserting we did.

    python scripts/check_plan_values.py            # uses a cached copy if present
    python scripts/check_plan_values.py --refresh  # re-download

Needs network on first run. Writes the extracted text to build/esdd2_plan.txt.
"""
import argparse
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ARXIV = "https://arxiv.org/pdf/2601.07303v5"
ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

WANT_LOGITS = ["1.22", "-1.54", "-1.89"]
WANT_TABLE = {"eval speech EER": "0.1993", "eval env EER": "0.4336",
              "test env EER": "0.4279"}


def fetch(refresh: bool) -> str:
    BUILD.mkdir(exist_ok=True)
    txt, pdf = BUILD / "esdd2_plan.txt", BUILD / "esdd2_plan.pdf"
    if txt.exists() and not refresh:
        return txt.read_text(errors="replace")
    if not pdf.exists() or refresh:
        print(f"  downloading {ARXIV}")
        req = urllib.request.Request(ARXIV, headers={"User-Agent": "esdd2-pooling-audit"})
        pdf.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    subprocess.run(["pdftotext", str(pdf), str(txt)], check=True)
    return txt.read_text(errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    try:
        text = fetch(a.refresh)
    except Exception as exc:                        # noqa: BLE001
        print(f"  could not fetch the plan: {exc}")
        print("  These three literals stay unchecked without network access.")
        return 2

    flat = re.sub(r"\s+", " ", text)
    bad = 0
    print("worked example, submission format section:")
    for v in WANT_LOGITS:
        hit = re.search(re.escape(v) + r"(?![0-9])", flat) is not None
        print(f"  {v:>7}  {'found' if hit else 'NOT FOUND'}")
        bad += not hit
    print("baseline table:")
    for label, v in WANT_TABLE.items():
        hit = re.search(re.escape(v) + r"(?![0-9])", flat) is not None
        print(f"  {label:<18}{v:>8}  {'found' if hit else 'NOT FOUND'}")
        bad += not hit
    print(f"\n  {bad} value(s) not found in the plan")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
