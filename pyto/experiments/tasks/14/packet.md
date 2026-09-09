# Task 14

Intent: determinism log oracle survives a different interpreter: the log keeps naming its Python, the comparison normalizes the version and skips by name when the hash algorithm differs
Starting point: 76bc3d2a51c0e5442a0e4e8f519fe7d01484e9f5 (land(task-11): Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test)
Verify: P=.venv/bin/python; [ -x "$P" ] || P=.venv/Scripts/python.exe; (cd pyto/experiments/grouped-ablation && "../../../$P" -m unittest test_replay.DeterminismMatrix -q)
Allow: pyto/experiments/grouped-ablation/test_replay.py pyto/experiments/grouped-ablation/replay.py
Candidate: 1 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/grouped-ablation/test_replay.py

```
pyto/experiments/grouped-ablation/test_replay.py | 8 +++++++-
 1 file changed, 7 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `cd pyto/experiments/grouped-ablation && python -m unittest test_replay.DeterminismMatrix -q` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         144  OK
    experiments/grouped-ablation    240  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           87  OK
    viewer-record-schema             19  OK
    
    ALL SUITES PASSED

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
