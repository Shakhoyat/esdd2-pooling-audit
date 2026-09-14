#!/usr/bin/env python3
"""Section 4.4: applicability is nearly free, and why that is a format artefact."""
import _common  # noqa: F401
from pooling_audit.recompute import dataset_counts, s4_format_confound

f = s4_format_confound()
c = dataset_counts()
print(f"sample-rate rule, full split:        F1 {f['header_rule_f1']:.4f}")
print(f"  share of inapplicable rows that are not 16 kHz mono: "
      f"{c['inapplicable_not_16k_mono_pct']:.0f}%")
print(f"format-matched subset: {f['n_fm_inapplicable']} inapplicable "
      f"against {f['n_fm_applicable']} applicable")
print(f"  sample-rate rule AUC there:        {f['header_auc_format_matched']:.4f} "
      f"(constant on the subset, so exactly one half)")
print(f"  submitted original-score gate:     {f['gate_auc_format_matched']:.4f}")
print(f"  same gate on the full split:       {f['gate_auc_full']:.4f}")
