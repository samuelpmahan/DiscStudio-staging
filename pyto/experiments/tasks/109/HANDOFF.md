# Task 109: brain: the blok generation lane, filed as a Part - proposal.brain.blok_generation, a seeded motif-patterned variation over the brain's Calculations through crisp vary, judged by the oracle Parts for correct, the benchmark Parts for fast and neat delta for cheap, with the winners' recurring motifs mined back into the motif set; and the same as a next entry on the backend map Part

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
git fetch origin exp/109
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/109:pyto/experiments/tasks/109/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 857c320 origin/exp/109 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain: the blok generation lane, filed as a Part - proposal.brain.blok_generation, a seeded motif-patterned variation over the brain's Calculations through crisp vary, judged by the oracle Parts for correct, the benchmark Parts for fast and neat delta for cheap, with the winners' recurring motifs mined back into the motif set; and the same as a next entry on the backend map Part

## Starting point

a6d6ae5ac0b422b867259a1b8fb26f4fba77a937 (land(task-108): brain kerchoo: the owner's speed pass across all four verticals - the loops hiding inside vectorised engines (an sp or np engine that called scipy or numpy once per element is one vectorised call now), backend=auto as the default when a caller names no engine, the plan Part extended to the stats, data and ml calcs that have bench Parts, and one Part px.exp.brain.bench.kerchoo recording before, after, speedup and the engine chosen for every calc touched). MAIN may have moved since: `git log --oneline 857c320..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/brain/backend/summary.py
- M  pyto/experiments/brain/store/backend.json

```
pyto/experiments/brain/backend/summary.py | 25 +++++++++++++++++++++++++
 pyto/experiments/brain/store/backend.json | 11 +++++++++++
 2 files changed, 36 insertions(+)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.uTbZi9Lhfe) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
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

{?} both runs are in the packet: the copy's venv and python 3.12.3 / numpy 2.5.3 / scipy 1.18.1 at
experiments/tasks/109/evidence/verify-python312-numpy253.txt. 756 tests, OK in both.
{?} proposal.brain.blok_generation sits at proposal.brain.<k>, not proposal.brain.<vertical>.<k>.
It is a lane about what the whole brain is now good for, not one vertical's finding, so it is
written with store.put rather than harness.finding. If the contract would rather every proposal be
owned by a vertical, this is the one to move.
{?} nothing here changes a Calculation, an engine or an answer. The only source change is
backend/summary.py; the store moves because it was rebuilt over it.
{?} the lane is filed, not started. The first thing it needs is the cross-kind PQL join that three
verticals filed independently tonight - joining px.exp.brain.oracle.* to px.exp.brain.bench.* on
(vertical, calc, case) - which is why that proposal is named from inside this one.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 109 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 109`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-109): brain: the blok generation lane, filed as a Part - proposal.brain.blok_generation, a seeded motif-patterned variation over the brain's Calculations through crisp vary, judged by the oracle Parts for correct, the benchmark Parts for fast and neat delta for cheap, with the winners' recurring motifs mined back into the motif set; and the same as a next entry on the backend map Part`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
