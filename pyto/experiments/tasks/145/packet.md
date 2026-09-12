# Task 145

Intent: the Pages deploy on main failed in its own browser check: the served page never mounted because dist carries pyto/viewer but not the painter port the app imports (pyto/consumers/discstudio-card/port/painter), which the embedded harness inlines and so never missed; the build copies the painter port, and the verify serves dist over HTTP and runs the browser test the way the workflow does
Starting point: 96561d1290183a306dba950876e02961a191e43f (board: **started** `task-144`: python -m pyto.study: an honest study of a csv,)
Verify: npm test && node scripts/build.mjs && node -e "require('fs').accessSync('dist/pyto/consumers/discstudio-card/port/painter/painter.mjs')"
Allow: scripts/build.mjs pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
