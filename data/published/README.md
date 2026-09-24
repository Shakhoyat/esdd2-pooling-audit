# Published tables that ship with this repository

## `esdd2_overview_table.csv`

The component-level equal error rates of the eleven ESDD2 systems that published
them, **test split**, transcribed from Table IV of the challenge overview:

> Xueping Zhang, Han Yin, Yang Xiao, Lin Zhang, Ting Dang, Rohan Kumar Das and
> Ming Li, "Overview of ESDD2: Environment-aware speech and sound deepfake
> detection challenge", Proc. IEEE ICMEW, 2026, arXiv:2606.10791v2.

Columns: `system`, `eer_env_test`, `eer_speech_test`, `is_reference_baseline`.

These are numbers reported in a paper, not corpus data, so they are transcribed
here rather than downloaded. They are the *only* input to the pairwise-ordering
result, which needs no per-clip data: given a published EER and the inapplicable
share, Theorem 2's interval follows in closed form.

**The inapplicable shares used with this table are the TEST-split shares**,
w0 = 0.52825 (environmental) and 0.39606 (speech). They are properties of the
corpus split, not of any system, and they are recorded in `paper_numbers.yaml`
with `tier: 0-published` because recomputing them would require the test labels,
which the paper does not use.

If you find a transcription error, it will show up as a `verify.py` failure on
`s2_max_gap_env`, `s2_max_gap_speech` or `s2_pairs_determined_*`.
