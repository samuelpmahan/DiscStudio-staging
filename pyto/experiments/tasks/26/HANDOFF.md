# Task 26: Ticks as circuits: tick_laws.py checks any pyto-run-record@1 against the node law (inside a Tick no Calculation consumes a sibling's produce, no two siblings produce one Part) and the loop law (nothing consumes a Part produced later), and reports total work versus critical path per Tick; no kernel change

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
git fetch origin exp/26
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/26:pyto/experiments/tasks/26/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 71e2cbb origin/exp/26 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

Ticks as circuits: tick_laws.py checks any pyto-run-record@1 against the node law (inside a Tick no Calculation consumes a sibling's produce, no two siblings produce one Part) and the loop law (nothing consumes a Part produced later), and reports total work versus critical path per Tick; no kernel change

## Starting point

71e2cbb57866744c6fd1b16665a30fb5844c03fd (root: {?} TicksAsCircuits, the owner's series/parallel question with the mapping as default). MAIN may have moved since: `git log --oneline 71e2cbb..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/CHANGES.md
- A  pyto/experiments/tick-laws/README.md
- A  pyto/experiments/tick-laws/test_tick_laws.py
- A  pyto/experiments/tick-laws/tick_laws.py

```
pyto/CHANGES.md                              |   2 +
 pyto/experiments/tick-laws/README.md         |  38 ++++
 pyto/experiments/tick-laws/test_tick_laws.py | 284 +++++++++++++++++++++++++++
 pyto/experiments/tick-laws/tick_laws.py      | 216 ++++++++++++++++++++
 4 files changed, 540 insertions(+)
```

## Evidence

- verify: `cd pyto/experiments/tick-laws && python3 -m unittest discover -s . -p 'test_*.py' && python3 tick_laws.py --check ../grouped-ablation/evidence/run-1/record.json ../students/evidence/run-1/record.json` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         155  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    240  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             10  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

{?} ActualEdgeCoverage: Records often leave `actual_consumes` empty, so this tool deliberately cannot certify all declared or `fn:` dependencies as parallel-safe. It reports only observed actual edges.
{?} TimingSemantics: Run records provide invocation durations, not measured parallel scheduling; work and critical path are a Tick-model estimate, and unknown durations remain null.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 26 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 26`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-26): Ticks as circuits: tick_laws.py checks any pyto-run-record@1 against the node law (inside a Tick no Calculation consumes a sibling's produce, no two siblings produce one Part) and the loop law (nothing consumes a Part produced later), and reports total work versus critical path per Tick; no kernel change`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
