# Task 146

Intent: the Pages deploy on main passed its browser check after 145 and failed one step later in scripts/review_checkpoint.mjs, which pins the browser count at 12 (it is 30) and holds a neat item without the frame requirement the review UI carries; the count is the report's own list, the neat item gains the frame requirement, and one script (scripts/verify_pages.sh) replays the workflow's steps locally so the local verify is the deploy's verify
Starting point: 16956cec7e3307f41eed209624ee800d6cff3680 (land(task-145): the Pages deploy on main failed in its own browser check: the served page never mounted because dist carries pyto/viewer but not the painter port the app imports (pyto/consumers/discstudio-card/port/painter), which the embedded harness inlines and so never missed; the build copies the painter port, and the verify serves dist over HTTP and runs the browser test the way the workflow does)
Verify: bash scripts/verify_pages.sh
Allow: scripts/review_checkpoint.mjs .neat/items/DS-STUDIO-02.json scripts/verify_pages.sh package.json pyto/BOARD.md pyto/questions.md
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
