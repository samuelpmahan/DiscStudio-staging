# Task 28

Intent: neat pack refuses with a sentence when the packet has no Verify line instead of exiting silently; land.sh runs the verifier and the suite with the repository's venv first on PATH so a bare python3 in a Verify line means the same thing in a copy and on MAIN
Starting point: f2954cc2f053fae8f5b01f6f7ea200773457b317 (land(task-27): a Calculation can produce several Parts: calc(... into=[a, b, ...]) publishes one Part per address from one invocation, the receipt lists every produce with its own digest, the record's produces and writes carry them all, and one-address calls are unchanged byte for byte)
Verify: bash pyto/scripts/neat.sh selftest
Allow: pyto/scripts/neat.sh pyto/scripts/land.sh pyto/LANDING.md pyto/experiments/tasks
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/LANDING.md
- M  pyto/scripts/land.sh
- M  pyto/scripts/neat.sh

```
pyto/LANDING.md      | 4 +++-
 pyto/scripts/land.sh | 4 +++-
 pyto/scripts/neat.sh | 7 +++++--
 3 files changed, 11 insertions(+), 4 deletions(-)
```

## Evidence

- verify: `bash pyto/scripts/neat.sh selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         193  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    244  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             10  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
