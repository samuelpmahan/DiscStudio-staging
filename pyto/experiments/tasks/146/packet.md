# Task 146

Intent: the Pages deploy on main passed its browser check after 145 and failed one step later in scripts/review_checkpoint.mjs, which pins the browser count at 12 (it is 30) and holds a neat item without the frame requirement the review UI carries; the count is the report's own list, the neat item gains the frame requirement, and one script (scripts/verify_pages.sh) replays the workflow's steps locally so the local verify is the deploy's verify
Starting point: 16956cec7e3307f41eed209624ee800d6cff3680 (land(task-145): the Pages deploy on main failed in its own browser check: the served page never mounted because dist carries pyto/viewer but not the painter port the app imports (pyto/consumers/discstudio-card/port/painter), which the embedded harness inlines and so never missed; the build copies the painter port, and the verify serves dist over HTTP and runs the browser test the way the workflow does)
Verify: bash scripts/verify_pages.sh
Allow: scripts/review_checkpoint.mjs .neat/items/DS-STUDIO-02.json scripts/verify_pages.sh package.json pyto/BOARD.md pyto/questions.md
Candidate: 4 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  .neat/items/DS-STUDIO-02.json
- M  package.json
- M  scripts/review_checkpoint.mjs
- A  scripts/verify_pages.sh

```
.neat/items/DS-STUDIO-02.json |  4 ++++
 package.json                  |  1 +
 scripts/review_checkpoint.mjs |  2 +-
 scripts/verify_pages.sh       | 17 +++++++++++++++++
 4 files changed, 23 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `bash scripts/verify_pages.sh` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.7n9oRd5E6y) (evidence/check_all.txt)
    suite                         tests  status
    library                         447  OK
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
