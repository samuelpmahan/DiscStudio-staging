# Task 78: card cascade editor as a PxC smoke test: four card projections (shelf, bag, single, competition) get cascading defaults global -> projection -> instance; each layer is a Part under px.discstudio.cards.*, fn.cards.effective and fn.cards.apply compose the effective card per projection inside the existing card chain, PQL prefix queries find overrides and inheritance, a recompose receipt says which edit recomposed which cards, and a three-pane editor (all cards, per-projection tabs, selected-card inspector) is retrofitted onto the existing surface; every friction is a proposal Part with its for, nothing is promoted

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
git fetch origin exp/78
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/78:pyto/experiments/tasks/78/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff afb918f origin/exp/78 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

card cascade editor as a PxC smoke test: four card projections (shelf, bag, single, competition) get cascading defaults global -> projection -> instance; each layer is a Part under px.discstudio.cards.*, fn.cards.effective and fn.cards.apply compose the effective card per projection inside the existing card chain, PQL prefix queries find overrides and inheritance, a recompose receipt says which edit recomposed which cards, and a three-pane editor (all cards, per-projection tabs, selected-card inspector) is retrofitted onto the existing surface; every friction is a proposal Part with its for, nothing is promoted

## Starting point

d47cd064281b0014caa1fb85c5b922cc7a5b61ef (land(task-77): USE.md section 4 still teaches the rule the owner overturned: 'the Calculations of one Tick are parallel branches, so none of them may read another's produce'; it now says what the kernel does since task 57 (inside a Tick the Calculations are a sequence in declared order, a later one may bind an earlier sibling's result, a Tick with no sibling reads may run at once, a read of a later sibling and two siblings on one address are refused) with a chained Tick in the block and its printed output, and every other page that repeats the old sentence is corrected). MAIN may have moved since: `git log --oneline afb918f..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/cards/CONTRACT.md
- A  pyto/experiments/cards/FINDINGS.md
- M  pyto/viewer/fixtures/discstudio-display-card.json
- M  pyto/viewer/test/adapters.test.mjs
- M  scripts/browser_test.py
- M  src/app.js
- A  src/cards-findings.js
- A  src/cards.js
- M  src/domain.js
- M  src/runtime.js
- M  src/seed.js
- M  src/style.css
- A  tests/cards.test.js
- M  tests/core.test.js
- M  tests/fixtures/serial-run-record.json

```
pyto/experiments/cards/CONTRACT.md                |  174 +++
 pyto/experiments/cards/FINDINGS.md                |   83 ++
 pyto/viewer/fixtures/discstudio-display-card.json | 1372 ++++++++++++++++++-
 pyto/viewer/test/adapters.test.mjs                |   10 +-
 scripts/browser_test.py                           |   60 +-
 src/app.js                                        |  111 +-
 src/cards-findings.js                             |   93 ++
 src/cards.js                                      |  188 +++
 src/domain.js                                     |   10 +-
 src/runtime.js                                    |  112 +-
 src/seed.js                                       |    8 +-
 src/style.css                                     |   33 +
 tests/cards.test.js                               |  204 +++
 tests/core.test.js                                |    4 +-
 tests/fixtures/serial-run-record.json             | 1523 ++++++++++++++++++++-
 15 files changed, 3842 insertions(+), 143 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.9UAx2t40ww) (evidence/check_all.txt)
    suite                         tests  status
    library                         435  OK
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

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 78 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 78`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-78): card cascade editor as a PxC smoke test: four card projections (shelf, bag, single, competition) get cascading defaults global -> projection -> instance; each layer is a Part under px.discstudio.cards.*, fn.cards.effective and fn.cards.apply compose the effective card per projection inside the existing card chain, PQL prefix queries find overrides and inheritance, a recompose receipt says which edit recomposed which cards, and a three-pane editor (all cards, per-projection tabs, selected-card inspector) is retrofitted onto the existing surface; every friction is a proposal Part with its for, nothing is promoted`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
