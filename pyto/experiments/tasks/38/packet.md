# Task 38

Intent: KT-MAC: chunk 3 notes that questions.sh prints a harmless BrokenPipe traceback after head; chunks 2 and 3 were dry-run as written
Starting point: c805deab9e400fd9bda97f75942b0d5219fc1e55 (land(task-37): the frontier: pyto/FRONTIER.md holds every candidate on the record merged into nine adds, each one OS piece plus the feature that shows it, in the order that reads best; the board points at it; tasks open from adds)
Verify: grep -q 'BrokenPipe' pyto/KT-MAC.md
Allow: pyto/KT-MAC.md pyto/experiments/tasks
Candidate: 1 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/KT-MAC.md

```
pyto/KT-MAC.md | 5 +++--
 1 file changed, 3 insertions(+), 2 deletions(-)
```

## Evidence

- verify: `grep -q 'BrokenPipe' pyto/KT-MAC.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         193  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    248  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             14  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
