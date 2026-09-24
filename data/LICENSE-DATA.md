# Licence for the data in this repository

The MIT licence in `../LICENSE` covers the **code** only. The artefacts below are
model outputs derived from a non-commercially licensed corpus, and carry the
corpus's terms forward.

## What this covers

    scores/        our per-clip scores for every system and seed, and for both
                   arms of the supplementary consistency experiment
    data/derived/  anonymous cluster integers and native audio formats per
                   evaluation clip, derived from the corpus

## Licence

These are released under **Creative Commons Attribution-NonCommercial 4.0
International (CC BY-NC 4.0)**.

    https://creativecommons.org/licenses/by-nc/4.0/

You may share and adapt them for non-commercial purposes with attribution.

## Required attribution

These scores are derived from **CompSpoofV2**, released under CC BY-NC 4.0 by
Xueping Zhang and Ming Li:

> Xueping Zhang, Yechen Wang, Linxi Li, Liwei Jin and Ming Li, "CompSpoof: A
> dataset and joint learning framework for component-level audio anti-spoofing
> countermeasures", Proc. IEEE ICASSP, 2026.
> Dataset: https://huggingface.co/datasets/XuepingZhang/ESDD2-CompSpoof-V2

The corpus authors state that they do not claim ownership of the original audio
and that users must also comply with the terms of each constituent corpus. That
obligation passes to anyone using these derived scores.

## What is NOT here

The CompSpoofV2 audio and labels, and the ESDD2 baseline's `prediction.txt`, are
**not redistributed**. They are fetched by `tools/fetch_data.py`, which verifies
a sha256 for each file. See `README.md` in this directory.
