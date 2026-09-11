# Task 111

Intent: the brain on the disc shelf: one PxC program over the studio's own material, the seven molds' flight numbers and the twelve discs' weights as dataset Parts, four Ticks (describe, correlate, cluster, regress) through the brain's Calculations, observed, with the record the Tick viewer draws
Starting point: 712a3ca7bac99caa8ebe4043d6b33f2613acd211 (land(task-110): brain/ml the kerchoo slice: the ml facade defaults to the plan instead of to py - ml/core.py's dispatch reads px.exp.brain.result.backend.plan when the caller names no engine, the plan is extended to the ml calcs that have bench Parts, py stays the reference and is still selectable by name - with knn_predict and softmax_fit re-benched and their rows appended to px.exp.brain.bench.kerchoo, and a finding for every ml calc that has no faster engine to choose)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py' && BRAIN_RECORDS=commit python -m experiments.brain.shelf
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/brain/records/brain_shelf.json
- A  pyto/experiments/brain/shelf.py
- A  pyto/experiments/brain/store/shelf.json

```
pyto/experiments/brain/records/brain_shelf.json | 465 ++++++++++++++++++++++++
 pyto/experiments/brain/shelf.py                 |  69 ++++
 pyto/experiments/brain/store/shelf.json         | 260 +++++++++++++
 3 files changed, 794 insertions(+)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py' && BRAIN_RECORDS=commit python -m experiments.brain.shelf` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.ND9n6sAJGI) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
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
