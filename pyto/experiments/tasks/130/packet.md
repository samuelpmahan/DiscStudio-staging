# Task 130

Intent: every disc looked the same: the painter port (2026-09-09) replaced the per-disc hue with one fixed base and accent for every disc that has no authored art colours, so twelve discs painted one wind-rose in one grey-green; a disc's sample hue is its colours again (base and accent derived from sampleHue when artBase/artAccent are not authored, exactly the original prepareDiscArt's rule), the sanitised-colour test expects the disc's own defaults, and the two art-bearing fixtures are regenerated from the real runtime
Starting point: 50746348e4094e3ee1e374399019fff15130b966 (land(task-129): the wedge: the Course route off the demo path, and the tease-then-razzle storyboard as a test that screenshots every beat)
Verify: npm test
Allow: src tests pyto/viewer/fixtures pyto/viewer/test pyto/experiments/tasks
Candidate: 5 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/viewer/fixtures/discstudio-display-card.json
- M  src/presentation.js
- M  src/seed.js
- M  tests/core.test.js
- M  tests/fixtures/serial-run-record.json

```
pyto/viewer/fixtures/discstudio-display-card.json | 142 ++++++++++++------
 src/presentation.js                               |  32 +++-
 src/seed.js                                       |   4 +-
 tests/core.test.js                                |   4 +-
 tests/fixtures/serial-run-record.json             | 171 +++++++++++++---------
 5 files changed, 237 insertions(+), 116 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.GJ1oeigYmq) (evidence/check_all.txt)
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
