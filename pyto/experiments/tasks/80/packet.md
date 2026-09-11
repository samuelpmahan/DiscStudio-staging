# Task 80

Intent: neat delta <a> <b>: the capability delta against cost of two landings, computed not noted: from each landing's receipt and git diff, capability gained (Calculations registered, user actions and controls added, behaviours verified) and cost (files, lines, new pages, new address roots, moved assertions, regenerated fixtures) per candidate, fn.neat.delta.evaluate pure over the two measurements, the Part px.exp.neat.delta.<a>.<b> under pyto/experiments/review/deltas, patterns per repository in a manifest; first record: 78 (a second page over the composer) against 79 (the composer refined)
Starting point: 4916d2b18d4163e9a8e62c3f727f9da8ee5a2130 (board: **started** `task-79`: the preset is the projection layer: the card casc)
Verify: cd pyto && python -m unittest tests.test_neat_delta
Allow: pyto/src/pyto/neat pyto/scripts/neat.sh pyto/tests pyto/experiments/review/deltas pyto/experiments/delta pyto/experiments/tasks pyto/USE.md
Candidate: 9 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/USE.md
- A  pyto/experiments/delta/patterns.json
- A  pyto/experiments/review/deltas/.gitkeep
- A  pyto/experiments/review/deltas/task-78-task-79.json
- A  pyto/experiments/review/deltas/task-78-task-79.record.json
- M  pyto/scripts/neat.sh
- M  pyto/src/pyto/neat/__init__.py
- A  pyto/src/pyto/neat/delta.py
- A  pyto/tests/test_neat_delta.py

```
pyto/USE.md                                        |  16 +
 pyto/experiments/delta/patterns.json               |  15 +
 pyto/experiments/review/deltas/.gitkeep            |   0
 .../experiments/review/deltas/task-78-task-79.json |  82 +++++
 .../review/deltas/task-78-task-79.record.json      | 308 +++++++++++++++++
 pyto/scripts/neat.sh                               |  13 +-
 pyto/src/pyto/neat/__init__.py                     |   3 +-
 pyto/src/pyto/neat/delta.py                        | 372 +++++++++++++++++++++
 pyto/tests/test_neat_delta.py                      | 137 ++++++++
 9 files changed, 943 insertions(+), 3 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_neat_delta` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.lTUteDuJah) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
