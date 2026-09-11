# Task 133: vertical content: a 1080x1920 portrait canvas beside the 1920x1080 one, composed by the same fn.comparison.layout, plus a reusable frame preset (fill, safe area, title strip, sponsor lockup on the cards cascade's global tokens) materialized by the same fn.overlay.svg, and exports that honour the orientation

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
git fetch origin exp/133
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/133:pyto/experiments/tasks/133/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 2487b37 origin/exp/133 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

vertical content: a 1080x1920 portrait canvas beside the 1920x1080 one, composed by the same fn.comparison.layout, plus a reusable frame preset (fill, safe area, title strip, sponsor lockup on the cards cascade's global tokens) materialized by the same fn.overlay.svg, and exports that honour the orientation

## Starting point

2487b379d17d28f07207414f51bdbe976958d8e1 (land(task-131): art assignment as a Calculation over the set, not a hash per item: fn.art.assign spreads first (a golden-ratio walk over the painter's families, every family used before any repeats) then groups (after coverage a disc takes the family of the disc it resembles, by mold), stable in the order the shelf holds its discs; px.art.assignment is a Part the card chain binds, an authored family still wins; four oracles as tests: coverage, spread, grouping, stability; the seed's twelve discs are assigned by it instead of by index). MAIN may have moved since: `git log --oneline 2487b37..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  scripts/browser_test.py
- M  src/app.js
- M  src/domain.js
- A  src/frames.js
- M  src/media.js
- M  src/presentation.js
- M  src/runtime.js
- M  src/seed.js
- M  src/style.css
- M  tests/core.test.js
- M  tests/fixtures/serial-run-record.json

```
scripts/browser_test.py               |  39 +++++++
 src/app.js                            |  39 +++++--
 src/domain.js                         |  13 ++-
 src/frames.js                         |  97 ++++++++++++++++++
 src/media.js                          |   7 +-
 src/presentation.js                   |  77 ++++++++++----
 src/runtime.js                        |  15 ++-
 src/seed.js                           |   2 +-
 src/style.css                         |   2 +-
 tests/core.test.js                    |  47 ++++++++-
 tests/fixtures/serial-run-record.json | 185 ++++++++++++++++++++++++++++------
 11 files changed, 448 insertions(+), 75 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.xhi4yFgnlv) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               756  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} FrameIsPartOfTheLayout: the frame is a Part (`px.overlay.frame`) that `fn.comparison.layout` reads
and `fn.overlay.svg` draws, which means the canvas size lives in two places at once -- the layout's
`orientation` field and the frame Calculation's output. It works because the frame is composed first
and everything downstream takes its size from the frame's canvas, but a Part that is half layout input
and half drawing is a shape the kernel has no word for. A `Canvas` first-class Part that both read
would say it better.

{?} SponsorIsGlobalOnly: the frame's sponsor lockup reads `px.discstudio.cards.global.sponsor` and not
the effective cascade for the comparison's preset, so the broadcast preset's own `sponsor: 'CHAINSPOT'`
override shows on the cards but not in the frame's lockup until the global token is set. That is what
"drawing on the cards cascade's global tokens" says, and it is also the thing a person will ask about
first. The alternative -- a fourth cascade layer for the overlay itself -- is a bigger change than this
slice.

{?} FixtureIsByteForByte: `tests/fixtures/serial-run-record.json` is compared byte for byte, so every
task that adds one Tick to the comparison regenerates a 220 KB fixture. Two writers touching the
comparison in the same sprint conflict on that file and on nothing else. A fixture that asserted the
Tick names and the counters rather than every value would take the same kill and never conflict.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 133 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 133`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-133): vertical content: a 1080x1920 portrait canvas beside the 1920x1080 one, composed by the same fn.comparison.layout, plus a reusable frame preset (fill, safe area, title strip, sponsor lockup on the cards cascade's global tokens) materialized by the same fn.overlay.svg, and exports that honour the orientation`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
