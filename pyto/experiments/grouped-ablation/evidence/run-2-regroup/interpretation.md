# run-2-regroup: cross-cutting 3x5 grouping

CROSS_GROUPS: {'h0': ['f00', 'f04', 'f07', 'f10', 'f13'], 'h1': ['f01', 'f03', 'f08', 'f11', 'f14'], 'h2': ['f02', 'f05', 'f06', 'f09', 'f12']}

split digest equal to run-1 (same seed/n, groups is the only changed input Part): True

## The plan's predicted bound, measured

research/ULTRACODE-WEEK.md Day 2 predicts: "no single drop exceeds +0.9 RMSE because each group holds at most two planted weights".
Largest |delta vs baseline| across the three cross-cutting drops: 1.8503.
No single drop exceeds +0.9 RMSE: False.
The predicted bound is REFUTED by measurement: 1.8503 against the predicted <= 0.9.
Run-1's largest |delta vs baseline| (evidence/run-1/comparison.json): 1.8653. This regroup is larger than run-1: False.
Planted |w| per group -- Day 1 (features.GROUPS): {'g0': 1.5, 'g1': 0.8, 'g2': 0, 'g3': 2.0, 'g4': 0}; this run (CROSS_GROUPS): {'h0': 1.5, 'h1': 0.8, 'h2': 2.0}.
Largest planted |w| in any one group: Day 1 2.0, cross-cutting 2.0; the regroup concentrates more planted weight into one group than Day 1 did: False.
Nonzero-weight features per group -- Day 1: {'g0': 1, 'g1': 1, 'g2': 0, 'g3': 1, 'g4': 0}; this run: {'h0': 1, 'h1': 1, 'h2': 1}.

## What changed against run-1, as compare_local.explain_changes reports it

Invocations skippable by digest (unchanged_upstream): ['split']. ms saved (run-1 receipts.json duration of those ids): 0.062
Ids only in this run (added): ['fit.drop_h0', 'fit.drop_h1', 'fit.drop_h2', 'score.drop_h0', 'score.drop_h1', 'score.drop_h2']
Ids only in run-1 (removed): ['fit.drop_g0', 'fit.drop_g1', 'fit.drop_g2', 'fit.drop_g3', 'fit.drop_g4', 'score.drop_g0', 'score.drop_g1', 'score.drop_g2', 'score.drop_g3', 'score.drop_g4']
Ids present in BOTH programs whose retained state changed, with the reason explain_changes computed: {'select': 'external', 'fit.all': 'args', 'compare': 'input'}
  fit.all: run-1 args={'columns': ['f00', 'f01', 'f02', 'f03', 'f04', 'f05', 'f06', 'f07', 'f08', 'f09', 'f10', 'f11', 'f12', 'f13', 'f14'], 'variant': 'all'} -> run-2 args={'columns': ['f00', 'f04', 'f07', 'f10', 'f13', 'f01', 'f03', 'f08', 'f11', 'f14', 'f02', 'f05', 'f06', 'f09', 'f12'], 'variant': 'all'}

Reconstruction required: no. program.py and calculations.py are imported unchanged (git diff against 1c5447f49545690bfd24450a07dfbd517ba95ddb shows program_lines_changed {'program.py': 0, 'calculations.py': 0, 'total': 0}); only the `groups` input Part and the variants list it produces via select_variants differ from run-1.
