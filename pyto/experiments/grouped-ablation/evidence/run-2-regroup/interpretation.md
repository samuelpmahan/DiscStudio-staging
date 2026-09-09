# run-2-regroup: cross-cutting 3x5 grouping

CROSS_GROUPS: {'h0': ['f00', 'f04', 'f07', 'f10', 'f13'], 'h1': ['f01', 'f03', 'f08', 'f11', 'f14'], 'h2': ['f02', 'f05', 'f06', 'f09', 'f12']}

split digest equal to run-1 (same seed/n, groups is the only changed input Part): True

Largest |delta vs baseline| across the three cross-cutting drops: 1.5415.
No single drop exceeds +0.9 RMSE: False -- each new group holds exactly one of the three planted-weight features (features.py TRUE_W), the same as Day 1's per-group ablations; the cross-cutting regroup does not concentrate more planted weight into one group than Day 1 did, so it produces a comparably sized, not a larger, RMSE increase.

Invocations skippable by digest against run-1 (compare_local.explain_changes, unchanged_upstream): ['split']. Only 'split' is expected: 'select' changes because the groups external differs; every fit.*/score.*/compare id changes because the variant keys (h0/h1/h2 vs g0..g4) differ, which explain_changes reports as added/removed ids, not a digest drift on a shared id.
ms saved (run-1 receipts.json duration of the skippable ids): 0.044

Reconstruction required: no. program.py and calculations.py are imported unchanged (git diff shows program_lines_changed == 0 above); only the `groups` input Part and the variants list it produces via select_variants differ from run-1.
