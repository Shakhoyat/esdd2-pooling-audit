PY ?= python
DRAWS ?= 2000
SPLIT ?= evaluation

.PHONY: help all verify test gate figures sync-paper manifest regenerate clean

help:
	@echo "make all         regenerate every number, both tables (.tex) and Figure 1 into results/"
	@echo "make verify      recompute every number from per-clip scores and compare to the paper"
	@echo "make test        the paper's numbers against committed results, plus unit tests (no data)"
	@echo "make gate        submission readiness: TODO, 'development', citations, page budget"
	@echo "make figures     Figure 1 into build/"
	@echo "make sync-paper  refresh paper/main.tex from the authors' source (SRC=path)"
	@echo "make manifest    rewrite and check MANIFEST.sha256 over every tracked file"
	@echo "make regenerate  tier 1, GPU: re-extract features and retrain the probes"

all:
	$(PY) scripts/make_results.py --split $(SPLIT) --draws $(DRAWS)
	cp results/fig_pooling.pdf paper/fig_pooling.pdf

verify:
	$(PY) verify.py --split $(SPLIT) --draws $(DRAWS)

test:
	$(PY) -m pytest

gate:
	$(PY) -m pytest -m gate

figures:
	$(PY) scripts/fig1.py

sync-paper:
	@test -n "$(SRC)" || (echo "usage: make sync-paper SRC=/path/to/main.tex" && false)
	$(PY) tools/sync_paper.py $(SRC)

manifest:
	@echo "Staging first: the manifest hashes TRACKED files, so anything not yet"
	@echo "added would be missing from it."
	git add -A
	$(PY) tools/manifest.py --write
	git add MANIFEST.sha256
	$(PY) tools/manifest.py --check

regenerate:
	@echo "Tier 1 needs the CompSpoofV2 audio and a GPU. See scripts/train/README.md."
	$(PY) scripts/train/extract_features.py --split train
	$(PY) scripts/train/train_probes.py --seeds 1337 1338 1339

clean:
	rm -rf build .pytest_cache src/pooling_audit/__pycache__ tests/__pycache__ scripts/__pycache__
