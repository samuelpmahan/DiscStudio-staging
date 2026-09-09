# Task 12: proof: the test as one script. proof.sh clones the branch fresh into a temp dir on this drive, runs the board's commands verbatim, writes one Today line with the result and a receipt under pyto/experiments/landings/proofs/

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging.git DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/12
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/12:pyto/experiments/tasks/12/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 76bc3d2 origin/exp/12 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

proof: the test as one script. proof.sh clones the branch fresh into a temp dir on this drive, runs the board's commands verbatim, writes one Today line with the result and a receipt under pyto/experiments/landings/proofs/

## Starting point

76bc3d2a51c0e5442a0e4e8f519fe7d01484e9f5 (land(task-11): Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test). MAIN may have moved since: `git log --oneline 76bc3d2..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/scripts/proof.sh

```
pyto/scripts/proof.sh | 149 ++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 149 insertions(+)
```

## Evidence

- verify: `bash pyto/scripts/proof.sh --selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 1, last line: SOME SUITES FAILED (logs in /tmp/tmp.UuDWjgdu5g) (evidence/check_all.txt)
    suite                         tests  status
    library                         144  OK
    experiments/grouped-ablation    240  FAIL
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           87  OK
    viewer-record-schema             19  OK
    
    SOME SUITES FAILED (logs in /tmp/tmp.UuDWjgdu5g)

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} Receipt result vocabulary: proof.sh writes `"result": "green"/"red"` per the brief, but
`check_receipts.sh` walks all of `pyto/experiments/landings/` (proofs/ included) and only accepts
`"result": "verified"/"failed"` with land.sh's key set. A committed proof receipt will read as
malformed if that script is ever run over the whole tree. Default taken: keep `green`/`red` as
specified (a proof is not a landing and carries its own schema, `pyto-proof-receipt@1`) and leave
`check_receipts.sh` untouched, since widening it is outside this task's three-file, 150-line bound.
{?} `cd` tracking is best-effort: proof.sh only recognizes a bare `cd <path>` line (optionally with
a trailing `#` comment) to update the working directory carried into the next step; a `cd` folded
into a compound command (e.g. `cd x && y`) would not update the tracked cwd for later steps. The
board's current block only uses a standalone `cd` line, so this does not bite today. Default taken:
leave it, since the board's test is the only input this script parses.
{?} Step granularity: each *line* of the fenced block is treated as one step, so
`python -m venv .venv && .venv/Scripts/python -m pip install ...` is one step even though it does
two things; if the venv step fails, pip install never runs (`&&` short-circuits) and that whole
line is reported as one failing step. Default taken: line-granularity, since the board's block is
already written one logical action per line and the brief calls the block's own lines "commands."

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 12 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 12`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-12): proof: the test as one script. proof.sh clones the branch fresh into a temp dir on this drive, runs the board's commands verbatim, writes one Today line with the result and a receipt under pyto/experiments/landings/proofs/`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
