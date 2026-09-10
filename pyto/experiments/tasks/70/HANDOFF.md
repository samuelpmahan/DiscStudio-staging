# Task 70: the batch carries only what needs the owner: a root label whose entry quotes the owner deciding counts as answered; neat default <n> <k> '<sentence>' files an agent's default as an answer of kind default (the item leaves the batch, stays overturnable in one sentence, and is written on the root as the session's default, never as the owner's words); neat ask prints the items that need the owner first and says how many there are; the 30 non-meaning items of batch 2 are filed as defaults by the session

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
git fetch origin exp/70
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/70:pyto/experiments/tasks/70/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff ebab765 origin/exp/70 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the batch carries only what needs the owner: a root label whose entry quotes the owner deciding counts as answered; neat default <n> <k> '<sentence>' files an agent's default as an answer of kind default (the item leaves the batch, stays overturnable in one sentence, and is written on the root as the session's default, never as the owner's words); neat ask prints the items that need the owner first and says how many there are; the 30 non-meaning items of batch 2 are filed as defaults by the session

## Starting point

2b2bcfd0303de2b01f4bd5ffdce96dd674dcded7 (land(task-68): the first batch through the integrated loop: neat ask run once on the tree that holds tasks 65, 66 and 67 together, its batch Part and run record kept as evidence under pyto/experiments/review; FRONTIER.md's Landed adds gain the three (the question loop, the difference before it is shown with counting before mining, the join's gate) in the owner's words). MAIN may have moved since: `git log --oneline ebab765..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/review/answers/AbsolutePathsInTheRecord.json
- A  pyto/experiments/review/answers/CompoundMolecules.json
- A  pyto/experiments/review/answers/ConceptMap.json
- A  pyto/experiments/review/answers/DiffNewIsAsymmetric.json
- A  pyto/experiments/review/answers/DiffPrintForm.json
- A  pyto/experiments/review/answers/DiffRemainderOcOrder.json
- A  pyto/experiments/review/answers/DocumentDropsArgs.json
- A  pyto/experiments/review/answers/FileIsNotAnEffect.json
- A  pyto/experiments/review/answers/HashRefUnchecked.json
- A  pyto/experiments/review/answers/HttpIsNotAnEffectKind.json
- A  pyto/experiments/review/answers/LabelsOutsideReadPqlGrammar.json
- A  pyto/experiments/review/answers/MoleculeAddress.json
- A  pyto/experiments/review/answers/NeatDiffCalculationRunForm.json
- A  pyto/experiments/review/answers/NeatWalkCheck.json
- A  pyto/experiments/review/answers/OnePartQuery.json
- A  pyto/experiments/review/answers/PartLabelKind.json
- A  pyto/experiments/review/answers/PathCutSwallowedQuotes.json
- A  pyto/experiments/review/answers/PxMolecules.json
- A  pyto/experiments/review/answers/RootItemScope.json
- A  pyto/experiments/review/answers/RootItemText.json
- A  pyto/experiments/review/answers/SecretsAreNotEffects.json
- A  pyto/experiments/review/answers/SubjectIsTheHeadSha.json
- A  pyto/experiments/review/answers/WalkReachability.json
- A  pyto/experiments/review/batches/3.json
- A  pyto/experiments/review/batches/4.json
- A  pyto/experiments/review/batches/5.json
- A  pyto/experiments/review/batches/6.json
- A  pyto/experiments/review/batches/7.json
- A  pyto/experiments/review/captures/6-219.json
- A  pyto/experiments/review/captures/6-220.json
- A  pyto/experiments/review/captures/6-221.json
- A  pyto/experiments/review/captures/6-222.json
- A  pyto/experiments/review/captures/6-223.json
- A  pyto/experiments/review/captures/6-224.json
- A  pyto/experiments/review/captures/6-225.json
- A  pyto/experiments/review/captures/6-226.json
- A  pyto/experiments/review/captures/6-227.json
- A  pyto/experiments/review/captures/6-228.json
- A  pyto/experiments/review/captures/6-229.json
- A  pyto/experiments/review/captures/6-230.json
- A  pyto/experiments/review/captures/6-231.json
- A  pyto/experiments/review/captures/6-232.json
- A  pyto/experiments/review/captures/6-233.json
- A  pyto/experiments/review/captures/6-234.json
- A  pyto/experiments/review/captures/6-235.json
- A  pyto/experiments/review/captures/6-236.json
- A  pyto/experiments/review/captures/6-237.json
- A  pyto/experiments/review/captures/6-238.json
- A  pyto/experiments/review/captures/6-239.json
- A  pyto/experiments/review/captures/6-240.json
- A  pyto/experiments/review/captures/6-241.json
- A  pyto/experiments/review/freezes/6-219.json
- A  pyto/experiments/review/freezes/6-220.json
- A  pyto/experiments/review/freezes/6-221.json
- A  pyto/experiments/review/freezes/6-222.json
- A  pyto/experiments/review/freezes/6-223.json
- A  pyto/experiments/review/freezes/6-224.json
- A  pyto/experiments/review/freezes/6-225.json
- A  pyto/experiments/review/freezes/6-226.json
- A  pyto/experiments/review/freezes/6-227.json
- A  pyto/experiments/review/freezes/6-228.json
- A  pyto/experiments/review/freezes/6-229.json
- A  pyto/experiments/review/freezes/6-230.json
- A  pyto/experiments/review/freezes/6-231.json
- A  pyto/experiments/review/freezes/6-232.json
- A  pyto/experiments/review/freezes/6-233.json
- A  pyto/experiments/review/freezes/6-234.json
- A  pyto/experiments/review/freezes/6-235.json
- A  pyto/experiments/review/freezes/6-236.json
- A  pyto/experiments/review/freezes/6-237.json
- A  pyto/experiments/review/freezes/6-238.json
- A  pyto/experiments/review/freezes/6-239.json
- A  pyto/experiments/review/freezes/6-240.json
- A  pyto/experiments/review/freezes/6-241.json
- A  pyto/experiments/review/runs/ask-3.json
- A  pyto/experiments/review/runs/ask-4.json
- A  pyto/experiments/review/runs/ask-5.json
- A  pyto/experiments/review/runs/ask-6.json
- A  pyto/experiments/review/runs/ask-7.json
- A  pyto/experiments/review/runs/default-6-219.json
- A  pyto/experiments/review/runs/default-6-220.json
- A  pyto/experiments/review/runs/default-6-221.json
- A  pyto/experiments/review/runs/default-6-222.json
- A  pyto/experiments/review/runs/default-6-223.json
- A  pyto/experiments/review/runs/default-6-224.json
- A  pyto/experiments/review/runs/default-6-225.json
- A  pyto/experiments/review/runs/default-6-226.json
- A  pyto/experiments/review/runs/default-6-227.json
- A  pyto/experiments/review/runs/default-6-228.json
- A  pyto/experiments/review/runs/default-6-229.json
- A  pyto/experiments/review/runs/default-6-230.json
- A  pyto/experiments/review/runs/default-6-231.json
- A  pyto/experiments/review/runs/default-6-232.json
- A  pyto/experiments/review/runs/default-6-233.json
- A  pyto/experiments/review/runs/default-6-234.json
- A  pyto/experiments/review/runs/default-6-235.json
- A  pyto/experiments/review/runs/default-6-236.json
- A  pyto/experiments/review/runs/default-6-237.json
- A  pyto/experiments/review/runs/default-6-238.json
- A  pyto/experiments/review/runs/default-6-239.json
- A  pyto/experiments/review/runs/default-6-240.json
- A  pyto/experiments/review/runs/default-6-241.json
- M  pyto/questions.md
- M  pyto/scripts/neat.sh
- M  pyto/scripts/walk.py
- M  pyto/src/pyto/neat/review.py
- M  pyto/tests/test_neat_review.py

