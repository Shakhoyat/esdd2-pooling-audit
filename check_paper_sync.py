#!/usr/bin/env python3
"""Check paper_numbers.yaml against the compiled PDF, in both directions.

    python check_paper_sync.py /path/to/main.pdf

Reports two lists:

  (a) YAML entries whose value does not appear in the PDF at all -- the YAML has
      drifted from the paper, or the paper changed a number.
  (b) numeric literals in the PDF with no YAML entry -- a number nobody is
      checking, which is how a stale value survives a revision.

Direction (b) is the one that matters: verify.py can only check what is listed,
so an unlisted literal is unguarded by construction.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

# Structure is stripped by CONTEXT rather than by ignoring digit ranges: a blanket
# "ignore small integers" rule would also hide a real claim that happens to be small.
CITATION = re.compile(r"\[[\d,\s\u2013-]+\]")        # [8], [2-4], [1, 5]
SECTION_REF = re.compile(r"\u00a7\s?\d+(\.\d+)?")     # section 4.2
FIGTAB_REF = re.compile(r"(?:Fig\.|Figure|Table|Theorem|Proposition|Eq\.)\s?\d+")
EQN_NUMBER = re.compile(r"\(\d\)")                    # equation (1), (2), (3)
SECTION_HEAD = re.compile(r"(?m)^\s*\d+(\.\d+)?\.\s")

def pdf_text(pdf: Path) -> str:
    out = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"pdftotext failed on {pdf}")
    return out.stdout


def body_text(raw: str) -> str:
    """Everything before the bibliography; reference entries are not claims."""
    i = raw.upper().rfind("REFERENCES")
    return raw[:i] if i > 0 else raw


def strip_structure(text: str) -> str:
    """Remove citation markers, cross-references and equation numbers."""
    text = SECTION_HEAD.sub(" ", text)
    for pat in (CITATION, SECTION_REF, FIGTAB_REF, EQN_NUMBER):
        text = pat.sub(" ", text)
    return text


def literals(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text)
    found = re.findall(r"(?<![\w.])(\d+\.\d+|\d{1,3}(?:,\d{3})+|\d+)(?![\w.])", flat)
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--yaml", type=Path,
                    default=Path(__file__).parent / "paper_numbers.yaml")
    a = ap.parse_args()
    if not a.pdf.exists():
        raise SystemExit(f"not found: {a.pdf}")

    spec = yaml.safe_load(open(a.yaml))["numbers"]
    raw = pdf_text(a.pdf)
    body = body_text(raw)
    flat = re.sub(r"\s+", " ", body)
    scan = re.sub(r"\s+", " ", strip_structure(body))

    # (a) YAML -> PDF
    missing = []
    for e in spec:
        if e.get("printed") is False:
            continue          # a checked quantity the paper does not print as a digit
        v = e["value"]
        s = f"{v:.{e['precision']}f}" if isinstance(v, float) else str(v)
        s_plain = s.lstrip("-")
        pat = re.escape(s_plain) + r"(?![0-9])"
        if not re.search(pat, flat):
            # integers may be typeset with a thousands separator
            alt = f"{int(v):,}" if isinstance(v, int) else None
            if not (alt and re.search(re.escape(alt), flat)):
                missing.append((e["id"], s, e["location"]))

    # (b) PDF -> YAML
    listed = set()
    for e in spec:
        v = e["value"]
        listed.add(f"{v:.{e['precision']}f}".lstrip("-") if isinstance(v, float) else str(v))
        if isinstance(v, int):
            listed.add(f"{v:,}")
    unguarded = {}
    for m in re.finditer(r"(?<![\w.])(\d+\.\d+|\d{1,3}(?:,\d{3})+|\d+)(?![\w.])", scan):
        tok = m.group(1)
        if tok in listed:
            continue
        if "." in tok and any(l.startswith(tok) or tok.startswith(l) for l in listed):
            continue
        ctx = scan[max(0, m.start() - 45):m.end() + 30].strip()
        unguarded.setdefault(tok, []).append(ctx)

    print(f"(a) YAML entries not found in the PDF: {len(missing)}")
    for rid, s, loc in missing:
        print(f"      {rid:<22}{s:>10}   {loc}")
    print(f"\n(b) PDF literals with no YAML entry: {len(unguarded)} distinct")
    for tok, ctxs in sorted(unguarded.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        print(f"      {tok:>8}  x{len(ctxs):<3} e.g. ...{ctxs[0]}...")

    if not missing and not unguarded:
        print("\n  in sync: every listed value appears, and every literal is listed")
    return 1 if (missing or unguarded) else 0


if __name__ == "__main__":
    sys.exit(main())
