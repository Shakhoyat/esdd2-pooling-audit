# Supplementary: the train/score consistency experiment

This experiment is **not reported in the paper**. It backs the remark in Section 4.3 that the
baseline masks Class 0 in both component losses, so its Class 0 outputs are unspecified.

The claim: training the component heads on the mandated mapping -- supervising
them on inapplicable clips instead of masking those clips out of both losses --
lowers the *reported* environmental EER by about 0.20 while component-only
detection does not improve. What the heads acquire is the ability to recognise an
untouched capture, not the ability to detect a synthesised environment.

## Pre-registration

The arms, the predictions and the decision rule were written down **before the
runs**, in commit `8694d0c` of the authors' development history, which is not public.
The experiment is reproducible from the scripts in this directory without reference
to it, and the per-clip scores of both arms ship in `scores/consistency/`.

What was pre-registered: two feature configurations (frozen BEATs layer 7 alone,
and layers 7-10 concatenated), three seeds each, two arms (**M**, the baseline's
mask; **C**, consistent with the mandated mapping), and four predictions about the
direction of the pooled value, the component-only value, the class-0 AUC and the
distance to the label-free fixed point (Section 2.3, "Post-hoc correction").

## Running it

    python scripts/consistency_experiment/run.py --config layer7 --seeds 1337 1338 1339
    python scripts/consistency_experiment/analyse.py

Tier 1: needs the training audio and a GPU. The reported wall clock for all
twelve runs was 195 s on a single RTX A6000, after feature extraction.
