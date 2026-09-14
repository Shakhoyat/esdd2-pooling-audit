"""The paper's numbers, one test per claim, named after where each claim appears.

These read the COMMITTED results/artefacts.json, so they run on a clean checkout
with nothing downloaded. verify.py is the other half: it recomputes those results
from per-clip scores. test_results_match_manifest stops the two drifting apart.

A failing test names the paper location and prints expected against actual.
"""
import hashlib
import json
import re
from pathlib import Path

import pytest

from pooling_audit.claims import CHECKABLE, compare, load_spec, resolve

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
SPEC = load_spec()
ENTRIES = [e for e in SPEC["numbers"] if e["tier"] in CHECKABLE and e.get("key")]


def _slug(e):
    loc = e["location"].replace("§", "sec")
    loc = re.sub(r"[^A-Za-z0-9]+", "_", loc).strip("_")
    return f"{loc}__{e['id']}"


@pytest.fixture(scope="session")
def artefacts():
    p = RESULTS / "artefacts.json"
    if not p.exists():
        pytest.skip("results/artefacts.json absent; run `make all`")
    return json.loads(p.read_text())


@pytest.mark.parametrize("entry", ENTRIES, ids=[_slug(e) for e in ENTRIES])
def test_claim(entry, artefacts):
    got = resolve(artefacts, entry["key"])
    if got is None:
        pytest.skip(f"{entry['location']}: input not present when results were built "
                    f"({entry.get('why', 'see paper_numbers.yaml')})")
    ok, shown, how = compare(entry, got)
    assert ok, (f"\n  paper location : {entry['location']}"
                f"\n  paper prints   : {entry['value']}"
                f"\n  recomputed     : {shown}   ({how})"
                f"\n  key            : {entry['key']}")


@pytest.mark.parametrize("name", ["table1.tex", "table2.tex"])
def test_table_rows_are_verbatim_in_the_paper(name):
    """Every generated table row must appear, character for character, in paper/main.tex."""
    frag, paper = RESULTS / name, REPO / "paper" / "main.tex"
    if not frag.exists() or not paper.exists():
        pytest.skip("results or paper/main.tex absent")
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    body = norm(paper.read_text())
    missing = [row for row in frag.read_text().splitlines() if row.strip() and norm(row) not in body]
    assert not missing, "rows generated from the scores that the paper does not contain:\n  " + \
        "\n  ".join(missing)


def test_results_match_manifest():
    """Committed results must be the bytes the recorded run produced."""
    m = RESULTS / "MANIFEST.json"
    if not m.exists():
        pytest.skip("results/MANIFEST.json absent; run `make all`")
    manifest = json.loads(m.read_text())
    bad = []
    for rel, want in manifest["outputs"].items():
        p = REPO / rel
        got = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        if got != want:
            bad.append(rel)
    assert not bad, f"results differ from MANIFEST.json (rerun `make all`): {bad}"


def test_every_yaml_entry_is_checked():
    """Nothing in paper_numbers.yaml may sit outside the checkable tiers."""
    unchecked = [e["id"] for e in SPEC["numbers"] if e["tier"] not in CHECKABLE or not e.get("key")]
    assert not unchecked, f"entries no test checks: {unchecked}"
