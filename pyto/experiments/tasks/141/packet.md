# Task 141

Intent: neat ask surfaces questions, not notes: batch 9 collated 359 items because a {?} line with no Label: form was accepted with its whole sentence as the label, so 88 evidence notes in packets became questions; a question is a labelled {?} Label: text line, prose after {?} is a note the batch counts per task and leaves out, the walk reads such a line as a note instead of failing, and batch 9 as collated is kept as the record of the defect
Starting point: aa83ee97c41128ad428da05564428a35c60d6761 (board: **started** `task-140`: neat ask surfaces questions, not notes: batch 9)
Verify: cd pyto && python -m unittest tests.test_neat_review tests.test_neat_diff tests.test_neat_gate tests.test_neat_delta && python scripts/walk.py --check
Allow: pyto/src/pyto/neat pyto/scripts/walk.py pyto/tests pyto/experiments/review pyto/experiments/tasks
Candidate: 5 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/review/batches/9.json
- A  pyto/experiments/review/runs/ask-9.json
- M  pyto/scripts/walk.py
- M  pyto/src/pyto/neat/review.py
- M  pyto/tests/test_neat_review.py

```
pyto/experiments/review/batches/9.json  | 2927 +++++++++++++++++++++++++++++++
 pyto/experiments/review/runs/ask-9.json | 1671 ++++++++++++++++++
 pyto/scripts/walk.py                    |   12 +-
 pyto/src/pyto/neat/review.py            |   73 +-
 pyto/tests/test_neat_review.py          |   90 +
 5 files changed, 4749 insertions(+), 24 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_neat_review tests.test_neat_diff tests.test_neat_gate tests.test_neat_delta && python scripts/walk.py --check` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.maLwMxW8X7) (evidence/check_all.txt)
    suite                         tests  status
    library                         447  OK
    experiments/brain               756  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
