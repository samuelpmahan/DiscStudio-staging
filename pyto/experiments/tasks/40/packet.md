# Task 40

Intent: parallel you can see: the Tick viewer draws a Tick's Calculations side by side when they are parallel branches, prints the Tick's work and latency and the run's critical path, shows placement when the record carries it, and tick_laws names Ticks; the students record is the demo page
Starting point: 53d31d925730b00a954afb7524e4c024d1760ef5 (board: **started** `task-39`: parallel for real and budgets: PcrRun runs the Ca)
Verify: cd pyto && node --test viewer/test/*.test.mjs && cd experiments/tick-laws && python3 -m unittest discover -s . -p 'test_*.py' && python3 tick_laws.py --check ../students/evidence/run-1/record.json
Allow: pyto/viewer/tick-viewer.html pyto/viewer/tick-viewer.js pyto/viewer/embed.mjs pyto/viewer/test pyto/experiments/tick-laws pyto/experiments/students/README.md pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} TickReportShape: the packet asked tick_laws for `"tick": {"index": i, "name": ...}`; `experiments/students/test_students.py` (outside this task's allow list) builds `{tick["tick"]: tick for tick in report["ticks"]}`, so a mapping there is an unhashable key and fails a suite this task must keep green. Shipped as `"tick": <index>` with a sibling `"name"`, which reads the same in text (`Tick 1 Stats: work_ms=...`); say the word and the nested shape lands with that test updated in the same commit.

{?} ContractKeysFailThePythonValidator: `viewer/test/record_schema.py` refuses unknown document fields, so the moment a real record carries `parallel`, `budget`, per-tick `latency_ms` or per-invocation `placement`, `tick_laws.py --check` (which validates through that file) refuses it -- the JS validator ignores them and renders them. `viewer/fixtures/parallel-demo.json` is therefore validated by the JS side only. record_schema.py belongs to another team and was not touched; the four keys need adding to its key tuples before any producer ships them.

{?} LatencyOfASerialTick: latency is `latency_ms` when the record carries it and otherwise the longest branch, for every Tick, including one whose Calculations are a chain -- so such a Tick prints a latency shorter than its work, which is what parallel would buy and not what the Tick took. This is exactly what `tick_laws.py` already reports, so the page and the checker agree; the alternative (sum for a serial Tick, max for a parallel one) would make them disagree.

{?} ViolationLinesStillSayTickIndexOnly: the per-Tick text lines now name the Tick, but law-violation messages still read `... in Tick 0`, because those strings are part of `--json` and the packet fixed `--json` as unchanged otherwise.

{?} PlaybackClockIsNowTheCriticalPath: with a parallel Tick's cards appearing together at the Tick's latency, the playback clock's last event lands on the run's critical path rather than on the sum of every duration; `viewer/test/playback.test.mjs` was rewritten to that law (5 of its tests changed), which is the one place an existing test's expectations were replaced rather than added to.
