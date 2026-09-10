# run-4-from-retained: split consumed as an external Part

digest(calculations.split(rows=run-1's retained rows)) == run-1 retained result digest for 'split': True -- this is the provenance join to run-1's fn:split by digest.

'split' present in this run's program: False (expected False: it is now an external Part, not a declared invocation).

Skipped Prepare invocations (compare_local.explain_changes(record_1, record_4)['removed']): ['split'].
ms saved (run-1 receipts.json duration of the skipped invocation(s)): 0.05

Reconstruction required: no. program.py and calculations.py are imported unchanged and never edited; only the retained *program dict* (data loaded from evidence/run-1/retained.json) is edited before retain.from_program rebuilds the rest through PCR.calc, which re-applies the writer/id rules exactly as it does for any other retained program (tests/test_retain.py::FromProgram::test_writer_and_id_rules_re_apply_on_import).
