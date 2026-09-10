# Task 59

Intent: the studio's runtime runs chains: exec.js under parallel: true no longer refuses a Tick whose Calculation reads a sibling's produce; such a Tick runs in declared order with each result published as it goes (a chain), a Tick with no sibling reads runs at once as before; two siblings declaring one address is still refused; the run record's schedule says which Ticks ran as chains; tests in tests/core.test.js
Starting point: 7ef7ea8a107987f50ec6af2a0c1ec5130f3cf6a1 (board: **started** `task-58`: the laws read chains: tick_laws.py, px laws and t)
Verify: node --test tests/*.test.js
Allow: src/core/exec.js src/runtime.js tests pyto/viewer/adapters.js pyto/viewer/RECORD.md pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/core/exec.js
- M  tests/core.test.js

```
src/core/exec.js   |  71 +++++++++++++++++++++++--------------
 tests/core.test.js | 102 ++++++++++++++++++++++++++++++++++++++++++-----------
 2 files changed, 126 insertions(+), 47 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.twMwmzS1Bm) (evidence/check_all.txt)
    suite                         tests  status
    library                         327  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} LawsParity: exec.js's docstring used to claim it refuses exactly the Ticks pyto/experiments/tick-laws/tick_laws.py refuses; at this starting point tick_laws.py still flags a sibling read as a node-law violation and task 58 is changing it separately, so the docstring now states the laws on its own and does not claim the two readers agree until 58 lands.
{?} SerialMode: a serial run's schedule (written only when budgeted) carries no per-Tick `mode`, matching RECORD.md's "absent means serial" for placement; the owner may prefer an explicit 'serial' value there instead of absence.
{?} ViewerRecord: pyto/viewer/adapters.js copies only placements and latency_ms off run.schedule and rejects no extra field, so per this task's rule adapters.js and RECORD.md are untouched: the receipt's `schedule` says which Ticks were chains, but the pyto-run-record@1 the viewer exports does not carry `mode` yet.
{?} RefusalPrefix: the backwards read and the duplicate producer are still refused only under parallel: true and keep the "parallel refused:" message prefix; a serial run is unchanged, where a backwards read reads whatever the board already holds or fails as a missing address.
