# Task 24

Intent: the board says when a task starts, not only when it lands: neat new writes a started line, neat kill a killed line, and land.sh --note writes any one plain line, commits and pushes it
Starting point: 9138dfc3d6a4b90f099ae2570fac4be31a7d0d8d (root: NeatLearning: one repo per client is already the model; two small gaps remain)
Verify: bash pyto/scripts/neat.sh selftest
Allow: pyto/scripts/neat.sh pyto/scripts/land.sh pyto/LANDING.md pyto/BOARD.md pyto/experiments/tasks
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/LANDING.md
- M  pyto/scripts/land.sh
- M  pyto/scripts/neat.sh

```
pyto/LANDING.md      |  5 +++++
 pyto/scripts/land.sh | 19 ++++++++++++++++++-
 pyto/scripts/neat.sh |  4 ++++
 3 files changed, 27 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `bash pyto/scripts/neat.sh selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         155  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    240  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                          103  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
