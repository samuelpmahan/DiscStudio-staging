# Task 7: Add a fast check that every bullet under BOARD.md's '## Today' starts with the exact '- YYYY-MM-DD HH:MM ' stamp the landing script's board() function writes, so a bug in that heredoc that corrupts the owner's one-page log is caught mechanically instead of by eyeballing.

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/7
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/7:pyto/experiments/tasks/7/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 1b38f28 origin/exp/7 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

Add a fast check that every bullet under BOARD.md's '## Today' starts with the exact '- YYYY-MM-DD HH:MM ' stamp the landing script's board() function writes, so a bug in that heredoc that corrupts the owner's one-page log is caught mechanically instead of by eyeballing.

## Starting point

1b38f283e1e12d29a6fa73077c14c2d749c3fba8 (land(windows-venv): the scripts find the repository's .venv on their own, so isolated child processes import pyto on Windows too; the D:/ commands make that venv). MAIN may have moved since: `git log --oneline 1b38f28..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/scripts/check_board_log.sh

```
pyto/scripts/check_board_log.sh | 42 +++++++++++++++++++++++++++++++++++++++++
 1 file changed, 42 insertions(+)
```

## Evidence

- verify: `bash pyto/scripts/check_board_log.sh   # exits 0 iff every non-blank line under '## Today' up to the next '## ' heading in pyto/BOARD.md matches '^- [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2} '; a few grep/sed calls, well under a second` exit 0 (evidence/verify.txt)
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

- {?} ScopeOfEveryBullet: the intent says "every bullet ... starts with the exact stamp"; two committed bullets already do not (BOARD.md's "2026-09-09 Socratic session..." and "2026-09-09 all day Day 3 running..." lines, both dates with no HH:MM). Enforcing the stamp on every bullet literally would fail today, and a check that already fails on 25+ committed lines is exactly the kind of friction the owner said gets disabled. So the check only enforces the stamp on lines carrying the literal `**landed**`/`**refused**` markers, which are the only two things board()'s two call sites (land.sh:62,178) ever pass it -- every such line today already conforms, and a heredoc bug would still leave those markers in place, garbled only in the stamp, so this scoping does not hide the bug it exists to catch. Default taken: scope to board()-marked lines; the owner may prefer the stricter reading and would then need the two grandfather lines fixed or reworded by hand first (nothing here deletes or rewrites BOARD.md).

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 7 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 7`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-7): Add a fast check that every bullet under BOARD.md's '## Today' starts with the exact '- YYYY-MM-DD HH:MM ' stamp the landing script's board() function writes, so a bug in that heredoc that corrupts the owner's one-page log is caught mechanically instead of by eyeballing.`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
