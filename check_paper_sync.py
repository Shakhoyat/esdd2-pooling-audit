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
CITATION = re.compile(                                # [8], [2-4], [1, 5], [8, Chs. 17-18], [7, \u00a76.4]
    r"\[\d+(?:\s*[,\u2013-]\s*\d+)*(?:,\s*(?:\u00a7\s?[\d.]+|Chs?\.\s?[\d\u2013-]+|pp?\.\s?[\d\u2013-]+))?\]")
EXPONENT = re.compile(r"10\s?[\u2212-]\s?\d+")         # 10^-12 typeset as "10-12": a scale, not a claim
# Formula notation, each pattern for one typeset shape. These are the unit and
# exponent digits of the proofs and definitions, never a measured value; every
# pattern requires its operator context, so a bare "1" in prose is still caught.
MATH_NOTATION = [
    re.compile(r"(?<![\w.])1\s?\u2212"),                  # 1 - w0, 1 - gamma
    re.compile(r"\u2212\s?1(?![\w.])"),                   # g^-1, k^-1 (inverses)
    re.compile(r"[=<\u2264]\s?1(?![\w.])"),               # = 1, < 1, <= 1
    re.compile(r"\(\s?0,\s?1\)|\bmin 1,"),                 # (0, 1); min(1, ...)
    re.compile(r"\u222b\ufe01?\s?1"),                      # integral from 0 to 1
    re.compile(r"\)\s?2(?=\s[A-Z])"),                     # (1 - w)^2 D
    re.compile(r"(?<=\bI )4(?=\s?\.)"),                   # I^4
    re.compile(r"\u2265\s?12\s?[\})]"),                   # >= 1/2 } or ), the fraction typeset as "12"
]
SECTION_REF = re.compile(r"\u00a7\s?\d+(\.\d+)?")     # section 4.2
FIGTAB_REF = re.compile(r"(?:Fig\.|Figure|Table|Theorem|Proposition|Eq\.|Section)\s?\d+")
EQN_NUMBER = re.compile(r"\(\d\)")                    # equation (1), (2), (3)
SECTION_HEAD = re.compile(r"(?m)^\s*\d+(\.\d+)?\.\s|^\s*\d+\s+(?=[A-Z][a-z])")   # "4. RESULTS" (spconf) or "4 Passages" (article)

def pdf_text(pdf: Path) -> str:
    out = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"pdftotext failed on {pdf}")
    return out.stdout


def body_text(raw: str, start: str = "ABSTRACT") -> str:
    """From the abstract to the first bibliography entry.

    The title block carries affiliation marks and the bibliography carries volume and page
    numbers; neither is a claim. The end is the first "[1] " entry, not the REFERENCES
    heading: when a float or a column break reorders the text layer, body text can follow
    the heading, and cutting at the heading would silently drop it.
    """
    j = raw.upper().find(start.upper())
    m = re.search(r"(?m)^\[1\] ", raw)
    end = m.start() if m else len(raw)
    text = raw[max(j, 0):end]
    return re.sub(r"(?m)^\s*\d+\.\s+REFERENCES\s*$", " ", text)


INLINE_FRACTION = re.compile(r"(?<![\w./])(\d+)\s?/\s?(\d+)(?![\w/]|\.\d)")   # "3/11" as typeset inline
TFRAC = re.compile(r"\\tfrac\s*(\{\d+\}|\d)\s*(\{\d+\}|\d)")


def source_fractions(tex: str) -> set[str]:
    """Every \\tfrac literal in the LaTeX source, as "num/den"."""
    strip = lambda g: g.strip("{}")
    return {f"{strip(a)}/{strip(b)}" for a, b in TFRAC.findall(tex)}


def fraction_region(scan: str) -> tuple[int, int]:
    """Proposition 2's proof in the text layer, where stacked fractions come out as digit runs."""
    i = scan.find("Proof. Let A, B and S")
    if i < 0:
        return (0, 0)
    j = scan.find("Relation to prior work", i)
    return (i, j if j > 0 else i)


