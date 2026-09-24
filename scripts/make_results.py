#!/usr/bin/env python3
"""`make all`: regenerate every number, both tables and Figure 1, then record a manifest.

    python scripts/make_results.py [--split evaluation] [--draws 2000]

Writes, all under results/:
  artefacts.json      every recomputed value, in the namespace paper_numbers.yaml uses
  table1.tex          Table 1's body rows, formatted exactly as the paper typesets them
  fig_*.pdf           the three paper figures, also copied into paper/
  MANIFEST.json       git SHA, seeds, and sha256 of every input and every output

results/ is committed, so tests/test_claims.py can check the paper's numbers on a
clean checkout with nothing downloaded. The manifest is what stops those committed
results drifting from the inputs that produced them.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import numpy as np  # noqa: E402

from pooling_audit import data, recompute  # noqa: E402

RESULTS = REPO / "results"
# Table 1 is TRANSPOSED: one row per (alpha_0, t_max) setting, one column per system, in the
# order the paper prints them.
T1_COLUMNS = ["beats_linear", "eat_linear", "beats_attentive", "two_encoder", "reference"]
T1_ROWS = [("(0,1)", r"$(0,1)$"), ("(1,1)", r"$(1,1)$"),
           ("(0,0.2)", r"$(0,0.2)$"),
           ("(w0/wa,1)", r"$(w_0/\wa,1)$")]
FIGURES = ["fig_identified", "fig_acds_mechanism", "fig_accurve"]


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o


def table1_tex(acds: dict) -> str:
    """Table 1's body, formatted exactly as the paper typesets it.

    Larger is better, so the best cell in each ROW is bold and the second best underlined --
    the emphasis is generated from the numbers, not carried by hand, which is what stops the
    paper's bold cell and the recomputed maximum drifting apart.
    """
    rows = acds["rows"]
    out = []
    for setting, label in T1_ROWS:
        vals = [rows[c][setting] for c in T1_COLUMNS]
        order = sorted(range(len(vals)), key=lambda i: -vals[i])
        best, second = order[0], order[1]
        cells = []
        for i, v in enumerate(vals):
            s = f"{v:.4f}"
            if i == best:
                cells.append(f"$\\mathbf{{{s}}}$")
            elif i == second:
                cells.append(f"$\\underline{{{s}}}$")
            else:
                cells.append(f"${s}$")
        out.append(f"{label}                       & " + " & ".join(cells) + " \\\\")
    return "\n".join(out) + "\n"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="evaluation", choices=["validation", "evaluation", "test"])
    ap.add_argument("--draws", type=int, default=2000)
    a = ap.parse_args()
    if a.split != "evaluation":
        raise SystemExit(f"--split {a.split}: per-clip scores are released for the evaluation split only.")

    RESULTS.mkdir(exist_ok=True)
    t0 = time.time()
    art = recompute.all_artefacts(n_draws=a.draws)
    (RESULTS / "artefacts.json").write_text(json.dumps(_jsonable(art), indent=1, sort_keys=True))
    (RESULTS / "table1.tex").write_text(table1_tex(art["acds"]))

    for fig in FIGURES:
        subprocess.run([sys.executable, str(REPO / "scripts" / f"{fig}.py")], check=True,
                       stdout=subprocess.DEVNULL)
        shutil.copy(REPO / "build" / f"{fig}.pdf", RESULTS / f"{fig}.pdf")
        shutil.copy(REPO / "build" / f"{fig}.pdf", REPO / "paper" / f"{fig}.pdf")

    root = data.data_root()
    inputs = sorted([*(REPO / "scores").rglob("*.npz"), *(REPO / "data" / "derived").glob("*.csv"),
                     *(REPO / "data" / "published").glob("*.csv"), REPO / "configs" / "systems.yaml",
                     REPO / "paper_numbers.yaml",
                     root / "eval_index.csv", root / "baseline_scores.txt"])
    outputs = sorted(p for p in RESULTS.iterdir() if p.name != "MANIFEST.json")

    def rel(p):
        try:
            return str(p.relative_to(REPO))
        except ValueError:
            return f"<data root>/{p.name}"       # downloaded, not redistributed

    manifest = dict(
        git_sha=subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
                               text=True).stdout.strip(),
        split=a.split,
        seeds=dict(table2_clustered_bootstrap=1337, reference_step_bootstrap=1337,
                   probe_training=[1337, 1338, 1339]),
        table2_draws=a.draws, reference_step_draws=1000,
        inputs={rel(p): sha256(p) for p in inputs if p.exists()},
        outputs={rel(p): sha256(p) for p in outputs},
        wall_clock_seconds=round(time.time() - t0, 1),
    )
    (RESULTS / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
    print(f"  results/ written: {len(outputs)} outputs, {len(manifest['inputs'])} inputs hashed, "
          f"{manifest['wall_clock_seconds']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
