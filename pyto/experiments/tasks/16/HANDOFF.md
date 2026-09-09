# Task 16: watch it think: the tick page plays a record Tick by Tick with play, pause and step, each Calculation's reads, writes and value appearing when it finished, at recorded speed or slower

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging.git DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/16
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/16:pyto/experiments/tasks/16/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 12c6528 origin/exp/16 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

watch it think: the tick page plays a record Tick by Tick with play, pause and step, each Calculation's reads, writes and value appearing when it finished, at recorded speed or slower

## Starting point

12c65281bf9999f5d44ff5b1b883594ca9d5cdb0 (proof: fresh clone on D:/ after task 15). MAIN may have moved since: `git log --oneline 12c6528..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/viewer/README.md
- M  pyto/viewer/embed.mjs
- A  pyto/viewer/test/playback.test.mjs
- M  pyto/viewer/test/render.test.mjs
- M  pyto/viewer/tick-viewer.html
- M  pyto/viewer/tick-viewer.js

```
pyto/viewer/README.md              |  17 ++++-
 pyto/viewer/embed.mjs              |  18 +++--
 pyto/viewer/test/playback.test.mjs |  94 ++++++++++++++++++++++++++
 pyto/viewer/test/render.test.mjs   |  16 +++++
 pyto/viewer/tick-viewer.html       |  20 ++++++
 pyto/viewer/tick-viewer.js         | 134 ++++++++++++++++++++++++++++++++++++-
 6 files changed, 289 insertions(+), 10 deletions(-)
```

## Evidence

- verify: `node --test pyto/viewer/test/*.test.mjs` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         144  OK
    experiments/grouped-ablation    240  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           95  OK
    viewer-record-schema             19  OK
    
    ALL SUITES PASSED

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} Default speed: the speed selector defaults to "10x slower" rather than "1x real" (a 26 ms run is over before anyone can watch it at 1x) or "100x slower" (dramatic but slow for a big record). Should the default depend on the record's total duration instead of being fixed?
{?} Now marker placement: "now" is shown only as text in the toolbar (`tick N · id`) plus the clock, not as a highlight on the Calculation's own card in the list below. Should the currently-completing card also get a visual (e.g. an outline or scroll-into-view), given the owner's "activations appearing" framing?
{?} Speed change mid-playback: changing the speed dropdown while Play is running restarts the schedule from the beginning at the new speed, rather than rescaling the remaining Calculations and continuing from where it was. Is restarting the right call, or should progress be preserved?
{?} `?play=1` / `--play` autostart: both begin playing immediately (not just switch to playback mode with the page paused, empty, waiting for a press of Play). Is autostart the right default for someone opening a shared link or an `embed.mjs --play` file?
{?} Partial durations: RECORD.md allows `duration_ms: null` per invocation. A record where only some Calculations have a duration still plays in "real duration" mode, and the untimed ones complete instantly (cost 0 ms) rather than falling back to 400 ms just for themselves. Is instant-for-the-untimed-ones the right mix, or should a missing duration cost the 400 ms fallback even inside an otherwise-timed run?

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 16 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 16`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-16): watch it think: the tick page plays a record Tick by Tick with play, pause and step, each Calculation's reads, writes and value appearing when it finished, at recorded speed or slower`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
