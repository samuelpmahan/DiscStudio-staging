# Task 30: every reader handles several produces: compare_local.py and pql_document.py in grouped-ablation stop assuming one into per invocation; tests for both

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
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/30
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/30:pyto/experiments/tasks/30/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 887454c origin/exp/30 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

every reader handles several produces: compare_local.py and pql_document.py in grouped-ablation stop assuming one into per invocation; tests for both

## Starting point

f1524b4ca3dcf6331f25f606934c412b8bde7627 (board: **started** `task-29`: students: Mean and Median run in one Tick as para). MAIN may have moved since: `git log --oneline 887454c..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/CHANGES.md
- M  pyto/experiments/grouped-ablation/compare_local.py
- M  pyto/experiments/grouped-ablation/pql_document.py
- M  pyto/experiments/grouped-ablation/test_second_experiment.py

```
pyto/CHANGES.md                                    |   2 +
 pyto/experiments/grouped-ablation/compare_local.py |  79 +++++++++-
 pyto/experiments/grouped-ablation/pql_document.py  |  20 +++
 .../grouped-ablation/test_second_experiment.py     | 174 +++++++++++++++++++++
 4 files changed, 270 insertions(+), 5 deletions(-)
```

## Evidence

- verify: `cd pyto && python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         193  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    248  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             11  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} PqlMultiProduceIsRefused: `to_pql_document` REFUSES a multi-produce invocation instead of emitting one, naming the invocation (`<Tick>.<id>`) and every address it declared. The readPql grammar has one `into` per Calculation and reads it with `text(...)`, a nonempty string (`src/core/exec.js:46`), and `invokePql` writes exactly that one address (`pxc.set(calculation.into, output)`, exec.js:58) -- there is no place in the document for a second address and no rule by which the reader could split one result across two, so emitting the first address (or a JSON array the reader rejects at parse time) would be a document that says something false about the program. Widening the grammar was not this task's to do; if the owner wants the browser to run multi-produce Calculations, that is a change to exec.js and to `candidates/readpql_check.mjs`, and this refusal is the line it would replace.
{?} ConsumersOfOverlap: `consumers_of` now matches two `fn:` refs when they read a Part in common, not only when they are the same string -- a bare `fn:<id>` (every Part that invocation published) lists the ids that bind `fn:<id>#<address>` for any one of them, and a qualified ref lists only the readers of that one produce. Exact string equality still matches, so every one-address answer is unchanged; the alternative was to leave it literal, which reports "nothing consumes `stats`" for an invocation whose whole fan-out binds it by qualified spelling.
{?} PxWriterLastWins: `_writer_of` keeps the old "later declaration wins" rule when two invocations publish the same address, now per address rather than per `into` field. A multi-produce invocation can therefore be the writer of one address and not of another it also declared, if a later invocation republishes the second. Nothing here refuses a republished address; `PxWrite.kind` already reports it as a `replacement` (task 27 `{?} MultiWriteKinds`).

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 30 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 30`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-30): every reader handles several produces: compare_local.py and pql_document.py in grouped-ablation stop assuming one into per invocation; tests for both`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
