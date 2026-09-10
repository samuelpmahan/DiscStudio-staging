# Task 26 brief: Ticks as circuits

This task exists because of a question a fresh agent asked under the stopping rule: "what is a
Tick supposed to mean to the person watching?" The owner's answer is on the root of questions,
`pyto/questions.md`, under `{?} TicksAsCircuits` and `{?} WhatIsATick`. Read those two entries
first; they are the design. Then `pyto/viewer/RECORD.md` (the run record contract) and
`pyto/viewer/test/record_schema.py` (the validator you will call). For house style, read
`pyto/experiments/students/grade.py` and its tests.

## The idea in one paragraph

A sequence of Ticks is a series circuit: the same store passes through every Tick, durations add,
one failure stops the run. The Calculations inside one Tick are parallel branches: each sees the
store as it stood when the Tick began, work adds while time is the longest branch. Two laws follow
and both are checkable from a run record today. Node law: inside a Tick, no Calculation consumes a
sibling's produce, and no two siblings produce the same Part. Loop law: nothing consumes a Part
that is produced only later in the run. Ticks are the author's series-parallel drawing over the
true graph the reads and writes define; the node law tests whether the drawing is honest.

## Build `pyto/experiments/tick-laws/`

- `tick_laws.py`: takes one or more `pyto-run-record@1` JSON files. For each: validate with the
  shared validator; check the node law and the loop law using the record's actual consumes and
  produces per invocation; report each violation with the Tick, the invocation ids and the Part;
  compute per Tick `work` (sum of its invocations' durations) and `latency` (max, the parallel
  model), and for the run the series sum of Tick latencies (the critical path under the Tick
  model) against total work. Print one line per Tick and one summary line, and say plainly that no
  parallel execution exists yet and this is what parallel would buy. `--check` exits 0 only if
  every file validates and both laws hold. `--json` prints the report as JSON. Use only the
  record's fields; import nothing from the kernel except the validator.
- `README.md`: half a page. Series, parallel, the two laws in one sentence each, what the numbers
  mean, the limit above. Use the students record as the worked example: if its Mean and Median
  Ticks are independent under the node law, say they could be one Tick.
- `test_tick_laws.py` (unittest): the two committed records pass both laws
  (`../grouped-ablation/evidence/run-1/record.json`, `../students/evidence/run-1/record.json`);
  a record edited in memory so a sibling consumes a sibling's produce fails the node law naming the
  right ids; two siblings producing one Part fails; consuming a later Tick's produce fails the
  loop law; work and latency are right on a tiny hand-built record with known durations; the
  `--check` exit codes. Each test's docstring names the line it guards. Mutation-check two claims
  and say which in the packet.
- Register the suite in `pyto/scripts/check_all.sh` the way the other `experiments/*/test_*.py`
  suites are discovered; pin no counts. One line in `pyto/CHANGES.md`.

## Bounds

No change under `pyto/src`. No new dependency. Small enough that a cold reader can explain it
from the packet alone. One `{?} Label: description` line per real uncertainty in
`pyto/experiments/tasks/26/packet.md` under "## Uncertain".

## Done means

```
cd pyto/experiments/tick-laws && python3 -m unittest discover -s . -p 'test_*.py' \
  && python3 tick_laws.py --check ../grouped-ablation/evidence/run-1/record.json ../students/evidence/run-1/record.json
bash pyto/scripts/check_all.sh     # from the repository root: ALL SUITES PASSED
```

Commit on `exp/26` with messages starting `exp/26:` and push. Do not land, do not touch MAIN,
do not run anything against another branch. If you cannot push to `exp/26`, push to any branch
and say its name. Then stop; the owner's session packs and lands it and writes the board line.
