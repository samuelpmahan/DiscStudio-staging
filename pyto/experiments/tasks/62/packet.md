# Task 62

Intent: decisions taken for the owner, to review: pyto/research/decisions-to-review.md lists every default the cloud session took in the owner's place, verified against the record by a second pass, grouped by what a Tick, Calculation, Part and receipt mean, then PQL and px, the viewer and studio, neat and the board, the classroom, CI, docs; each entry names where it sits on the record, whether it is still in force, and the one sentence that overturns it
Starting point: fb8f64311e569d31867b11139316f6da6aa9b220 (land(task-61): the Mac's next three: KT-MAC.md's hand-off carries what the three-OS run at 55471ca showed after task 55, so the Mac session starts on facts: macOS bash 3.2 fails neat selftest's 'landing commit' check (land 0 inside the selftest); Windows Git Bash aborts make_class.sh after the first refusal (autocrlf); Windows prints the PQL repr of U+FFFD as \\ufffd in USE.md section 6)
Verify: test -s pyto/research/decisions-to-review.md && grep -q 'To overturn' pyto/research/decisions-to-review.md
Allow: pyto/research pyto/FRONTIER.md pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 1, see below

## Candidate

- M  pyto/FRONTIER.md
- A  pyto/research/decisions-to-review.md

```
pyto/FRONTIER.md                     |  20 ++
 pyto/research/decisions-to-review.md | 424 +++++++++++++++++++++++++++++++++++
 2 files changed, 444 insertions(+)
```

## Evidence

- verify: `test -s pyto/research/decisions-to-review.md && grep -q 'To overturn' pyto/research/decisions-to-review.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 1, last line: SOME SUITES FAILED (logs in /tmp/tmp.xibzfAsSpW) (evidence/check_all.txt)
    suite                         tests  status
    library                         336  FAIL
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules             5  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
