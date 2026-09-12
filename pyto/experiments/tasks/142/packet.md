# Task 142

Intent: the demo gets a URL: the Pages workflow also deploys on a push to the sprint branch (the owner, 2026-09-12: 'PageRouter'), so the studio, its build, the browser test and the review page go live from claude/os-sprint-st8hnu without a merge to main
Starting point: 2c30a328c2025f1615b8d720961301d567ae4171 (board: **killed** `task-140`: nothing landed; exp/140 is kept)
Verify: node -e "const y=require('fs').readFileSync('.github/workflows/pages.yml','utf8'); if(!/branches: \[main, claude\/os-sprint-st8hnu\]/.test(y)) process.exit(1)"
Allow: .github/workflows/pages.yml pyto/experiments/tasks
Candidate: 1 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  .github/workflows/pages.yml

```
.github/workflows/pages.yml | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

## Evidence

- verify: `node -e "const y=require('fs').readFileSync('.github/workflows/pages.yml','utf8'); if(!/branches: \[main, claude\/os-sprint-st8hnu\]/.test(y)) process.exit(1)"` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.jOMz1LkcXI) (evidence/check_all.txt)
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
