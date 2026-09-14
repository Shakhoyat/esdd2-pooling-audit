#!/usr/bin/env python3
"""Write or check MANIFEST.sha256 over every tracked file.

A manifest that lists a zero-length file is a packaging bug, so --check fails on
one rather than reporting a matching hash for an empty file.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"


def tracked() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    return sorted(ROOT / line for line in out.stdout.split("\n")
                  if line and line != "MANIFEST.sha256")


def digest(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    files = tracked()

    if a.write:
        lines = []
        for p in files:
            if p.stat().st_size == 0:
                print(f"  REFUSING: {p.relative_to(ROOT)} is empty")
                return 1
            lines.append(f"{digest(p)}  {p.relative_to(ROOT)}  {p.stat().st_size}")
        MANIFEST.write_text("\n".join(lines) + "\n")
        print(f"  wrote {MANIFEST.name}: {len(lines)} files")

    if a.check:
        if not MANIFEST.exists():
            print("  no MANIFEST.sha256")
            return 1
        want = {}
        for line in MANIFEST.read_text().split("\n"):
            if not line.strip():
                continue
            h, rel, size = line.rsplit("  ", 2)
            want[rel] = (h, int(size))
        bad = 0
        seen = set()
        for p in files:
            rel = str(p.relative_to(ROOT))
            seen.add(rel)
            if rel not in want:
                print(f"  MISSING FROM MANIFEST: {rel}")
                bad += 1
                continue
            h, size = want[rel]
            if p.stat().st_size == 0:
                print(f"  EMPTY FILE: {rel}")
                bad += 1
            elif p.stat().st_size != size or digest(p) != h:
                print(f"  CHANGED: {rel}")
                bad += 1
        for rel in set(want) - seen:
            print(f"  IN MANIFEST BUT NOT TRACKED: {rel}")
            bad += 1
        print(f"  checked {len(files)} files, {bad} problem(s)")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
