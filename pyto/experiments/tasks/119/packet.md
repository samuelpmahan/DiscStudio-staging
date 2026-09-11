# Task 119

Intent: S6 Round: a deterministic search over S5's walkable cells from each tee to its basket and on to the next tee, legs that never cross an obstacle cell, unreachable reported rather than straightened, and the difference from the straight-leg route as a Part
Starting point: 4a1048c579a812b9fbe8bac0c3533196d67a7fa6 (land(task-118): the Course route: a capture becomes a course stage by stage on the record, with the canonical raster drawn once and each Stage's produce overlaid on it)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks
Candidate: 10 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/lab/map.js
- A  src/lab/s6.js
- M  src/lab/stage-sources.js
- A  src/lab/stages/S6.args.json
- A  src/lab/stages/S6.mmd
- M  src/lab/store/lab.json
- A  src/lab/store/records/S6.invariants.json
- A  src/lab/store/records/S6.json
- A  src/lab/store/records/S6.vs-straight.json
- A  tests/lab-s6.test.js

```
src/lab/map.js                            |   20 +-
 src/lab/s6.js                             |  295 ++++++++
 src/lab/stage-sources.js                  |    4 +-
 src/lab/stages/S6.args.json               |    1 +
 src/lab/stages/S6.mmd                     |   25 +
 src/lab/store/lab.json                    | 1099 +++++++++++++++++++++++++++-
 src/lab/store/records/S6.invariants.json  |  183 +++++
 src/lab/store/records/S6.json             | 1119 +++++++++++++++++++++++++++++
 src/lab/store/records/S6.vs-straight.json |  157 ++++
 tests/lab-s6.test.js                      |  183 +++++
 10 files changed, 3080 insertions(+), 6 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.c8nDO5jjfT) (evidence/check_all.txt)
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
