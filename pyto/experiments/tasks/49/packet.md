# Task 49

Intent: oc, effects with receipts: an OperationalCalculation (oc. prefix) may perform effects only through an Effects handle the run gives it (write_text, read_text, now_ms, random, env); every effect is recorded in the receipt and the run record; replay feeds recorded effect results back and refuses a tampered one; fn. Calculations get no effects; px effects lists them; testimony byte-identical observe on and off
Starting point: 46303dd6deb50b05be812d8a07c20e49d68e6205 (board: **started** `task-48`: the JavaScript runtime speaks the same schedule:)
Verify: cd pyto && python3 -m unittest tests.test_receipts tests.test_materialize tests.test_semantics tests.test_first_class tests.test_parallel tests.test_budget tests.test_effects tests.test_px
Allow: pyto/src/pyto/pcr.py pyto/src/pyto/core.py pyto/src/pyto/effects.py pyto/src/pyto/materialize.py pyto/src/pyto/px.py pyto/src/pyto/__init__.py pyto/tests pyto/viewer/RECORD.md pyto/viewer/test/record_schema.py pyto/viewer/test/test_record_schema.py pyto/viewer/fixtures pyto/experiments/grouped-ablation/evidence pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
