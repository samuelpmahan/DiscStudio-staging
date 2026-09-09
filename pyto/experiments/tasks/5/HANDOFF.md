# Task 5: Add a standalone, sub-second selftest that every committed landing receipt JSON (verified and failed) has the fields land.sh actually writes, so a schema regression in land.sh is caught without running check_all.sh or a scratch clone.

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/5
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/5:pyto/experiments/tasks/5/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 1b38f28 origin/exp/5 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

Add a standalone, sub-second selftest that every committed landing receipt JSON (verified and failed) has the fields land.sh actually writes, so a schema regression in land.sh is caught without running check_all.sh or a scratch clone.

## Starting point

1b38f283e1e12d29a6fa73077c14c2d749c3fba8 (land(windows-venv): the scripts find the repository's .venv on their own, so isolated child processes import pyto on Windows too; the D:/ commands make that venv). MAIN may have moved since: `git log --oneline 1b38f28..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/scripts/check_receipts.sh

```
pyto/scripts/check_receipts.sh | 57 ++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 57 insertions(+)
```

## Evidence

- verify: `bash pyto/scripts/check_receipts.sh   # exits 0 iff every receipt.json under pyto/experiments/landings/**/*.json has the required keys for its result type and 'result' is 'verified' or 'failed'; runs in well under a second, no venv, no git network call` exit 0 (evidence/verify.txt)
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

- {?} Key presence only: check_receipts.sh checks that each required key exists, not its type or
  shape (e.g. `check_all.counts` could silently become a list instead of an object, `claimed`
  could become a string, and the check would still pass). Matched the caveman-simple / no-friction
  instruction; a stricter shape check is easy to add later if the owner wants it.
- {?} Where receipts live: it walks every `*.json` under `pyto/experiments/landings/`, trusting
  LANDING.md's word that the whole directory is receipts (one JSON per landing attempt, verified
  ones under an id folder, failed ones under `failed/`). If some other JSON ever lands there for
  an unrelated reason, this would flag it as a bad receipt.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 5 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 5`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-5): Add a standalone, sub-second selftest that every committed landing receipt JSON (verified and failed) has the fields land.sh actually writes, so a schema regression in land.sh is caught without running check_all.sh or a scratch clone.`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
