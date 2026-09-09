# Task 9: Add a fast, isolated check that land.sh's early refusal paths (bad package name, unknown branch, dirty file outside allowed paths) exit 1 and write a failed/*.json receipt without ever reaching check_all.sh, so the refusal contract is verified in under a second instead of only by hand-run scratch clones.

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/9
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/9:pyto/experiments/tasks/9/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 1b38f28 origin/exp/9 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

Add a fast, isolated check that land.sh's early refusal paths (bad package name, unknown branch, dirty file outside allowed paths) exit 1 and write a failed/*.json receipt without ever reaching check_all.sh, so the refusal contract is verified in under a second instead of only by hand-run scratch clones.

## Starting point

1b38f283e1e12d29a6fa73077c14c2d749c3fba8 (land(windows-venv): the scripts find the repository's .venv on their own, so isolated child processes import pyto on Windows too; the D:/ commands make that venv). MAIN may have moved since: `git log --oneline 1b38f28..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/scripts/check_land_refusals.sh

```
pyto/scripts/check_land_refusals.sh | 100 ++++++++++++++++++++++++++++++++++++
 1 file changed, 100 insertions(+)
```

## Evidence

- verify: `bash pyto/scripts/check_land_refusals.sh   # builds a throwaway git repo under mktemp, calls land.sh with no args (expect exit 2), then with a dirty file outside --allow (expect exit 1 and a new pyto/experiments/landings/failed/*.json), asserts the working tree it started from is untouched; no check_all.sh, no network, sub-second` exit 0 (evidence/verify.txt)
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

- {?} BadPackageName: the intent named "bad package name" as one of the three refusal paths, but land.sh has no format check on the package string at all -- only a missing-package check ("usage: land.sh ...", exit 2, no receipt, since it never reaches fail()). I tested that no-argument case instead and treated it as the intended meaning; if the owner meant something else by "bad", nothing here catches it.
- {?} BoardRewriteReset: every refusal calls board(), which rewrites the tracked pyto/BOARD.md in place before the receipt is written; the check resets BOARD.md with `git checkout` between refusals so the next one's scope check only sees the file that test introduces as dirty. That reset is standing in for "someone lands after a refusal, wiping its own board line" -- true in the real repo too, just not usually noticed inside one script's runtime.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 9 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 9`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-9): Add a fast, isolated check that land.sh's early refusal paths (bad package name, unknown branch, dirty file outside allowed paths) exit 1 and write a failed/*.json receipt without ever reaching check_all.sh, so the refusal contract is verified in under a second instead of only by hand-run scratch clones.`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
