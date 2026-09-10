# Task 35

Intent: students: grade.py check 4 matches each Tick as a list line of its own on the hand-off page, not as a substring anywhere, so deleting one step's line is caught even when the name appears elsewhere; the missing-Tick test removes Stats
Starting point: 1f8f671a766aac70dd5de81299a03fb700a64af1 (board: **started** `task-34`: interrupts are typed and a shared desk is graded)
Verify: cd pyto/experiments/students && python3 -m unittest discover -s . -p 'test_*.py' && python3 grade.py --run evidence/run-1 --handoff HANDOFF.md
Allow: pyto/experiments/students pyto/CHANGES.md pyto/experiments/tasks
Candidate: 4 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/CHANGES.md
- M  pyto/experiments/students/README.md
- M  pyto/experiments/students/grade.py
- M  pyto/experiments/students/test_students.py

```
pyto/CHANGES.md                            |   2 +
 pyto/experiments/students/README.md        |  10 ++-
 pyto/experiments/students/grade.py         |  65 +++++++++++++++--
 pyto/experiments/students/test_students.py | 112 ++++++++++++++++++++++++-----
 4 files changed, 166 insertions(+), 23 deletions(-)
```

## Evidence

- verify: `cd pyto/experiments/students && python3 -m unittest discover -s . -p 'test_*.py' && python3 grade.py --run evidence/run-1 --handoff HANDOFF.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         193  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    248  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             14  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} DecidedLineWentIntoTask29sPacket: the brief said to replace the `{?} MissingTickTestStillRemovesHistogram` note by adding "- Decided: check 4 needs one list line per Tick; the substring gap from task 29 is closed." to packet.md's Uncertain section. The note lives in `tasks/29/packet.md`, so the Decided line replaced it there (with a parenthetical saying it was settled in task 35) rather than being added here, where it would leave the note itself standing. If the owner wanted the line in this packet instead, it is one move.
