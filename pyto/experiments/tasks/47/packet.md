# Task 47

Intent: neat never reuses an id: next_id also counts the landing receipts (task-N, undo-task-N, failed), so an undone or killed task's number is not handed out again; selftest proves it
Starting point: cb5736cfe509c9005ffefed75147ad1ff352bce1 (land(task-40): parallel you can see: the Tick viewer draws a Tick's Calculations side by side when they are parallel branches, prints the Tick's work and latency and the run's critical path, shows placement when the record carries it, and tick_laws names Ticks; the students record is the demo page)
Verify: bash pyto/scripts/neat.sh selftest
Allow: pyto/scripts/neat.sh pyto/LANDING.md pyto/experiments/tasks
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/BOARD.md
- M  pyto/LANDING.md
- M  pyto/scripts/neat.sh

```
pyto/BOARD.md        |  2 ++
 pyto/LANDING.md      |  1 +
 pyto/scripts/neat.sh | 12 ++++++++++++
 3 files changed, 15 insertions(+)
```

## Evidence

- verify: `bash pyto/scripts/neat.sh selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         248  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    249  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             14  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
