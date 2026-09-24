#!/usr/bin/env python3
"""Copy the paper source into paper/, with comments and the embedded style file removed.

    python tools/sync_paper.py /path/to/authors/main.tex

The authors' working source carries internal provenance comments. This publishes
the paper, not those notes: full-line comments are deleted, and an inline comment
keeps its bare `%` but loses its text. Keeping that `%` matters -- in LaTeX a
trailing `%` suppresses the line-end space, so deleting it could change the
typeset output. `\\%` is a literal percent sign and is left alone.

The authors' single-file source embeds the ICASSP kit's spconf.sty in a
filecontents* block so that Overleaf needs nothing else. That file carries no
licence statement and is not redistributed here (paper/README.md), so the block is
removed: the published copy expects spconf.sty from the author kit beside it.

Afterwards it compiles both files and checks their text layers are identical, so
stripping comments cannot silently change the paper.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INLINE = re.compile(r"(?<!\\)%.*$")
EMBEDDED_STY = re.compile(r"\\begin\{filecontents\*?\}(\[[^\]]*\])?\{spconf\.sty\}.*?\\end\{filecontents\*?\}\n?", re.S)


def strip(tex: str) -> str:
    tex = EMBEDDED_STY.sub("", tex)
    out = []
    for line in tex.split("\n"):
        if re.match(r"^\s*%", line):
            continue
        out.append(INLINE.sub("%", line).rstrip() if INLINE.search(line) else line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def pdftext(tex: Path, workdir: Path) -> str:
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex.name], cwd=workdir,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pdf = workdir / tex.with_suffix(".pdf").name
    return subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    a = ap.parse_args()
    src = a.source.resolve()
    stripped = strip(src.read_text())
    (REPO / "paper").mkdir(exist_ok=True)
    (REPO / "paper" / "main.tex").write_text(stripped)
    print(f"  wrote paper/main.tex: {len(stripped.splitlines())} lines "
          f"(source {len(src.read_text().splitlines())})")

    # Assets the paper \includegraphics: taken by glob rather than by a hard-coded list, which
    # went stale the moment fig_pooling was replaced by the three current figures and left the
    # compile-equivalence check silently comparing two papers with a missing graphic.
    assets = ["spconf.sty"] + sorted(f.name for f in src.parent.glob("fig_*.pdf"))
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        for name in assets:
            if (src.parent / name).exists():
                shutil.copy(src.parent / name, d / name)
        if not (d / "spconf.sty").exists():
            print("  spconf.sty not beside the source; skipping the compile-equivalence check")
            return 0
        print(f"  assets copied for the check: {', '.join(assets)}")
        (d / "a").mkdir(); (d / "b").mkdir()
        for sub in ("a", "b"):
            for name in assets:
                if (d / name).exists():
                    shutil.copy(d / name, d / sub / name)
        shutil.copy(src, d / "a" / "main.tex")
        (d / "b" / "main.tex").write_text(stripped)
        ta, tb = pdftext(d / "a" / "main.tex", d / "a"), pdftext(d / "b" / "main.tex", d / "b")
        same = ta == tb
        print(f"  compile-equivalence: text layers {'IDENTICAL' if same else 'DIFFER'}")
        return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
