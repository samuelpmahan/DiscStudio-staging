# Task 58: the laws read chains: tick_laws.py, px laws and the two reference readers stop calling a read of an earlier sibling a node-law violation; a Tick whose Calculations read earlier siblings is a chain (runs in order, its latency is the sum), a Tick with no sibling reads is parallel; a read of a later sibling and two siblings producing one address remain violations; the students and ablation records still pass

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
git fetch origin exp/58
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/58:pyto/experiments/tasks/58/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 19ad992 origin/exp/58 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the laws read chains: tick_laws.py, px laws and the two reference readers stop calling a read of an earlier sibling a node-law violation; a Tick whose Calculations read earlier siblings is a chain (runs in order, its latency is the sum), a Tick with no sibling reads is parallel; a read of a later sibling and two siblings producing one address remain violations; the students and ablation records still pass

## Starting point

dc62a1b08965a8f9d05ff23ac1b277ba2d616d69 (board: **started** `task-57`: chains inside a Tick: the owner, 2026-09-10: 'Cal). MAIN may have moved since: `git log --oneline 19ad992..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/students/HANDOFF.md
- M  pyto/experiments/students/test_students.py
- M  pyto/experiments/tick-laws/README.md
- M  pyto/experiments/tick-laws/test_tick_laws.py
- M  pyto/experiments/tick-laws/tick_laws.py
- M  pyto/src/pyto/px.py
- M  pyto/tests/test_px.py
- M  pyto/viewer/adapters.js
- M  pyto/viewer/test/parallel-view.test.mjs
- M  pyto/viewer/test/playback.test.mjs
- M  pyto/viewer/tick-viewer.js

```
pyto/experiments/students/HANDOFF.md         |   4 +-
 pyto/experiments/students/test_students.py   |   5 +-
 pyto/experiments/tick-laws/README.md         |  30 ++++--
 pyto/experiments/tick-laws/test_tick_laws.py | 131 ++++++++++++++++++++++-----
 pyto/experiments/tick-laws/tick_laws.py      |  59 +++++++++---
 pyto/src/pyto/px.py                          |  15 ++-
 pyto/tests/test_px.py                        |  47 ++++++++--
 pyto/viewer/adapters.js                      |   3 +-
 pyto/viewer/test/parallel-view.test.mjs      |  27 +++++-
 pyto/viewer/test/playback.test.mjs           |   7 +-
 pyto/viewer/tick-viewer.js                   |  45 +++++++--
 11 files changed, 301 insertions(+), 72 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_px && python -m unittest discover -s experiments/tick-laws -p 'test_*.py' && python -m unittest discover -s viewer/test -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.GAKtKsaFWd) (evidence/check_all.txt)
    suite                         tests  status
    library                         328  OK
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
{?} ChainSuffixOnlyWhenChained: `px laws` prints `(N parallel, M chain)` on the node-law line, and `chain` on a `--times` Tick line, only when the record has at least one chain; a chain-free record prints exactly as before. Reason: `tests/fixtures/px/laws-*.txt` (the byte-for-byte expected output of the two committed records) sit outside this task's Allow line. If you want `(4 parallel, 0 chain)` on every record, drop the guard in `cmd_laws` and regenerate the three fixtures.
{?} ChainLatencyIsTheWholeTick: a chain Tick's latency is the sum of every duration in it (the Tick runs in order), not the longest path through the sibling-read graph; a Tick that mixes a chain with an independent branch counts as all-series, in tick_laws.py and in the viewer's critical path alike.
{?} SingletonCountsAsParallel: tick_laws.py classifies a Tick of one Calculation (and an empty Tick) as `parallel` (no sibling reads), so the students record counts 4 parallel; the viewer's `isParallelTick`/`isChainTick` keep requiring two Calculations for either badge, as before.
{?} LimitationLineUnchanged: LIMITATION never stated the old rule (it speaks of reads, writes and what parallel would buy) and is the first line of the three px fixtures, so it stays; the rule and the owner's sentence live in tick_laws.py's docstring and README.
{?} HandoffSentence: HANDOFF.md's "inside one Tick it claims none" stated the old rule, so one clause was added in the student's voice ("claims an order only where one Calculation reads another's result"); the rest of the page is left as the cold read caught it (questions.md, WhatIsATick).

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 58 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 58`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-58): the laws read chains: tick_laws.py, px laws and the two reference readers stop calling a read of an earlier sibling a node-law violation; a Tick whose Calculations read earlier siblings is a chain (runs in order, its latency is the sum), a Tick with no sibling reads is parallel; a read of a later sibling and two siblings producing one address remain violations; the students and ablation records still pass`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
