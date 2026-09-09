# Task 4: Stop `neat kill` from deleting the abandoned task's branch (local and on origin); only remove the disposable worktree directory.

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/4
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/4:pyto/experiments/tasks/4/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 1b38f28 origin/exp/4 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

Stop `neat kill` from deleting the abandoned task's branch (local and on origin); only remove the disposable worktree directory.

## Starting point

1b38f283e1e12d29a6fa73077c14c2d749c3fba8 (land(windows-venv): the scripts find the repository's .venv on their own, so isolated child processes import pyto on Windows too; the D:/ commands make that venv). MAIN may have moved since: `git log --oneline 1b38f28..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/scripts/neat.sh

```
pyto/scripts/neat.sh | 6 ++----
 1 file changed, 2 insertions(+), 4 deletions(-)
```

## Evidence

- verify: `id=$(bash pyto/scripts/neat.sh new "throwaway" | sed -n 's/^Task \([0-9]*\).*/\1/p'); bash pyto/scripts/neat.sh kill "$id"; git rev-parse --verify "exp/$id" >/dev/null && [ ! -d "EXP/$id" ] && ! bash pyto/scripts/neat.sh list | awk '{print $1}' | grep -qx "$id"` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         103  OK
    experiments/grouped-ablation    230  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           83  OK
    viewer-record-schema             19  OK
    
    ALL SUITES PASSED

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
- {?} Verify field rewritten: the Verify string given at task creation was prose ("note <id> ...
  then `git rev-parse ...` should still resolve"), not executable bash, and its backticks would
  have been expanded by the shell that invoked `neat new` itself. I rewrote it to a literal
  one-line script with the same intent (make a throwaway task, kill it, check the branch survives,
  the worktree dir is gone, and it drops off `neat list`) so `neat pack` actually runs it instead
  of recording a spurious non-zero exit. Manually re-derived and re-ran before packing; owner may
  want to confirm the translation kept the intent.
- {?} Origin branch left forever: `neat kill` now leaves `exp/<id>` on origin too, unbounded, for
  every killed task from now on. That matches "nothing is deleted" and "Losers are kept" (`pyto/BOARD.md:202-203`)
  but there is no companion command to reap old killed branches later if the owner ever wants one;
  out of scope for this change (bounds: one file, one intent).

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 4 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 4`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-4): Stop `neat kill` from deleting the abandoned task's branch (local and on origin); only remove the disposable worktree directory.`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
