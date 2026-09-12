# Task 142

Intent: the demo gets a URL: the Pages workflow also deploys on a push to the sprint branch (the owner, 2026-09-12: 'PageRouter'), so the studio, its build, the browser test and the review page go live from claude/os-sprint-st8hnu without a merge to main
Starting point: 2c30a328c2025f1615b8d720961301d567ae4171 (board: **killed** `task-140`: nothing landed; exp/140 is kept)
Verify: node -e "const y=require('fs').readFileSync('.github/workflows/pages.yml','utf8'); if(!/branches: \[main, claude\/os-sprint-st8hnu\]/.test(y)) process.exit(1)"
Allow: .github/workflows/pages.yml pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
