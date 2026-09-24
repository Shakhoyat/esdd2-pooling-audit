#!/usr/bin/env python3
"""Tier 1: train the frozen-encoder probes that produce our per-clip scores.

    python scripts/train/train_probes.py --system beats_linear --seeds 1337 1338 1339
    python scripts/train/train_probes.py --smoke                 # 500 cached clips, 1 seed

Every setting -- layers, seeds, steps, learning rate, weight decay, batch -- is
read from configs/systems.yaml. Nothing is hard-coded here, so the paper's
configuration and a rerun cannot drift apart.

Writes <data root>/scores_regenerated/<system>.npz in the schema
scores/README.md documents, which is what verify.py consumes. It writes there
rather than over scores/ so a rerun never silently replaces the scores the paper
used.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import numpy as np  # noqa: E402
import yaml  # noqa: E402

from pooling_audit import data  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    cfgs = yaml.safe_load(open(REPO / "configs" / "systems.yaml"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", default="beats_linear",
                    choices=sorted(k for k in cfgs["systems"] if "encoder" in cfgs["systems"][k]))
    ap.add_argument("--seeds", type=int, nargs="+", default=cfgs["seeds"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--smoke", action="store_true",
                    help="500 cached eval clips, one seed, few steps; exercises the path")
    a = ap.parse_args()

    import torch
    from pooling_audit.heads import train_linear_probe

    spec = cfgs["systems"][a.system]
    tcfg = dict(cfgs["training"]["probe"])
    root = data.data_root()
    enc = spec["encoder"]

    if a.smoke:
        a.seeds, a.limit, tcfg["steps"] = a.seeds[:1], 500, 50
        split = "eval"          # the only split whose features the smoke run caches
    else:
        split = "train"

    feats = root / "features" / f"{split}.{enc}.feat.npy"
    if not feats.exists():
        print(f"  features not found at {feats}")
        print("  Run scripts/train/extract_features.py first; see that script's docstring.")
        return 2

    idx = data.load_index()
    X = np.load(feats, mmap_mode="r")
    n = min(len(X), a.limit or len(X))
    x = torch.from_numpy(np.ascontiguousarray(X[:n][:, spec["layers"], :]).astype(np.float32)).flatten(1)
    y = idx.label_id.to_numpy()[:n]

    if a.smoke:
        # Train on the first half, score the whole slice. This exercises the code
        # path; it reproduces nothing and is not a result.
        cut = n // 2
        x_tr, y_tr = x[:cut], y[:cut]
        print(f"  SMOKE: {a.system}, layers {spec['layers']}, {cut} train / {n} scored, "
              f"{tcfg['steps']} steps, seed {a.seeds[0]}")
    else:
        x_tr, y_tr = x, y

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    t0 = time.time()
    probs = np.stack([train_linear_probe(x_tr, y_tr, x, s, tcfg, dev) for s in a.seeds])
    el = time.time() - t0

    # scores schema: [original, speech, env], bona-fide-oriented
    scores = np.stack([probs[:, :, 0],
                       probs[:, :, [0, 1, 3]].sum(-1),
                       probs[:, :, [0, 1, 2]].sum(-1)], axis=-1)
    dst = root / "scores_regenerated" / f"{a.system}.npz"
    dst.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(dst, filename=idx["filename"].to_numpy().astype(str)[:n],
                        seeds=np.asarray(a.seeds), scores=scores.astype(np.float32),
                        predictions=probs.argmax(-1).astype(np.int64))
    print(f"  wrote {dst}  scores {scores.shape}  in {el:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
