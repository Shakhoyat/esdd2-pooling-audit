# Derived metadata

Two small files that let `verify.py` run without the corpus's large archives.
Both are **derived from CompSpoofV2** and are covered by `../../LICENSE-DATA`
(CC BY-NC 4.0, with the CompSpoofV2 attribution required there), not by the MIT
licence that covers the code.

| file | size | derived from | replaces |
|---|---|---|---|
| `clusters.csv` | 1.4 MB | `eval_source/metadata/eval.csv` | `eval_source.tar.gz`, 10.9 GB |
| `native_format.csv` | 1.3 MB | the evaluation audio headers | `eval.tar.gz`, 5.0 GB |

## What is in them, and what is not

`clusters.csv` is `filename, env_cluster, speech_cluster` where the two cluster
columns are **anonymous integers**, numbered by order of first appearance. They
carry **no source file names, no corpus names, no generator names** — nothing
beyond "these two clips share an environmental source". That is all the clustered
bootstrap needs, and it is deliberately all that is here.

`native_format.csv` is `filename, native_sr, native_channels`: two technical
integers per clip, read from the audio headers. Neither file lets anyone
reconstruct audio.

## Regenerating them, and checking ours

If you have the archives, rebuild both and compare:

```bash
python tools/derive_metadata.py --from-local /path/to/CompSpoofV2 --write
sha256sum build/derived/*.csv
grep derived MANIFEST.sha256        # what we shipped
```

The hashes should match byte for byte. If they do not, the corpus release has
changed under us and `verify.py` will say so on the entries that depend on these
files.

## How `verify.py` uses them

`load_index()` fills blank columns from here. Columns already present in your
`eval_index.csv` always win, so building the index from the full archives
overrides these files rather than being overridden by them.
