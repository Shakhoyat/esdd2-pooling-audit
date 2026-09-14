# Data

**Nothing in this directory is redistributed corpus audio.** The repository ships
one file of numbers transcribed from a published table (`published/`); everything
else you download yourself, under the original terms.

## What `verify.py` needs

Put these under a directory of your choice and point `ESDD2_AUDIT_DATA` at it,
or place them in `data/local/` (which `.gitignore` excludes):

    eval_index.csv        one row per evaluation clip
                          filename,label_id,native_sr,native_channels,
                          env_clip_id,speech_clip_id
    baseline_scores.txt   the released ESDD2 baseline submission, pipe-separated
                          filename|pred_label|score_original|score_speech|score_env
    scores/<system>.npz   per-clip scores, see ../scores/README.md

## Terms, and why redistribution is limited

| artefact | terms | what we do |
|---|---|---|
| **CompSpoofV2 corpus** | **CC BY-NC 4.0**, access-gated on Hugging Face (you must accept the licence and be signed in). The authors state they do not claim ownership of the source audio and that users must also comply with the terms of each constituent corpus. | **Not redistributed.** Download it yourself; `tools/fetch_data.py` builds `eval_index.csv` from it and prints the checksum. |
| **ESDD2 baseline code** (`ESDD2-Baseline`) | **CC BY-NC 4.0**, stated in its README. No `LICENSE` file is present in the repository, only that README line. | **Not copied.** `src/pooling_audit/eer.py` is a reimplementation from the published description, with the original file and behaviour cited in its docstring. |
| **ESDD2 baseline submission** (`prediction.txt`) | Distributed inside that same CC BY-NC 4.0 repository, so the same terms apply. It is derived from the corpus. | **Not redistributed.** It comes with the baseline repository; its sha256 is in `checksums.txt`. |
| **Our own per-clip scores** | Ours to license, but they are *keyed by CompSpoofV2 clip identifiers* and are a derived work of a CC BY-NC corpus. | **Shipped** in `../scores/` under CC BY-NC 4.0 (`../LICENSE-DATA`), with CompSpoofV2 attribution required. |
| **Derived metadata** (`derived/`) | Anonymous cluster integers and native audio format per evaluation clip, derived from the corpus. | **Shipped** under CC BY-NC 4.0 (`../LICENSE-DATA`). See `derived/README.md`. |

**CC BY-NC 4.0 permits redistribution with attribution for non-commercial use.** On that basis
the authors decided to ship what is small, derived and needed for verification — our per-clip
scores and two anonymous metadata files — and not to ship the corpus or the baseline's scores, which
are theirs to distribute and sit behind an access gate. The corpus is itself assembled from other
corpora, and that obligation passes on to anyone using the derived files.

## Checksums

`checksums.txt` holds the sha256 of every file you download, as we used it: `eval_label.csv`,
`eval_source/metadata/eval.csv` and the baseline's `submission/prediction.txt`. Compare with
`sha256sum -c` from the directory that contains them. `tools/fetch_data.py --checksums` prints the
hashes of whatever is in your data root. The shipped files are covered by `../MANIFEST.sha256`, and
`../results/MANIFEST.json` records the hash of every input the committed results were built from.
