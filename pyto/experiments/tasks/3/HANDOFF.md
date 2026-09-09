# Task 3: neat anywhere: the same seven commands in any git repo, no pyto assumptions, with a selftest that proves new, pack, land and undo in a scratch repo in under two minutes

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/3
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/3:pyto/experiments/tasks/3/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff e072078 origin/exp/3 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

neat anywhere: the same seven commands in any git repo, no pyto assumptions, with a selftest that proves new, pack, land and undo in a scratch repo in under two minutes

## Starting point

50ec3f7b87108ebe6d9bc5f0e448bfbbc4a8dca3 (checkpoint: neat ids count origin's exp branches; board: undo tested). MAIN may have moved since: `git log --oneline e072078..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/scripts/land.sh
- M  pyto/scripts/neat.sh

```
pyto/scripts/land.sh | 108 ++++++++++++++++++++++++++++++---------
 pyto/scripts/neat.sh | 140 ++++++++++++++++++++++++++++++++++++++++++---------
 2 files changed, 200 insertions(+), 48 deletions(-)
```

## Evidence

- verify: `bash pyto/scripts/neat.sh selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         144  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    240  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                          103  OK
    viewer-record-schema             19  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
- {?} Plain-mode handoff: `neat pack` still writes a handoff with pyto-specific setup and `check_all.sh` commands; this approved selftest repair did not change that output.
- {?} Java verification: the selftest uses `Verify: true`; Java, Spring, Camunda, and test-automation commands must be supplied in a real task packet and were not run here.
- {?} Windows path form: MAIN's `hostpath` used `cygpath -m` (D:/...), this branch used `cygpath -w` (D:\...) for pip's target; the merge keeps one helper and the brief's `-w`, so MAIN's python install check now compares realpaths of the backslash form. Neither form could be exercised here (no cygpath on Linux); if the owner's D:/ run disagrees, flip the flag in `hostpath` alone.
- {?} `neat kill`: this branch deleted the abandoned branch locally and on origin, MAIN stopped deleting anything and prints the two commands instead. The two cannot both hold, so the merge keeps MAIN's (the later decision, task-4); the selftest does not cover kill either way.
- {?} Plain-mode receipt: the claimed/unclaimed split in land.sh still filters the literal `pyto/experiments/landings/` prefix, so in a plain repository a `.neat/landings/` file committed since base is recorded as claimed. Both sides had this; the merge left it untouched rather than widening the change.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 3 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 3`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-3): neat anywhere: the same seven commands in any git repo, no pyto assumptions, with a selftest that proves new, pack, land and undo in a scratch repo in under two minutes`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
