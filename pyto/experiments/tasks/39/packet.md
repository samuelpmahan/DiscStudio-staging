# Task 39

Intent: parallel for real and budgets: PcrRun runs the Calculations inside a Tick concurrently when the node law holds, records placement per invocation, refuses a sibling result ref at bind time; a run takes a time budget and stops at a Tick boundary with the record saying where; testimony byte-identical serial versus parallel
Starting point: 0debaf30cfd58da2fd65860d320438abe3bbee54 (board: **sprint** 2026-09-10 02:20 UTC on branch claude/os-sprint-st8hnu: the o)
Verify: cd pyto && python3 -m unittest tests.test_receipts tests.test_materialize tests.test_semantics tests.test_first_class tests.test_parallel tests.test_budget
Allow: pyto/src/pyto/pcr.py pyto/src/pyto/materialize.py pyto/tests pyto/viewer/RECORD.md pyto/viewer/test/record_schema.py pyto/viewer/test/test_record_schema.py pyto/viewer/adapters.js pyto/viewer/test/adapters.test.mjs pyto/viewer/fixtures pyto/experiments/grouped-ablation/evidence pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
