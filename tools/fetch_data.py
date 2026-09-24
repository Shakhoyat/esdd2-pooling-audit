#!/usr/bin/env python3
"""Fetch what tier 0 needs, and build eval_index.csv from it.

CompSpoofV2 is CC BY-NC 4.0 and access-gated, so nothing is redistributed here.
This downloads from the official source, records a sha256 for every file, and
assembles the index `verify.py` reads.

    python tools/fetch_data.py --labels-only     # 2.4 MB, covers most of tier 0
    python tools/fetch_data.py --from-local /path/to/CompSpoofV2
    python tools/fetch_data.py --checksums       # print sha256 of what is present

## What each download buys

The dataset publishes `eval_label.csv` as a STANDALONE file, so the bulk of
tier 0 needs 2.4 MB and no audio. The rest is behind large archives:

  eval_label.csv          2.4 MB   label_id for every evaluation clip.
                                   -> every EER, Table 1 point estimates,
                                      sections 2, 3, 4.2, 4.3, 4.4, Figure 1
  eval.tar.gz             5.0 GB   the audio. Needed only to read each clip's
                                   NATIVE sample rate and channel count.
                                   -> section 4.4's format-matched numbers
  eval_source.tar.gz     10.9 GB   per-component provenance, which gives the
                                   source clip ids.
                                   -> the clustered bootstrap intervals
  development.tar.gz       88 GB   training and validation metadata, in five
                                   parts. Only 46 MB of it is the CSVs, but a
                                   split gzip stream cannot be partially
                                   extracted, so it is all or nothing.
                                   -> the 175,361 and 24,864 clip counts

Provenance columns in `eval_label.csv` are redacted to "-" by the organisers;
the clip ids live in `eval_source/metadata/eval.csv`. That is why the bootstrap
needs the larger archive.
"""
import argparse
import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HF = "https://huggingface.co/datasets/XuepingZhang/ESDD2-CompSpoof-V2/resolve/main"

LABEL_TO_ID = {"original": 0, "bonafide_bonafide": 1, "spoof_bonafide": 2,
               "bonafide_spoof": 3, "spoof_spoof": 4}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def build_index(src: Path, out: Path) -> int:
    """Build eval_index.csv from whatever of the corpus is present."""
    labels = src / "eval_label.csv"
    if not labels.exists():
        print(f"  eval_label.csv not found under {src}")
        return 2
    rows = list(csv.DictReader(open(labels)))
    prov = {}
    pmeta = src / "eval_source" / "metadata" / "eval.csv"
    if pmeta.exists():
        for r in csv.DictReader(open(pmeta)):
            key = Path(r["audio_path"]).name
            prov[key] = (r.get("env_path", "-"), r.get("speech_path", "-"))
        print(f"  provenance found: clip ids available for {len(prov)} clips")
    else:
        print("  eval_source/metadata/eval.csv absent: bootstrap clusters will "
              "fall back to one cluster per clip, and the CI entries stay unchecked")

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["filename", "label_id", "native_sr", "native_channels",
                    "env_clip_id", "speech_clip_id"])
        for r in rows:
            name = Path(r["audio_path"]).name
            env, sp = prov.get(name, ("-", "-"))
            w.writerow([name, LABEL_TO_ID[r["label"]], "", "",
                        Path(env).stem if env not in ("-", "") else "",
                        Path(sp).stem if sp not in ("-", "") else ""])
    print(f"  wrote {out} with {len(rows)} rows")
    print("  native_sr and native_channels are left blank: they are read from the "
          "audio headers, so section 4.4's entries need eval.tar.gz")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-local", type=Path,
                    help="a CompSpoofV2 checkout you already have")
    ap.add_argument("--labels-only", action="store_true",
                    help="download only eval_label.csv (2.4 MB)")
    ap.add_argument("--checksums", action="store_true")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "local")
    a = ap.parse_args()

    if a.checksums:
        for p in sorted((a.out).rglob("*")):
            if p.is_file():
                print(f"  {sha256(p)}  {p.relative_to(a.out)}  {p.stat().st_size}")
        return 0

    if a.from_local:
        return build_index(a.from_local, a.out / "eval_index.csv")

    if a.labels_only:
        import urllib.request
        a.out.mkdir(parents=True, exist_ok=True)
        dst = a.out / "eval_label.csv"
        url = f"{HF}/eval_label.csv"
        print(f"  downloading {url}")
        print("  NOTE: the dataset is access-gated. If this returns 401, accept the")
        print("  licence at https://huggingface.co/datasets/XuepingZhang/ESDD2-CompSpoof-V2")
        print("  and set HF_TOKEN, or use --from-local.")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "esdd2-pooling-audit"})
            dst.write_bytes(urllib.request.urlopen(req, timeout=120).read())
        except Exception as exc:                    # noqa: BLE001
            print(f"  download failed: {exc}")
            return 2
        print(f"  sha256 {sha256(dst)}")
        return build_index(a.out, a.out / "eval_index.csv")

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
