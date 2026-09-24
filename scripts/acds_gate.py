#!/usr/bin/env python3
"""Section 4.5: predicted applicability -- lambda, rho, the gated EERs and the errors.

    python scripts/acds_gate.py

The gate is read off the submission alone: gamma_a = 1 - sigma(score_original), keep an axis
where gamma_a >= 1/2. lambda is the share of the gated positive set that is a structural zero,
rho the share of the applicable positives the gate drops. Proposition 3 assumes rho = 0; it is
not 0 here, which is why the leak correction makes the error worse on both axes rather than
zero, and why the paper reports the measurement instead of applying the correction.
"""
import _common  # noqa: F401
from pooling_audit.acds_artefacts import acds_gate

g = acds_gate()
print(f"gate: gamma_a >= {g['gate_threshold']}\n")
rows = [
    ("lambda, structural-zero share of the gated positives", "lam"),
    ("rho, share of the applicable positives dropped", "rho"),
    ("ACDS(0,1), annotated partition", "acds_annotated"),
    ("ACDS(0,1), predicted partition", "acds_gated"),
    ("absolute error, predicted vs annotated", "abs_error_gated"),
    ("leak-corrected by (6)", "leak_corrected"),
    ("absolute error after the correction", "abs_error_corrected"),
    ("EER on the gated set, structural zeros kept", "eer_gated"),
    ("component-only EER, annotated partition", "eer_annotated"),
    ("pooled EER, the published protocol", "eer_pooled"),
    ("gated EER error against the annotated value", "err_gated_eer"),
    ("pooled EER error against the annotated value", "err_pooled_eer"),
]
print(f"{'quantity':54s}{'env':>10s}{'speech':>10s}")
for label, key in rows:
    print(f"{label:54s}{g['env'][key]:10.5f}{g['speech'][key]:10.5f}")
print("\nrho > 0 on both axes: Proposition 3's hypothesis is not met on this submission, so (6)")
print("does not apply and the uncorrected value is what the paper reports.")
