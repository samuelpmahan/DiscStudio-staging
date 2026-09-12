# Task 145

Intent: the Pages deploy on main failed in its own browser check: the served page never mounted because dist carries pyto/viewer but not the painter port the app imports (pyto/consumers/discstudio-card/port/painter), which the embedded harness inlines and so never missed; the build copies the painter port, and the verify serves dist over HTTP and runs the browser test the way the workflow does
Starting point: 96561d1290183a306dba950876e02961a191e43f (board: **started** `task-144`: python -m pyto.study: an honest study of a csv,)
Verify: npm test && node scripts/build.mjs && node -e "require('fs').accessSync('dist/pyto/consumers/discstudio-card/port/painter/painter.mjs')"
Allow: scripts/build.mjs pyto/experiments/tasks
Candidate: 1 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  scripts/build.mjs

```
scripts/build.mjs | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

## Evidence

- verify: `npm test && node scripts/build.mjs && node -e "require('fs').accessSync('dist/pyto/consumers/discstudio-card/port/painter/painter.mjs')"` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.Bk5cxbEjGF) (evidence/check_all.txt)
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
