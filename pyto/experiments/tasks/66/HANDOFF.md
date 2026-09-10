# Task 66: the difference is computed before it is shown, and counting comes before mining: pyto/src/pyto/neat/diff.py registers fn.neat.diff.candidates (two PQL documents and a seed store in, px.exp.blok.diff.<a>.<b> out: structural same or different, each output same, changed or new by value digest, and the remainder no calculation settled; documents with oc. calls are not run and say so); neat diff prints it and keeps the Part under pyto/experiments/review/diffs; pyto/experiments/molecules/transitions.py registers fn.molecules.transitions (every run record's invocation-to-invocation and Part-to-invocation transition counted, px.exp.molecules.transitions, stable order) and report.md opens with the count table before any molecule

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
git fetch origin exp/66
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/66:pyto/experiments/tasks/66/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 73b36d8 origin/exp/66 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the difference is computed before it is shown, and counting comes before mining: pyto/src/pyto/neat/diff.py registers fn.neat.diff.candidates (two PQL documents and a seed store in, px.exp.blok.diff.<a>.<b> out: structural same or different, each output same, changed or new by value digest, and the remainder no calculation settled; documents with oc. calls are not run and say so); neat diff prints it and keeps the Part under pyto/experiments/review/diffs; pyto/experiments/molecules/transitions.py registers fn.molecules.transitions (every run record's invocation-to-invocation and Part-to-invocation transition counted, px.exp.molecules.transitions, stable order) and report.md opens with the count table before any molecule

## Starting point

c0368114ed2864f030f0f5d19b03d23d4cfef34f (board: **started** `task-65`: the question loop as Parts and Calculations: pyto). MAIN may have moved since: `git log --oneline 73b36d8..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/molecules/mine.py
- M  pyto/experiments/molecules/molecules.py
- M  pyto/experiments/molecules/report.md
- M  pyto/experiments/molecules/test_molecules.py
- A  pyto/experiments/molecules/transitions.py
- A  pyto/experiments/review/diffs/.gitkeep
- M  pyto/scripts/neat.sh
- A  pyto/src/pyto/neat/diff.py
- A  pyto/tests/fixtures/blok/cards.json
- A  pyto/tests/fixtures/blok/registry.py
- A  pyto/tests/test_neat_diff.py

```
pyto/experiments/molecules/mine.py           |  22 +-
 pyto/experiments/molecules/molecules.py      |  28 ++-
 pyto/experiments/molecules/report.md         |  77 ++++--
 pyto/experiments/molecules/test_molecules.py |  34 ++-
 pyto/experiments/molecules/transitions.py    | 102 ++++++++
 pyto/experiments/review/diffs/.gitkeep       |   0
 pyto/scripts/neat.sh                         |  15 +-
 pyto/src/pyto/neat/diff.py                   | 349 +++++++++++++++++++++++++++
 pyto/tests/fixtures/blok/cards.json          |  37 +++
 pyto/tests/fixtures/blok/registry.py         |  39 +++
 pyto/tests/test_neat_diff.py                 | 236 ++++++++++++++++++
 11 files changed, 908 insertions(+), 31 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_neat_diff && python -m unittest discover -s experiments/molecules -p 'test_*.py' && python experiments/molecules/mine.py --check` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.TnV7T5Fpos) (evidence/check_all.txt)
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

{?} DiffNewIsAsymmetric: the outputs vocabulary (same/changed/new/unknown) has no fifth word for "removed", so an address only one of the two documents declares as `into` -- on either side -- is reported "new" rather than told apart by direction. Every fixture here has matching address sets on both sides so this never actually fires; worth a direction-aware word if a future diff compares documents that genuinely add or drop an address.
{?} DiffPrintForm: the CLI prints the diff value pretty (two-space indent, sorted keys -- px.py's own meaning of "canonical JSON" for a value meant to be read) while the sha256 inside the written Part hashes the compact, no-whitespace form (retain.py's canonical_json/digest_of, reused for the digest only). "Prints the diff value as canonical JSON" could mean either spelling; I kept the two uses separate rather than picking one JSON style for both.
{?} NeatDiffCalculationRunForm: `fn.neat.diff.candidates` is registered in a PxC and invoked with `pxc.call(...)` (USE.md section 3's plain form), not run through a PCR of its own with observe=True; only the two document sub-runs it triggers are `PCR.run(..., observe=True)` and materialized (the two records the packet asks for beside the Part). A more literal reading of "every Calculation runs through an observed PCR" would also wrap the comparison step itself, leaving it a receipt too.
{?} DiffRemainderOcOrder: the remainder lists every label (a's then b's) followed by one "not run: <call> is oc." line per oc. call found, in encounter order (a's Ticks then b's), not deduplicated -- a document naming the same oc. call twice gets two identical lines. Not specified either way in the packet.
{?} LabelsOutsideReadPqlGrammar: documents here carry a top-level `labels` list the JS `readPql` grammar (pql_document.py's own docstring) does not define; treated as this module's private, presentation-only extension and stripped before `structural_digest`/`run_document` see the document. Untested against the real reader, which would presumably just ignore the unknown key.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 66 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 66`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-66): the difference is computed before it is shown, and counting comes before mining: pyto/src/pyto/neat/diff.py registers fn.neat.diff.candidates (two PQL documents and a seed store in, px.exp.blok.diff.<a>.<b> out: structural same or different, each output same, changed or new by value digest, and the remainder no calculation settled; documents with oc. calls are not run and say so); neat diff prints it and keeps the Part under pyto/experiments/review/diffs; pyto/experiments/molecules/transitions.py registers fn.molecules.transitions (every run record's invocation-to-invocation and Part-to-invocation transition counted, px.exp.molecules.transitions, stable order) and report.md opens with the count table before any molecule`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
