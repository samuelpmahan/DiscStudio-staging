# Task 87

Intent: brain/backend the facade: fn.brain.backend.<op> with engines py/np/sp for matmul, solve, lstsq, cumsum, histogram, sort, argsort, select_k, pairwise, eig, svd, fft; one place where the json-able, total-order and sign-canonical semantics every engine must meet are pinned, with the py engine as the readable reference and the stubs (general non-symmetric eig, svd's u and v) refused loudly rather than answered wrongly
Starting point: 0b4d8ac18b52ad3ce144fb81492209c3cce2c6e0 (land(task-83): brain ml foundation: the ml vertical's shared core (backend dispatch py/np, matrix helpers, seeded generators, part/oracle/bench/record writers) plus linear regression closed form and gradient descent, ridge, regression metrics (mse/mae/r2) and seeded train-test split and k-fold, each a Calculation fn.brain.ml.<name> with oracle Parts, tests and benchmarks)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain/backend pyto/experiments/tasks
Candidate: 4 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/brain/backend/cases.py
- A  pyto/experiments/brain/backend/ops.py
- A  pyto/experiments/brain/backend/test_ops.py
- M  pyto/experiments/brain/records/ml.regression.json

```
pyto/experiments/brain/backend/cases.py           | 125 +++++
 pyto/experiments/brain/backend/ops.py             | 591 ++++++++++++++++++++++
 pyto/experiments/brain/backend/test_ops.py        | 175 +++++++
 pyto/experiments/brain/records/ml.regression.json |  24 +-
 4 files changed, 903 insertions(+), 12 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.C5ki7INu5C) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               133  OK
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

{?} sp engines that are numpy's: cumsum, sort and argsort have no distinct scipy call worth the
name, so their `sp` engine is numpy's, said out loud in the docstring. The alternative was three
ops with two engines; keeping three engines everywhere keeps the oracle table square.
{?} svd returns singular values only. u and v carry a per-column sign freedom that the engines
spend differently; canonicalising them is real work and it is recorded as a stub in the map part
rather than half-done.
{?} eig refuses a complex spectrum rather than returning `{"real", "imag"}` the way fft does.
fft is always complex so the convention is free; eig is usually real and a caller who gets two
lists back would have to branch. If the ml vertical needs complex eigenvalues, that is a finding.
{?} the py engine of solve refuses a singular matrix at |pivot| < 1e-300, which is a different
question from numpy's condition-number view; the three engines agree on the obvious singular case
that the test pins, and may disagree on a nearly-singular one.
