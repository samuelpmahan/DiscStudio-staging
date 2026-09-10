# Task 68: the first batch through the integrated loop: neat ask run once on the tree that holds tasks 65, 66 and 67 together, its batch Part and run record kept as evidence under pyto/experiments/review; FRONTIER.md's Landed adds gain the three (the question loop, the difference before it is shown with counting before mining, the join's gate) in the owner's words

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
git fetch origin exp/68
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/68:pyto/experiments/tasks/68/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 58549df origin/exp/68 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the first batch through the integrated loop: neat ask run once on the tree that holds tasks 65, 66 and 67 together, its batch Part and run record kept as evidence under pyto/experiments/review; FRONTIER.md's Landed adds gain the three (the question loop, the difference before it is shown with counting before mining, the join's gate) in the owner's words

## Starting point

dfd020b77d3fb1e46c4c0274712fd80261d51b8d (land(task-66): the difference is computed before it is shown, and counting comes before mining: pyto/src/pyto/neat/diff.py registers fn.neat.diff.candidates (two PQL documents and a seed store in, px.exp.blok.diff.<a>.<b> out: structural same or different, each output same, changed or new by value digest, and the remainder no calculation settled; documents with oc. calls are not run and say so); neat diff prints it and keeps the Part under pyto/experiments/review/diffs; pyto/experiments/molecules/transitions.py registers fn.molecules.transitions (every run record's invocation-to-invocation and Part-to-invocation transition counted, px.exp.molecules.transitions, stable order) and report.md opens with the count table before any molecule). MAIN may have moved since: `git log --oneline 58549df..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/FRONTIER.md
- A  pyto/experiments/review/batches/2.json
- A  pyto/experiments/review/runs/ask-2.json

```
pyto/FRONTIER.md                        |   23 +
 pyto/experiments/review/batches/2.json  | 1955 +++++++++++++++++++++++++++++++
 pyto/experiments/review/runs/ask-2.json | 1467 +++++++++++++++++++++++
 3 files changed, 3445 insertions(+)
```

## Evidence

- verify: `cd pyto && test -s experiments/review/batches/2.json && python -m unittest tests.test_neat_review tests.test_neat_diff tests.test_neat_gate && grep -q 'task 67' FRONTIER.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.iBKg1NNRzo) (evidence/check_all.txt)
    suite                         tests  status
    library                         366  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} RootLabelsCountAsOpen: batch 2 holds 278 items and 117 of them are labels already on pyto/questions.md, most with a decision in prose under them; the collator counts a root label as open until an answer file exists for it. Whether a root entry with an Owner line or a Decided line is already answered is the owner's to say; until then the batch is long.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 68 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 68`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-68): the first batch through the integrated loop: neat ask run once on the tree that holds tasks 65, 66 and 67 together, its batch Part and run record kept as evidence under pyto/experiments/review; FRONTIER.md's Landed adds gain the three (the question loop, the difference before it is shown with counting before mining, the join's gate) in the owner's words`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
