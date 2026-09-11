# Task 129

Intent: the wedge: the Course route off the demo path, and the tease-then-razzle storyboard as a test that screenshots every beat
Starting point: 7169f3c72203eb0d86067bf07346cd04edb1db5f (board: **killed** `task-128`: nothing landed; exp/128 is kept)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/demo_beats.py scripts/build.mjs scripts/serve.mjs pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  scripts/demo_beats.py
- M  src/app.js

```
scripts/demo_beats.py | 208 ++++++++++++++++++++++++++++++++++++++++++++++++++
 src/app.js            |  17 +++--
 2 files changed, 220 insertions(+), 5 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.kBqkbWyGp1) (evidence/check_all.txt)
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
