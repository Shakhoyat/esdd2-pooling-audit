# Verification report

Audit of every printed number in `paper/main.tex`, recomputed from raw per-clip scores and the published ESDD2 overview table.

Generated 2026-09-24 13:06 UTC by `verify/generate_report.py`, Python 3.13.11, against commit `9f2f75d5898747b864ab1f7582c7a4440ff00b85` (working tree had uncommitted changes at generation time).
Regenerate with `python verify/generate_report.py`; do not hand-edit the Summary or "All entries" sections below, they are overwritten on every run.

## Summary

| | count |
|---|---|
| Manifest entries (`verify/numbers_manifest.csv`) | 82 |
| Recomputed rows (`verify/numbers_recomputed.csv`) | 82 |
| Matched (`match=yes`) | **82** |
| Mismatched (`match=no`) | **0** |
| Not recomputable (any other value) | **0** |

No mismatches. Every manifest entry with a `match` value of `yes` reproduces the printed number at printed precision.

## All entries

Full manifest, joined with its recomputed value, in manifest order. This table is rebuilt from the two CSVs on every run of this script.

10 of these rows are marked *(not a literal digit — see "how printed")* in the location column: their `printed` value is not literally the Arabic numeral in the paper's text. Most spell a small number as a word ("fourteen" -> printed `14`); a few encode a stated bound or assertion (e.g. the paper says a residual is "below $10^{-15}$", so `printed` is the assertion's own bound-check value `1.0` and `recomputed` is the measured residual scaled against that bound, not the raw residual) -- the "how printed / note" column always says which, so `printed=1.0` next to `recomputed=0.22` in such a row is a passing check, not a discrepancy. Read the note before reading the numbers as a direct comparison.

