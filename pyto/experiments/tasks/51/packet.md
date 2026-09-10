# Task 51

Intent: CI runs to completion: check_all.yml no longer cancels a run in progress when the next landing pushes, and skips pushes that touch only the board or the landing receipts, so every landing gets its three-OS receipt
Starting point: 41a1e1e907baaff4aaca965222b5a63d2ac0e258 (land(task-46): the suite is green on three OSes and two Python versions: the grouped-ablation suite fails on CI under Python 3.12 (ubuntu and windows) and the students grader fails on windows; find the cause from the CI logs and a local Python 3.10 run, fix it in the tests or the scripts without regenerating evidence, and make check_all.yml upload the per-suite logs as the receipt)
Verify: python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/check_all.yml')); assert d['concurrency']['cancel-in-progress'] is False; assert 'paths-ignore' in d[True]['push']; print('yaml ok')"
Allow: .github/workflows/check_all.yml pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
