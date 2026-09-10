# Task 63: the walk: the owner, 2026-09-10: 'make it real easy for me and Astra to step through your landings, inspect changes, keep all PQL, PxC, etc front of mind automatically'. pyto/scripts/walk.py builds walk.html from the record alone: one step per landing in order (intent, the owner's words it quotes, the receipt, files changed with counts and the diff folded, the packet's {?} lines, which of the seven concepts it touched with their one-line definitions pinned at the top of every step, and the sentence that undoes it); arrow keys step; --text N prints one step for an agent and neat walk N dispatches to it; same tree, same bytes; a test pins that every landing on the board has a step

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
git fetch origin exp/63
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/63:pyto/experiments/tasks/63/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 351f568 origin/exp/63 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the walk: the owner, 2026-09-10: 'make it real easy for me and Astra to step through your landings, inspect changes, keep all PQL, PxC, etc front of mind automatically'. pyto/scripts/walk.py builds walk.html from the record alone: one step per landing in order (intent, the owner's words it quotes, the receipt, files changed with counts and the diff folded, the packet's {?} lines, which of the seven concepts it touched with their one-line definitions pinned at the top of every step, and the sentence that undoes it); arrow keys step; --text N prints one step for an agent and neat walk N dispatches to it; same tree, same bytes; a test pins that every landing on the board has a step

## Starting point

14b0b407dd10be18da7c5ee24930f42bc5625392 (land(task-60): SUBDUE-PxC-PQL moonshot (the owner's last call of the sprint, not OS): mine the run records for molecules. A new experiment pyto/experiments/molecules builds one labelled graph from every committed pyto-run-record@1 (invocations labelled by Calculation address, Parts by address shape; reads, writes and declared-order edges), runs the SUBDUE miner from hiding-primitives over it, and names each mined substructure a molecule: a repeated chain of Calculations over Part shapes, emitted as a PQL document that runs it, a PQL query that finds its Parts in a store, and the compression it buys in bits; report.md is rebuilt byte for byte and --check refuses drift; tests pin determinism and that every instance really embeds in its record). MAIN may have moved since: `git log --oneline 351f568..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/KT-MAC.md
- M  pyto/scripts/neat.sh
- A  pyto/scripts/walk.py
- A  pyto/tests/test_walk.py

```
pyto/KT-MAC.md          |  26 +++
 pyto/scripts/neat.sh    |  19 +-
 pyto/scripts/walk.py    | 480 ++++++++++++++++++++++++++++++++++++++++++++++++
 pyto/tests/test_walk.py |  75 ++++++++
 4 files changed, 598 insertions(+), 2 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_walk && python scripts/walk.py --check` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.tWbsTif9C1) (evidence/check_all.txt)
    suite                         tests  status
    library                         336  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules             5  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} RefusedAndKilledSteps: the walk has one step per **landed** line only; refused, killed and started lines are not steps (a refusal has no landing commit to diff). If the owner wants the refusals shown as beats between landings, they would go in as steps without a diff.
{?} ConceptMap: changed paths map to the seven words by a fixed table (core.py and px.py to PxC and Part, pql.py to PQL, pcr.py to PCR and Tick and Calculation, effects.py to Calculation, materialize.py and pyto/viewer to receipt and record, neat.sh, land.sh and the classroom to neat, src/ to the studio, pyto/experiments to experiments, the rest to docs). Three of those names (record, the studio, experiments, docs) are not among the seven and get one-line meanings of their own; a landing whose only changed files are receipts and evidence shows as "experiments".
{?} AbsolutePathsInTheRecord: the record itself carries a machine's absolute path in places (refused lines on the board, check_all.txt); the page replaces every such path with "(absolute path cut)" so the same tree gives the same bytes on any machine. The receipts and the board are untouched.
{?} OwnerQuotes: the owner's words are taken from single or double quotes that follow "owner" and a colon or comma in the intent, the landing subject or the packet's Intent line; a quote the intent paraphrases without quote marks is not found.
{?} NeatWalkCheck: neat walk --check is also accepted (dispatches to walk.py --check) though the brief named only walk, walk N and walk --page.
{?} PathCutSwallowedQuotes: the first build cut an escaped quote along with a path 190 times (the verifier's find); the cut now stops before an html entity. The concept map also filed tests and the other kernel files under docs; tests are their own concept now and the rest of pyto/src is PxC.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 63 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 63`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-63): the walk: the owner, 2026-09-10: 'make it real easy for me and Astra to step through your landings, inspect changes, keep all PQL, PxC, etc front of mind automatically'. pyto/scripts/walk.py builds walk.html from the record alone: one step per landing in order (intent, the owner's words it quotes, the receipt, files changed with counts and the diff folded, the packet's {?} lines, which of the seven concepts it touched with their one-line definitions pinned at the top of every step, and the sentence that undoes it); arrow keys step; --text N prints one step for an agent and neat walk N dispatches to it; same tree, same bytes; a test pins that every landing on the board has a step`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
