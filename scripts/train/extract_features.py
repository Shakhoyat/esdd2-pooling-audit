#!/usr/bin/env python3
"""Tier 1: frozen-encoder features. One forward pass per clip, no training.

    python scripts/train/extract_features.py --encoder beats --split eval --limit 500

Writes <data root>/features/<split>.<encoder>.feat.npy, shaped
(n_clips, n_layers, 2*D): mean and std over time, per layer, per clip.

## Encoder code and weights are NOT vendored here

BEATs is MIT-licensed (microsoft/unilm) and could be redistributed, but its
checkpoints are published through third-party mirrors and the other encoders
have their own terms, so this script imports the encoder from a checkout you
provide:

    export ENCODER_SRC=/path/to/a/tree/containing/models/enc_beats.py
    export BEATS_CKPT=/path/to/BEATs_iter3_plus_AS2M.pt

Without those it exits with a message rather than a traceback. Tier 0 needs
none of this.
"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pooling_audit import data  # noqa: E402

LAYERS = {"beats": 12, "eat": 12, "sslam": 12, "xlsr": 12}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--encoder", default="beats", choices=sorted(LAYERS))
    ap.add_argument("--split", default="eval", choices=["train", "val", "eval"])
    ap.add_argument("--limit", type=int, default=None,
                    help="smoke mode: only the first N clips")
    ap.add_argument("--batch", type=int, default=16)
    a = ap.parse_args()

    src = os.environ.get("ENCODER_SRC")
    if not src:
        print("  ENCODER_SRC is not set.")
        print("  Tier 1 needs the encoder implementation and its checkpoint; see the")
        print("  module docstring. Tier 0 (make verify) needs neither.")
        return 2
    sys.path.insert(0, src)

    root = data.data_root()
    audio_dir = root / "audio" / a.split
    if not audio_dir.exists():
        print(f"  audio not found at {audio_dir}")
        return 2

    import numpy as np
    import soundfile as sf
    import torch

    idx = data.load_index()
    names = idx["filename"].tolist()[: a.limit]
    print(f"  {a.encoder} on {a.split}: {len(names)} clips, cuda={torch.cuda.is_available()}")

    from models.enc_beats import BEATsEncoder     # noqa: E402
    enc = BEATsEncoder()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    if hasattr(enc, "to"):
        enc.to(dev)

    t0 = time.time()
    out = None
    for i in range(0, len(names), a.batch):
        wavs = []
        for n in names[i:i + a.batch]:
            w, sr = sf.read(audio_dir / n, dtype="float32", always_2d=True)
            wavs.append(torch.from_numpy(w.mean(1)))
        L = max(len(w) for w in wavs)
        batch = torch.stack([torch.nn.functional.pad(w, (0, L - len(w))) for w in wavs]).to(dev)
        with torch.no_grad():
            o = enc.encode(batch)
        # EncoderOutput.hidden_states is per-layer [B, T_i, D_i]; pooling is
        # mean and std over time, which is what the paper's probes consume.
        h = torch.stack([torch.cat([x.mean(1), x.std(1)], dim=-1)
                         for x in o.hidden_states], dim=1)
        f = h.float().cpu().numpy()
        if out is None:
            out = np.empty((len(names),) + f.shape[1:], dtype=np.float16)
        out[i:i + len(wavs)] = f.astype(np.float16)
        print(f"    {min(i + a.batch, len(names))}/{len(names)}", end="\r", flush=True)

    dst = root / "features" / f"{a.split}.{a.encoder}.feat.npy"
    dst.parent.mkdir(parents=True, exist_ok=True)
    np.save(dst, out)
    el = time.time() - t0
    print(f"\n  wrote {dst}  shape {out.shape}  in {el:.1f}s "
          f"({len(names) / el:.1f} clips/s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
