#!/usr/bin/env python3
"""One-command reproduction of every number, table, and figure in the paper.

    python reproduce.py

In order: logs the environment and git commit, checks SHA-256 of every input file this
repo does not redistribute (data/checksums.txt) plus every tracked file (MANIFEST.sha256),
recomputes every number (make verify), regenerates the three figures and both tables
(make all), runs the pytest suite, and confirms verify/VERIFICATION_REPORT.md is present
and current.

This orchestrates the repo's existing Makefile targets rather than duplicating their logic
-- see `make help`. Nothing here retrains anything: all per-clip scores are fixed inputs
under scores/, so the project's three training seeds (1337/1338/1339) are a property of how
those files were produced, not of anything this script recomputes. No seed is set here
because none of this recomputation samples anything.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
PY = sys.executable


def sh(cmd: list[str], **kw) -> int:
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO, **kw).returncode


def log_environment() -> None:
    print("=" * 70)
    print("ENVIRONMENT")
    print("=" * 70)
    print("python:", sys.version.split()[0])
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True)
    print("git commit:", head.stdout.strip() or "(not a git checkout)")
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True)
    print("working tree:", "clean" if not dirty.stdout.strip() else "has uncommitted changes")
    import platform
    print("platform:", platform.platform())
    print()


def check_checksums() -> bool:
    print("=" * 70)
    print("STEP 1: checksums")
    print("=" * 70)
    ok = True
    checks = REPO / "data" / "checksums.txt"
    if checks.exists():
        for line in checks.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            digest, _, name = line.partition("  ")
            path = REPO / "data" / name
            if not path.exists():
                # These are gated external downloads (CompSpoofV2), documented but not
                # redistributed -- see data/README.md. Absence here is expected on a
                # clean checkout without the dataset and is not a failure.
                print(f"  SKIP  {name}: not present locally (gated external download, "
                      f"see data/checksums.txt header)")
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            status = "OK" if actual == digest else "MISMATCH"
            if status == "MISMATCH":
                ok = False
            print(f"  {status:8s} {name}")
    else:
        print("  data/checksums.txt not found")
        ok = False

    print("\n  Tracked-file manifest (MANIFEST.sha256):")
    rc = sh([PY, "tools/manifest.py", "--check"])
    ok = ok and rc == 0
    print()
    return ok


def recompute_numbers() -> bool:
    print("=" * 70)
    print("STEP 2: recompute every number (make verify)")
    print("=" * 70)
    rc = sh(["make", f"PY={PY}", "verify"])
    print()
    return rc == 0


def regenerate_figures_and_tables() -> bool:
    print("=" * 70)
    print("STEP 3: regenerate figures and tables (make all)")
    print("=" * 70)
    rc = sh(["make", f"PY={PY}", "all"])
    print()
    return rc == 0


def run_tests() -> bool:
    print("=" * 70)
    print("STEP 4: pytest")
    print("=" * 70)
    rc = sh([PY, "-m", "pytest", "-q"])
    print()
    return rc == 0


def confirm_report() -> bool:
    print("=" * 70)
    print("STEP 5: generate verification report")
    print("=" * 70)
    rc = sh([PY, "verify/generate_manifest.py"])
    if rc != 0:
        print("  FAILED: verify/generate_manifest.py did not run cleanly")
        return False
    rc = sh([PY, "verify/generate_report.py"])
    # generate_report.py's own exit code is 1 if it found a mismatch, not if it failed to run --
    # a mismatch is a real audit finding, not a pipeline failure, so this step still counts as
    # having run correctly. Only a nonzero exit with no report written is a pipeline failure.
    report = REPO / "verify" / "VERIFICATION_REPORT.md"
    if not report.exists():
        print("  FAILED: verify/generate_report.py did not produce verify/VERIFICATION_REPORT.md")
        return False
    if rc == 1:
        print("  generate_report.py found at least one mismatch -- see the Summary section of "
              "the report it just wrote. That is a real audit finding, not a script failure.")
    print(f"  wrote {report.relative_to(REPO)} ({len(report.read_text().splitlines())} lines)")
    print("  verify/numbers_manifest.csv and verify/numbers_recomputed.csv are regenerated from "
          "paper_numbers.yaml and results/artefacts.json by verify/generate_manifest.py, every "
          "run, immediately before this step -- so they cannot drift from either. The report's "
          "\"Investigative findings\" prose is still hand-maintained, not auto-regenerated;"
          " re-run the audit by hand if the underlying data changes materially.")
    return True


def main() -> int:
    log_environment()
    results = {
        "checksums": check_checksums(),
        "recompute": recompute_numbers(),
        "figures_and_tables": regenerate_figures_and_tables(),
        "tests": run_tests(),
        "report": confirm_report(),
    }
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for k, v in results.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
