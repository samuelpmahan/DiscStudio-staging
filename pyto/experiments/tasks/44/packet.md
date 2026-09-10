# Task 44

Intent: the suite runs on three operating systems in CI: a GitHub Action runs check_all.sh on ubuntu, macos and windows on every push to the sprint branch, with the neat selftest and the students grader, so portability is a check with a receipt
Starting point: ed6cdde98122e2e9f365adf856823e5d2e60e076 (board: **started** `task-43`: a class in a repo and the desk that teaches the t)
Verify: python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/check_all.yml')); print('yaml ok')"
Allow: .github/workflows/check_all.yml pyto/LANDING.md pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  .github/workflows/check_all.yml
- M  pyto/LANDING.md

```
.github/workflows/check_all.yml | 59 +++++++++++++++++++++++++++++++++++++++++
 pyto/LANDING.md                 |  1 +
 2 files changed, 60 insertions(+)
```

## Evidence

- verify: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/check_all.yml')); print('yaml ok')"` exit 0 (evidence/verify.txt)
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
