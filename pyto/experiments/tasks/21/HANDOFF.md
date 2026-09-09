# Task 21: The studio exports its own run record: an Export run record action produces a pyto-run-record@1 JSON for the current composition through the existing adapter, and a link opens the Tick render page with that record embedded; no new state store, no renderer fork, no field whitelist

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/21
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/21:pyto/experiments/tasks/21/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 7d2448d origin/exp/21 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

The studio exports its own run record: an Export run record action produces a pyto-run-record@1 JSON for the current composition through the existing adapter, and a link opens the Tick render page with that record embedded; no new state store, no renderer fork, no field whitelist

## Starting point

7d2448de2e38568967ca14fc8f1a722da7cd7b5d (land(task-0): Day 3 close-out: the record contract says what both runtimes do (declared_consumes, nested array cap), run_cached derives hit or miss from counters, viewer and materializer agree on every fixture). MAIN may have moved since: `git log --oneline 7d2448d..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  .neat/items/DS-STUDIO-02.json
- M  pyto/viewer/embed.mjs
- M  scripts/browser_test.py
- M  scripts/build.mjs
- M  scripts/review_checkpoint.mjs
- M  src/app.js
- M  src/review-data.js
- M  src/runtime.js
- M  tests/core.test.js

```
.neat/items/DS-STUDIO-02.json |  6 ++++
 pyto/viewer/embed.mjs         | 62 ++++++++++++++++++++++++++++++++---------
 scripts/browser_test.py       | 43 ++++++++++++++++++++++++++--
 scripts/build.mjs             |  2 +-
 scripts/review_checkpoint.mjs |  2 +-
 src/app.js                    | 45 ++++++++++++++++++++++++++++--
 src/review-data.js            |  3 +-
 src/runtime.js                | 19 ++++++++++++-
 tests/core.test.js            | 65 +++++++++++++++++++++++++++++++++++++++++++
 9 files changed, 224 insertions(+), 23 deletions(-)
```

## Evidence

- verify: `npm test && node --test pyto/viewer/test/*.test.mjs && python3 scripts/browser_test.py --embedded` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         123  OK
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

{?} RunRecordAddress: the record is kept at `px.run.<pcr>` (the reserved `run` second segment, pyto/BOARD.md:135-136), so a second export of the same composition replaces the first; if one document per execution must be retained, the address needs a run-id segment.
- Decided: scripts/review_checkpoint.mjs now expects ten browser checks (was nine); the tenth is the run-record export. Owner can undo with neat undo 21.
- Decided: scripts/build.mjs copies pyto/viewer/ into dist/ so the deployed static site loads the viewer it now imports. Owner can undo with neat undo 21.
{?} EmbeddedHarnessOrigin: tests/embedded_harness.py (outside the allowed set) mounts the app on about:blank, where no relative URL resolves and the viewer sources cannot be fetched, so scripts/browser_test.py --embedded runs the new run-record block on a real local origin (Python stdlib server) and opens the produced page over file://.
{?} ChromiumPath: scripts/browser_test.py --embedded launched /usr/bin/chromium, which does not exist in this worktree; it now prefers /opt/pw-browsers/chromium and falls back to the old path.
{?} EmbedTopLevelAwait: pyto/viewer/embed.mjs now loads node:fs/node:path/node:url behind a top-level `await import()` guarded on `process.versions.node`, so the same module imports in the browser; the CLI and buildPage/embedFile signatures are unchanged.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 21 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 21`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-21): The studio exports its own run record: an Export run record action produces a pyto-run-record@1 JSON for the current composition through the existing adapter, and a link opens the Tick render page with that record embedded; no new state store, no renderer fork, no field whitelist`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
