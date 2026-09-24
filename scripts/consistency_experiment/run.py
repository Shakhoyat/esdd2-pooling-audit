#!/usr/bin/env python3
"""Tier 1: the supplementary train/score consistency experiment.

    python scripts/consistency_experiment/run.py --config layer7 --seeds 1337
    python scripts/consistency_experiment/run.py --smoke

Two arms, identical but for one line -- the component loss mask, which
configs/systems.yaml states explicitly:

    M   mask = is_mixture   the inapplicable clips are excluded from both
                            component losses, as the released baseline does
    C   mask = all          both heads are supervised on them, per the mapping
                            the scorer mandates

Pre-registered before the runs; see README.md in this directory.
Writes <data root>/consistency_regenerated/<config>_<arm>_<seed>.npz, never over
the scores the paper used.
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
    ap.add_argument("--config", default="layer7",
                    choices=sorted(cfgs["consistency_configs"]))
    ap.add_argument("--seeds", type=int, nargs="+", default=cfgs["seeds"])
    ap.add_argument("--arms", nargs="+", default=["M", "C"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    import torch
    from pooling_audit.heads import score_component_heads, train_component_heads

    spec = cfgs["consistency_configs"][a.config]
    tcfg = dict(cfgs["training"]["component_heads"])
    root = data.data_root()

    if a.smoke:
        a.seeds, a.limit, tcfg["steps"] = a.seeds[:1], 500, 50
        split = "eval"
    else:
        split = "train"

    feats = root / "features" / f"{split}.{spec['encoder']}.feat.npy"
    if not feats.exists():
        print(f"  features not found at {feats}")
        print("  Run scripts/train/extract_features.py --encoder "
              f"{spec['encoder']} first.")
        return 2

    idx = data.load_index()
    X = np.load(feats, mmap_mode="r")
    n = min(len(X), a.limit or len(X))
    x = torch.from_numpy(np.ascontiguousarray(X[:n][:, spec["layers"], :]).astype(np.float32)).flatten(1)
    y = idx.label_id.to_numpy()[:n]
    cut = n // 2 if a.smoke else n
    dev = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"  {'SMOKE: ' if a.smoke else ''}{a.config} layers {spec['layers']}, "
          f"arms {a.arms}, seeds {a.seeds}, {tcfg['steps']} steps")
    out = root / "consistency_regenerated"
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    for arm in a.arms:
        for sd in a.seeds:
            net, norm = train_component_heads(x[:cut], y[:cut], arm, sd, tcfg, dev)
            sc = score_component_heads(net, norm, x, dev)
            np.savez_compressed(out / f"{a.config}_{arm}_{sd}.npz",
                                filename=idx["filename"].to_numpy().astype(str)[:n],
                                scores=sc.astype(np.float32))
            print(f"    arm {arm} seed {sd}: scored {sc.shape}")
    print(f"  {len(a.arms) * len(a.seeds)} run(s) in {time.time() - t0:.1f}s -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
