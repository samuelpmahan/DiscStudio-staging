# Task 106

Intent: brain/backend the three findings the night itself produced, as Parts: the judge could not be another session (no route to a scoped worker existed, so every branch was written in one session and the judge is a pure function of the recorded oracle and benchmark Parts - weaker as independence, stronger as evidence, and the bracket says which it is), a copy that did not really merge claims MAIN's commits (neat update stops on a regenerated record, and bringing the copy forward by restoring that one file leaves MAIN's tip not an ancestor, so land.sh computes the candidate from the task's starting point and a verified receipt refuses), and a case that names its engines keeps the refusal in the record; plus the store and the map rebuilt over them
Starting point: 254f751e28aea4736c0d4dd0d99dfc9325f1be52 (land(task-105): brain ml out-of-bag: a random forest scores itself on the rows each of its trees never saw, so a held-out number comes free with the fit; the bag each tree drew is recorded, oob_predict votes only the trees that missed a row, and the oob score is oracled against a real held-out split)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/backend/summary.py
- M  pyto/experiments/brain/store/backend.json

```
pyto/experiments/brain/backend/summary.py |   42 +
 pyto/experiments/brain/store/backend.json | 1499 +++++++++++++++--------------
 2 files changed, 801 insertions(+), 740 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.TOaE62bxLV) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               751  OK
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

{?} both runs are in the packet: the copy's venv (python 3.11, numpy 2.4.6) through the Verify
line, and python 3.12.3 with numpy 2.5.3 and scipy 1.18.1 at
experiments/tasks/106/evidence/verify-python312-numpy253.txt. 751 tests, OK in both.
{?} `the_judge_could_not_be_another_session` is a finding about how this vertical's own evidence
was made, and it is written down because a reader a month from now cannot tell a mechanical judge
from an independent one by looking at the bracket's scores. Every bracket names its judge.
{?} `a_copy_that_did_not_really_merge_claims_mains_commits` is a finding about neat, not about the
brain. It is recorded here rather than fixed here: the brain verticals do not own pyto/scripts, and
the proposal (neat update should not report success unless MAIN's tip is an ancestor afterwards) is
a one-line check someone who does own it should make.
{?} nothing in this task changes a Calculation or an engine: the only source change is
backend/summary.py, and the store and records move because they were rebuilt over it. The brain
suite is unchanged in count except for what the new Parts add to the navigate tests.
