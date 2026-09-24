# Tier 1: regenerating the scores from audio

Tier 0 (`make verify`) needs none of this. Tier 1 exists so the per-clip scores
themselves can be reproduced rather than taken on trust.

## Status — read this before relying on it

| entry point | state |
|---|---|
| `extract_features.py` | **smoke-tested end to end.** 500 evaluation clips through frozen BEATs in 2.6 s on one RTX A6000 (191 clips/s), output shape (500, 13, 1536). |
| `train_probes.py` | **smoke-tested end to end.** `--smoke`: 250 train / 500 scored cached evaluation clips, 50 steps, seed 1337, in 1.8 s. |
| `../consistency_experiment/run.py` | **smoke-tested end to end.** `--smoke`: arms M and C, layer 7, seed 1337, 50 steps, in 1.5 s. |

"Smoke-tested" means the path runs and produces correctly shaped output on a
small subset. The two trainers are ports of the scripts that produced the paper's scores, with every
setting read from `configs/systems.yaml`; the smoke runs train on half of the 500 cached evaluation
clips, which exercises the code and reproduces nothing. It does **not** mean the paper's numbers were reproduced from
audio; they were not. The per-clip scores in `scores/` are the ones the paper
used, and tier 0 verifies every published number against them.

## Encoder code and weights are not vendored

BEATs itself is MIT-licensed (microsoft/unilm), so redistributing it would be
permitted, but its checkpoints come through third-party mirrors and the other
encoders carry their own terms. So the extractor imports from a checkout you
point it at:

    export ENCODER_SRC=/path/to/tree/containing/models/enc_beats.py
    export BEATS_CKPT=/path/to/BEATs_iter3_plus_AS2M.pt
    python scripts/train/extract_features.py --encoder beats --split eval --limit 500

Without those it exits with a message rather than a traceback.

## Layer selection is not re-run

Layers were chosen once on a generator holdout and are fixed in
`configs/systems.yaml`, which `verify.py` also checks the paper's layer
references against. A rerun reproduces the reported systems; it does not
reselect. BEATs 7-10, EAT 4-8, SSLAM 4-8, XLS-R 3-7, and for the two-encoder
probe BEATs 7-10 on the environmental axis with XLS-R 3-7 on the speech axis.
