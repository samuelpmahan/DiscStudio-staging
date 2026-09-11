# Task 134

Intent: finding the RIGHT disc: one fn.shelf.query Calculation over the whole shelf, ranked search across every field including plastic, disc type and the flight numbers ('buzzz 177', 'midrange -1'), the quick filters (in this bag, in no bag, has photo), the sorts (recently added, maker, mold, disc type, speed, weight) and grouping by maker or disc type, with a compact and a card view that both keep every disc's own art
Starting point: f4fe05e13fdd5b8556c0d46f1b4271b1f341a2fb (land(task-132): adding a disc is one gesture: the shelf's + opens a composer with the facts that matter first (maker, mold, plastic, weight, colour, photo) and sensible defaults, and one disc.create command through dispatch makes the maker, the mold and the disc together, so one undo takes the whole disc back and nothing is ever named 'My new disc')
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/demo_beats.py pyto/experiments/tasks
Candidate: 7 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  scripts/browser_test.py
- M  scripts/demo_beats.py
- M  src/app.js
- M  src/runtime.js
- A  src/shelf.js
- M  src/style.css
- A  tests/shelf.test.js

```
scripts/browser_test.py |  45 ++++++++++++++++++++
 scripts/demo_beats.py   |  11 +++++
 src/app.js              |  45 ++++++++++++++++----
 src/runtime.js          |  17 +++++++-
 src/shelf.js            | 108 ++++++++++++++++++++++++++++++++++++++++++++++++
 src/style.css           |  27 ++++++++++++
 tests/shelf.test.js     |  90 ++++++++++++++++++++++++++++++++++++++++
 7 files changed, 333 insertions(+), 10 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.SaWpZCu8rg) (evidence/check_all.txt)
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