def explained_by_fractions(tok: str, fracs: set[str]) -> bool:
    digits = set()
    for f in fracs:
        n, d = f.split("/")
        digits |= {n, d, n + d, d + n}
    return tok in digits or tok in {"0", "1"}


def strip_structure(text: str) -> str:
    """Remove citation markers, cross-references and equation numbers."""
    text = SECTION_HEAD.sub(" ", text)
    for pat in (CITATION, SECTION_REF, FIGTAB_REF, EQN_NUMBER, EXPONENT, *MATH_NOTATION):
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
    ap.add_argument("--document", default="paper", choices=["paper", "extended"],
                    help="which document's entries direction (a) expects: the paper or PROOFS.pdf")
    ap.add_argument("--body-start", default="ABSTRACT",
                    help="text that marks where claims begin (PROOFS.pdf has no abstract)")
    ap.add_argument("--tex", type=Path, default=Path(__file__).parent / "paper" / "main.tex",
                    help="LaTeX source, for fractions the text layer cannot show")
    a = ap.parse_args()
    if not a.pdf.exists():
        raise SystemExit(f"not found: {a.pdf}")

    doc = yaml.safe_load(open(a.yaml))
    spec = doc["numbers"]
    literature = doc.get("meta", {}).get("literature_literals", []) if a.document == "paper" else []
    tex = a.tex.read_text() if a.tex.exists() else ""
    fracs = source_fractions(tex)
    raw = pdf_text(a.pdf)
    body = body_text(raw, a.body_start)
    flat = re.sub(r"\s+", " ", body)
    scan = re.sub(r"\s+", " ", strip_structure(body))

    # (a) YAML -> PDF
    missing = []
    for e in spec:
        if a.document not in e.get("document", ["paper"]):
            continue          # printed in the other document
        if e.get("printed") is False:
            continue          # a checked quantity the paper does not print as a digit
        v = e["value"]
        if isinstance(v, str) and "/" in v:
            # inline fractions are read from the text layer; a stacked \\tfrac only from the source
            in_text = any(f"{n}/{d}" == v for n, d in INLINE_FRACTION.findall(flat))
            if not (in_text or v in fracs):
                missing.append((e["id"], v, e["location"]))
            continue
        s = f"{v:.{e['precision']}f}" if isinstance(v, float) else str(v)
        s_plain = s.lstrip("-")
        # bounded on BOTH sides: "80" must not match inside "0.1580", nor "7" inside "0.7"
        pat = r"(?<![0-9.])" + re.escape(s_plain) + r"(?![0-9])"
        if not re.search(pat, flat):
            # integers may be typeset with a thousands separator
            alt = f"{int(v):,}" if isinstance(v, int) else None
            if not (alt and re.search(re.escape(alt), flat)):
                missing.append((e["id"], s, e["location"]))

    # (b) PDF -> YAML
    listed = set()
    for e in spec:
        v = e["value"]
        if isinstance(v, str):
            continue
        listed.add(f"{v:.{e['precision']}f}".lstrip("-") if isinstance(v, float) else str(v))
        if isinstance(v, int):
            listed.add(f"{v:,}")
    for lit in literature:                     # dates and counts that trace to a citation
        if lit["context"] not in flat:
            missing.append((lit["token"], lit["token"], f"literature: {lit['context']}"))
        listed.add(lit["token"])
    listed_fracs = {e["value"] for e in spec if isinstance(e["value"], str)}
    unlisted_fracs = fracs - listed_fracs
    # a listed inline fraction is one literal, not two integers; an unlisted one stays visible as its parts
    scan = INLINE_FRACTION.sub(lambda m: " " if f"{m.group(1)}/{m.group(2)}" in listed_fracs else m.group(0), scan)
    for f in sorted(unlisted_fracs):
        missing.append(("(unlisted fraction)", f, "\\tfrac in main.tex with no YAML entry"))
    r0, r1 = fraction_region(scan)
    unguarded = {}
    for m in re.finditer(r"(?<![\w.])(\d+\.\d+|\d{1,3}(?:,\d{3})+|\d+)(?![\w.])", scan):
        tok = m.group(1)
        if tok in listed:
            continue
        if r0 <= m.start() < r1 and explained_by_fractions(tok, fracs):
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