| id | file | location | printed | recomputed (unrounded) | recomputed (rounded) | match | how printed / note |
|---|---|---|---|---|---|---|---|
| `s2_containment` | paper/main.tex | §2.3 Theorem 2: containment checked in the released code *(not a literal digit — see "how printed")* | 0.0 | 0.0 | 0.0 | yes | stated in words ('the released code constructs an admissible system that matches both EERs within numerical precision'); checked as zero violations over random admissible systems — upper bound |
| `s2_attainment` | paper/main.tex | §2.3 Theorem 2: every sampled value attained *(not a literal digit — see "how printed")* | 1.0 | 5.551115123125783e-05 | 0.0 | yes | stated in words, not as a bound digit; checked as worst crossing residual x 1e12 <= 1 — upper bound |
| `s2_witness_pooled` | paper/main.tex | §2.3: the released code's admissible system matches the ESDD2 baseline's published pooled EER *(not a literal digit — see "how printed")* | 0.4336 | 0.43361689365142697 | 0.4336 | yes | the paper says the released code constructs a matching admissible system; this is the published value it reproduces — equal at 4 dp |
| `s2_witness_comp` | paper/main.tex | §2.3: the same witness at the lower endpoint of the identified interval *(not a literal digit — see "how printed")* | 0.0000 | 0.0 | 0.0000 | yes | the lower endpoint that witness sits at, given w_0=0.5323 and the published 0.4336 — equal at 4 dp |
| `fig2_area_roc` | paper/main.tex | Fig. 2 legend, area under ROC_a (= AUC_a) | 0.8740 | 0.8740471542433768 | 0.8740 | yes | equal at 4 dp |
| `fig2_area_r0` | paper/main.tex | Fig. 2 legend, area under alpha_0 R_0 (= alpha_0(1-AUC_0)) | 0.7130 | 0.712983084783209 | 0.7130 | yes | equal at 4 dp |
| `fig2_area_ac` | paper/main.tex | Fig. 2 legend, area under AC (= ACDS(1,1)) | 0.1611 | 0.16106406946016769 | 0.1611 | yes | equal at 4 dp |
| `s41_step_gap` | paper/main.tex | §4.1 trapezoidal vs step rule, at most 4e-4 | 4 | 2.938875168388977 | 3 | yes | printed as the bound 4 x 10^-4; checked as the worst gap x 1e4 <= 4 — upper bound |
| `s41_eval` | paper/main.tex | §4.1 evaluation clips | 27605 | 27605.0 | 27605 | yes | equal at 0 dp |
| `s41_sr` | paper/main.tex | §4.1 kHz | 16 | 16.0 | 16 | yes | equal at 0 dp |
| `s41_seeds` | paper/main.tex | §4.1 three random seeds *(not a literal digit — see "how printed")* | 3 | 3.0 | 3 | yes | spelled as a word in the paper — equal at 0 dp |
| `t1_max_sd` | paper/main.tex | Table 1 caption, seed s.d. bound *(not a literal digit — see "how printed")* | 0.0015 | 0.0015 | 0.0015 | yes | internal check backing 'mean over three random seeds'; not itself a printed digit — equal at 4 dp |
| `t1_head_c_mid` | paper/main.tex | §4.2 the constant c=0.5 | 0.5 | 0.5 | 0.5 | yes | equal at 1 dp |
| `t1_beats_c0` | paper/main.tex | Abstract / §4.2, BEATs Linear at c=0 | 0.5382 | 0.5381910522152452 | 0.5382 | yes | equal at 4 dp |
| `t1_beats_c05` | paper/main.tex | Abstract / §4.2, BEATs Linear at c=0.5 | 0.1412 | 0.1411868091577938 | 0.1412 | yes | equal at 4 dp |
| `t1_beats_spread` | paper/main.tex | §4.2 / Table 1 caption, BEATs Linear spread | 0.3970 | 0.3970042430574514 | 0.3970 | yes | equal at 4 dp |
| `t1_eat_c0` | paper/main.tex | §4.2, EAT Linear at c=0 | 0.5400 | 0.5399753633156226 | 0.5400 | yes | equal at 4 dp |
| `t1_ref_comp` | paper/main.tex | §4.3, ESDD2 baseline component-only environmental EER | 0.2090 | 0.2089891109115402 | 0.2090 | yes | equal at 4 dp |
| `t1a_beats_01` | paper/main.tex | Table 1, BEATs Linear (0,1) | 0.9240 | 0.9239953730728933 | 0.9240 | yes | equal at 4 dp |
| `t1a_beats_11` | paper/main.tex | Table 1, BEATs Linear (1,1) | 0.9169 | 0.9168903672207872 | 0.9169 | yes | equal at 4 dp |
| `t1a_beats_02` | paper/main.tex | Table 1, BEATs Linear (0,0.2) | 0.7032 | 0.7031628030983385 | 0.7032 | yes | equal at 4 dp |
| `t1a_beats_w` | paper/main.tex | Table 1, BEATs Linear (w0/wa,1) | 0.9159 | 0.9159086832061069 | 0.9159 | yes | equal at 4 dp |
| `t1a_eat_01` | paper/main.tex | Table 1, EAT Linear (0,1) | 0.8859 | 0.8859293874419997 | 0.8859 | yes | equal at 4 dp |
| `t1a_eat_11` | paper/main.tex | Table 1, EAT Linear (1,1) | 0.8487 | 0.8486544568124709 | 0.8487 | yes | equal at 4 dp |
| `t1a_eat_02` | paper/main.tex | Table 1, EAT Linear (0,0.2) | 0.5522 | 0.5521886974255352 | 0.5522 | yes | equal at 4 dp |
| `t1a_eat_w` | paper/main.tex | Table 1, EAT Linear (w0/wa,1) | 0.8435 | 0.8435042564735817 | 0.8435 | yes | equal at 4 dp |
| `t1a_attn_01` | paper/main.tex | Table 1, BEATs Attentive (0,1) | 0.9248 | 0.9248095625654843 | 0.9248 | yes | equal at 4 dp |
| `t1a_attn_11` | paper/main.tex | Table 1, BEATs Attentive (1,1) | 0.5760 | 0.5759815980463433 | 0.5760 | yes | equal at 4 dp |
| `t1a_attn_02` | paper/main.tex | Table 1, BEATs Attentive (0,0.2) | 0.7081 | 0.7081426636380108 | 0.7081 | yes | equal at 4 dp |
| `t1a_attn_w` | paper/main.tex | Table 1, BEATs Attentive (w0/wa,1) | 0.5278 | 0.5277847571471336 | 0.5278 | yes | equal at 4 dp |
| `t1a_twoenc_01` | paper/main.tex | Table 1, BEATs + XLS-R (0,1) | 0.9268 | 0.9267991225116 | 0.9268 | yes | equal at 4 dp |
| `t1a_twoenc_11` | paper/main.tex | Table 1, BEATs + XLS-R (1,1) | 0.5544 | 0.5544346908234318 | 0.5544 | yes | equal at 4 dp |
| `t1a_twoenc_02` | paper/main.tex | Table 1, BEATs + XLS-R (0,0.2) | 0.7465 | 0.7465489447687471 | 0.7465 | yes | equal at 4 dp |
| `t1a_twoenc_w` | paper/main.tex | Table 1, BEATs + XLS-R (w0/wa,1) | 0.5030 | 0.5029858647657536 | 0.5030 | yes | equal at 4 dp |
| `t1a_ref_01` | paper/main.tex | Table 1, ESDD2 baseline (0,1) | 0.8740 | 0.8740471542433768 | 0.8740 | yes | equal at 4 dp |
| `t1a_ref_11` | paper/main.tex | Table 1, ESDD2 baseline (1,1) | 0.1611 | 0.16106406946016769 | 0.1611 | yes | equal at 4 dp |
| `t1a_ref_02` | paper/main.tex | Table 1, ESDD2 baseline (0,0.2) | 0.6526 | 0.6525852043107319 | 0.6526 | yes | equal at 4 dp |
| `t1a_ref_w` | paper/main.tex | Table 1, ESDD2 baseline (w0/wa,1) | 0.0626 | 0.06255266614279281 | 0.0626 | yes | equal at 4 dp |
| `t1a_tmax` | paper/main.tex | Table 1, t_max = 0.2 row | 0.2 | 0.2 | 0.2 | yes | equal at 1 dp |
| `t1a_identity` | paper/main.tex | §4.4 both invariance properties hold within 1e-15 *(not a literal digit — see "how printed")* | 1.0 | 0.11102230246251565 | 0.1 | yes | printed as the bound 10^-15; checked as the worst identity residual x 1e15 <= 1 — upper bound |
| `s42_spread_max` | paper/main.tex | §4.2 varies by up to | 0.3970 | 0.3970042430574514 | 0.3970 | yes | equal at 4 dp |
| `s42_beats_c0` | paper/main.tex | §4.2 BEATs Linear at c=0 | 0.5382 | 0.5381910522152452 | 0.5382 | yes | equal at 4 dp |
| `s42_eat_c0` | paper/main.tex | §4.2 EAT Linear at c=0 | 0.5400 | 0.5399753633156226 | 0.5400 | yes | equal at 4 dp |
| `s42_c_mid` | paper/main.tex | §4.2 probability-valued c=0.5 | 0.5 | 0.5 | 0.5 | yes | equal at 1 dp |
| `s42_twoenc_bound` | paper/main.tex | §4.2 BEATs + XLS-R boundary distance | 0.026 | 0.026 | 0.026 | yes | equal at 3 dp |
| `s42_mindcf_pooled` | paper/main.tex | §4.2 pooled minDCF at ASVspoof 5 costs | 0.9994 | 0.9994117647058823 | 0.9994 | yes | equal at 4 dp |
| `s42_mindcf_comp` | paper/main.tex | §4.2 component-only (P_a) minDCF at ASVspoof 5 costs | 0.5865 | 0.5864902334979794 | 0.5865 | yes | equal at 4 dp |
| `s42_mindcf_resid` | paper/main.tex | §4.2 minDCF residual against the weighted mean | 0.19 | 0.1931193166306151 | 0.19 | yes | equal at 2 dp |
| `s42_auc_resid` | paper/main.tex | §4.2 every area residual below 1e-15 *(not a literal digit — see "how printed")* | 1.0 | 0.0 | 0.0 | yes | printed as the bound 10^-15 — upper bound |
| `s43_env_comp` | paper/main.tex | §4.3 environmental component-only EER | 0.2090 | 0.2089891109115402 | 0.2090 | yes | equal at 4 dp |
| `s43_speech_comp` | paper/main.tex | §4.3 speech component-only EER | 0.1906 | 0.19057251408358442 | 0.1906 | yes | equal at 4 dp |
| `s43_env_dist` | paper/main.tex | §4.3 environmental EER increase from structural zeros | 0.2246 | 0.22462990908131947 | 0.2246 | yes | equal at 4 dp |
| `s43_speech_dist` | paper/main.tex | §4.3 speech EER increase from structural zeros | 0.0087 | 0.008743385723876035 | 0.0087 | yes | equal at 4 dp |
| `s43_total` | paper/main.tex | §4.3 reported gap | 0.2343 | 0.23430312018539923 | 0.2343 | yes | equal at 4 dp |
| `s43_pooling_net` | paper/main.tex | §4.3 pooling explains, of the gap | 0.2159 | 0.21588652335744343 | 0.2159 | yes | equal at 4 dp |
| `s43_pooling_pct` | paper/main.tex | §4.3 pooling share of the gap (92%) | 92 | 92.1398414099722 | 92 | yes | the paper prints '(92%)'; the measured share is 92.14 — lower bound |
| `s44a_cross` | paper/main.tex | §4.4 ranking changes from alpha_0 = 0.125 onward | 0.125 | 0.12479472479558787 | 0.125 | yes | equal at 3 dp |
| `s44a_cross_again` | paper/main.tex | §4.4 / Fig. 3 caption, all five intersections occur below | 0.125 | 0.12479472479558787 | 0.125 | yes | equal at 3 dp |
| `s44a_w0_over_wa` | paper/main.tex | §4.4 the ESDD2 protocol cost w0/wa | 1.138 | 1.138167938931298 | 1.138 | yes | equal at 3 dp |
| `s44a_span01` | paper/main.tex | §4.4 ACDS(0,1) range | 0.053 | 0.05275196826822326 | 0.053 | yes | equal at 3 dp |
| `s44a_span_alarm` | paper/main.tex | §4.4 1 - AUC_0 range | 0.706 | 0.7058780789311029 | 0.706 | yes | equal at 3 dp |
| `s44a_eat_02` | paper/main.tex | §4.4 EAT Linear at t_max = 0.2 | 0.5522 | 0.5521886974255352 | 0.5522 | yes | equal at 4 dp |
| `s44a_ref_02` | paper/main.tex | §4.4 ESDD2 baseline at t_max = 0.2 | 0.6526 | 0.6525852043107319 | 0.6526 | yes | equal at 4 dp |
| `s44a_n_cross` | paper/main.tex | §4.4 all five environmental crossings *(not a literal digit — see "how printed")* | 5 | 5.0 | 5 | yes | spelled as a word in the paper — equal at 0 dp |
| `s45_gate_threshold` | paper/main.tex | §4.5 thresholding gamma at 1/2 *(not a literal digit — see "how printed")* | 0.5 | 0.5 | 0.5 | yes | typeset as the fraction 1/2 — equal at 1 dp |
| `s45_lam_env` | paper/main.tex | §4.5 contamination rate, environmental | 0.0026 | 0.002629416598192276 | 0.0026 | yes | equal at 4 dp |
| `s45_lam_sp` | paper/main.tex | §4.5 contamination rate, speech | 0.0015 | 0.0015084378240784388 | 0.0015 | yes | equal at 4 dp |
| `s45_eer_gated_env` | paper/main.tex | §4.5 gated EER, environmental | 0.2028 | 0.20282710563118356 | 0.2028 | yes | equal at 4 dp |
| `s45_eer_gated_sp` | paper/main.tex | §4.5 gated EER, speech | 0.1892 | 0.18922281082789139 | 0.1892 | yes | equal at 4 dp |
| `s45_eer_ann_env` | paper/main.tex | §4.5 component-only EER, environmental | 0.2090 | 0.2089891109115402 | 0.2090 | yes | equal at 4 dp |
| `s45_eer_ann_sp` | paper/main.tex | §4.5 component-only EER, speech | 0.1906 | 0.19057251408358442 | 0.1906 | yes | equal at 4 dp |
| `s45_err_gated_env` | paper/main.tex | §4.5 gated EER absolute error, environmental | 0.0062 | 0.006162005280356653 | 0.0062 | yes | equal at 4 dp |
| `s45_err_gated_sp` | paper/main.tex | §4.5 gated EER absolute error, speech | 0.0013 | 0.00134970325569303 | 0.0013 | yes | equal at 4 dp |
| `s45_pooled_env` | paper/main.tex | §4.5 pooled EER, environmental | 0.4336 | 0.4336190199928597 | 0.4336 | yes | equal at 4 dp |
| `s45_pooled_sp` | paper/main.tex | §4.5 pooled EER, speech | 0.1993 | 0.19931589980746045 | 0.1993 | yes | equal at 4 dp |
| `s45_err_pool_env` | paper/main.tex | §4.5 pooled EER error, environmental | 0.2246 | 0.22462990908131947 | 0.2246 | yes | equal at 4 dp |
| `s45_err_pool_sp` | paper/main.tex | §4.5 pooled EER error, speech | 0.0087 | 0.008743385723876035 | 0.0087 | yes | equal at 4 dp |
| `s45_acds_err_env` | paper/main.tex | §4.5 ACDS(0,1) error under the gate, environmental | 0.0050 | 0.005018345539116287 | 0.0050 | yes | equal at 4 dp |
| `s45_acds_err_sp` | paper/main.tex | §4.5 ACDS(0,1) error under the gate, speech | 0.0006 | 0.0006191351627258257 | 0.0006 | yes | equal at 4 dp |
| `s45_rho_env` | paper/main.tex | §4.5 fraction of P_a excluded, environmental | 0.0734 | 0.07343511450381679 | 0.0734 | yes | equal at 4 dp |
| `s45_rho_sp` | paper/main.tex | §4.5 fraction of P_a excluded, speech | 0.0565 | 0.05648106904231631 | 0.0565 | yes | equal at 4 dp |
| `s45_corrected_env` | paper/main.tex | §4.5 error after correcting only for contamination, environmental | 0.0066 | 0.006579192029979919 | 0.0066 | yes | equal at 4 dp |

