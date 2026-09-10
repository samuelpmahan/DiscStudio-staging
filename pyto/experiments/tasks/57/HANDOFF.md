# Task 57: chains inside a Tick: the owner, 2026-09-10: 'Calculations inside a Tick must be independent was added as a rule, while your existing ChainSpot program deliberately chains dependent Calculations inside a Tick. Your definition was the moment that sequence becomes inspectable.' The kernel stops refusing a Calculation that binds an earlier sibling's result; inside a Tick the Calculations are a sequence in declared order and the Tick boundary is where the sequence becomes inspectable; a Tick with no sibling reads may run at once, a Tick with them runs in order even under parallel=True; two siblings producing one address is still refused; the decision goes on pyto/questions.md in the owner's words

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
git fetch origin exp/57
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/57:pyto/experiments/tasks/57/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 7a29ecf origin/exp/57 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

chains inside a Tick: the owner, 2026-09-10: 'Calculations inside a Tick must be independent was added as a rule, while your existing ChainSpot program deliberately chains dependent Calculations inside a Tick. Your definition was the moment that sequence becomes inspectable.' The kernel stops refusing a Calculation that binds an earlier sibling's result; inside a Tick the Calculations are a sequence in declared order and the Tick boundary is where the sequence becomes inspectable; a Tick with no sibling reads may run at once, a Tick with them runs in order even under parallel=True; two siblings producing one address is still refused; the decision goes on pyto/questions.md in the owner's words

## Starting point

97f318d4ddc4d9b52162e1736171de2d7caafce5 (land(task-56): the frontier says what the second wave landed: FRONTIER.md's Landed adds gains one line each for tasks 48 (the JS runtime speaks the same schedule), 49 (oc, effects with receipts), 50 (effects on the page), 51 (CI runs to completion), 52 (USE.md, executed) and 55 (green on macOS and Windows), each named by the task's own intent line, so the one file that says what got built is complete at the end of the sprint). MAIN may have moved since: `git log --oneline 7a29ecf..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/CHANGES.md
- M  pyto/USE.md
- M  pyto/experiments/grouped-ablation/evidence/disc-stats-sidecar.json
- M  pyto/experiments/grouped-ablation/evidence/lf-source-drift.log
- M  pyto/experiments/grouped-ablation/evidence/replay/forged-record-refused.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-2-regroup.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-3-reinput.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-4-from-retained.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/digest-forged.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/module-leak.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/registry-forged.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/source-sha-mismatch.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/value-forged-rows.log
- M  pyto/experiments/grouped-ablation/evidence/run-1/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/reuse-ledger.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/mutating-baseline-refused-record.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/retained-tampered.json
- M  pyto/questions.md
- M  pyto/src/pyto/pcr.py
- M  pyto/tests/test_parallel.py

```
pyto/CHANGES.md                                    |  16 +++
 pyto/USE.md                                        |  21 ++--
 .../evidence/disc-stats-sidecar.json               |   2 +-
 .../grouped-ablation/evidence/lf-source-drift.log  |   8 +-
 .../evidence/replay/forged-record-refused.log      |  18 +--
 .../replay/fresh-process-run-2-regroup.log         |  18 +--
 .../replay/fresh-process-run-3-reinput.log         |  18 +--
 .../replay/fresh-process-run-4-from-retained.log   |  18 +--
 .../evidence/replay/fresh-process.log              |  18 +--
 .../evidence/replay/refusals/digest-forged.log     |  18 +--
 .../evidence/replay/refusals/module-leak.log       |  18 +--
 .../evidence/replay/refusals/registry-forged.log   |  18 +--
 .../replay/refusals/source-sha-mismatch.log        |  18 +--
 .../evidence/replay/refusals/value-forged-rows.log |  18 +--
 .../grouped-ablation/evidence/run-1/retained.json  |   4 +-
 .../evidence/run-2-regroup/commit.txt              |   2 +-
 .../evidence/run-2-regroup/receipts.json           |  44 ++++----
 .../evidence/run-2-regroup/retained.json           |   4 +-
 .../evidence/run-2-regroup/timings.json            |   4 +-
 .../evidence/run-3-reinput/commit.txt              |   2 +-
 .../evidence/run-3-reinput/receipts.json           |  60 +++++-----
 .../evidence/run-3-reinput/retained.json           |   4 +-
 .../evidence/run-3-reinput/timings.json            |   6 +-
 .../evidence/run-4-from-retained/commit.txt        |   2 +-
 .../evidence/run-4-from-retained/receipts.json     |  56 ++++-----
 .../evidence/run-4-from-retained/retained.json     |   4 +-
 .../evidence/run-4-from-retained/timings.json      |   2 +-
 .../evidence/run-6-cached/interpretation.md        |   6 +-
 .../evidence/run-6-cached/reuse-ledger.json        |  16 +--
 .../tamper/mutating-baseline-refused-record.json   |   4 +-
 .../evidence/tamper/retained-tampered.json         |   4 +-
 pyto/questions.md                                  |  43 +++++++
 pyto/src/pyto/pcr.py                               | 125 +++++++++++++--------
 pyto/tests/test_parallel.py                        | 103 +++++++++++------
 34 files changed, 427 insertions(+), 295 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_parallel tests.test_multi_into tests.test_use` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.NS2lCgIX8q) (evidence/check_all.txt)
    suite                         tests  status
    library                         330  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} SidecarDigest: pyto/experiments/grouped-ablation/evidence/disc-stats-sidecar.json carries pcr.py's source digest and the disc-stats suite rewrites it whenever the kernel changes, so it is on this task's allow list as it was on task 39's; a kernel change that forgets it is refused at landing, which is what happened to this task's first attempt (20260910T041052Z-task-57).
{?} EvidencePinsTheKernel: the grouped-ablation evidence (retained.json, the replay logs, the cached ledger) carries pcr.py's provider digest, so a kernel change turns that suite red on MAIN even when every kernel test is green (second attempt, 20260910T041436Z-task-57). Regenerated here with the experiment's own scripts (run.py, run_regrouped.py, run_reinput.py, run_from_retained.py, run_cached.py, replay.py, all --force), as tasks 22 and 39 did; 250 tests green after. Whether evidence should pin the kernel's source at all, or only the Calculations' own, is the open question.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 57 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 57`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-57): chains inside a Tick: the owner, 2026-09-10: 'Calculations inside a Tick must be independent was added as a rule, while your existing ChainSpot program deliberately chains dependent Calculations inside a Tick. Your definition was the moment that sequence becomes inspectable.' The kernel stops refusing a Calculation that binds an earlier sibling's result; inside a Tick the Calculations are a sequence in declared order and the Tick boundary is where the sequence becomes inspectable; a Tick with no sibling reads may run at once, a Tick with them runs in order even under parallel=True; two siblings producing one address is still refused; the decision goes on pyto/questions.md in the owner's words`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
