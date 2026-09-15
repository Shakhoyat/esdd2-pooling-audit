# Publishing this repository

`main` is pushed to `github.com/Shakhoyat/esdd2-pooling-audit`, private. Nothing is tagged. These
are the commands for Shujon to run.

---

## Still open before tagging — corresponding author and ORCiDs

**"Md" or "Md."** is settled: author 4 is `Md Rezwanul Haque` by his own usage, authors 1 and 3
are `Md.`, and the paper, `CITATION.cff` and the CMS record must all keep that difference.

**Corresponding author and ORCiDs** are not settled. Every author needs a validated ORCiD in the
CMS (a missing one withdraws the submission). The same answers go in three places:

- [ ] `CITATION.cff` — `email:` on the corresponding author, `orcid:` on every author
- [ ] the paper's `\name{}` block, if the corresponding author is to be marked there
- [ ] the CMS submission record

A tag is meant to be the thing the paper points at, so do this before tagging.

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

- [x] **(a) Repository exists and `main` is pushed, still private.** The URL is
      now fixed and will not change.
- [x] **(b) The real URL is in the paper**, at the end of the abstract, and in
      `CITATION.cff`.
- [ ] **(c) Produce the final PDF.** Compile, and treat this file as frozen.
- [ ] **(d) Sync check against that exact PDF:**
      ```bash
      python check_paper_sync.py /path/to/final/main.pdf
      ```
      Rebuild `PROOFS.pdf` from the frozen source and check it too:
      `python check_paper_sync.py PROOFS.pdf --document extended --tex paper/proofs.tex --body-start "Theorem 1: statement"`.
      Both directions must be **0**, for both documents: every listed value appears in the PDF, and
      every numeric literal in the PDF is listed. Also run `make verify` (0 failed),
      `make test` (all pass), `ESDD2_PAPER_PDF=/path/to/final/main.pdf make gate`
      (all pass) and `make manifest` (0 problems).
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
