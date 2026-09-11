# Task 87: brain/backend the facade: fn.brain.backend.<op> with engines py/np/sp for matmul, solve, lstsq, cumsum, histogram, sort, argsort, select_k, pairwise, eig, svd, fft; one place where the json-able, total-order and sign-canonical semantics every engine must meet are pinned, with the py engine as the readable reference and the stubs (general non-symmetric eig, svd's u and v) refused loudly rather than answered wrongly

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
git fetch origin exp/87
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/87:pyto/experiments/tasks/87/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff fd1a59d origin/exp/87 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain/backend the facade: fn.brain.backend.<op> with engines py/np/sp for matmul, solve, lstsq, cumsum, histogram, sort, argsort, select_k, pairwise, eig, svd, fft; one place where the json-able, total-order and sign-canonical semantics every engine must meet are pinned, with the py engine as the readable reference and the stubs (general non-symmetric eig, svd's u and v) refused loudly rather than answered wrongly

## Starting point

0b4d8ac18b52ad3ce144fb81492209c3cce2c6e0 (land(task-83): brain ml foundation: the ml vertical's shared core (backend dispatch py/np, matrix helpers, seeded generators, part/oracle/bench/record writers) plus linear regression closed form and gradient descent, ridge, regression metrics (mse/mae/r2) and seeded train-test split and k-fold, each a Calculation fn.brain.ml.<name> with oracle Parts, tests and benchmarks). MAIN may have moved since: `git log --oneline fd1a59d..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/brain/backend/cases.py
- A  pyto/experiments/brain/backend/ops.py
- A  pyto/experiments/brain/backend/test_ops.py
- M  pyto/experiments/brain/records/ml.regression.json

```
pyto/experiments/brain/backend/cases.py           | 125 +++++
 pyto/experiments/brain/backend/ops.py             | 591 ++++++++++++++++++++++
 pyto/experiments/brain/backend/test_ops.py        | 175 +++++++
 pyto/experiments/brain/records/ml.regression.json |  24 +-
 4 files changed, 903 insertions(+), 12 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.C5ki7INu5C) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               133  OK
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

{?} sp engines that are numpy's: cumsum, sort and argsort have no distinct scipy call worth the
name, so their `sp` engine is numpy's, said out loud in the docstring. The alternative was three
ops with two engines; keeping three engines everywhere keeps the oracle table square.
{?} svd returns singular values only. u and v carry a per-column sign freedom that the engines
spend differently; canonicalising them is real work and it is recorded as a stub in the map part
rather than half-done.
{?} eig refuses a complex spectrum rather than returning `{"real", "imag"}` the way fft does.
fft is always complex so the convention is free; eig is usually real and a caller who gets two
lists back would have to branch. If the ml vertical needs complex eigenvalues, that is a finding.
{?} the py engine of solve refuses a singular matrix at |pivot| < 1e-300, which is a different
question from numpy's condition-number view; the three engines agree on the obvious singular case
that the test pins, and may disagree on a nearly-singular one.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 87 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 87`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-87): brain/backend the facade: fn.brain.backend.<op> with engines py/np/sp for matmul, solve, lstsq, cumsum, histogram, sort, argsort, select_k, pairwise, eig, svd, fft; one place where the json-able, total-order and sign-canonical semantics every engine must meet are pinned, with the py engine as the readable reference and the stubs (general non-symmetric eig, svd's u and v) refused loudly rather than answered wrongly`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
