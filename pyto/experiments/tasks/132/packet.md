# Task 132

Intent: adding a disc is one gesture: the shelf's + opens a composer with the facts that matter first (maker, mold, plastic, weight, colour, photo) and sensible defaults, and one disc.create command through dispatch makes the maker, the mold and the disc together, so one undo takes the whole disc back and nothing is ever named 'My new disc'
Starting point: c0ee1b08d53898804afe4927f85f9e5a4b131085 (board: **started** `task-131`: art assignment as a Calculation over the set, no)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/demo_beats.py pyto/experiments/tasks
Candidate: 6 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  index.html
- M  scripts/browser_test.py
- M  src/app.js
- M  src/domain.js
- M  src/style.css
- M  tests/core.test.js

```
index.html              |  2 +-
 scripts/browser_test.py | 31 +++++++++++++++++++++++++
 src/app.js              | 62 ++++++++++++++++++++++++++++++++++++++-----------
 src/domain.js           | 28 ++++++++++++++++++++++
 src/style.css           | 20 ++++++++++++++++
 tests/core.test.js      | 29 +++++++++++++++++++++++
 6 files changed, 157 insertions(+), 15 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.MPxGhfmUIM) (evidence/check_all.txt)
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
