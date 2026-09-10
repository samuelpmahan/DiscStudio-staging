# Task 44

Intent: the suite runs on three operating systems in CI: a GitHub Action runs check_all.sh on ubuntu, macos and windows on every push to the sprint branch, with the neat selftest and the students grader, so portability is a check with a receipt
Starting point: ed6cdde98122e2e9f365adf856823e5d2e60e076 (board: **started** `task-43`: a class in a repo and the desk that teaches the t)
Verify: python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/check_all.yml')); print('yaml ok')"
Allow: .github/workflows/check_all.yml pyto/LANDING.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
