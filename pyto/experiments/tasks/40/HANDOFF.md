# Task 40: parallel you can see: the Tick viewer draws a Tick's Calculations side by side when they are parallel branches, prints the Tick's work and latency and the run's critical path, shows placement when the record carries it, and tick_laws names Ticks; the students record is the demo page

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Stop here first (the owner's rule)

Read this page, `pyto/BOARD.md`, and the packet. No fourth file yet. Then write the one question
you would answer by reading another hundred thousand tokens of code, and ask the owner instead.
His answer is worth more than the reading: the last session that read everything first was
confidently wrong about half of it, and one sentence from him undid each wrong half. The answer
goes on `pyto/questions.md` verbatim, as `{?} Label: ...` with his words, so the next agent starts
one stupid question deeper. Only then read further and do the work below.

## Get the code (once)

```
git clone -b claude/os-sprint-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/40
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/40:pyto/experiments/tasks/40/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 2b1e082 origin/exp/40 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

parallel you can see: the Tick viewer draws a Tick's Calculations side by side when they are parallel branches, prints the Tick's work and latency and the run's critical path, shows placement when the record carries it, and tick_laws names Ticks; the students record is the demo page

## Starting point

53d31d925730b00a954afb7524e4c024d1760ef5 (board: **started** `task-39`: parallel for real and budgets: PcrRun runs the Ca). MAIN may have moved since: `git log --oneline 2b1e082..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/CHANGES.md
- M  pyto/experiments/students/README.md
- M  pyto/experiments/tick-laws/README.md
- M  pyto/experiments/tick-laws/test_tick_laws.py
- M  pyto/experiments/tick-laws/tick_laws.py
- A  pyto/viewer/fixtures/parallel-demo.json
- A  pyto/viewer/test/parallel-view.test.mjs
- M  pyto/viewer/test/playback.test.mjs
- M  pyto/viewer/tick-viewer.html
- M  pyto/viewer/tick-viewer.js

```
pyto/CHANGES.md                              |   1 +
 pyto/experiments/students/README.md          |  11 +-
 pyto/experiments/tick-laws/README.md         |  12 +-
 pyto/experiments/tick-laws/test_tick_laws.py |  36 +++-
 pyto/experiments/tick-laws/tick_laws.py      |  12 +-
 pyto/viewer/fixtures/parallel-demo.json      | 237 ++++++++++++++++++++++++
 pyto/viewer/test/parallel-view.test.mjs      | 257 +++++++++++++++++++++++++++
 pyto/viewer/test/playback.test.mjs           |  99 ++++++++---
 pyto/viewer/tick-viewer.html                 |  18 ++
 pyto/viewer/tick-viewer.js                   | 199 ++++++++++++++++++++-
 10 files changed, 842 insertions(+), 40 deletions(-)
```

## Evidence

- verify: `cd pyto && node --test viewer/test/*.test.mjs && cd experiments/tick-laws && python3 -m unittest discover -s . -p 'test_*.py' && python3 tick_laws.py --check ../students/evidence/run-1/record.json` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         248  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    248  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             14  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} TickReportShape: the packet asked tick_laws for `"tick": {"index": i, "name": ...}`; `experiments/students/test_students.py` (outside this task's allow list) builds `{tick["tick"]: tick for tick in report["ticks"]}`, so a mapping there is an unhashable key and fails a suite this task must keep green. Shipped as `"tick": <index>` with a sibling `"name"`, which reads the same in text (`Tick 1 Stats: work_ms=...`); say the word and the nested shape lands with that test updated in the same commit.

{?} ContractKeysFailThePythonValidator: `viewer/test/record_schema.py` refuses unknown document fields, so the moment a real record carries `parallel`, `budget`, per-tick `latency_ms` or per-invocation `placement`, `tick_laws.py --check` (which validates through that file) refuses it -- the JS validator ignores them and renders them. `viewer/fixtures/parallel-demo.json` is therefore validated by the JS side only. record_schema.py belongs to another team and was not touched; the four keys need adding to its key tuples before any producer ships them.

{?} LatencyOfASerialTick: latency is `latency_ms` when the record carries it and otherwise the longest branch, for every Tick, including one whose Calculations are a chain -- so such a Tick prints a latency shorter than its work, which is what parallel would buy and not what the Tick took. This is exactly what `tick_laws.py` already reports, so the page and the checker agree; the alternative (sum for a serial Tick, max for a parallel one) would make them disagree.

{?} ViolationLinesStillSayTickIndexOnly: the per-Tick text lines now name the Tick, but law-violation messages still read `... in Tick 0`, because those strings are part of `--json` and the packet fixed `--json` as unchanged otherwise.

{?} StudentsDemoPageIsBakedAndStale: `experiments/students/evidence/run-1/tick-viewer.html` is baked by `homework.py` through `embed.mjs`, so the committed demo page still carries the previous renderer -- the side-by-side Stats Tick is in `pyto/viewer/tick-viewer.html` (drop the record on it) but not in that committed file. Regenerating it means writing under `experiments/students/evidence/`, outside this task's allow list, so it was left alone; one `python homework.py --out evidence/run-1` re-bakes it.

{?} PlaybackClockIsNowTheCriticalPath: with a parallel Tick's cards appearing together at the Tick's latency, the playback clock's last event lands on the run's critical path rather than on the sum of every duration; `viewer/test/playback.test.mjs` was rewritten to that law (5 of its tests changed), which is the one place an existing test's expectations were replaced rather than added to.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 40 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 40`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-40): parallel you can see: the Tick viewer draws a Tick's Calculations side by side when they are parallel branches, prints the Tick's work and latency and the run's critical path, shows placement when the record carries it, and tick_laws names Ticks; the students record is the demo page`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
