# run-3-reinput: seed and n changed

seed=11, n=800 (Day 1: seed=7, n=400); same 5x3 grouping (features.GROUPS) and the same variants list (select_variants({'groups': GROUPS}) is unchanged, so this is literally Day 1's program run over 800 freshly drawn rows instead of 400.

split digest equal to run-1: False -- expected False: split's args include the rows themselves (calculations.py:split), and a new seed and a different n change every row.

Ranking (ablations only): drop_g3 > drop_g0 > drop_g1. The planted ranking (drop_g3 > drop_g0 > drop_g1, features.py TRUE_W) is expected to hold regardless of seed/n (Day 1 kill criterion, verified across seeds 3, 11, 13, 99 in the completeness critic's checks).

Invocations skippable by digest against run-1 (compare_local.explain_changes, unchanged_upstream): ['select']. 'select' is the one id whose inputs, args and external value (features.GROUPS) are byte-identical to run-1 and whose result digest therefore matches -- the only genuinely reusable invocation when just the rows change.
ms saved (run-1 receipts.json duration of the skippable ids): 0.04

Reconstruction required: no. program.py and calculations.py are imported unchanged (program_lines_changed == 0 above); only seed and n (and the rows they produce) differ from run-1.
