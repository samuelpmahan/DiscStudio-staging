# Task 139

Intent: bags that never feel limiting: a disc reads as being in several bags at once (the shelf row names them), one tap adds or removes it from the shelf or from the bag, the order inside a bag is the owner's by arrows or by dragging the grip (one drop, one bag.reorder command, one undo), a bag is duplicated with bag.duplicate and renamed in place, an empty bag invites with the discs you would reach for, and nothing on the shelf side caps a bag
Starting point: e12de747811f49b6f838099fa1d0ee86b1005c5b (land(task-138): the card cascade's header says which preset each projection composes with, and it now says the true one: single composes with layout.singlePresetId (OnTheCourse's Single Disc mode), competition with layout.presetId)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/demo_beats.py pyto/experiments/tasks
Candidate: 6 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  scripts/browser_test.py
- M  scripts/demo_beats.py
- M  src/app.js
- M  src/domain.js
- M  src/style.css
- A  tests/bags.test.js

```
scripts/browser_test.py | 58 +++++++++++++++++++++++++++++++++++++++++++++++++
 scripts/demo_beats.py   |  9 ++++++++
 src/app.js              | 54 +++++++++++++++++++++++++++++++++++++++------
 src/domain.js           | 10 +++++++++
 src/style.css           | 26 ++++++++++++++++++++++
 tests/bags.test.js      | 47 +++++++++++++++++++++++++++++++++++++++
 6 files changed, 197 insertions(+), 7 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.uDKUwKJ6G0) (evidence/check_all.txt)
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
