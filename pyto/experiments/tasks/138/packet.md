# Task 138

Intent: the card cascade's header says which preset each projection composes with, and it now says the true one: single composes with layout.singlePresetId (OnTheCourse's Single Disc mode), competition with layout.presetId
Starting point: d9645ccf249355f6880cc5e30b898511a8cd7cb8 (land(task-137): SingleCard and the export queue: Single Disc mode composes one disc with a spotlight design made for it (the photo large, the numbers legible, a winner mark that scales, the score/highlight/winner it has in the battle, an export named after the disc), and every export is a queued job that runs in order - all states, this battle vertical, every disc in the battle - each leaving an export.record receipt and a file, the queue surviving navigation, failures as sentences)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/demo_beats.py pyto/experiments/tasks
Candidate: 1 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/cards.js

```
src/cards.js | 6 ++++--
 1 file changed, 4 insertions(+), 2 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.xBHK6rm6wx) (evidence/check_all.txt)
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
