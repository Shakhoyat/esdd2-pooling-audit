#!/usr/bin/env python3
"""Derive the two small metadata files that would save a 16 GB download.

    python tools/derive_metadata.py --from-local /path/to/CompSpoofV2 --write

The two files ship in data/derived/ (approved by the authors, CC BY-NC 4.0 under
LICENSE-DATA). This tool REGENERATES them from the archives into build/derived/, so
you can confirm the shipped copies byte for byte:

    sha256sum build/derived/*.csv
    grep derived MANIFEST.sha256

  clusters.csv      per-clip ANONYMOUS cluster numbers from eval_source/metadata/eval.csv
                    (10.9 GB archive): an integer per clip, numbered by first appearance,
                    with no source file, corpus or generator names. Unlocks the bootstrap
                    interval entries and the shared-row count.

  native_format.csv per-clip native sample rate and channel count, read from the audio
                    headers (5.0 GB archive). Unlocks the Section 4.4 format-confound entries.

Neither file lets anyone reconstruct audio.
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-local", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=ROOT / "build" / "derived")
    ap.add_argument("--write", action="store_true",
                    help="actually write; without it, only report what would be written")
    a = ap.parse_args()

    src = a.from_local
    meta = src / "eval_source" / "metadata" / "eval.csv"
    labels = src / "eval_label.csv"
    if not labels.exists():
        print(f"  eval_label.csv not found under {src}")
        return 2

    names = [Path(r["audio_path"]).name for r in csv.DictReader(open(labels))]
    a.out.mkdir(parents=True, exist_ok=True)

    # (a) anonymous clusters
    rows_c = []
    if meta.exists():
        prov = {}
        for r in csv.DictReader(open(meta)):
            prov[Path(r["audio_path"]).name] = (r.get("env_path", "-"), r.get("speech_path", "-"))
        seen_e, seen_s = {}, {}
        for n in names:
            e, s = prov.get(n, ("-", "-"))
            ek = Path(e).stem if e not in ("-", "") else f"__{n}"
            sk = Path(s).stem if s not in ("-", "") else f"__{n}"
            rows_c.append([n, seen_e.setdefault(ek, len(seen_e)),
                           seen_s.setdefault(sk, len(seen_s))])
        print(f"  clusters.csv    {len(rows_c)} rows, "
              f"{len(seen_e)} env / {len(seen_s)} speech clusters")
    else:
        print(f"  eval_source metadata absent at {meta}; clusters.csv not derivable")

    # (b) native format, read from audio headers
    rows_f = []
    audio = src / "eval" / "audio"
    if audio.exists():
        try:
            import soundfile as sf
        except ImportError:
            print("  soundfile not installed; native_format.csv not derivable")
            audio = None
        if audio:
            for i, n in enumerate(names):
                info = sf.info(audio / n)
                rows_f.append([n, int(info.samplerate), int(info.channels)])
                if i % 5000 == 0:
                    print(f"    headers {i}/{len(names)}", end="\r", flush=True)
            print(f"\n  native_format.csv {len(rows_f)} rows")
    else:
        print(f"  eval audio absent at {audio}; native_format.csv not derivable")

    if not a.write:
        print("\n  dry run: nothing written. Pass --write to produce the files.")
        return 0
    for fn, hdr, rows in (("clusters.csv", ["filename", "env_cluster", "speech_cluster"], rows_c),
                          ("native_format.csv", ["filename", "native_sr", "native_channels"], rows_f)):
        if not rows:
            continue
        p = a.out / fn
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(hdr)
            w.writerows(rows)
        print(f"  wrote {p}  {p.stat().st_size / 1024:.0f} KB")
    print("\n  Compare against the shipped copies: grep derived MANIFEST.sha256")
    return 0


if __name__ == "__main__":
    sys.exit(main())
