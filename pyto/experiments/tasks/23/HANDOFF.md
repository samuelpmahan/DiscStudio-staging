# Task 23: students: a homework-sized PCR with a hand-off page graded mechanically by grade.py, leaving only the plain-words explanation to a cold reader; no kernel change

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/23
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/23:pyto/experiments/tasks/23/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff d13fcd1 origin/exp/23 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
```

## Why this repository is worth twenty minutes

pyto is a Python transfer of a design the owner proved three times in JavaScript and TypeScript
(ChainSpot, ChessLab, EmbodiedWumpusWorld): a store of named values (PxC), pure functions over them
(Calculations), and a program that names which functions run in which order (a PCR, made of Ticks).
Every run leaves receipts: what each function read and wrote, how long it took, and a digest of its
source. From receipts you get three things for free: a cache (same inputs and digest, skip the call,
also across processes), a replay that verifies a shipped record in a fresh process, and a per-Tick
view of what the algorithm used. The founding need is the last one: the owner's course-map parser
had to fit five seconds on a phone, and nothing it used was visible. pyto is the workshop where that
visibility is designed before it is stripped for speed. JavaScript is first class; Python is where
the design is checked.

Do not take that from this page. In two minutes:

```
bash pyto/scripts/check_all.sh                                        # nine suites, ~600 tests
python pyto/experiments/grouped-ablation/run_cached.py --out /tmp/hit  # a miss, then two hits, one from a fresh process
node pyto/viewer/embed.mjs pyto/viewer/fixtures/pyto-grouped-ablation.json --out /tmp/hit/ticks.html
```

The tests were checked by mutation (each guards a specific line). The fixtures for the JavaScript
port are 440 byte-exact cases. `pyto/questions.md` is where anyone unsure writes `{?} Label: ...`
and the owner answers; read it before assuming. `pyto/BOARD.md` is the owner's one page.

## What was asked

students: a homework-sized PCR with a hand-off page graded mechanically by grade.py, leaving only the plain-words explanation to a cold reader; no kernel change

## Starting point

d13fcd1c38eab147d1a9d01b2c6c4e4ebf7abf90 (board and root: research lane closed; owner's framing (workspace, educational)). MAIN may have moved since: `git log --oneline d13fcd1..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/CHANGES.md
- A  pyto/experiments/students/HANDOFF.md
- A  pyto/experiments/students/README.md
- A  pyto/experiments/students/evidence/run-1/receipts.json
- A  pyto/experiments/students/evidence/run-1/record.json
- A  pyto/experiments/students/evidence/run-1/tick-viewer.html
- A  pyto/experiments/students/grade.py
- A  pyto/experiments/students/homework.py
- A  pyto/experiments/students/test_students.py
- M  pyto/scripts/check_all.sh

```
pyto/CHANGES.md                                    |    2 +
 pyto/experiments/students/HANDOFF.md               |   69 +
 pyto/experiments/students/README.md                |   95 +
 .../students/evidence/run-1/receipts.json          |  159 ++
 .../students/evidence/run-1/record.json            |  415 +++++
 .../students/evidence/run-1/tick-viewer.html       | 1966 ++++++++++++++++++++
 pyto/experiments/students/grade.py                 |  335 ++++
 pyto/experiments/students/homework.py              |  304 +++
 pyto/experiments/students/test_students.py         |  298 +++
 pyto/scripts/check_all.sh                          |    6 +-
 10 files changed, 3648 insertions(+), 1 deletion(-)
```

## Evidence

- verify: none beyond the suite
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         155  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    240  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                          103  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
- {?} Compared fields: `grade.py:COMPARED_OUT` drops the whole `source` block (runtime
  version and commit) and the two timing fields (`counters.wall_ms`,
  `ticks[].invocations[].duration_ms`) before check 2 compares. `source` is dropped
  because the record is committed at one commit and replayed at another, so keeping it
  would fail every landing; the timings because two runs never agree on them. The
  alternative was to write `commit: null` and never record durations at all, which
  loses telemetry the owner asked for ("max telemetry"). The dropped fields are printed
  in the report, so nothing is hidden, but a student could edit `duration_ms` freely
  and no check would notice.
- {?} What "every file" means in check 4: `grade.py:homework_files` walks the experiment
  directory and calls every file it finds (minus `__pycache__` and `.pyc`) a file the
  hand-off must name. That makes the committed evidence files -- `evidence/run-1/record.json`,
  `receipts.json`, `tick-viewer.html` -- part of the hand-off's obligation, which reads
  right for "which files I touched" but means a student who runs `homework.py --out
  evidence/run-2` fails check 4 until they mention run-2 as well. The alternative was a
  hand-maintained list in `homework.py`, which check 4 could not then be said to verify.
- {?} Substring matching: check 4 asks whether the Tick name and the file name appear
  anywhere in the hand-off text, case-sensitively. A hand-off that names a Tick only
  inside an unrelated sentence passes. Anything stronger (a per-Tick bullet, a required
  heading) would be a format rule on a page whose whole point is the student's own words.
- {?} Where the cold reader's answer goes: `grade.py` prints the hand-off and the
  question and stops. Nothing records the answer, compares it to the program, or scores
  it -- there is no `--cold-reader-answer` flag and no judge. The explicability gate in
  LANDING.md has a judge (a human or an agent reading the diff); whether the classroom
  version should have the same one, and where its verdict would be stored, is the owner's
  call.
- {?} `tick-viewer.html` is committed (81 KB) so the browser page ships with the run it
  describes, the way grouped-ablation commits its own. It is 8x the record it embeds and
  is rebuilt byte-identically by `node pyto/viewer/embed.mjs`, so committing it buys only
  "opens from disk with no build step" -- which is the board's test, hence the choice.
- {?} Rounding: `mean_score` rounds to two decimals and `median_score` does not round at
  all. The hand-off says so as a `{?}` line, on purpose: it is a real inconsistency left
  in the homework so the cold reader has something honest to catch. If the owner would
  rather the shipped homework be clean, both should round.
- {?} `homework.SOURCE_OF` is a hand-written map from invocation id to the function whose
  source digest check 3 recomputes. It could be derived from the PCR instead (the
  invocation's Calculation address -> its `calculate` attribute), which would remove the
  chance of the map drifting from the program; it is spelled out because a student
  reading check 3 can see what is being compared to what.
- {?} Registration: `pyto/scripts/check_all.sh` discovers `experiments/<name>/test_*.py`
  in a loop, so the only registration this suite needed was existing. The edit to
  check_all.sh is a comment saying that is the mechanism and naming this suite; if the
  owner would rather check_all.sh not mention individual suites, revert that hunk and
  nothing about the run changes.
- {?} Mutation checks (three, each applied to a scratch copy and reverted; the files are
  byte-identical after): dropping `result_sha256` from `grade.py:compared` is killed by
  `TamperedRecord.test_flipping_one_result_digest_fails_the_replay_check`; comparing
  `check_handoff`'s Tick names against an empty list is killed by
  `Handoff.test_a_missing_tick_line_fails_check_four`; removing the `sorted(...)` from
  `homework.py:parse_scores` is killed by
  `CommittedEvidence.test_grade_exits_zero_on_the_committed_evidence`. The third mutation
  fails checks 2 AND 3 together (the source digest of the edited function moves too),
  which is worth knowing: check 3 shadows check 2 for any defect that is an edit to a
  Calculation's own source, and check 2 is only reached alone by an edit to the record.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 23 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 23`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-23): students: a homework-sized PCR with a hand-off page graded mechanically by grade.py, leaving only the plain-words explanation to a cold reader; no kernel change`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