```
.../review/answers/AbsolutePathsInTheRecord.json   |   11 +
 .../review/answers/CompoundMolecules.json          |   11 +
 pyto/experiments/review/answers/ConceptMap.json    |   11 +
 .../review/answers/DiffNewIsAsymmetric.json        |   11 +
 pyto/experiments/review/answers/DiffPrintForm.json |   11 +
 .../review/answers/DiffRemainderOcOrder.json       |   11 +
 .../review/answers/DocumentDropsArgs.json          |   11 +
 .../review/answers/FileIsNotAnEffect.json          |   11 +
 .../review/answers/HashRefUnchecked.json           |   11 +
 .../review/answers/HttpIsNotAnEffectKind.json      |   11 +
 .../answers/LabelsOutsideReadPqlGrammar.json       |   11 +
 .../review/answers/MoleculeAddress.json            |   11 +
 .../review/answers/NeatDiffCalculationRunForm.json |   11 +
 pyto/experiments/review/answers/NeatWalkCheck.json |   11 +
 pyto/experiments/review/answers/OnePartQuery.json  |   11 +
 pyto/experiments/review/answers/PartLabelKind.json |   11 +
 .../review/answers/PathCutSwallowedQuotes.json     |   11 +
 pyto/experiments/review/answers/PxMolecules.json   |   11 +
 pyto/experiments/review/answers/RootItemScope.json |   11 +
 pyto/experiments/review/answers/RootItemText.json  |   11 +
 .../review/answers/SecretsAreNotEffects.json       |   11 +
 .../review/answers/SubjectIsTheHeadSha.json        |   11 +
 .../review/answers/WalkReachability.json           |   11 +
 pyto/experiments/review/batches/3.json             | 2051 +++++++++++++++++++
 pyto/experiments/review/batches/4.json             | 2052 ++++++++++++++++++++
 pyto/experiments/review/batches/5.json             | 1941 ++++++++++++++++++
 pyto/experiments/review/batches/6.json             | 1941 ++++++++++++++++++
 pyto/experiments/review/batches/7.json             | 1757 +++++++++++++++++
 pyto/experiments/review/captures/6-219.json        |   11 +
 pyto/experiments/review/captures/6-220.json        |   11 +
 pyto/experiments/review/captures/6-221.json        |   11 +
 pyto/experiments/review/captures/6-222.json        |   11 +
 pyto/experiments/review/captures/6-223.json        |   11 +
 pyto/experiments/review/captures/6-224.json        |   11 +
 pyto/experiments/review/captures/6-225.json        |   11 +
 pyto/experiments/review/captures/6-226.json        |   11 +
 pyto/experiments/review/captures/6-227.json        |   11 +
 pyto/experiments/review/captures/6-228.json        |   11 +
 pyto/experiments/review/captures/6-229.json        |   11 +
 pyto/experiments/review/captures/6-230.json        |   11 +
 pyto/experiments/review/captures/6-231.json        |   11 +
 pyto/experiments/review/captures/6-232.json        |   11 +
 pyto/experiments/review/captures/6-233.json        |   11 +
 pyto/experiments/review/captures/6-234.json        |   11 +
 pyto/experiments/review/captures/6-235.json        |   11 +
 pyto/experiments/review/captures/6-236.json        |   11 +
 pyto/experiments/review/captures/6-237.json        |   11 +
 pyto/experiments/review/captures/6-238.json        |   11 +
 pyto/experiments/review/captures/6-239.json        |   11 +
 pyto/experiments/review/captures/6-240.json        |   11 +
 pyto/experiments/review/captures/6-241.json        |   11 +
 pyto/experiments/review/freezes/6-219.json         |    8 +
 pyto/experiments/review/freezes/6-220.json         |    8 +
 pyto/experiments/review/freezes/6-221.json         |    8 +
 pyto/experiments/review/freezes/6-222.json         |    8 +
 pyto/experiments/review/freezes/6-223.json         |    8 +
 pyto/experiments/review/freezes/6-224.json         |    8 +
 pyto/experiments/review/freezes/6-225.json         |    8 +
 pyto/experiments/review/freezes/6-226.json         |    8 +
 pyto/experiments/review/freezes/6-227.json         |    8 +
 pyto/experiments/review/freezes/6-228.json         |    8 +
 pyto/experiments/review/freezes/6-229.json         |    8 +
 pyto/experiments/review/freezes/6-230.json         |    8 +
 pyto/experiments/review/freezes/6-231.json         |    8 +
 pyto/experiments/review/freezes/6-232.json         |    8 +
 pyto/experiments/review/freezes/6-233.json         |    8 +
 pyto/experiments/review/freezes/6-234.json         |    8 +
 pyto/experiments/review/freezes/6-235.json         |    8 +
 pyto/experiments/review/freezes/6-236.json         |    8 +
 pyto/experiments/review/freezes/6-237.json         |    8 +
 pyto/experiments/review/freezes/6-238.json         |    8 +
 pyto/experiments/review/freezes/6-239.json         |    8 +
 pyto/experiments/review/freezes/6-240.json         |    8 +
 pyto/experiments/review/freezes/6-241.json         |    8 +
 pyto/experiments/review/runs/ask-3.json            | 1669 ++++++++++++++++
 pyto/experiments/review/runs/ask-4.json            | 1670 ++++++++++++++++
 pyto/experiments/review/runs/ask-5.json            | 1671 ++++++++++++++++
 pyto/experiments/review/runs/ask-6.json            | 1671 ++++++++++++++++
 pyto/experiments/review/runs/ask-7.json            | 1671 ++++++++++++++++
 pyto/experiments/review/runs/default-6-219.json    |  189 ++
 pyto/experiments/review/runs/default-6-220.json    |  189 ++
 pyto/experiments/review/runs/default-6-221.json    |  189 ++
 pyto/experiments/review/runs/default-6-222.json    |  189 ++
 pyto/experiments/review/runs/default-6-223.json    |  189 ++
 pyto/experiments/review/runs/default-6-224.json    |  189 ++
 pyto/experiments/review/runs/default-6-225.json    |  189 ++
 pyto/experiments/review/runs/default-6-226.json    |  189 ++
 pyto/experiments/review/runs/default-6-227.json    |  189 ++
 pyto/experiments/review/runs/default-6-228.json    |  189 ++
 pyto/experiments/review/runs/default-6-229.json    |  189 ++
 pyto/experiments/review/runs/default-6-230.json    |  189 ++
 pyto/experiments/review/runs/default-6-231.json    |  189 ++
 pyto/experiments/review/runs/default-6-232.json    |  189 ++
 pyto/experiments/review/runs/default-6-233.json    |  189 ++
 pyto/experiments/review/runs/default-6-234.json    |  189 ++
 pyto/experiments/review/runs/default-6-235.json    |  189 ++
 pyto/experiments/review/runs/default-6-236.json    |  189 ++
 pyto/experiments/review/runs/default-6-237.json    |  189 ++
 pyto/experiments/review/runs/default-6-238.json    |  189 ++
 pyto/experiments/review/runs/default-6-239.json    |  189 ++
 pyto/experiments/review/runs/default-6-240.json    |  189 ++
 pyto/experiments/review/runs/default-6-241.json    |  189 ++
 pyto/questions.md                                  |   94 +
 pyto/scripts/neat.sh                               |   15 +-
 pyto/scripts/walk.py                               |    5 +-
 pyto/src/pyto/neat/review.py                       |  119 +-
 pyto/tests/test_neat_review.py                     |   38 +
 107 files changed, 23377 insertions(+), 25 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_neat_review && python scripts/walk.py --check` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.J1jRGeOm4n) (evidence/check_all.txt)
    suite                         tests  status
    library                         368  OK
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
{?} NeedsOwnerIsAWord: a packet line needs the owner when it contains the word owner; that is the agent's own declaration and it misses lines that change meaning without saying so (ChainLatencyIsTheWholeTick, MoleculeAddress, FileIsNotAnEffect were filed as defaults by this rule and are raised in chat by hand).
{?} RootIsCounted: root entries are counted as open on the root and never re-asked in a batch, because the root is the owner's own page; an entry that quotes him deciding is answered.
{?} ReviewPageScope: every packet up to task 59 is the review page's, so its lines are not asked again; the number is a constant in review.py.
{?} DefaultSentences: the 23 defaults filed here restate each packet line's first clause; two were mangled by the shell on the first pass and refiled by hand.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 70 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 70`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-70): the batch carries only what needs the owner: a root label whose entry quotes the owner deciding counts as answered; neat default <n> <k> '<sentence>' files an agent's default as an answer of kind default (the item leaves the batch, stays overturnable in one sentence, and is written on the root as the session's default, never as the owner's words); neat ask prints the items that need the owner first and says how many there are; the 30 non-meaning items of batch 2 are filed as defaults by the session`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
