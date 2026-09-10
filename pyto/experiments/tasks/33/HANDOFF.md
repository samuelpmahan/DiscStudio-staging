# Task 33: neat land from a remote: neat land <id> --from <url-or-remote> <branch> fetches a branch from another repository and lands it here with the same verifier, allowed paths and receipt, so a student's desk in its own repo can be shared into a class repo with one command; selftest covers it with a second scratch repository

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
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/33
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/33:pyto/experiments/tasks/33/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 47210a7 origin/exp/33 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

neat land from a remote: neat land <id> --from <url-or-remote> <branch> fetches a branch from another repository and lands it here with the same verifier, allowed paths and receipt, so a student's desk in its own repo can be shared into a class repo with one command; selftest covers it with a second scratch repository

## Starting point

d8ccde810b9fc2f600c27795c8247c2fb956f7a1 (board: **started** `task-32`: a score in the receipt: a verifier can print one). MAIN may have moved since: `git log --oneline 47210a7..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/LANDING.md
- M  pyto/scripts/neat.sh

```
pyto/LANDING.md      |  7 +++-
 pyto/scripts/neat.sh | 95 ++++++++++++++++++++++++++++++++++++++++++++++------
 2 files changed, 91 insertions(+), 11 deletions(-)
```

## Evidence

- verify: `bash pyto/scripts/neat.sh selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         193  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    248  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             11  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} NeatFromRefName: the fetched desk lands from `refs/neat/from/<id>`, namespaced by id so it never collides with a local `exp/<id>` (task 0 here and task 0 on a desk are different tasks), and deleted on success and on refusal; a plain branch `neat-from-<id>` would be visible in `git branch` instead, at the price of showing up in every branch listing. Say the word if you want it visible.
{?} NeatFromVerify: "the same verifier" is read literally: the shared packet's Verify line is run in the class repo exactly as written. If the desk's Verify names a path only that desk has (its own test file), the verifier exits non-zero and the landing refuses with that exit code and a failed receipt, which is honest but unhelpful for a class where the teacher's tests are the real verifier. The alternative is a `--verify` override on the landing that replaces the packet's line; that means a shared desk can be graded by the class's verifier rather than its own.
{?} NeatFromId: the id on the command line names the packet path inside the incoming branch (`<tasks>/<id>/packet.md`), so a desk packed as task 3 must land here as task 3 and takes that number in the class repo. Ids are not translated. If two desks pack task 0, the second one lands only after the first has landed or been undone.
{?} NeatFromCleanup: a landing from a remote deletes nothing on the other side and nothing local: no `rm -rf EXP/<id>` (that folder here would be a different task) and no `push origin --delete exp/<id>`. The desk's branch stays until its owner removes it; unsharing here is `neat undo <id>`.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 33 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 33`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-33): neat land from a remote: neat land <id> --from <url-or-remote> <branch> fetches a branch from another repository and lands it here with the same verifier, allowed paths and receipt, so a student's desk in its own repo can be shared into a class repo with one command; selftest covers it with a second scratch repository`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
