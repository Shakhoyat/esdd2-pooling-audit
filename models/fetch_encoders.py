#!/usr/bin/env python3
"""Download the encoder checkpoints and verify each against its sha256.

    python models/fetch_encoders.py
    python models/fetch_encoders.py --only beats --dest ~/encoders
    python models/fetch_encoders.py --verify          # hash what is present

Weights are not redistributed with this repository. A file whose hash does not
match is reported and left in place rather than silently used, because a
mismatched encoder would produce scores that look plausible and are not ours.
"""
import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

HF = "https://huggingface.co"

ENCODERS = {
    "beats": dict(repo="lpepino/beats_ckpts", file="BEATs_iter3_plus_AS2M.pt",
                  sha256="d43cbfad4d7b56381c061d7a24774f908d4d94c72961f6eb1d9090ff18cd8d34",
                  size=345 * 1024**2),
    "sslam": dict(repo="ta012/SSLAM_pretrain", file="model.safetensors",
                  sha256="8ec670adb241c710422ddd894ff1bade142ef0b25cf1ee68577aa45f89432298",
                  size=344 * 1024**2),
    "eat":   dict(repo="worstchan/EAT-base_epoch30_pretrain", file="model.safetensors",
                  sha256="8623072d09aac4f3ad1168b4fed3a24e4f68fe1da25b9fe733375efb237e5f48",
                  size=344 * 1024**2),
    "xlsr":  dict(repo="facebook/wav2vec2-xls-r-300m", file="pytorch_model.bin",
                  sha256="d5e490574712ad0a6736923b9ed11d4cd51c78609c36205f704fc4e87b11d2e0",
                  size=1250 * 1024**2),
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=sorted(ENCODERS))
    ap.add_argument("--dest", type=Path, default=Path(__file__).parent / "checkpoints")
    ap.add_argument("--verify", action="store_true", help="hash what is present, download nothing")
    a = ap.parse_args()

    wanted = [a.only] if a.only else sorted(ENCODERS)
    a.dest.mkdir(parents=True, exist_ok=True)
    bad, checked = 0, 0
    for name in wanted:
        spec = ENCODERS[name]
        dst = a.dest / f"{name}_{spec['file']}"
        if not dst.exists():
            if a.verify:
                print(f"  {name:6s} absent")
                continue          # not counted as verified, and not counted as bad
            url = f"{HF}/{spec['repo']}/resolve/main/{spec['file']}"
            print(f"  {name:6s} downloading {spec['size'] / 1024**2:.0f} MB from {url}")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "esdd2-pooling-audit"})
                with urllib.request.urlopen(req, timeout=300) as r, open(dst, "wb") as f:
                    while chunk := r.read(1 << 22):
                        f.write(chunk)
            except Exception as exc:                 # noqa: BLE001
                print(f"  {name:6s} DOWNLOAD FAILED: {exc}")
                bad += 1
                continue
        got = sha256(dst)
        ok = got == spec["sha256"]
        print(f"  {name:6s} {'OK  ' if ok else 'HASH MISMATCH'} {got[:16]}...  {dst}")
        checked += 1
        bad += not ok
    absent = len(wanted) - checked - bad if a.verify else 0
    print(f"\n  {checked - bad}/{len(wanted)} verified"
          + (f", {len(wanted) - checked} absent" if a.verify and checked < len(wanted) else "")
          + (f", {bad} failed" if bad else ""))
    return 1 if (bad or (a.verify and checked == 0)) else 0


if __name__ == "__main__":
    sys.exit(main())
