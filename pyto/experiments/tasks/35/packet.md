# Task 35

Intent: students: grade.py check 4 matches each Tick as a list line of its own on the hand-off page, not as a substring anywhere, so deleting one step's line is caught even when the name appears elsewhere; the missing-Tick test removes Stats
Starting point: 1f8f671a766aac70dd5de81299a03fb700a64af1 (board: **started** `task-34`: interrupts are typed and a shared desk is graded)
Verify: cd pyto/experiments/students && python3 -m unittest discover -s . -p 'test_*.py' && python3 grade.py --run evidence/run-1 --handoff HANDOFF.md
Allow: pyto/experiments/students pyto/CHANGES.md pyto/experiments/tasks
Candidate: 5 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/CHANGES.md
- M  pyto/experiments/students/README.md
- M  pyto/experiments/students/grade.py
- M  pyto/experiments/students/test_students.py
- M  pyto/experiments/tasks/29/packet.md

```
 pyto/CHANGES.md                            |   2 +
 pyto/experiments/students/README.md        |  10 ++-
 pyto/experiments/students/grade.py         |  65 +++++++++++++++--
 pyto/experiments/students/test_students.py | 112 ++++++++++++++++++++++++-----
 pyto/experiments/tasks/29/packet.md        |   3 +-
 5 files changed, 168 insertions(+), 24 deletions(-)
```

HANDOFF.md is unchanged: its four Tick bullets are already `- **Name** -- ...`, which
is one of the three accepted forms. `evidence/run-1` is unchanged: nothing in the
program moved, so there is nothing to regenerate.

## Evidence

- verify: `cd pyto/experiments/students && python3 -m unittest discover -s . -p 'test_*.py' && python3 grade.py --run evidence/run-1 --handoff HANDOFF.md` exit 0 (evidence/verify.txt)
    Ran 14 tests -- OK
    PASS  4 hand-off
            one list line each for all 4 Tick(s): Parse, Stats, Letters, Histogram
            names all 8 file(s)
    mechanical: 4 of 4 checks passed
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
    viewer                          107  OK
    viewer-record-schema             24  OK
- mutation: `grade.py:check_handoff` back to the task-29 rule (`name not in handoff_text`) -> Handoff.test_a_missing_stats_line_fails_check_four_even_though_the_prose_says_stats fails (grade exits 0 where 1 was asserted): killed.
- mutation: `grade.py:names_tick` loosened to `name in bullet` -> Handoff.test_the_three_accepted_bullet_forms_and_nothing_else fails on `"*Mean* and *Median* live in Stats"`: killed.

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} DecidedLineWentIntoTask29sPacket: the brief said to replace the `{?} MissingTickTestStillRemovesHistogram` note by adding "- Decided: check 4 needs one list line per Tick; the substring gap from task 29 is closed." to packet.md's Uncertain section. The note lives in `tasks/29/packet.md`, so the Decided line replaced it there (with a parenthetical saying it was settled in task 35) rather than being added here, where it would leave the note itself standing. If the owner wanted the line in this packet instead, it is one move.
