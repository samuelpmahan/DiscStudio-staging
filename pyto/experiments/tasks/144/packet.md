# Task 144

Intent: python -m pyto.study: an honest study of a csv, every step a brain Calculation through an observed PCR, with a store, records and a Tick page
Starting point: 717436e0a26b721fcecd18d23610c1f4ec6201f1 (land(task-143): the owner's answers of 2026-09-12 filed in his words: the export queue (a queued job is instantiated, starts as a Sequence consumed once chosen, a smart start for longer batches), the two battle receipts (in ChainSpot a Receipt IS the text and renders together), single means OnTheCourse's Single Disc as intended, and the canvas stays on the layout until he says otherwise; batch 10 collated under the fixed rule)
Verify: cd pyto && ${PYTHON:-python} -m unittest tests.test_study tests.test_use
Allow: pyto/src/pyto/study.py pyto/tests/test_study.py pyto/scripts/neat.sh pyto/USE.md pyto/experiments/tasks
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/scripts/neat.sh
- A  pyto/src/pyto/study.py
- A  pyto/tests/test_study.py

```
pyto/scripts/neat.sh     |   13 +-
 pyto/src/pyto/study.py   | 1787 ++++++++++++++++++++++++++++++++++++++++++++++
 pyto/tests/test_study.py |  334 +++++++++
 3 files changed, 2133 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_study tests.test_use` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.HOWo28Qboo) (evidence/check_all.txt)
    suite                         tests  status
    library                         472  OK
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
