# Task 147

Intent: pyto study on a table that is not tiny: a seeded sample where the method's cost is quadratic, a refusal where a training fold is narrower than the fit, the separator and the hole spelling the caller's, the entry point callable in a fresh process, and USE.md section 11
Starting point: abfcfff8466300e7b305c863a52c9dae9c1d3624 (land(task-144): python -m pyto.study: an honest study of a csv, every step a brain Calculation through an observed PCR, with a store, records and a Tick page)
Verify: cd pyto && ${PYTHON:-python} -m unittest tests.test_study tests.test_use
Allow: pyto/src/pyto/study.py pyto/tests/test_study.py pyto/USE.md pyto/experiments/tasks
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/USE.md
- M  pyto/src/pyto/study.py
- M  pyto/tests/test_study.py

```
pyto/USE.md              |  97 +++++++++++++++++++++++++++++++++++++
 pyto/src/pyto/study.py   | 122 +++++++++++++++++++++++++++++++++++++----------
 pyto/tests/test_study.py |  86 +++++++++++++++++++++++++++++++++
 3 files changed, 280 insertions(+), 25 deletions(-)
```

## Evidence

- verify: `cd pyto && ${PYTHON:-python} -m unittest tests.test_study tests.test_use` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.qnV6ftsMUo) (evidence/check_all.txt)
    suite                         tests  status
    library                         477  OK
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
