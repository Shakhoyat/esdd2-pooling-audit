# Encoder checkpoints

**No weights are vendored here.** Each encoder is fetched from its published
source and verified against the sha256 below — the same bytes the paper's scores
were produced from.

    python models/fetch_encoders.py            # all four
    python models/fetch_encoders.py --only beats
    python models/fetch_encoders.py --verify   # hash what is already present

Tier 0 (`make verify`) needs none of this. Only tier 1 does.

## What the paper used

| encoder | file | size | sha256 |
|---|---|---|---|
| **BEATs** iter3+ AS2M | `BEATs_iter3_plus_AS2M.pt` | 345 MB | `d43cbfad4d7b56381c061d7a24774f908d4d94c72961f6eb1d9090ff18cd8d34` |
| **SSLAM** pretrain | `model.safetensors` | 344 MB | `8ec670adb241c710422ddd894ff1bade142ef0b25cf1ee68577aa45f89432298` |
| **EAT** base epoch30 pretrain | `model.safetensors` | 344 MB | `8623072d09aac4f3ad1168b4fed3a24e4f68fe1da25b9fe733375efb237e5f48` |
| **XLS-R** 300m | `pytorch_model.bin` | 1.2 GB | `d5e490574712ad0a6736923b9ed11d4cd51c78609c36205f704fc4e87b11d2e0` |

Sources:

| encoder | repository |
|---|---|
| BEATs | `https://huggingface.co/lpepino/beats_ckpts` |
| SSLAM | `https://huggingface.co/ta012/SSLAM_pretrain` |
| EAT | `https://huggingface.co/worstchan/EAT-base_epoch30_pretrain` |
| XLS-R | `https://huggingface.co/facebook/wav2vec2-xls-r-300m` |

## Two things worth knowing before you trust these

**BEATs is a third-party mirror.** Microsoft publishes the original BEATs
checkpoints on OneDrive, which is not scriptable, so `lpepino/beats_ckpts` is
what the paper used. The `cfg` embedded in the checkpoint matches the published
BEATs-iter3+ specification (12 layers, 768 wide, deep-norm, GRU relative
position bias), which is the best provenance available short of the official
download. The **code** is MIT (microsoft/unilm); only the weights come from the
mirror.

**XLS-R has two files with the same weights.** `pytorch_model.bin` and
`model.safetensors` are both published; the hash above is the `.bin`, which is
what the paper loaded. The safetensors file is
`683ca455157e8c9da75a67eb0c7737768f3db9f0876e3ca1fec53320babdfe6b` if you prefer
that format.

Each upstream repository carries its own licence. Check it before use; this
repository's MIT licence does not extend to them.
