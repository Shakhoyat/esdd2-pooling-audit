# Our per-clip scores

One `.npz` per system, each holding

    filename      (n,)      clip identifiers, matching eval_index.csv
    seeds         (k,)      1337, 1338, 1339
    scores        (k, n, 3) [score_original, score_speech, score_env]
    predictions   (k, n)    the five-class argmax

Systems: `beats_linear`, `eat_linear`, `beats_attentive`, `two_encoder`,
`sslam_linear`, `xlsr_linear`. The first four are the probe rows of Table 1; the
last two appear only in Section 2's collapsibility check.

Both arms of the supplementary consistency experiment (not reported in the paper; see
`scripts/consistency_experiment/README.md`) are in `consistency/`: two frozen-BEATs
feature configurations (layer 7 alone, layers 7-10 concatenated), arms M and C, seeds 1337-1339,
twelve files, each holding `filename` and `scores` (n, 2) as [speech, env].

These are model outputs, not audio: about 21 MB in total. They are **keyed by CompSpoofV2 clip
identifiers** and derived from a CC BY-NC 4.0 corpus, so they are released under **CC BY-NC 4.0**
(`../data/LICENSE-DATA.md`) with CompSpoofV2 attribution required. Their sha256 are in `../MANIFEST.sha256`.
