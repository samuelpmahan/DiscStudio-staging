# Task 55

Intent: green on macOS and Windows: the three failures at a9e3b1a were the tests, not the kernel. test_use.py compares CRLF stdout on Windows to LF text; test_classroom.py spells bash so Windows resolves WSL's instead of Git's; test_parallel's overlap check gave four threads 50 ms to start and a slow macOS runner took 114. Each test is made true on the platform it runs on without loosening what it proves
Starting point: 48d08984047b080ed8b2edbd5ccb335f0f93de09 (board: **killed** `task-53`: nothing landed; exp/53 is kept)
Verify: cd pyto && python -m unittest tests.test_use tests.test_parallel && python -m unittest discover -s experiments/classroom -p 'test_*.py'
Allow: pyto/tests/test_use.py pyto/tests/test_parallel.py pyto/experiments/classroom/test_classroom.py pyto/experiments/tasks
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/classroom/test_classroom.py
- M  pyto/tests/test_parallel.py
- M  pyto/tests/test_use.py

```
pyto/experiments/classroom/test_classroom.py |  8 +++++++-
 pyto/tests/test_parallel.py                  | 28 +++++++++++++++++++++++-----
 pyto/tests/test_use.py                       |  9 ++++++++-
 3 files changed, 38 insertions(+), 7 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_use tests.test_parallel && python -m unittest discover -s experiments/classroom -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.HNNDXdMwZn) (evidence/check_all.txt)
    suite                         tests  status
    library                         327  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
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
{?} ThreeCoreRunner: macos-latest has 3 cores and the Fan Tick has 4 branches, so its pool is 3 workers and the fourth branch can never overlap the first three there. The overlap test now asserts min(branches, cpu_count) branches started before the first finished. The latency test two below it still expects the Fan Tick under 150 ms (4 x 50 x 0.75); on 3 cores that is two rounds, about 100 ms plus thread start, and a slow runner could cross it. Left as is until it fails once; cure would be the same measured-against-the-branches shape.
{?} WindowsNewlines: the CRLF undo is in test_use.py's run_block, Windows only, before the byte comparison. The alternative was to reconfigure stdout inside every USE.md block, which would have put a Windows line in a document meant to be read. The document stays clean; the test carries the platform.
