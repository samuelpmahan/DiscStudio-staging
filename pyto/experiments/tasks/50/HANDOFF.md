# Task 50: effects you can see and the sprint on the one page: the Tick viewer shows an invocation's effects (kind, path, digest) when the record carries them and draws oc Calculations distinctly; the students demo page is regenerated with the side-by-side renderer; KT-MAC gains the px shell in chunk 3 and a classroom chunk 7; FRONTIER records the sprint's landed adds

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
git fetch origin exp/50
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/50:pyto/experiments/tasks/50/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff bc70a0c origin/exp/50 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

effects you can see and the sprint on the one page: the Tick viewer shows an invocation's effects (kind, path, digest) when the record carries them and draws oc Calculations distinctly; the students demo page is regenerated with the side-by-side renderer; KT-MAC gains the px shell in chunk 3 and a classroom chunk 7; FRONTIER records the sprint's landed adds

## Starting point

defc5b93a8623c6c418d2abc71d867b9848e98f2 (land(task-47): neat never reuses an id: next_id also counts the landing receipts (task-N, undo-task-N, failed), so an undone or killed task's number is not handed out again; selftest proves it). MAIN may have moved since: `git log --oneline bc70a0c..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/CHANGES.md
- M  pyto/FRONTIER.md
- M  pyto/KT-MAC.md
- M  pyto/experiments/students/README.md
- M  pyto/experiments/students/evidence/run-1/tick-viewer.html
- A  pyto/viewer/fixtures/effects-demo.json
- A  pyto/viewer/test/effects-view.test.mjs
- A  pyto/viewer/test/students-card-tree.golden.txt
- M  pyto/viewer/tick-viewer.html
- M  pyto/viewer/tick-viewer.js

```
pyto/CHANGES.md                                    |   1 +
 pyto/FRONTIER.md                                   | 159 +++++------
 pyto/KT-MAC.md                                     |  60 ++++
 pyto/experiments/students/README.md                |   9 +-
 .../students/evidence/run-1/tick-viewer.html       | 313 ++++++++++++++++++++-
 pyto/viewer/fixtures/effects-demo.json             | 136 +++++++++
 pyto/viewer/test/effects-view.test.mjs             | 248 ++++++++++++++++
 pyto/viewer/test/students-card-tree.golden.txt     | 279 ++++++++++++++++++
 pyto/viewer/tick-viewer.html                       |  16 ++
 pyto/viewer/tick-viewer.js                         |  82 +++++-
 10 files changed, 1205 insertions(+), 98 deletions(-)
```

## Evidence

- verify: `cd pyto && node --test viewer/test/*.test.mjs && cd experiments/students && python3 -m unittest discover -s . -p 'test_*.py' && python3 grade.py --run evidence/run-1 --handoff HANDOFF.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.znvyaTr3Ns) (evidence/check_all.txt)
    suite                         tests  status
    library                         285  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} EffectsFailThePythonValidatorTheSameWayTheParallelKeysDo: `viewer/fixtures/effects-demo.json` is otherwise valid on purpose -- the only thing `viewer/test/record_schema.py` refuses in it is the word `effects` (`ticks[0].invocations[0]: unknown field(s) effects not in RECORD.md`), so `px ps`, `px laws` and anything else that validates through that file exit 2 on it today. The JS validator ignores unknown fields and renders them, which is why the fixture is validated by the JS side only. This is exactly task 40's `{?} ContractKeysFailThePythonValidator` with a fifth key: `effects` needs adding to record_schema.py's invocation key tuple (and RECORD.md needs the field written down) before any producer ships it. Both files belong to other teams and were not touched. The fixture drops task 40's `latency_ms` for the same reason -- it is not part of this contract and it was the only other refusal.
{?} EffectDigestIsTwelveHexWithTheWholeOneOnTheTitle: the packet said "the digest's first 12 hex", and the card already prints `impl <12 hex>…` and `digest <16 hex>…`, so an effect row prints the first twelve with the same ellipsis and carries the whole digest on the row's `title`. Nothing is lost and the row stays one line; if the owner wants the bare twelve with no ellipsis, or sixteen to match the invocation's own digest, it is one argument in `renderEffects`.
{?} OcIsAboutTheAddressNotTheEffects: the `oc` chip and the card's border come from the calculation address alone, so an `oc.` Calculation that performed no effect is still drawn as an oc card with nothing under it, and a `fn.` Calculation that somehow carried effects would show the rows without the chip. That reads the contract as "oc is what a Calculation *is*, effects are what it *did*". The alternative -- mark the cards that actually did something -- would hide the OperationalCalculation that was allowed to touch the world and chose not to, which is the more interesting of the two.
{?} TheAsBeforeTestIsACommittedTree: "renders exactly as before" is pinned against `viewer/test/students-card-tree.golden.txt`, a 280-line serialization of the whole students page taken from the renderer as task 40 left it, before any of this task's code existed. It is the strongest form of the claim available without a browser, and it means a deliberate change to any card must regenerate that file -- and no script does: it is written by the test's own `serialize`, so regenerating it is a copy of eight lines. If the owner would rather that file did not exist, the weaker version is asserting the students page carries no `effect` nodes, which the two mutations below would both have survived.
{?} TheDemoPageWasRebuiltNotRerun: `experiments/students/evidence/run-1/tick-viewer.html` was rebuilt from its own committed `record.json` with `embed.mjs`, so `record.json` and `receipts.json` are byte for byte what they were (git diff empty) and run-1 is still the run that was shipped. Task 40's `{?} StudentsDemoPageIsBakedAndStale` suggested `python homework.py --out evidence/run-1`, which would rewrite all three; the record would very probably come back identical apart from the durations, and the durations are exactly what nothing may compare. Rebuilding only the page keeps the evidence and fixes the staleness.
{?} SprintAddsAreNamedByTheirTaskIntent: the owner named the sprint (his sentence is quoted at the head of FRONTIER's "Landed adds") and named none of the eight adds under it, so each entry is named by its own task intent line and the sentence after it is this session's description of what you see, marked as such in the file's header. Tasks 39 and 46 landed at 03:06 and 03:03 on the sprint branch, after this copy was cut, so their entries are written from the board's landed lines rather than from their packets, which are not in this copy.
{?} FIsPartlyLandedNotLanded: adds A to E moved to "Landed adds" whole; F did not. CI proves `check_all.sh` on three operating systems (44, 46), but F's own two sentences -- `proof.sh` green on the Mac with the same receipt shape, and a landing that edits `land.sh` itself landing cleanly -- are both untouched and both want the machine. F is therefore left in the open list with a "partly landed" head and what is left spelled out, rather than moved. Four residuals of the landed adds are listed under them so they are not lost with the add.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 50 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 50`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-50): effects you can see and the sprint on the one page: the Tick viewer shows an invocation's effects (kind, path, digest) when the record carries them and draws oc Calculations distinctly; the students demo page is regenerated with the side-by-side renderer; KT-MAC gains the px shell in chunk 3 and a classroom chunk 7; FRONTIER records the sprint's landed adds`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
