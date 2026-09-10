# Task 76

Intent: a landing finishes on its own when a candidate deletes a file and starts ignoring it: land.sh step 5 staged each dirty path with git add -A, which is fatal for a deleted path that .gitignore now covers (task 75's landing passed every suite and died at the commit; finished by hand); the stage step now removes a deleted path from the index and adds the rest, and the selftest lands a candidate that deletes and ignores one file
Starting point: 062f39af5030652c84f1436644a89097bf19d78f (land(task-75): crisp, second pass, what the owner settled today: two digests on every proposal, pnc over the Parts and Calculations only and review over structure, labels, prompt and candidates, so a label changes review and never pnc; crisp cards emits a set as Blok cards (root labelled, root unlabelled, each variant) with both digests; a binding may be live or pinned (address, or address plus sha256 that must match the store's value); an A-Star's known and unresolved seed the template's existing Parts and its {?} slots; and partness propagates instead of refusing: a Part computed from a part is a part, its receipt names its basis, force mode records a part binding as basis rather than refusing it, px ls shows provisional values with their basis, and the landing receipt counts provisional Parts; production is gated at promotion, never at binding)
Verify: cd pyto && bash scripts/neat.sh selftest
Allow: pyto/scripts/land.sh pyto/scripts/neat.sh pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/scripts/land.sh
- M  pyto/scripts/neat.sh

```
pyto/scripts/land.sh |  7 ++++++-
 pyto/scripts/neat.sh | 13 +++++++++++++
 2 files changed, 19 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `cd pyto && bash scripts/neat.sh selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.xwzABjkcn0) (evidence/check_all.txt)
    suite                         tests  status
    library                         435  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
