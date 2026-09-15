"""Build gate over paper/main.tex. Run with `make gate`.

Fails if: a TODO survives; the word "development" appears (an earlier draft
mislabelled the evaluation split); a \\bibitem is never cited or a \\cite has no
\\bibitem; or the compiled PDF exceeds 5 pages or carries non-reference content
on page 5.

The page checks need a compiled PDF. Point ESDD2_PAPER_PDF at one, or put
spconf.sty in paper/ (it is not redistributed) and the gate compiles it.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.gate
REPO = Path(__file__).resolve().parents[1]
TEX = REPO / "paper" / "main.tex"
PAGE_LIMIT = 5


@pytest.fixture(scope="module")
def tex():
    if not TEX.exists():
        pytest.skip("paper/main.tex absent; run tools/sync_paper.py")
    return TEX.read_text()


def body(t):
    return t[t.index("\\begin{document}"):] if "\\begin{document}" in t else t


def test_no_TODO(tex):
    hits = [i + 1 for i, l in enumerate(tex.splitlines()) if "TODO" in l]
    assert not hits, f"TODO survives on paper/main.tex lines {hits}"


def test_no_development_split(tex):
    hits = [i + 1 for i, l in enumerate(tex.splitlines()) if re.search(r"\bdevelopment\b", l, re.I)]
    assert not hits, (f"'development' on lines {hits}: the paper's split is the evaluation split, "
                      "and an earlier draft mislabelled it")


def test_citations_resolve_both_ways(tex):
    cited = set()
    # the optional locator matters: \cite[Chs.~17--18]{aczel1989} must count as a citation
    for group in re.findall(r"\\cite[a-z]*(?:\[[^\]]*\])?\{([^}]*)\}", body(tex)):
        cited.update(k.strip() for k in group.split(","))
    items = set(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}", tex))
    assert not (cited - items), f"\\cite with no \\bibitem: {sorted(cited - items)}"
    assert not (items - cited), f"\\bibitem never cited: {sorted(items - cited)}"


@pytest.fixture(scope="module")
def pdf(tmp_path_factory):
    env = os.environ.get("ESDD2_PAPER_PDF")
    if env:
        return Path(env)
    if not (REPO / "paper" / "spconf.sty").exists():
        pytest.skip("no compiled PDF: set ESDD2_PAPER_PDF, or add spconf.sty to paper/")
    d = tmp_path_factory.mktemp("paper")
    for f in ("main.tex", "spconf.sty", "fig_pooling.pdf"):
        shutil.copy(REPO / "paper" / f, d / f)
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"], cwd=d,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return d / "main.pdf"


def pages_text(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    return [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), str(pdf), "-"],
                           capture_output=True, text=True).stdout for i in range(1, n + 1)]


def test_page_count(pdf):
    n = len(pages_text(pdf))
    assert n <= PAGE_LIMIT, f"compiled PDF is {n} pages; the limit is {PAGE_LIMIT} (4 content + 1 references)"


def test_page5_is_references_only(pdf):
    pages = pages_text(pdf)
    if len(pages) < PAGE_LIMIT:
        return
    p5 = pages[PAGE_LIMIT - 1]
    head = p5.upper().find("REFERENCES")
    ref_page = next((i for i, t in enumerate(pages) if "REFERENCES" in t.upper()), None)
    # the heading's own section number ("6. REFERENCES") is not body text
    before_heading = re.sub(r"\d+\.\s*$", "", p5[:head].strip()) if head != -1 else ""
    assert ref_page is not None and ref_page <= PAGE_LIMIT - 1 and (
        head == -1 or not before_heading or ref_page < PAGE_LIMIT - 1), \
        (f"page {PAGE_LIMIT} carries body text: the REFERENCES heading is on page "
         f"{None if ref_page is None else ref_page + 1}")


def test_citation_pattern_accepts_locators():
    """A \\cite with an optional locator is still a citation (regression: Chs. 17--18)."""
    t = r"\begin{document} see~\cite[\S6.4]{a} and \cite[Chs.~17--18]{b,c} \bibitem{a}\bibitem{b}\bibitem{c}"
    cited = set()
    for group in re.findall(r"\\cite[a-z]*(?:\[[^\]]*\])?\{([^}]*)\}", body(t)):
        cited.update(k.strip() for k in group.split(","))
    assert cited == {"a", "b", "c"}


def test_section_number_before_references_is_not_body_text():
    """Regression: a page 5 that starts with "6. REFERENCES" is references-only."""
    p5 = "6. REFERENCES\n[1] Lin Zhang, ..."
    head = p5.upper().find("REFERENCES")
    assert not re.sub(r"\d+\.\s*$", "", p5[:head].strip())
