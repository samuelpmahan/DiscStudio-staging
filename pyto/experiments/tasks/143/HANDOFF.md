# Task 143: the owner's answers of 2026-09-12 filed in his words: the export queue (a queued job is instantiated, starts as a Sequence consumed once chosen, a smart start for longer batches), the two battle receipts (in ChainSpot a Receipt IS the text and renders together), single means OnTheCourse's Single Disc as intended, and the canvas stays on the layout until he says otherwise; batch 10 collated under the fixed rule

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
git fetch origin exp/143
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/143:pyto/experiments/tasks/143/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff aa56e29 origin/exp/143 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the owner's answers of 2026-09-12 filed in his words: the export queue (a queued job is instantiated, starts as a Sequence consumed once chosen, a smart start for longer batches), the two battle receipts (in ChainSpot a Receipt IS the text and renders together), single means OnTheCourse's Single Disc as intended, and the canvas stays on the layout until he says otherwise; batch 10 collated under the fixed rule

## Starting point

aa56e2932a7ec1fa0bfb4bf4309fbbc2318e04d0 (land(task-142): the demo gets a URL: the Pages workflow also deploys on a push to the sprint branch (the owner, 2026-09-12: 'PageRouter'), so the studio, its build, the browser test and the review page go live from claude/os-sprint-st8hnu without a merge to main). MAIN may have moved since: `git log --oneline aa56e29..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/review/answers/FrameIsPartOfTheLayout.json
- A  pyto/experiments/review/answers/OneBattleTwoReceipts.json
- A  pyto/experiments/review/answers/QueueIsSessionState.json
- A  pyto/experiments/review/answers/SinglePresetIsTheProjection.json
- A  pyto/experiments/review/batches/10.json
- A  pyto/experiments/review/captures/10-240.json
- A  pyto/experiments/review/captures/10-245.json
- A  pyto/experiments/review/captures/10-247.json
- A  pyto/experiments/review/captures/10-249.json
- A  pyto/experiments/review/freezes/10-240.json
- A  pyto/experiments/review/freezes/10-245.json
- A  pyto/experiments/review/freezes/10-247.json
- A  pyto/experiments/review/freezes/10-249.json
- A  pyto/experiments/review/runs/answer-10-245.json
- A  pyto/experiments/review/runs/answer-10-247.json
- A  pyto/experiments/review/runs/answer-10-249.json
- A  pyto/experiments/review/runs/ask-10.json
- A  pyto/experiments/review/runs/default-10-240.json
- M  pyto/questions.md

```
.../review/answers/FrameIsPartOfTheLayout.json     |   11 +
 .../review/answers/OneBattleTwoReceipts.json       |   11 +
 .../review/answers/QueueIsSessionState.json        |   11 +
 .../answers/SinglePresetIsTheProjection.json       |   11 +
 pyto/experiments/review/batches/10.json            | 2251 ++++++++++++++++++++
 pyto/experiments/review/captures/10-240.json       |   11 +
 pyto/experiments/review/captures/10-245.json       |   11 +
 pyto/experiments/review/captures/10-247.json       |   11 +
 pyto/experiments/review/captures/10-249.json       |   11 +
 pyto/experiments/review/freezes/10-240.json        |    8 +
 pyto/experiments/review/freezes/10-245.json        |    8 +
 pyto/experiments/review/freezes/10-247.json        |    8 +
 pyto/experiments/review/freezes/10-249.json        |    8 +
 pyto/experiments/review/runs/answer-10-245.json    |  189 ++
 pyto/experiments/review/runs/answer-10-247.json    |  189 ++
 pyto/experiments/review/runs/answer-10-249.json    |  189 ++
 pyto/experiments/review/runs/ask-10.json           | 1703 +++++++++++++++
 pyto/experiments/review/runs/default-10-240.json   |  189 ++
 pyto/questions.md                                  |   16 +
 19 files changed, 4846 insertions(+)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_neat_review` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.edXbqlpLPK) (evidence/check_all.txt)
    suite                         tests  status
    library                         447  OK
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

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 143 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 143`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-143): the owner's answers of 2026-09-12 filed in his words: the export queue (a queued job is instantiated, starts as a Sequence consumed once chosen, a smart start for longer batches), the two battle receipts (in ChainSpot a Receipt IS the text and renders together), single means OnTheCourse's Single Disc as intended, and the canvas stays on the layout until he says otherwise; batch 10 collated under the fixed rule`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
