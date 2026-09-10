# Task 46: the suite is green on three OSes and two Python versions: the grouped-ablation suite fails on CI under Python 3.12 (ubuntu and windows) and the students grader fails on windows; find the cause from the CI logs and a local Python 3.10 run, fix it in the tests or the scripts without regenerating evidence, and make check_all.yml upload the per-suite logs as the receipt

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
git fetch origin exp/46
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/46:pyto/experiments/tasks/46/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff c712cf2 origin/exp/46 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the suite is green on three OSes and two Python versions: the grouped-ablation suite fails on CI under Python 3.12 (ubuntu and windows) and the students grader fails on windows; find the cause from the CI logs and a local Python 3.10 run, fix it in the tests or the scripts without regenerating evidence, and make check_all.yml upload the per-suite logs as the receipt

## Starting point

0f9f6d32e8213e9dee91f7ef54b6cc9ef6603b6c (land(task-45): KT answers: five questions from the local session (what moved registry to OS and what is unproved; which corrections overturned the most and where the old assumptions survive; glue that holds real methods; what a successor would follow and miss; when a question advanced the project) answered from the record at pyto/research/kt-answers.md). MAIN may have moved since: `git log --oneline c712cf2..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  .github/workflows/check_all.yml
- M  pyto/CHANGES.md
- M  pyto/experiments/grouped-ablation/test_replay.py
- M  pyto/experiments/students/grade.py
- M  pyto/experiments/students/homework.py
- M  pyto/experiments/students/test_students.py
- M  pyto/scripts/check_all.sh

```
.github/workflows/check_all.yml                  | 39 +++++++++++++--
 pyto/CHANGES.md                                  |  1 +
 pyto/experiments/grouped-ablation/test_replay.py | 61 +++++++++++++++++++++++-
 pyto/experiments/students/grade.py               | 19 +++++++-
 pyto/experiments/students/homework.py            |  8 +++-
 pyto/experiments/students/test_students.py       | 36 ++++++++++++++
 pyto/scripts/check_all.sh                        |  8 +++-
 7 files changed, 163 insertions(+), 9 deletions(-)
```

## Evidence

- verify: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/check_all.yml'))" && cd pyto && python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py' && cd experiments/students && python3 -m unittest discover -s . -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.EdFOAFo2cL) (evidence/check_all.txt)
    suite                         tests  status
    library                         248  OK
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

{?} NotAVersionDrift: the task and the board both start from "digests drift between Python 3.11 and 3.14", and that is not what these two suites were failing on. Both suites are green here under 3.11 (the worktree .venv), 3.12 and 3.13, byte for byte, and both CI failures reproduce with no interpreter change at all. Nothing was loosened and no pinned digest was touched, so there is no version to record in a receipt for this fix. The 3.11 ubuntu matrix entry is still added, because the drift claim itself is still unproved and now at least two versions are watched on every push.

{?} ShallowCloneSkip: `test_the_committed_stamp_names_a_commit_git_knows` now skips, rather than fails, when `git cat-file -e` cannot resolve the stamped sha AND `git rev-parse --is-shallow-repository` says the checkout is truncated. That is a real weakening of one claim in one situation, and the honest reading is "the history was not checked here". Two things hold it: the sha-shape assertion is never skipped, and `test_the_shallow_escape_hatch_is_shut_in_this_checkout` fails if the helper ever says "shallow" where git says "not shallow". The primary fix is the workflow's `fetch-depth: 0`, so CI checks the claim for real; the owner may prefer to drop the skip entirely and let a shallow clone go red.

{?} DirtyStamp: `evidence/run-1/retained.json` records `retained.commit` as `af0e30f21c2e64cdf66a01932d6c558ab18d509f-dirty`, i.e. the evidence was regenerated from a tree with uncommitted edits and the record says so. The test strips the suffix and always has. Not touched here (regenerating evidence is out of scope), but the `-dirty` says that what was measured is not exactly any commit, which is worth a decision.

{?} UnverifiedOnWindows: the `grade.py` fix is for a `ValueError` that only arises when two paths are on different Windows drive letters, which cannot happen on this Linux machine. What is verified here is the premise and the fallback: `ntpath.relpath` is asserted to raise on the exact `C:` / `D:` pair the runner produces, and `display_path` is asserted to return the absolute path when `os.path.relpath` raises. The end-to-end claim -- that the four windows tests now pass -- is inferred from the log (returncode 1 with an empty stdout, from the first line of the report) and is unproved until a windows job runs.

{?} LogsInTheWorkspace: `CHECK_ALL_LOGS` points CI at `$PWD/test-results/check-all-logs`, inside the checkout. `test-results/` is gitignored, so the suites that compare `git status --porcelain` see nothing new, but it is still the repository rather than a temp dir; `${{ runner.temp }}` was not used because its value is a backslash path that bash on windows-latest mangles.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 46 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 46`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-46): the suite is green on three OSes and two Python versions: the grouped-ablation suite fails on CI under Python 3.12 (ubuntu and windows) and the students grader fails on windows; find the cause from the CI logs and a local Python 3.10 run, fix it in the tests or the scripts without regenerating evidence, and make check_all.yml upload the per-suite logs as the receipt`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
