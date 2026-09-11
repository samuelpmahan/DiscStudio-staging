# Task 107: brain/stats and brain/data close the night: the empirical cdf and its quantile inverse against scipy.stats.ecdf, and the two findings this vertical owes the backend vertical -- what stats and data each had to do by hand because the facade has no op for it, with the workaround taken and the op proposed

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
git fetch origin exp/107
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/107:pyto/experiments/tasks/107/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 9d593df origin/exp/107 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain/stats and brain/data close the night: the empirical cdf and its quantile inverse against scipy.stats.ecdf, and the two findings this vertical owes the backend vertical -- what stats and data each had to do by hand because the facade has no op for it, with the workaround taken and the op proposed

## Starting point

248fb102ae3ca440fed84d80fce22400f3846cc0 (board: **started** `task-106`: brain/backend the three findings the night itsel). MAIN may have moved since: `git log --oneline 9d593df..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/brain/data/build.py
- M  pyto/experiments/brain/records/data.pipeline.json
- M  pyto/experiments/brain/records/stats.analysis.json
- M  pyto/experiments/brain/stats/build.py
- M  pyto/experiments/brain/stats/summaries.py
- M  pyto/experiments/brain/stats/summaries_cases.py
- M  pyto/experiments/brain/stats/test_summaries.py
- M  pyto/experiments/brain/store/data.json
- M  pyto/experiments/brain/store/stats.json

```
pyto/experiments/brain/data/build.py               |   15 +
 pyto/experiments/brain/records/data.pipeline.json  |   10 +-
 pyto/experiments/brain/records/stats.analysis.json |   12 +-
 pyto/experiments/brain/stats/build.py              |   16 +
 pyto/experiments/brain/stats/summaries.py          |   48 +-
 pyto/experiments/brain/stats/summaries_cases.py    |   15 +
 pyto/experiments/brain/stats/test_summaries.py     |   30 +
 pyto/experiments/brain/store/data.json             |  234 ++---
 pyto/experiments/brain/store/stats.json            | 1020 ++++++++++++++------
 9 files changed, 992 insertions(+), 408 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.jvoV3GZ1ZH) (evidence/check_all.txt)
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

{?} Two stacks, both green (756 tests): evidence/verify-py312.txt is the whole brain suite on
python 3.12.3 + numpy 2.5.3 + scipy 1.18.1 as well as the copy's own venv.
{?} The two findings this adds are addressed to the BACKEND vertical and name what each of
these two verticals had to write by hand because the facade has no op for it:
proposal.brain.stats.the_linear_algebra_this_vertical_wrote_by_hand (four hand-written
decompositions inside one vertical) and
proposal.brain.data.the_signal_processing_this_vertical_does_not_have (convolve, correlate,
interpolate, rfft -- the four primitives every missing time-series calculation is missing).
Each says the workaround taken and the op proposed.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 107 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 107`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-107): brain/stats and brain/data close the night: the empirical cdf and its quantile inverse against scipy.stats.ecdf, and the two findings this vertical owes the backend vertical -- what stats and data each had to do by hand because the facade has no op for it, with the workaround taken and the op proposed`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
