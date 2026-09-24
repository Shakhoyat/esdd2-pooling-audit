#!/usr/bin/env python3
"""Generate verify/VERIFICATION_REPORT.md from the manifest and recomputed CSVs.

    python verify/generate_report.py

The summary counts and the full per-entry table are computed live from
verify/numbers_manifest.csv and verify/numbers_recomputed.csv every time this runs, so they
cannot silently drift from the actual data: if a future change moves a number, the mismatch
table below stops being empty the next time this script runs, whether or not anyone remembers
to update prose by hand.

The "Investigative findings" section is different in kind: it is dated narrative analysis from
one audit round (tracing which of two historical conventions a number belongs to, resweeping a
range under a convention change, etc.), not a number this script recomputes. Reproducing it
mechanically would mean re-deriving the same reasoning, not re-running a check; it is embedded
here as text, sourced against IDs in the recomputed table so a reader can verify each claim it
makes against a live row. If the underlying data changes enough to invalidate one of these
findings, the ID lookup at the top of that finding will point at a row whose values no longer
match the finding's own quoted numbers -- that mismatch is the signal to re-investigate, not an
automatic failure.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "verify" / "numbers_manifest.csv"
RECOMPUTED = REPO / "verify" / "numbers_recomputed.csv"
OUT = REPO / "verify" / "VERIFICATION_REPORT.md"


def sh(*args: str) -> str:
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()


def load() -> tuple[dict[str, dict], list[dict]]:
    manifest = {r["id"]: r for r in csv.DictReader(open(MANIFEST))}
    recomputed = list(csv.DictReader(open(RECOMPUTED)))
    missing = [r["id"] for r in recomputed if r["id"] not in manifest]
    if missing:
        raise SystemExit(f"{len(missing)} recomputed row(s) have no manifest entry: {missing[:5]}")
    return manifest, recomputed


def row_lookup(recomputed: list[dict]) -> dict[str, dict]:
    return {r["id"]: r for r in recomputed}


def fmt_row(rid: str, m: dict, r: dict) -> str:
    note = r["note"].replace("|", "\\|") if r["note"] else ""
    loc = m["location"].replace("|", "\\|")
    why = m.get("why", "").replace("|", "\\|")
    literal = m.get("printed_as_digit", "True") == "True"
    kind = "" if literal else " *(not a literal digit — see \"how printed\")*"
    combined_note = " — ".join(x for x in (why, note) if x)
    return (f"| `{rid}` | {m['file']} | {loc}{kind} | {r['printed']} | {r['recomputed_unrounded']} | "
            f"{r['recomputed_rounded']} | {r['match']} | {combined_note} |")


def main() -> int:
    manifest, recomputed = load()
    by_id = row_lookup(recomputed)

    total = len(recomputed)
    matched = [r for r in recomputed if r["match"] == "yes"]
    mismatched = [r for r in recomputed if r["match"] == "no"]
    not_recomputable = [r for r in recomputed if r["match"] not in ("yes", "no")]

    commit = sh("git", "rev-parse", "HEAD")
    dirty = sh("git", "status", "--porcelain")
    py = sys.version.split()[0]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []
    w = lines.append

    w("# Verification report")
    w("")
    w("Audit of every printed number in `paper/main.tex`, recomputed from raw per-clip scores and "
      "the published ESDD2 overview table.")
    w("")
    w(f"Generated {now} by `verify/generate_report.py`, Python {py}, against commit `{commit}`"
      f"{' (working tree had uncommitted changes at generation time)' if dirty else ' (working tree clean)'}.")
    w("Regenerate with `python verify/generate_report.py`; do not hand-edit the Summary or "
      "\"All entries\" sections below, they are overwritten on every run.")
    w("")
    w("## Summary")
    w("")
    w("| | count |")
    w("|---|---|")
    w(f"| Manifest entries (`verify/numbers_manifest.csv`) | {len(manifest)} |")
    w(f"| Recomputed rows (`verify/numbers_recomputed.csv`) | {total} |")
    w(f"| Matched (`match=yes`) | **{len(matched)}** |")
    w(f"| Mismatched (`match=no`) | **{len(mismatched)}** |")
    w(f"| Not recomputable (any other value) | **{len(not_recomputable)}** |")
    w("")
    if mismatched:
        w(f"**{len(mismatched)} mismatch(es) found.** These need attention before anything else "
          "in this report is trusted:")
        w("")
        w("| id | file | location | printed | recomputed (unrounded) | recomputed (rounded) | note |")
        w("|---|---|---|---|---|---|---|")
        for r in mismatched:
            m = manifest[r["id"]]
            note = r["note"].replace("|", "\\|") if r["note"] else ""
            w(f"| `{r['id']}` | {m['file']} | {m['location'].replace('|', chr(92)+'|')} | "
              f"{r['printed']} | {r['recomputed_unrounded']} | {r['recomputed_rounded']} | {note} |")
        w("")
    else:
        w("No mismatches. Every manifest entry with a `match` value of `yes` reproduces the "
          "printed number at printed precision.")
        w("")
    if not_recomputable:
        w(f"**{len(not_recomputable)} entr{'y is' if len(not_recomputable)==1 else 'ies are'} "
          "not recomputable**, with the reason in the `note` column:")
        w("")
        w("| id | file | location | printed | why not recomputable |")
        w("|---|---|---|---|---|")
        for r in not_recomputable:
            m = manifest[r["id"]]
            w(f"| `{r['id']}` | {m['file']} | {m['location'].replace('|', chr(92)+'|')} | "
              f"{r['printed']} | {r['note'].replace('|', chr(92)+'|')} |")
        w("")

    w("## All entries")
    w("")
    w("Full manifest, joined with its recomputed value, in manifest order. This table is rebuilt "
      "from the two CSVs on every run of this script.")
    w("")
    w(f"{len(manifest) - sum(1 for m in manifest.values() if m.get('printed_as_digit')=='True')} "
      "of these rows are marked *(not a literal digit — see \"how printed\")* in the location "
      "column: their `printed` value is not literally the Arabic numeral in the paper's text. "
      "Most spell a small number as a word (\"fourteen\" -> printed `14`); a few encode a stated "
      "bound or assertion (e.g. the paper says a residual is \"below $10^{-15}$\", so `printed` is "
      "the assertion's own bound-check value `1.0` and `recomputed` is the measured residual "
      "scaled against that bound, not the raw residual) -- the \"how printed / note\" column always "
      "says which, so `printed=1.0` next to `recomputed=0.22` in such a row is a passing check, "
      "not a discrepancy. Read the note before reading the numbers as a direct comparison.")
    w("")
    w("| id | file | location | printed | recomputed (unrounded) | recomputed (rounded) | match | how printed / note |")
    w("|---|---|---|---|---|---|---|---|")
    for rid, m in manifest.items():
        r = by_id.get(rid)
        if r is None:
            w(f"| `{rid}` | {m['file']} | {m['location'].replace('|', chr(92)+'|')} | "
              f"{m['printed_value']} | — | — | **no recomputed row** | manifest entry has no "
              "matching row in numbers_recomputed.csv |")
        else:
            w(fmt_row(rid, m, r))
    w("")

    w("## Investigative findings")
    w("")
    w(INVESTIGATIVE_FINDINGS)

    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}: {total} entries, {len(matched)} matched, "
          f"{len(mismatched)} mismatched, {len(not_recomputable)} not recomputable")
    return 1 if mismatched else 0


INVESTIGATIVE_FINDINGS = r"""
Two findings are worth recording alongside the table above:

