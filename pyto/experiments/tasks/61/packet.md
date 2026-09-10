# Task 61

Intent: the Mac's next three: KT-MAC.md's hand-off carries what the three-OS run at 55471ca showed after task 55, so the Mac session starts on facts: macOS bash 3.2 fails neat selftest's 'landing commit' check (land 0 inside the selftest); Windows Git Bash aborts make_class.sh after the first refusal (autocrlf); Windows prints the PQL repr of U+FFFD as \\ufffd in USE.md section 6
Starting point: 92de9b172793baeb08d680fb7b2561df5ef75630 (board: **started** `task-60`: SUBDUE-PxC-PQL moonshot (the owner's last call of)
Verify: grep -q 'landing commit' pyto/KT-MAC.md && grep -q 'ufffd' pyto/KT-MAC.md && grep -q 'make_class.sh' pyto/KT-MAC.md
Allow: pyto/KT-MAC.md pyto/experiments/tasks
Candidate: 1 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/KT-MAC.md

```
pyto/KT-MAC.md | 13 +++++++++++++
 1 file changed, 13 insertions(+)
```

## Evidence

- verify: `grep -q 'landing commit' pyto/KT-MAC.md && grep -q 'ufffd' pyto/KT-MAC.md && grep -q 'make_class.sh' pyto/KT-MAC.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.FsbxTCuef8) (evidence/check_all.txt)
    suite                         tests  status
    library                         330  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
