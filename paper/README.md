# Paper source

`main.tex` is the submitted paper's source with the authors' internal comments
removed. It is **generated** — do not edit it here:

```bash
python tools/sync_paper.py /path/to/authors/main.tex
```

That script deletes every comment's text but keeps each inline `%`, because in
LaTeX a trailing `%` suppresses a line-end space and removing it could change the
typeset output. It then compiles both the source and the stripped copy and checks
that their text layers are identical.

`fig_pooling.pdf` is Figure 1, copied from `results/` after `make all`. It is
pixel-identical to the figure in the submitted PDF.

## To compile

`spconf.sty` is **not** included. It is the IEEE ICASSP author-kit style file and
carries no licence statement, so it is not ours to redistribute. Get it from the
ICASSP 2027 author kit, place it here, then:

```bash
cd paper && pdflatex main.tex && pdflatex main.tex
```

The references are inlined in `main.tex`, so no BibTeX run is needed.

Figures and the paper text are covered by `../LICENSE-DATA` (CC BY-NC 4.0),
because they are derived from CompSpoofV2; the code is MIT.
