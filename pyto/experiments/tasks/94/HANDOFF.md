# Task 94: brain/stats and brain/data, the second wave: kolmogorov-smirnov one and two sample, the wilcoxon signed-rank test and the p-value beside a pearson correlation, all with a pure-python tail (birnbaum-tingey, hodges, the limiting kolmogorov) that matches scipy exactly; a third group-by engine npsort that sorts once and reduces whole columns with numpy cumsum and reduceat, entered as the third candidate of the group-by bracket; melt as pivot's inverse and describe_table, the one place the data vertical calls the stats vertical

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
git fetch origin exp/94
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/94:pyto/experiments/tasks/94/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff f66c703 origin/exp/94 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain/stats and brain/data, the second wave: kolmogorov-smirnov one and two sample, the wilcoxon signed-rank test and the p-value beside a pearson correlation, all with a pure-python tail (birnbaum-tingey, hodges, the limiting kolmogorov) that matches scipy exactly; a third group-by engine npsort that sorts once and reduces whole columns with numpy cumsum and reduceat, entered as the third candidate of the group-by bracket; melt as pivot's inverse and describe_table, the one place the data vertical calls the stats vertical

## Starting point

46cf6e2d4b003ccb641578962b981dcc04918151 (board: **started** `task-93`: brain/backend the evidence and the tournaments: f). MAIN may have moved since: `git log --oneline f66c703..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/brain/data/build.py
- M  pyto/experiments/brain/data/frame.py
- M  pyto/experiments/brain/data/frame_cases.py
- M  pyto/experiments/brain/data/referee.py
- A  pyto/experiments/brain/data/shaping.py
- A  pyto/experiments/brain/data/shaping_cases.py
- A  pyto/experiments/brain/data/sorted_groups.py
- M  pyto/experiments/brain/data/test_build.py
- M  pyto/experiments/brain/data/test_frame.py
- A  pyto/experiments/brain/data/test_shaping.py
- M  pyto/experiments/brain/records/data.pipeline.json
- M  pyto/experiments/brain/records/stats.analysis.json
- M  pyto/experiments/brain/stats/build.py
- A  pyto/experiments/brain/stats/nonparametric.py
- A  pyto/experiments/brain/stats/nonparametric_cases.py
- A  pyto/experiments/brain/stats/test_nonparametric.py
- M  pyto/experiments/brain/store/data.json
- M  pyto/experiments/brain/store/stats.json

```
pyto/experiments/brain/data/build.py               |   72 +-
 pyto/experiments/brain/data/frame.py               |   42 +-
 pyto/experiments/brain/data/frame_cases.py         |   27 +-
 pyto/experiments/brain/data/referee.py             |    7 +-
 pyto/experiments/brain/data/shaping.py             |  107 +
 pyto/experiments/brain/data/shaping_cases.py       |  103 +
 pyto/experiments/brain/data/sorted_groups.py       |   87 +
 pyto/experiments/brain/data/test_build.py          |   33 +-
 pyto/experiments/brain/data/test_frame.py          |   34 +-
 pyto/experiments/brain/data/test_shaping.py        |  129 +
 pyto/experiments/brain/records/data.pipeline.json  |   12 +-
 pyto/experiments/brain/records/stats.analysis.json |   12 +-
 pyto/experiments/brain/stats/build.py              |   27 +-
 pyto/experiments/brain/stats/nonparametric.py      |  321 ++
 .../experiments/brain/stats/nonparametric_cases.py |  124 +
 pyto/experiments/brain/stats/test_nonparametric.py |  146 +
 pyto/experiments/brain/store/data.json             | 4290 ++++++++++++++------
 pyto/experiments/brain/store/stats.json            | 1132 +++++-
 18 files changed, 5298 insertions(+), 1407 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.LCRp2ZM7Ma) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               540  OK
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
   `bash pyto/scripts/neat.sh drop 94 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 94`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-94): brain/stats and brain/data, the second wave: kolmogorov-smirnov one and two sample, the wilcoxon signed-rank test and the p-value beside a pearson correlation, all with a pure-python tail (birnbaum-tingey, hodges, the limiting kolmogorov) that matches scipy exactly; a third group-by engine npsort that sorts once and reduces whole columns with numpy cumsum and reduceat, entered as the third candidate of the group-by bracket; melt as pivot's inverse and describe_table, the one place the data vertical calls the stats vertical`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
