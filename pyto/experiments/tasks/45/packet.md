# Task 45

Intent: KT answers: five questions from the local session (what moved registry to OS and what is unproved; which corrections overturned the most and where the old assumptions survive; glue that holds real methods; what a successor would follow and miss; when a question advanced the project) answered from the record at pyto/research/kt-answers.md
Starting point: 313711fbecffb6e22cfbe9e4afe4f3eef5df8384 (land(task-44): the suite runs on three operating systems in CI: a GitHub Action runs check_all.sh on ubuntu, macos and windows on every push to the sprint branch, with the neat selftest and the students grader, so portability is a check with a receipt)
Verify: test -f pyto/research/kt-answers.md && grep -q '^## 5' pyto/research/kt-answers.md
Allow: pyto/research/kt-answers.md pyto/research/START-HERE.md pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/research/START-HERE.md
- A  pyto/research/kt-answers.md

```
pyto/research/START-HERE.md |  2 ++
 pyto/research/kt-answers.md | 81 +++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 83 insertions(+)
```

## Evidence

- verify: `test -f pyto/research/kt-answers.md && grep -q '^## 5' pyto/research/kt-answers.md` exit 0 (evidence/verify.txt)
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
