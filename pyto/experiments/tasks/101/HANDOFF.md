# Task 101: brain/stats and brain/data, the last wave: the robust simple regressions (theil-sen and siegel repeated medians) and the whole simple-regression verdict in one Calculation, all against scipy; and the three series transforms a pipeline still wants: percentage change, the expanding (whole-history) statistics on the same cumulative pass as the rolling ones, and linear interpolation over the holes

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
git fetch origin exp/101
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/101:pyto/experiments/tasks/101/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 3810850 origin/exp/101 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain/stats and brain/data, the last wave: the robust simple regressions (theil-sen and siegel repeated medians) and the whole simple-regression verdict in one Calculation, all against scipy; and the three series transforms a pipeline still wants: percentage change, the expanding (whole-history) statistics on the same cumulative pass as the rolling ones, and linear interpolation over the holes

## Starting point

c84c961a82c757bd0fa2f37a654b8108bac75ffb (board: **started** `task-100`: brain/backend the benchmark Parts are what decid). MAIN may have moved since: `git log --oneline 3810850..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/brain/data/test_timeseries.py
- M  pyto/experiments/brain/data/timeseries.py
- M  pyto/experiments/brain/data/timeseries_cases.py
- M  pyto/experiments/brain/records/data.pipeline.json
- M  pyto/experiments/brain/records/stats.analysis.json
- M  pyto/experiments/brain/stats/build.py
- A  pyto/experiments/brain/stats/robust.py
- A  pyto/experiments/brain/stats/robust_cases.py
- A  pyto/experiments/brain/stats/test_robust.py
- M  pyto/experiments/brain/store/data.json
- M  pyto/experiments/brain/store/stats.json

```
pyto/experiments/brain/data/test_timeseries.py     |   66 +
 pyto/experiments/brain/data/timeseries.py          |   86 +-
 pyto/experiments/brain/data/timeseries_cases.py    |   75 +
 pyto/experiments/brain/records/data.pipeline.json  |   10 +-
 pyto/experiments/brain/records/stats.analysis.json |   12 +-
 pyto/experiments/brain/stats/build.py              |    9 +-
 pyto/experiments/brain/stats/robust.py             |  172 ++
 pyto/experiments/brain/stats/robust_cases.py       |  105 ++
 pyto/experiments/brain/stats/test_robust.py        |  136 ++
 pyto/experiments/brain/store/data.json             | 1860 +++++++++++++++++---
 pyto/experiments/brain/store/stats.json            | 1204 ++++++++++---
 11 files changed, 3184 insertions(+), 551 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.FQDOmdhHh7) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               701  OK
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

{?} Two stacks: evidence/verify-py312.txt is the whole brain suite on python 3.12.3 + numpy
2.5.3 + scipy 1.18.1 as well as the copy's own venv. Both are green (693 tests).
{?} fn.brain.data.expanding is fn.brain.data.rolling with the window set to the length of the
series, and nothing else: the same three engines, the same oracle shape, and the cumsum engine
is what turns an expanding statistic from O(n^2) into O(n).
{?} theil_sen reproduces scipy's confidence interval exactly, including the two rank indices
scipy takes from Sen (1968) equation 2.6 -- the interval is part of the oracle, not just the slope.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 101 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 101`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-101): brain/stats and brain/data, the last wave: the robust simple regressions (theil-sen and siegel repeated medians) and the whole simple-regression verdict in one Calculation, all against scipy; and the three series transforms a pipeline still wants: percentage change, the expanding (whole-history) statistics on the same cumulative pass as the rolling ones, and linear interpolation over the holes`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
