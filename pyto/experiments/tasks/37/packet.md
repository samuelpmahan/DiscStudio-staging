# Task 37

Intent: the frontier: pyto/FRONTIER.md holds every candidate on the record merged into nine adds, each one OS piece plus the feature that shows it, in the order that reads best; the board points at it; tasks open from adds
Starting point: aec51601d8a123869655dcb11930672ef6afe12d (root: {?} Frontier, the owner's method for planning adds)
Verify: test -f pyto/FRONTIER.md && grep -q '^### A\.' pyto/FRONTIER.md && grep -q '^## Landed adds' pyto/FRONTIER.md && grep -q 'FRONTIER.md' pyto/BOARD.md
Allow: pyto/FRONTIER.md pyto/BOARD.md pyto/LANDING.md pyto/experiments/tasks
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/BOARD.md
- A  pyto/FRONTIER.md
- M  pyto/LANDING.md

```
pyto/BOARD.md    |   6 ++
 pyto/FRONTIER.md | 167 +++++++++++++++++++++++++++++++++++++++++++++++++++++++
 pyto/LANDING.md  |   1 +
 3 files changed, 174 insertions(+)
```

## Evidence

- verify: `test -f pyto/FRONTIER.md && grep -q '^### A\.' pyto/FRONTIER.md && grep -q '^## Landed adds' pyto/FRONTIER.md && grep -q 'FRONTIER.md' pyto/BOARD.md` exit 0 (evidence/verify.txt)
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
