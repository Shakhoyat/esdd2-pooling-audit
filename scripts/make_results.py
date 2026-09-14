#!/usr/bin/env python3
"""`make all`: regenerate every number, both tables and Figure 1, then record a manifest.

    python scripts/make_results.py [--split evaluation] [--draws 2000]

Writes, all under results/:
  artefacts.json      every recomputed value, in the namespace paper_numbers.yaml uses
  table1.tex          Table 1's body rows, formatted exactly as the paper typesets them
  table2.tex          Table 2's body rows, likewise
  fig_pooling.pdf     Figure 1
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
T1_ORDER = [("beats_linear", "BEATs probe   "), ("eat_linear", "EAT probe     "),
            ("beats_attentive", "attentive head"), ("two_encoder", "two-encoder   "),
            ("reference", "reference     ")]


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


def cell(x, bold=False):
    s = f"{x:.4f}"
    return f"$\\mathbf{{{s}}}$" if bold else f"${s}$"


def table1_tex(t1: dict) -> str:
    rows = t1["rows"]
    top = max(rows, key=lambda k: rows[k]["spread"])
    out = []
    for key, label in T1_ORDER:
        r = rows[key]
        m = r["mean"]
        out.append(f"{label} & {cell(m['0'])} & {cell(m['0.5'])} & {cell(m['prior'])} & "
                   f"{cell(r['spread'], bold=key == top)} & {cell(r['component_only'])} \\\\")
    return "\n".join(out) + "\n"


def table2_tex(t2: dict) -> str:
    out = []
    for axis, label in (("env", "environment"), ("speech", "speech     ")):
        d = t2[axis]
        out.append(f"{label} & {cell(d['pooled'])} & {cell(d['cond'])} & {cell(d['comp'])} & "
                   f"{cell(d['err_pooled'])} & {cell(d['err_cond'], bold=True)} \\\\")
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
    (RESULTS / "table1.tex").write_text(table1_tex(art["t1"]))
    (RESULTS / "table2.tex").write_text(table2_tex(art["t2"]))

    subprocess.run([sys.executable, str(REPO / "scripts" / "fig1.py")], check=True,
                   stdout=subprocess.DEVNULL)
    shutil.copy(REPO / "build" / "fig_pooling.pdf", RESULTS / "fig_pooling.pdf")

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
