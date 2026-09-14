# The train/score consistency experiment (Section 4.3)

The claim: training the component heads on the mandated mapping -- supervising
them on inapplicable clips instead of masking those clips out of both losses --
lowers the *reported* environmental EER by about 0.20 while component-only
detection does not improve. What the heads acquire is the ability to recognise an
untouched capture, not the ability to detect a synthesised environment.

## Pre-registration

The arms, the predictions and the decision rule were written down **before the
runs**, in commit `8694d0c` of the authors' working repository. That repository
is private: it contains reviewer correspondence and draft material that is not
ours to publish. We are not asking you to take the timestamp on trust -- the
commit hash is recorded here so that it can be checked if the history is ever
opened, and the experiment itself is reproducible from the scripts in this
directory without reference to it.

What was pre-registered: two feature configurations (frozen BEATs layer 7 alone,
and layers 7-10 concatenated), three seeds each, two arms (**M**, the baseline's
mask; **C**, consistent with the mandated mapping), and four predictions about the
direction of the pooled value, the component-only value, the class-0 AUC and the
distance to the Proposition 3 fixed point.

## Running it

    python scripts/consistency_experiment/run.py --config layer7 --seeds 1337 1338 1339
    python scripts/consistency_experiment/analyse.py

Tier 1: needs the training audio and a GPU. The reported wall clock for all
twelve runs was 195 s on a single RTX A6000, after feature extraction.
