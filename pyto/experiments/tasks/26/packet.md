# Task 26

Intent: Ticks as circuits: tick_laws.py checks any pyto-run-record@1 against the node law (inside a Tick no Calculation consumes a sibling's produce, no two siblings produce one Part) and the loop law (nothing consumes a Part produced later), and reports total work versus critical path per Tick; no kernel change
Starting point: 71e2cbb57866744c6fd1b16665a30fb5844c03fd (root: {?} TicksAsCircuits, the owner's series/parallel question with the mapping as default)
Verify: cd pyto/experiments/tick-laws && python3 -m unittest discover -s . -p 'test_*.py' && python3 tick_laws.py --check ../grouped-ablation/evidence/run-1/record.json ../students/evidence/run-1/record.json
Allow: pyto/experiments/tick-laws pyto/scripts/check_all.sh pyto/CHANGES.md pyto/experiments/tasks
Candidate: 4 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/CHANGES.md
- A  pyto/experiments/tick-laws/README.md
- A  pyto/experiments/tick-laws/test_tick_laws.py
- A  pyto/experiments/tick-laws/tick_laws.py

```
pyto/CHANGES.md                              |   2 +
 pyto/experiments/tick-laws/README.md         |  38 ++++
 pyto/experiments/tick-laws/test_tick_laws.py | 284 +++++++++++++++++++++++++++
 pyto/experiments/tick-laws/tick_laws.py      | 216 ++++++++++++++++++++
 4 files changed, 540 insertions(+)
```

## Evidence

- verify: `cd pyto/experiments/tick-laws && python3 -m unittest discover -s . -p 'test_*.py' && python3 tick_laws.py --check ../grouped-ablation/evidence/run-1/record.json ../students/evidence/run-1/record.json` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         155  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    240  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             10  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

{?} ActualEdgeCoverage: Records often leave `actual_consumes` empty, so this tool deliberately cannot certify all declared or `fn:` dependencies as parallel-safe. It reports only observed actual edges.
{?} TimingSemantics: Run records provide invocation durations, not measured parallel scheduling; work and critical path are a Tick-model estimate, and unknown durations remain null.

- Credit: Codex built what the brief said. The brief specified "actual consumes", which was wrong; Codex's question under the stopping rule ("why doesn't using another Calculation's result count as an actual read?") exposed it, and the fix (result reads are reads, resolved through `into`) was applied on top of Codex's work by the cloud session. The error was the brief's, not Codex's.
