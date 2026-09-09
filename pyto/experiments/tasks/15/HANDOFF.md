# Task 15: proof.sh gives each run its own output dir: the board's pyto-hit path is substituted like the clone path, so a second proof on one machine cannot trip over the first

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging.git DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/15
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/15:pyto/experiments/tasks/15/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 3b6c3ae origin/exp/15 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

proof.sh gives each run its own output dir: the board's pyto-hit path is substituted like the clone path, so a second proof on one machine cannot trip over the first

## Starting point

3b6c3ae047eaea552c2cd109ce5931c061b8cf34 (proof: fresh clone on D:/ after tasks 12, 13, 14 (receipt under pyto/experiments/proofs)). MAIN may have moved since: `git log --oneline 3b6c3ae..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/scripts/proof.sh

```
pyto/scripts/proof.sh | 10 +++++++++-
 1 file changed, 9 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `bash pyto/scripts/proof.sh --selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         144  OK
    experiments/grouped-ablation    240  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           87  OK
    viewer-record-schema             19  OK
    
    ALL SUITES PASSED

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 15 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 15`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-15): proof.sh gives each run its own output dir: the board's pyto-hit path is substituted like the clone path, so a second proof on one machine cannot trip over the first`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
