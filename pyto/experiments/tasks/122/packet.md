# Task 122

Intent: draw a Stage by the addresses it publishes, not by its number: the Course overlay becomes an address table, the searched round joins the pipeline, and the renumbered S4-S7 draw themselves as they land
Starting point: 10c512c5e985964718dbc7aac45281b615182827 (land(task-120): your discs on the course the studio just built: S4 and S5 in the pipeline and on the raster, and an arrangement that stands the bag's DisplayCards at the holes)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/build.mjs scripts/serve.mjs pyto/experiments/tasks
Candidate: 6 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  scripts/browser_test.py
- M  src/app.js
- M  src/lab/stages.js
- M  src/runtime.js
- M  src/style.css
- M  tests/lab-pipeline.test.js

```
scripts/browser_test.py    |  23 +++-
 src/app.js                 |   3 +-
 src/lab/stages.js          | 321 ++++++++++++++++++++++++++++++---------------
 src/runtime.js             |  23 ++--
 src/style.css              |  10 ++
 tests/lab-pipeline.test.js |  50 ++++++-
 6 files changed, 306 insertions(+), 124 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.GUilrOLvER) (evidence/check_all.txt)
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
