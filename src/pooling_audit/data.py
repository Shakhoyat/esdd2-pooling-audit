"""Loading. Everything comes from per-clip files; nothing comes from a cached result.

Set the data root with the environment variable ESDD2_AUDIT_DATA, or place the
files under ./data/local/. See data/README.md for what to download and the
checksums to verify.

Expected layout under the data root:

    eval_index.csv        one row per evaluation clip:
                          filename,label_id,native_sr,native_channels,
                          env_clip_id,speech_clip_id
    baseline_scores.txt   the released ESDD2 baseline submission, pipe-separated:
                          filename|pred_label|score_original|score_speech|score_env
    scores/<system>.npz   our per-clip scores: arrays `filename` (n,),
                          `seeds` (k,), `scores` (k, n, 3) ordered
                          [original, speech, env], `predictions` (k, n)

The published eleven-system table ships with the repository, in
data/published/esdd2_overview_table.csv, because it is a table of numbers from a
paper rather than corpus data.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]


def data_root() -> Path:
    root = os.environ.get("ESDD2_AUDIT_DATA")
    p = Path(root).expanduser() if root else REPO / "data" / "local"
    if not p.exists():
        raise SystemExit(
            f"data root not found: {p}\n"
            "Set ESDD2_AUDIT_DATA to the directory holding eval_index.csv, "
            "baseline_scores.txt and scores/. See data/README.md."
        )
    return p


DERIVED = REPO / "data" / "derived"


def _fill_from_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Fill blank columns from data/derived/, so the large archives are optional.

    `eval_label.csv` alone (2.4 MB) gives filenames and labels. The source clip
    ids live in a 10.9 GB archive and the native sample rates in a 5.0 GB one, so
    both are also shipped here as small derived files. Columns already present in
    the index win: if you built the index from the archives, nothing is replaced.
    """
    def blank(col):
        return col not in df.columns or df[col].isna().all() or             (df[col].astype(str).str.strip().isin(["", "-", "nan"])).all()

    clusters, fmt = DERIVED / "clusters.csv", DERIVED / "native_format.csv"
    if (blank("env_clip_id") or blank("speech_clip_id")) and clusters.exists():
        c = pd.read_csv(clusters)
        df = df.drop(columns=[x for x in ("env_clip_id", "speech_clip_id")
                              if x in df.columns]).merge(
            c.rename(columns={"env_cluster": "env_clip_id",
                              "speech_cluster": "speech_clip_id"}),
            on="filename", how="left", validate="one_to_one")
    if (blank("native_sr") or blank("native_channels")) and fmt.exists():
        f = pd.read_csv(fmt)
        df = df.drop(columns=[x for x in ("native_sr", "native_channels")
                              if x in df.columns]).merge(
            f, on="filename", how="left", validate="one_to_one")
    return df


def _canonical_order(df: pd.DataFrame) -> pd.DataFrame:
    """Put rows in the corpus label file's order, whatever order the index arrived in.

    Every bootstrap here resamples by row position, so the same data in a different
    row order gives different intervals. data/derived/clusters.csv ships in the order
    of CompSpoofV2's eval_label.csv, so it defines the order.
    """
    ref = DERIVED / "clusters.csv"
    if not ref.exists():
        return df
    order = pd.read_csv(ref, usecols=["filename"])["filename"]
    if len(order) != len(df) or set(order) != set(df["filename"]):
        raise SystemExit("eval_index.csv does not contain exactly the evaluation clips "
                         "listed in data/derived/clusters.csv")
    return df.set_index("filename").loc[order].reset_index()


def load_index() -> pd.DataFrame:
    """One row per evaluation clip, in the corpus label file's order."""
    df = pd.read_csv(data_root() / "eval_index.csv")
    if "filename" not in df.columns or "label_id" not in df.columns:
        raise SystemExit("eval_index.csv needs at least `filename` and `label_id`")
    df = _canonical_order(df)
    df = _fill_from_derived(df)
    need = {"filename", "label_id", "native_sr", "native_channels",
            "env_clip_id", "speech_clip_id"}
    missing = need - set(df.columns)
    if missing:
        raise SystemExit(
            f"eval_index.csv is missing columns: {sorted(missing)}\n"
            "Either build it from the full corpus, or keep data/derived/ in place."
        )
    return df


def load_baseline(index: pd.DataFrame) -> pd.DataFrame:
    """The released baseline submission, aligned to the index order."""
    p = data_root() / "baseline_scores.txt"
    pred = pd.read_csv(p, sep="|", header=None,
                       names=["filename", "pred", "s_original", "s_speech", "s_env"])
    out = pred.set_index("filename").loc[index["filename"]].reset_index()
    if len(out) != len(index):
        raise SystemExit("baseline scores do not align one-to-one with the index")
    return out


def load_system(name: str, index: pd.DataFrame) -> dict:
    """Our own per-clip scores for one system, aligned to the index order."""
    z = np.load(data_root() / "scores" / f"{name}.npz", allow_pickle=False)
    order = pd.Series(range(len(z["filename"])), index=z["filename"].astype(str))
    pos = order.loc[index["filename"]].to_numpy()
    return dict(seeds=z["seeds"], scores=z["scores"][:, pos, :],
                predictions=z["predictions"][:, pos])


def load_published_table() -> pd.DataFrame:
    """The eleven challenge systems' published component EERs (ships with the repo)."""
    return pd.read_csv(REPO / "data" / "published" / "esdd2_overview_table.csv")


def repo_scores_dir() -> Path:
    """Our own scores ship with the repository; see LICENSE-DATA."""
    return REPO / "scores"


def align(filenames, index: pd.DataFrame) -> np.ndarray:
    """Row order that puts `filenames` into the index's canonical order."""
    order = pd.Series(range(len(filenames)), index=pd.Index(filenames).astype(str))
    return order.loc[index["filename"]].to_numpy()


def cluster_ids(index: pd.DataFrame, axis: str) -> np.ndarray:
    """Bootstrap cluster per row: the source component clip, else the clip itself.

    Returned as integers assigned by ORDER OF FIRST APPEARANCE, not as the raw
    identifier strings. The corpus and our cache spell these ids differently
    while inducing the same partition, and the bootstrap resamples clusters in
    sorted order, so raw strings would make the intervals depend on a naming
    convention rather than on the data. First-appearance integers are canonical
    for any spelling of the same grouping.
    """
    col = {"env": "env_clip_id", "speech": "speech_clip_id"}[axis]
    ids = index[col].astype(str).to_numpy()
    blank = index[col].isna().to_numpy() | (ids == "None") | (ids == "") | (ids == "nan") | (ids == "-")
    raw = np.where(blank, index["filename"].astype(str).to_numpy(), ids)
    seen, out = {}, np.empty(len(raw), dtype=np.int64)
    for i, v in enumerate(raw):
        out[i] = seen.setdefault(v, len(seen))
    return out
