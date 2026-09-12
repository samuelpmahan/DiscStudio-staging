# Task 150: the owner, 2026-09-12: 'come up with some compiler-ish efficiency pass to prevent things like this? Encode a path to trusting the sparsification of things' -- neat hot names the hot Calculations and the shape of their values over one run record (a dense list that would be an array, cost per element, an over-cap value, a cache that isn't there), and neat equiv rebuilds every receipt's inputs, runs a candidate and witnesses that it reproduces every recorded result

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
git clone -b main https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/150
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/150:pyto/experiments/tasks/150/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 7c354c0 origin/exp/150 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the owner, 2026-09-12: 'come up with some compiler-ish efficiency pass to prevent things like this? Encode a path to trusting the sparsification of things' -- neat hot names the hot Calculations and the shape of their values over one run record (a dense list that would be an array, cost per element, an over-cap value, a cache that isn't there), and neat equiv rebuilds every receipt's inputs, runs a candidate and witnesses that it reproduces every recorded result

## Starting point

7c354c04e7da2a5323fdb3a92e4ccf8223068cfe (board: **started** `task-149`: materializing a record with big values is cheap:). MAIN may have moved since: `git log --oneline 7c354c0..origin/main` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/USE.md
- M  pyto/scripts/neat.sh
- A  pyto/src/pyto/neat/equiv.py
- A  pyto/src/pyto/neat/hot.py
- A  pyto/tests/test_neat_equiv.py
- A  pyto/tests/test_neat_hot.py
- M  pyto/tests/test_use.py

```
pyto/USE.md                   | 125 ++++++++++++
 pyto/scripts/neat.sh          |  26 ++-
 pyto/src/pyto/neat/equiv.py   | 430 ++++++++++++++++++++++++++++++++++++++++
 pyto/src/pyto/neat/hot.py     | 452 ++++++++++++++++++++++++++++++++++++++++++
 pyto/tests/test_neat_equiv.py | 277 ++++++++++++++++++++++++++
 pyto/tests/test_neat_hot.py   | 201 +++++++++++++++++++
 pyto/tests/test_use.py        |   1 +
 7 files changed, 1511 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `bash pyto/scripts/check_all.sh` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.8c7EXF6XNY) (evidence/check_all.txt)
    suite                         tests  status
    library                         528  OK
    experiments/brain               756  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} HotPerElementThreshold: neat hot calls an invocation per-element when it spends more than 50 ns on each element, over at least 1024 of them. Calibrated on the generation: dense, every stage trips it (render 1358 ns per pixel, fitness 345, encode 86); over arrays nothing does. The default stands until the owner says otherwise; it is one number at the top of hot.py and --per-element overrides it per run.

{?} EquivShapeNotInTheDigest: neat equiv canonicalizes a (256, 256, 3) uint8 array and the flat list of 196,608 ints to the same bytes -- the shape is deliberately not in the digest, because the owner's own trust was the 32 pixel hashes and a list of pixels is the same pixels as an array of them. The default is that a reshape is not a difference; if a candidate should have to reproduce the shape too, that is one line in canonical.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 150 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 150`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-150): the owner, 2026-09-12: 'come up with some compiler-ish efficiency pass to prevent things like this? Encode a path to trusting the sparsification of things' -- neat hot names the hot Calculations and the shape of their values over one run record (a dense list that would be an array, cost per element, an over-cap value, a cache that isn't there), and neat equiv rebuilds every receipt's inputs, runs a candidate and witnesses that it reproduces every recorded result`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
