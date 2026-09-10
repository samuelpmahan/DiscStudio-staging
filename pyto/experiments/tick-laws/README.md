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
`ticks`, and `summary`. Text mode prints each Tick, a summary, and the explicit
fact that no parallel execution exists yet. `--json` emits JSON only; `--check`
uses text mode and exits nonzero on validation or law failure.

Duration values are conservative: an empty Tick has zero work and latency; any
unknown or invalid invocation duration makes that Tick's work and latency
`null`. Run work and critical path are `null` when any Tick is unknown.

The analyzer API is importable:

```python
from tick_laws import analyze_record, analyze_records, load_record, validate_record
```

## Worked students example

The five singleton Ticks have total work and series latency of 0.132211 ms. Mean and Median both bind fn:parse and write distinct Parts px.students.mean and px.students.median; neither depends on the other, so they could share one Tick. That grouping keeps total work at 0.132211 ms and reduces ideal series latency to 0.112981 ms, excluding overhead.

A serial run's latency series is the sum of Tick latencies. If independent branches share a Tick, that Tick's latency is the maximum branch duration while its work remains the sum of branch durations.
