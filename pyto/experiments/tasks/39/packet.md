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

{?} ScheduleFieldsOptional: the contract says a serial run writes `"placement": null`, but a serial run's record is compared byte for byte against committed evidence by `experiments/students/grade.py` (check 2 drops `duration_ms` and `counters.wall_ms` and nothing else, and `students/` is outside this task's allow list), and `latency_ms` is a wall clock that moves between two identical runs. Taken as the default: the four fields are written **together and only** when the run was parallel, was given a budget, or was stopped by one, so "absent means serial, unbudgeted" is the whole rule in both validators and a serial record is byte for byte what it was. Owner: say the word and `run_record` writes them always, and `students/evidence/run-1/record.json` is regenerated with `latency_ms` added to grade.py's not-compared list.

{?} ParallelFailure: a branch that raises stops the run before anything of its Tick is published, so its siblings' work is discarded and they file no receipts -- the price of "the store never sees half a Tick". `{?} TicksAsCircuits` wants the other reading ("a failing branch leaves its siblings' receipts and shows as a hole downstream"), which needs a partial-Tick publish and a receipt for a Calculation whose Part was never written. Left as it is, with a test only for the atomicity, until the owner picks which of the two the record should show.

{?} ParallelDurations: in a parallel run an invocation's `duration_ms` is measured from the worker picking it up to its Part being published, so it includes the wait for its slowest sibling, and a Tick's `sum(duration_ms)` is therefore *not* the work it would have taken serially. `latency_ms` is exact either way. Alternative: stop the clock when the call returns and leave the publish out of it, which makes the work figure honest and the "what did PCR.run do on this invocation's behalf" reading less so.

{?} WorkerNumbering: `placement.worker` is handed out in the order threads first pick work up **within one Tick**, so it is stable in a run but means nothing across Ticks or across runs, and the same OS thread can be worker 0 in one Tick and worker 1 in the next. Enough to read "these two really did overlap" off a record; not enough to say "the same worker ran both of these".
