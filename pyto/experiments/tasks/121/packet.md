# Task 121

Intent: renumber the invented Stages to the owner's S4-S7: the nearest-anchor hole assembly becomes the HolesByNearestAnchor fallback, the course graph and the A* round become S7 Pathfinding, and S4/S5/S6 are freed for recovery, the tee-to-badge ray and the straight holes
Starting point: b83025b8e686ff8c61585ab351a86d7e1d9e1c53 (land(task-119): S6 Round: a deterministic search over S5's walkable cells from each tee to its basket and on to the next tee, legs that never cross an obstacle cell, unreachable reported rather than straightened, and the difference from the straight-leg route as a Part)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks
Candidate: 22 files, see below
Evidence: suite exit 0, see below

## Candidate

- R074  src/lab/s4.js  src/lab/holes-nearest.js
- M  src/lab/map.js
- R081  src/lab/s5.js  src/lab/s7course.js
- R079  src/lab/s6.js  src/lab/s7round.js
- M  src/lab/stage-sources.js
- R100  src/lab/stages/S4.args.json  src/lab/stages/HolesByNearestAnchor.args.json
- R095  src/lab/stages/S4.mmd  src/lab/stages/HolesByNearestAnchor.mmd
- R100  src/lab/stages/S5.args.json  src/lab/stages/S7.course.args.json
- R097  src/lab/stages/S5.mmd  src/lab/stages/S7.course.mmd
- R100  src/lab/stages/S6.args.json  src/lab/stages/S7.round.args.json
- R094  src/lab/stages/S6.mmd  src/lab/stages/S7.round.mmd
- M  src/lab/store/lab.json
- R077  src/lab/store/records/S4.invariants.json  src/lab/store/records/HolesByNearestAnchor.invariants.json
- R099  src/lab/store/records/S4.json  src/lab/store/records/HolesByNearestAnchor.json
- R081  src/lab/store/records/S5.invariants.json  src/lab/store/records/S7.course.invariants.json
- R099  src/lab/store/records/S5.json  src/lab/store/records/S7.course.json
- R078  src/lab/store/records/S6.invariants.json  src/lab/store/records/S7.round.invariants.json
- R099  src/lab/store/records/S6.json  src/lab/store/records/S7.round.json
- R090  src/lab/store/records/S6.vs-straight.json  src/lab/store/records/S7.vs-straight.json
- R077  tests/lab-s4.test.js  tests/lab-holes-nearest.test.js
- R080  tests/lab-s5.test.js  tests/lab-s7course.test.js
- R082  tests/lab-s6.test.js  tests/lab-s7round.test.js

```
src/lab/{s4.js => holes-nearest.js}                |  86 +++++++------
 src/lab/map.js                                     |  33 ++---
 src/lab/{s5.js => s7course.js}                     |  77 ++++++------
 src/lab/{s6.js => s7round.js}                      |  97 +++++++--------
 src/lab/stage-sources.js                           |  12 +-
 ...S4.args.json => HolesByNearestAnchor.args.json} |   0
 .../stages/{S4.mmd => HolesByNearestAnchor.mmd}    |   2 +-
 .../stages/{S5.args.json => S7.course.args.json}   |   0
 src/lab/stages/{S5.mmd => S7.course.mmd}           |   2 +-
 .../stages/{S6.args.json => S7.round.args.json}    |   0
 src/lab/stages/{S6.mmd => S7.round.mmd}            |   2 +-
 src/lab/store/lab.json                             | 135 +++++++++++----------
 ...s.json => HolesByNearestAnchor.invariants.json} |  50 ++++----
 .../records/{S4.json => HolesByNearestAnchor.json} |   4 +-
 ...5.invariants.json => S7.course.invariants.json} |  52 ++++----
 src/lab/store/records/{S5.json => S7.course.json}  |   2 +-
 ...S6.invariants.json => S7.round.invariants.json} |  50 ++++----
 src/lab/store/records/{S6.json => S7.round.json}   |   2 +-
 .../{S6.vs-straight.json => S7.vs-straight.json}   |  22 ++--
 .../{lab-s4.test.js => lab-holes-nearest.test.js}  |  48 ++++----
 tests/{lab-s5.test.js => lab-s7course.test.js}     |  44 +++----
 tests/{lab-s6.test.js => lab-s7round.test.js}      |  46 +++----
 22 files changed, 392 insertions(+), 374 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.Q5mfnsCRYr) (evidence/check_all.txt)
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
