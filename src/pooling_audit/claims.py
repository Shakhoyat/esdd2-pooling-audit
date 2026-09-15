"""Compare a recomputed value against what the paper prints.

Shared by verify.py (recomputes from per-clip scores) and tests/test_claims.py
(checks the committed results/artefacts.json), so the two can never disagree about
what counts as a match.
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
CHECKABLE = {0, "0", "0-published"}


def load_spec() -> dict:
    return yaml.safe_load(open(REPO / "paper_numbers.yaml"))


def resolve(art: dict, dotted: str):
    """Walk a dotted path, tolerating dict keys that themselves contain dots (e.g. '0.5')."""
    node, rest = art, dotted
    while rest:
        if isinstance(node, (list, tuple)):
            head, _, rest = rest.partition(".")
            node = node[int(head)]
            continue
        if not isinstance(node, dict):
            raise KeyError(dotted)
        for cand in sorted(node.keys(), key=lambda k: -len(str(k))):
            c = str(cand)
            if rest == c:
                return node[cand]
            if rest.startswith(c + "."):
                node, rest = node[cand], rest[len(c) + 1:]
                break
        else:
            raise KeyError(f"{dotted} (stuck at {rest!r})")
    return node


def compare(entry: dict, got) -> tuple[bool, str, str]:
    """Return (ok, recomputed-as-printed, how it was compared)."""
    if isinstance(entry["value"], str) and "/" in entry["value"]:
        from fractions import Fraction
        return Fraction(str(got)) == Fraction(entry["value"]), str(got), "exact fraction"
    p = entry["precision"]
    got_f = float(got)
    shown = f"{round(got_f, p):.{p}f}"
    mode = entry.get("compare")
    if mode in ("bound_below", "bound_above"):
        # the paper states an upper bound: "at machine precision", "within x"
        return got_f <= float(entry["value"]) * (1 + 1e-9), shown, "upper bound"
    if mode == "bound_above_reversed":
        # the paper states a lower bound: "at least x"
        return got_f >= float(entry["value"]) * (1 - 1e-9), shown, "lower bound"
    want = round(float(entry["value"]), p)
    return abs(round(got_f, p) - want) < 0.5 * 10 ** (-p), shown, f"equal at {p} dp"