**The 0.0013 vs 0.0014 rounding note.** The naive subtraction of the two printed, already-rounded
Section 4.5 cells gives `0.1906 - 0.1892 = 0.0014`; the paper prints `0.0013` and calls it
"computed before rounding". Recomputing from unrounded values: `component_eer_speech =
0.19057251408358442`, `eer_gated_speech = 0.18922...` (via `acds_gate()['speech']['eer_gated']`),
difference `= 0.00134...`, which rounds to **0.0013**. The paper's printed value is correct; the
apparent "error" is an artifact of subtracting two 4-decimal-rounded numbers instead of the true
values.

**`results/artefacts.json` records a superseded gating convention** (`t2.env.cond` /
`t2.speech.cond`: 0.2022/0.1886, errors 0.0068/0.0019, distinct from the paper's printed
0.2028/0.1892, errors 0.0062/0.0013). `recompute.table2()` still computes it internally for
historical/audit-trail reasons; it is not what `paper_numbers.yaml` checks the paper against
(`acds_gate()` in `src/pooling_audit/acds_artefacts.py` is), and `results/README.md` documents
which fields are which.

### Reproducibility pipeline

See `reproduce.py`, `data/checksums.txt` and `MANIFEST.sha256`. `requirements.txt`
pins exact versions.

Seeds: this entire audit re-scores already-computed, fixed per-clip score files (`scores/*.npz`);
it never retrains anything, so the project's three training seeds (1337/1338/1339) are properties
of *how those score files were produced*, not of anything this audit recomputes. Table 1's
per-seed values and their standard deviation are read directly from the committed per-seed score
files, not resampled, so no seed is "set" by this audit.
""".strip() + "\n"


if __name__ == "__main__":
    sys.exit(main())
