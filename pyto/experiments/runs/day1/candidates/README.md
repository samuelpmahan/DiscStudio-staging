# candidates/ (Day 1)

The four reader-*.py files are the reader-phase probes the day was built from: verbatim copies of the session scratchpad's ablation_spike.py, probe_rules.py, probe_projection.py and probe_roundtrip.py (LF, unmodified), retained so that every lane origin can be cited from inside the repository. They were not merged as code; each was superseded by the lane output named below:

- reader-ablation_spike.py -> experiments/grouped-ablation/{features,calculations,program,run}.py (Lane C). Verified grouped ablation: 5 groups x 3 features, leave-one-group-out, ranking drop_g3 > drop_g0 > drop_g1 recovered. The spike hard-codes random.seed(7) at line 6 and its make_data has no seed parameter; the landed features.py threads the seed explicitly (features.py:30-32 make_data(seed, n)) and its Calculations are module-level functions in REGISTRY (the spike's lambdas were not retained).
- reader-probe_rules.py -> tests/test_semantics.py (Lane B; cited as a source at tests/test_semantics.py:9): the fail-loud and silent rules with file:line that the 31 characterization tests pin. Its lambdas are probe inputs only; nothing lambda-shaped was retained.
- reader-probe_projection.py -> tests/test_semantics.py ProjectionTest.test_table_projection_drops_provenance (critic gap 13; cited at tests/test_semantics.py:9).
- reader-probe_roundtrip.py -> cited as a source at tests/test_semantics.py:9 (PQL/PCR/Pcr are not Parts and PCR has no serializer, which the Day 2 retain.py design in research/ULTRACODE-WEEK.md relies on); no Day 1 file is a direct port.

No lane's first draft was rejected in favour of a competing design on Day 1. The only deletion was tests.test_first_class.SharedResultFanoutTest.test_render_disc_result_is_the_same_object_for_both_cards after it survived its mutation in verification round 1 (mutation-kill.md, 'Round 1 history'); it was replaced by test_published_part_is_the_direct_result_object (tests/test_first_class.py:221).
