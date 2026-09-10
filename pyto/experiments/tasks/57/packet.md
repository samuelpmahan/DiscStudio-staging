# Task 57

Intent: chains inside a Tick: the owner, 2026-09-10: 'Calculations inside a Tick must be independent was added as a rule, while your existing ChainSpot program deliberately chains dependent Calculations inside a Tick. Your definition was the moment that sequence becomes inspectable.' The kernel stops refusing a Calculation that binds an earlier sibling's result; inside a Tick the Calculations are a sequence in declared order and the Tick boundary is where the sequence becomes inspectable; a Tick with no sibling reads may run at once, a Tick with them runs in order even under parallel=True; two siblings producing one address is still refused; the decision goes on pyto/questions.md in the owner's words
Starting point: 97f318d4ddc4d9b52162e1736171de2d7caafce5 (land(task-56): the frontier says what the second wave landed: FRONTIER.md's Landed adds gains one line each for tasks 48 (the JS runtime speaks the same schedule), 49 (oc, effects with receipts), 50 (effects on the page), 51 (CI runs to completion), 52 (USE.md, executed) and 55 (green on macOS and Windows), each named by the task's own intent line, so the one file that says what got built is complete at the end of the sprint)
Verify: cd pyto && python -m unittest tests.test_parallel tests.test_multi_into tests.test_use
Allow: pyto/src/pyto/pcr.py pyto/tests pyto/USE.md pyto/questions.md pyto/CHANGES.md pyto/experiments/grouped-ablation/evidence/disc-stats-sidecar.json pyto/experiments/tasks
Candidate: 5 files, see below
Evidence: suite exit 1, see below

## Candidate

- M  pyto/CHANGES.md
- M  pyto/USE.md
- M  pyto/questions.md
- M  pyto/src/pyto/pcr.py
- M  pyto/tests/test_parallel.py

```
pyto/CHANGES.md             |  16 ++++++
 pyto/USE.md                 |  21 +++++---
 pyto/questions.md           |  43 +++++++++++++++
 pyto/src/pyto/pcr.py        | 125 +++++++++++++++++++++++++++-----------------
 pyto/tests/test_parallel.py | 103 ++++++++++++++++++++++++------------
 5 files changed, 220 insertions(+), 88 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_parallel tests.test_multi_into tests.test_use` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 1, last line: SOME SUITES FAILED (logs in /tmp/tmp.lEhBhZ7rML) (evidence/check_all.txt)
    suite                         tests  status
    library                         329  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    203  FAIL
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} SidecarDigest: pyto/experiments/grouped-ablation/evidence/disc-stats-sidecar.json carries pcr.py's source digest and the disc-stats suite rewrites it whenever the kernel changes, so it is on this task's allow list as it was on task 39's; a kernel change that forgets it is refused at landing, which is what happened to this task's first attempt (20260910T041052Z-task-57).
