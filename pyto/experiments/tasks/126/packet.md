# Task 126

Intent: the port's map, honest after the renumbering: S4-S7 under ran, the stubs that S4 recovery actually retired removed, and what S7 still owes the straight holes written down as the next step with its for
Starting point: b396f603875af8f71ad3009f8ca02c369780fe3d (land(task-124): S5 Tee->Badge and S6 straight holes: a tee's pointing end read off its own pixels, the ray cast at the badge it points at, and the basket found by continuing that ray past the badge -- three points on a line, with the badges whose ray finds nothing reported as doglegs)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/lab/map.js
- M  src/lab/store/lab.json

```
src/lab/map.js         |  9 +++++----
 src/lab/store/lab.json | 22 +++++++++++++---------
 2 files changed, 18 insertions(+), 13 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.2qybBzDbJN) (evidence/check_all.txt)
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
