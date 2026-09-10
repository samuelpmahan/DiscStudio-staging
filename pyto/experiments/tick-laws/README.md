# Tick laws

`tick_laws.py` validates run-record JSON and checks two observed dependency
laws:

```sh
python pyto/experiments/tick-laws/tick_laws.py --check record.json
python pyto/experiments/tick-laws/tick_laws.py --json record.json
```

The node law reports a Calculation that reads a Part a sibling in the same Tick
produced, and two siblings producing one Part. The loop law reports a read whose
only producers come in later Ticks. A read is every input binding: `px:` bindings
are store reads, `fn:` bindings are result reads resolved through the producer's
`into` (a result read is a read; see `pyto/questions.md`, ResultReadsAreReads),
unioned with `actual_consumes`. A write is `actual_produces` plus the declared
`into`, which may be one address or several.

The report always has `ok`, `valid`, `limitation`, `violations`, `laws`,
`ticks`, and `summary`. A Tick is a step the program named, so it is reported by
that name: each entry of `ticks` is `{"tick": <index>, "name": <the record's tick
name>, "work_ms": ..., "latency_ms": ...}`, and text mode prints
`Tick 1 Stats: work_ms=... latency_ms=...` rather than a bare position. Text mode
also prints a summary and the explicit fact that no parallel execution exists
yet. `--json` emits JSON only; `--check` uses text mode and exits nonzero on
validation or law failure.

Duration values are conservative: an empty Tick has zero work and latency; any
unknown or invalid invocation duration makes that Tick's work and latency
`null`. Run work and critical path are `null` when any Tick is unknown.

The analyzer API is importable:

```python
from tick_laws import analyze_record, analyze_records, load_record, validate_record
```

## Worked students example

The students record now has four Ticks, one of them parallel: Parse, Stats, Letters, Histogram. Stats holds mean and median, which both bind fn:parse and write distinct Parts px.students.mean and px.students.median; neither depends on the other, so the node law passes and the two are branches of one Tick. Stats is therefore the only Tick in that record whose work exceeds its latency -- work is the sum of the two branches, latency is the longer of them -- and the three singleton Ticks have work equal to latency. In the committed `evidence/run-1` that reads as `Tick 1 Stats: work_ms=0.040953000279841945 latency_ms=0.025237000045308378` -- the Stats Tick by name -- with run work_ms=0.110298 against critical_path_ms=0.094582; the exact microseconds move on every re-run, the inequality does not. The Tick viewer draws that same Tick as two cards side by side and prints the same two numbers under it (`pyto/viewer/tick-viewer.js`).

A serial run's latency series is the sum of Tick latencies. If independent branches share a Tick, that Tick's latency is the maximum branch duration while its work remains the sum of branch durations.
