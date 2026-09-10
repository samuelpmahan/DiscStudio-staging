# Task 65: the question loop as Parts and Calculations: pyto/src/pyto/neat/review.py registers fn.neat.review.collate (every unanswered {?} line from the packets, the root and the diff Parts becomes one numbered batch Part proposal.neat.batch.<n>, same inputs same bytes), oc.neat.review.captureHumanText (the owner's reply as bytes, empty refused, neat.capture.review.<n>.<k>.response), fn.tidy.freezeText (sha256 of the exact bytes, a different rewrite at the same address refused, tidy.freeze.review.<n>.<k>.response) and fn.neat.review.file (the frozen bytes appended to pyto/questions.md under their label verbatim, technical half beside); neat ask, neat answer and neat answers run them as observed PCRs that leave run records under pyto/experiments/review; the walk shows each step's open questions and which are answered

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
git fetch origin exp/65
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/65:pyto/experiments/tasks/65/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 17845fa origin/exp/65 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the question loop as Parts and Calculations: pyto/src/pyto/neat/review.py registers fn.neat.review.collate (every unanswered {?} line from the packets, the root and the diff Parts becomes one numbered batch Part proposal.neat.batch.<n>, same inputs same bytes), oc.neat.review.captureHumanText (the owner's reply as bytes, empty refused, neat.capture.review.<n>.<k>.response), fn.tidy.freezeText (sha256 of the exact bytes, a different rewrite at the same address refused, tidy.freeze.review.<n>.<k>.response) and fn.neat.review.file (the frozen bytes appended to pyto/questions.md under their label verbatim, technical half beside); neat ask, neat answer and neat answers run them as observed PCRs that leave run records under pyto/experiments/review; the walk shows each step's open questions and which are answered

## Starting point

2f1dafe4cb5f8e4096c3a5289cd3997799f0b36a (land(task-64): the owner's words on what this is for and how the frontier runs through him: pyto/questions.md gains SuperGoogle (verbatim: a Python lib anyone can use to figure stuff out so long as they do something real and meaningful; AI as super Google and Python creator powers he can conceive but not implement; not distilling anything; the projection of his reasoning is a molecule) and TinyQuestions (the frontier workflow is tailored for subagent throughput through him: as many little questions as possible, answered by him, filed in his words; defaults are for nothing that carries meaning); FRONTIER.md's opening paragraph says so). MAIN may have moved since: `git log --oneline 17845fa..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/review/batches/1.json
- A  pyto/experiments/review/runs/ask-1.json
- M  pyto/scripts/neat.sh
- M  pyto/scripts/walk.py
- M  pyto/src/pyto/neat/__init__.py
- A  pyto/src/pyto/neat/review.py
- A  pyto/tests/test_neat_review.py

```
pyto/experiments/review/batches/1.json  | 1850 +++++++++++++++++++++++++++++++
 pyto/experiments/review/runs/ask-1.json | 1467 ++++++++++++++++++++++++
 pyto/scripts/neat.sh                    |   32 +-
 pyto/scripts/walk.py                    |   28 +-
 pyto/src/pyto/neat/__init__.py          |   20 +-
 pyto/src/pyto/neat/review.py            |  563 ++++++++++
 pyto/tests/test_neat_review.py          |  255 +++++
 7 files changed, 4207 insertions(+), 8 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_neat_review tests.test_walk && python scripts/walk.py --check` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.T7rCI1NunU) (evidence/check_all.txt)
    suite                         tests  status
    library                         356  OK
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
{?} FileIsNotAnEffect: fn.neat.review.file mutates pyto/questions.md directly inside its own Python body rather than through an oc./Effects handle, on the reading that "oc. only where an effect happens: reading a human's text, the network, the clock" scopes the effect boundary to captureHumanText alone and treats reading and appending to committed tree files (questions.md, packets) as ordinary computation over the tree -- the same reading that lets fn.neat.review.collate read every packet and questions.md directly. The packet's own Intent line names it fn., so I built it that way, but "appending to a real file" is exactly what effects.py's write_text verb exists for, and nothing about the file mutation lands on a receipt's effect ledger the way the clock read does. Is treating committed-tree reads and writes as fn. right, or should file's questions.md append go through oc. and an Effects handle instead?
{?} RootItemText: collate's root-origin items (task="root") use the heading's first non-empty body line as `text` (falling back to the label when a heading has none before the next), since the packet names only "the labels of pyto/questions.md (### {?} Label)" as the input and does not say what "text" should be for a root item. Is the first body line the right preview, or should it be the bare label, the whole entry, or something else?
{?} RootItemScope: the real questions.md carries 102 "### {?}" headings naming 117 labels (five headings group several labels on one comma-separated line, e.g. "### {?} PromotionScope, {?} ReceiptExport, ..."; three of the 117 are themselves duplicate labels, already flagged as {?} QuestionsDuplicateLabels), and since "answered" means only "an answer file exists for its label", every one of the 117 surfaces as an open root item the first time neat ask runs, including ones already marked "Status: resolved" in prose -- 263 items in batch 1 on this tree (146 packet + 117 root). Is surfacing every historical label right (a one-time backlog the TinyQuestions pipeline works through), or should root items be limited to labels whose own Status line says open/provisional?
{?} BatchItemTextLength: collate carries each packet {?} line's text verbatim, and some packet lines are a full paragraph (task-1's three lines each run past 600 characters); "neat ask" prints them unabridged in "N. [task] Label: text". Is verbatim right for a batch meant to be many *tiny* questions through the owner, or should long text be summarized or truncated for the printed list (with the Part still carrying the full text)?
{?} WalkReachability: the walk lists every landing commit reachable from HEAD (a copy that merged MAIN sees MAIN's landings behind the merge), each diffed against its first parent; on MAIN this is the same set as before.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 65 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 65`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-65): the question loop as Parts and Calculations: pyto/src/pyto/neat/review.py registers fn.neat.review.collate (every unanswered {?} line from the packets, the root and the diff Parts becomes one numbered batch Part proposal.neat.batch.<n>, same inputs same bytes), oc.neat.review.captureHumanText (the owner's reply as bytes, empty refused, neat.capture.review.<n>.<k>.response), fn.tidy.freezeText (sha256 of the exact bytes, a different rewrite at the same address refused, tidy.freeze.review.<n>.<k>.response) and fn.neat.review.file (the frozen bytes appended to pyto/questions.md under their label verbatim, technical half beside); neat ask, neat answer and neat answers run them as observed PCRs that leave run records under pyto/experiments/review; the walk shows each step's open questions and which are answered`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
