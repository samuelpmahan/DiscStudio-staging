# Task 32

Intent: a score in the receipt: a verifier can print one line 'score: <passed> of <total>' and land.sh keeps it in the landing receipt and the Today line; neat list shows the score beside each landed task; verifiers that print no score are unchanged
Starting point: 06337e2f044e30990a8f749f0ae538e40847980c (land(task-30): every reader handles several produces: compare_local.py and pql_document.py in grouped-ablation stop assuming one into per invocation; tests for both)
Verify: bash pyto/scripts/neat.sh selftest && bash pyto/scripts/check_receipts.sh
Allow: pyto/scripts/neat.sh pyto/scripts/land.sh pyto/scripts/check_receipts.sh pyto/LANDING.md pyto/experiments/tasks
Candidate: 4 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/LANDING.md
- M  pyto/scripts/check_receipts.sh
- M  pyto/scripts/land.sh
- M  pyto/scripts/neat.sh

```
pyto/LANDING.md                |  4 ++++
 pyto/scripts/check_receipts.sh | 25 ++++++++++++++++++++++++-
 pyto/scripts/land.sh           | 23 +++++++++++++++++++----
 pyto/scripts/neat.sh           | 32 ++++++++++++++++++++++++++++----
 4 files changed, 75 insertions(+), 9 deletions(-)
```

## Evidence

- verify: `bash pyto/scripts/neat.sh selftest && bash pyto/scripts/check_receipts.sh` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         193  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    248  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             11  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} Score column: `neat list` grew a fourth column (`id state files score intent`) instead of reusing the
`files` position, so a landed task keeps room for both counts; open and packed rows print `-` there because
nothing has landed for them yet. If the owner would rather keep three columns, `files` is the one to reuse.
{?} Several score lines: the LAST line matching `^score: N of M` wins, so a verifier that scores parts can
print a total at the end; the alternative (sum them, or refuse more than one) was not taken.
{?} Refused landings: the refusal's board line carries ` score N/M`, but the failed receipt under
`landings/failed/` still has no `score` field -- only the landing receipt gained one, as the packet asked.
{?} Which receipt `neat list` reads: the newest `<stamp>-task-<id>` landing, so a task landed twice shows its
latest score; `undo-task-<id>` receipts are deliberately not matched.
