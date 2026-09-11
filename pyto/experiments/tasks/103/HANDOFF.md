# Task 103: brain/backend six more primitives and the case table learns which engines answer: matrix_rank, pinv, correlate, diff, gradient and outer, each with its oracle Part per engine and benchmark Parts at three sizes; and the py engine of matrix_rank refuses the band its own svd cannot resolve - taking square roots of the eigenvalues of a-transpose-a squares the condition number, so a truly zero singular value comes back near sqrt of eps and numpy's rank tolerance sits far below anything that engine can see - which is why a case may now name the engines that answer it instead of being deleted from the table

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
git fetch origin exp/103
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/103:pyto/experiments/tasks/103/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 43f6c09 origin/exp/103 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain/backend six more primitives and the case table learns which engines answer: matrix_rank, pinv, correlate, diff, gradient and outer, each with its oracle Part per engine and benchmark Parts at three sizes; and the py engine of matrix_rank refuses the band its own svd cannot resolve - taking square roots of the eigenvalues of a-transpose-a squares the condition number, so a truly zero singular value comes back near sqrt of eps and numpy's rank tolerance sits far below anything that engine can see - which is why a case may now name the engines that answer it instead of being deleted from the table

## Starting point

daad2bf5dc3d87920640b20d188bfe6599b28c97 (land(task-102): brain ml multiclass: softmax (multinomial) logistic regression beside the one-vs-rest one, and gradient boosting for classification on the logistic loss with its second-order step, each fit and predict a separate Calculation over a json-able model Part, oracled against scipy minimising the same cross-entropy and against the probabilities the fit itself recorded). MAIN may have moved since: `git log --oneline 43f6c09..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/brain/backend/cases.py
- M  pyto/experiments/brain/backend/evidence.py
- M  pyto/experiments/brain/backend/ops.py
- M  pyto/experiments/brain/backend/summary.py
- M  pyto/experiments/brain/backend/test_evidence.py
- M  pyto/experiments/brain/backend/test_ops.py
- A  pyto/experiments/brain/records/brain_backend_correlate.json
- A  pyto/experiments/brain/records/brain_backend_diff.json
- A  pyto/experiments/brain/records/brain_backend_gradient.json
- A  pyto/experiments/brain/records/brain_backend_matrix_rank.json
- A  pyto/experiments/brain/records/brain_backend_outer.json
- A  pyto/experiments/brain/records/brain_backend_pinv.json
- M  pyto/experiments/brain/store/backend.json

```
pyto/experiments/brain/backend/cases.py            |   52 +-
 pyto/experiments/brain/backend/evidence.py         |    6 +-
 pyto/experiments/brain/backend/ops.py              |  203 +-
 pyto/experiments/brain/backend/summary.py          |   11 +-
 pyto/experiments/brain/backend/test_evidence.py    |    3 +-
 pyto/experiments/brain/backend/test_ops.py         |   66 +-
 .../brain/records/brain_backend_correlate.json     |  730 +++
 .../brain/records/brain_backend_diff.json          |  355 ++
 .../brain/records/brain_backend_gradient.json      |  358 ++
 .../brain/records/brain_backend_matrix_rank.json   |  257 +
 .../brain/records/brain_backend_outer.json         |  262 +
 .../brain/records/brain_backend_pinv.json          |  452 ++
 pyto/experiments/brain/store/backend.json          | 6697 +++++++++++++++++---
 13 files changed, 8698 insertions(+), 754 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.IRoxcfSl7z) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               728  OK
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

{?} both runs are in the packet: the copy's venv (python 3.11, numpy 2.4.6) through the Verify
line, and python 3.12.3 with numpy 2.5.3 and scipy 1.18.1 at
experiments/tasks/103/evidence/verify-python312-numpy253.txt. 728 tests, OK in both.
{?} a case may now carry `engines=("np", "sp")`. It is not a way to excuse a disagreement - every
engine a case names must still match the reference - it is how a case one engine refuses BY DESIGN
stays in the table instead of being quietly deleted from it. Two cases use it today
(matrix_rank/deficient_6x4 and pinv/deficient_6x4) and the map says why.
{?} the py engine of matrix_rank refuses a band rather than answering in it: between numpy's rank
tolerance (max(m,n) * eps * sigma_max) and its own svd's error floor (about sqrt(eps) * sigma_max),
a singular value is genuinely ambiguous to an engine that went through a^T a. The floor constant is
sqrt of the float64 epsilon, written as a literal; a one-sided jacobi svd would remove the whole
question and is in the map's next list.
{?} the py engine of pinv is r^-1 q^T from the reduced qr, so it is a left inverse of a
full-column-rank matrix and nothing else. It refuses the rest by name; np and sp answer.
{?} correlate's sp engine is pinned to scipy.signal.correlate(method="direct") so all three engines
do the same arithmetic; an fft-based correlate is a different backend with a different tolerance.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 103 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 103`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-103): brain/backend six more primitives and the case table learns which engines answer: matrix_rank, pinv, correlate, diff, gradient and outer, each with its oracle Part per engine and benchmark Parts at three sizes; and the py engine of matrix_rank refuses the band its own svd cannot resolve - taking square roots of the eigenvalues of a-transpose-a squares the condition number, so a truly zero singular value comes back near sqrt of eps and numpy's rank tolerance sits far below anything that engine can see - which is why a case may now name the engines that answer it instead of being deleted from the table`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
