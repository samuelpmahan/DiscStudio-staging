# Task 25

Intent: the hand-off starts with a stopping rule: read the named files and no more, write the one question you would answer by reading another 100k tokens, ask the owner, stop; the answer goes on the root verbatim
Starting point: b558911c59cb9b8ad02073534ffbf27433f5e85b (mirror: removed; the bundle repo is filled by hand when wanted)
Verify: bash pyto/scripts/neat.sh selftest
Allow: pyto/scripts/neat.sh pyto/LANDING.md pyto/questions.md pyto/BOARD.md pyto/experiments/tasks
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/LANDING.md
- M  pyto/questions.md
- M  pyto/scripts/neat.sh

```
pyto/LANDING.md      | 5 +++++
 pyto/questions.md    | 9 +++++++++
 pyto/scripts/neat.sh | 9 +++++++++
 3 files changed, 23 insertions(+)
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