## Investigative findings

Two findings are worth recording alongside the table above:

**The 0.0013 vs 0.0014 rounding note.** The naive subtraction of the two printed, already-rounded
Section 4.5 cells gives `0.1906 - 0.1892 = 0.0014`; the paper prints `0.0013` and calls it
"computed before rounding". Recomputing from unrounded values: `component_eer_speech =
0.19057251408358442`, `eer_gated_speech = 0.18922...` (via `acds_gate()['speech']['eer_gated']`),
difference `= 0.00134...`, which rounds to **0.0013**. The paper's printed value is correct; the
apparent "error" is an artifact of subtracting two 4-decimal-rounded numbers instead of the true
values.

**`results/artefacts.json` records a superseded gating convention** (`t2.env.cond` /
`t2.speech.cond`: 0.2022/0.1886, errors 0.0068/0.0019, distinct from the paper's printed
0.2028/0.1892, errors 0.0062/0.0013). `recompute.table2()` still computes it internally for
historical/audit-trail reasons; it is not what `paper_numbers.yaml` checks the paper against
(`acds_gate()` in `src/pooling_audit/acds_artefacts.py` is), and `results/README.md` documents
which fields are which.

### Reproducibility pipeline

See `reproduce.py`, `data/checksums.txt` and `MANIFEST.sha256`. `requirements.txt`
pins exact versions.

Seeds: this entire audit re-scores already-computed, fixed per-clip score files (`scores/*.npz`);
it never retrains anything, so the project's three training seeds (1337/1338/1339) are properties
of *how those score files were produced*, not of anything this audit recomputes. Table 1's
per-seed values and their standard deviation are read directly from the committed per-seed score
files, not resampled, so no seed is "set" by this audit.

