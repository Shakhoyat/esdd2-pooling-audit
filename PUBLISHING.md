# Publishing this repository

Nothing here has been pushed or tagged. These are the commands for Shujon to run.

---

## TODO before any of this — one decision, three files

**"Md" or "Md."?** Author 4 is `Md Rezwanul Haque` in the paper (no full stop)
while authors 1 and 3 use `Md.`. **And who is the corresponding author?** The
paper marks none, and the CMS requires one.

Both answers have to land in three places at once, or the submission record, the
citation file and the PDF will disagree:

- [ ] `CITATION.cff` — two `given-names` entries, and add the corresponding author
- [ ] `icassp2027/paper/merged/main.tex` — the `\name{}` block
- [ ] the CMS submission record

Ask Rezwan which spelling he uses. Do this before tagging; a tag is meant to be
the thing the paper points at, and a name fix afterwards means retagging.

---

## 1. Push, from the right directory, as the right account

```bash
# ALWAYS from inside this repository. The main working repo it sits in is NEVER
# pushed -- that one holds reviewer correspondence, drafts and internal notes.
cd path/to/esdd2-pooling-audit

git rev-parse --show-toplevel   # must end in /esdd2-pooling-audit
gh auth status                  # the ACTIVE account must own the remote you create
```

This machine has had more than one GitHub account logged in. A push authenticated
as the wrong one fails with **"Repository not found"**, not a permission error, so
check first rather than debugging the symptom.

Create an **empty** repository on GitHub — no README, no `.gitignore`, no licence,
since this repository has all three and an initial commit would conflict.
Suggested name `esdd2-pooling-audit`. **Keep it private for now.**

```bash
git remote add origin https://github.com/<your-account>/esdd2-pooling-audit.git
git push -u origin main
```

22 MB, of which 21 MB is `scores/` and 2.7 MB `data/derived/`. Inside every
GitHub limit; no LFS needed.

---

## 2. Release checklist, in this order

The order matters: the URL has to be in the PDF **before** the PDF is final, and
the tag has to sit on the commit that the final PDF was checked against. Nothing
is recompiled after the sync check.

- [ ] **(a) Repository exists and `main` is pushed, still private.** The URL is
      now fixed and will not change.
- [ ] **(b) Put the real URL in the paper.** §4.1 reads `github.com/REPLACE`.
      Replace it with the repository URL.
- [ ] **(c) Produce the final PDF.** Compile, and treat this file as frozen.
- [ ] **(d) Sync check against that exact PDF:**
      ```bash
      python check_paper_sync.py /path/to/final/main.pdf
      ```
      Direction (a) must be **0**. Direction (b) should contain only affiliation
      superscripts and exponents — read the contexts and confirm nothing real is
      in it. Also run `make verify` (every entry verified, 0 failed), `make test` (all pass) and
      `make manifest` (0 problems).
- [ ] **(e) Tag the commit that passed (d), and make the repository public.**
      ```bash
      git tag -a v1.0-submission -m "ICASSP 2027 submission"
      git push origin v1.0-submission
      ```
      Then Settings → General → Danger Zone → Change visibility → Public.
- [ ] **(f) Upload that exact PDF.** The one from (c) that (d) passed against.
      **Do not recompile between (d) and (f)** — a rebuild changes the PDF and
      the sync check no longer refers to the file you submitted.

### Optional: archive the tag for a DOI

Once the repository is public, [Zenodo](https://zenodo.org) can mint a DOI for a
GitHub release. Enable the repository in Zenodo's GitHub settings, then publish a
release from the `v1.0-submission` tag; Zenodo archives that snapshot and issues
a DOI. Worth doing if the camera-ready can cite it — a DOI survives the
repository being renamed or moved, which a bare URL does not.

---

## 3. What is deliberately not in the repository

- **Corpus and baseline scores.** CC BY-NC 4.0 and access-gated; fetched by
  `tools/fetch_data.py` against recorded sha256.
- **Encoder weights.** Fetched and hash-verified by `models/fetch_encoders.py`.
- **Probe checkpoints.** Never retained; see the README's Roadmap.

What *is* shipped: our per-clip scores, and `data/derived/` — anonymous cluster
integers and native audio formats, 2.7 MB replacing 15.9 GB of archives. Both are
CC BY-NC 4.0 under `LICENSE-DATA`, with CompSpoofV2 attribution required.
