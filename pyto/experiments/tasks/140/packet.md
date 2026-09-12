# Task 140

Intent: neat ask surfaces questions, not notes: batch 9 collated 359 items because every packet's Uncertain section is harvested whether it carries a {?} label or an evidence note; collate keeps only {?}-labelled items and filed defaults, ranks the owner's open ones first, and the batch says how many notes it left out; batch 9 as collated tonight is kept as the record of the defect
Starting point: 9ac0f53aca6d79464400fcb658e85ad956539468 (land(task-139): bags that never feel limiting: a disc reads as being in several bags at once (the shelf row names them), one tap adds or removes it from the shelf or from the bag, the order inside a bag is the owner's by arrows or by dragging the grip (one drop, one bag.reorder command, one undo), a bag is duplicated with bag.duplicate and renamed in place, an empty bag invites with the discs you would reach for, and nothing on the shelf side caps a bag)
Verify: cd pyto && python -m unittest tests.test_neat_review
Allow: pyto/src/pyto/neat pyto/tests pyto/experiments/review pyto/experiments/tasks
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

- verify: `cd pyto && python -m unittest tests.test_neat_review` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.jBET5BDSaG) (evidence/check_all.txt)
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
