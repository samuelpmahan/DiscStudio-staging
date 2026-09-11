# Task 81: brain harness: experiments/brain shared harness (store over pxc, dataset/synthetic, oracle, bench, bracket/judge/decide, finding, map_part, navigate through pql), map module, backend package, brain extra in pyproject and neat copy-venv install of [drawing,brain]

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
git fetch origin exp/81
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/81:pyto/experiments/tasks/81/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 5de2067 origin/exp/81 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain harness: experiments/brain shared harness (store over pxc, dataset/synthetic, oracle, bench, bracket/judge/decide, finding, map_part, navigate through pql), map module, backend package, brain extra in pyproject and neat copy-venv install of [drawing,brain]

## Starting point

077d3475e36922d52ab6bc437883dd9b634a75e5 (land(task-80): neat delta <a> <b>: the capability delta against cost of two landings, computed not noted: from each landing's receipt and git diff, capability gained (Calculations registered, user actions and controls added, behaviours verified) and cost (files, lines, new pages, new address roots, moved assertions, regenerated fixtures) per candidate, fn.neat.delta.evaluate pure over the two measurements, the Part px.exp.neat.delta.<a>.<b> under pyto/experiments/review/deltas, patterns per repository in a manifest; first record: 78 (a second page over the composer) against 79 (the composer refined)). MAIN may have moved since: `git log --oneline 5de2067..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/brain/CONTRACT.md
- A  pyto/experiments/brain/__init__.py
- A  pyto/experiments/brain/backend/__init__.py
- A  pyto/experiments/brain/example.py
- A  pyto/experiments/brain/harness.py
- A  pyto/experiments/brain/map.py
- A  pyto/experiments/brain/records/brain_example.json
- A  pyto/experiments/brain/store/backend.json
- A  pyto/experiments/brain/test_harness.py
- M  pyto/pyproject.toml
- M  pyto/scripts/neat.sh

```
pyto/experiments/brain/CONTRACT.md                | 122 ++++
 pyto/experiments/brain/__init__.py                |   6 +
 pyto/experiments/brain/backend/__init__.py        |   7 +
 pyto/experiments/brain/example.py                 | 125 ++++
 pyto/experiments/brain/harness.py                 | 724 ++++++++++++++++++++++
 pyto/experiments/brain/map.py                     |  19 +
 pyto/experiments/brain/records/brain_example.json | 119 ++++
 pyto/experiments/brain/store/backend.json         | 252 ++++++++
 pyto/experiments/brain/test_harness.py            | 340 ++++++++++
 pyto/pyproject.toml                               |   3 +
 pyto/scripts/neat.sh                              |   2 +-
 11 files changed, 1718 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.zcMQ5rbgXn) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain                48  OK
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

{?} dataset/synthetic arity: CONTRACT.md lists `dataset(name, for_, columns, rows)` and
`synthetic(name, for_, seed, shape, kind)` without a store, while oracle/bench/bracket/finding/map_part
all take the store first. harness.py takes the store first for all of them and also binds every helper
as a `Store` method, so both spellings read: `harness.dataset(store, name, ...)` and `store.dataset(name, ...)`.
{?} store/<vertical>.json scope: `save(vertical)` persists the addresses THIS process wrote, merged over
whatever the file already held, rather than everything in the PxC. That is what keeps a vertical that ran
`load_store()` from writing the other verticals' parts back into its own file. It also means a part written
by another process and only read here is not re-saved.
{?} non-finite floats: a part value holding nan/inf round-trips through python's json but is not valid JSON
for a stricter reader. harness.jsonable lets it through and harness.close treats nan as matching nan; if the
sprint wants strictness, that is the line to change.
{?} the committed store/backend.json and records/brain_example.json hold wall-clock benchmark numbers, so
they differ byte for byte on every rebuild. They are receipts, not fixtures, and no test pins their contents.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 81 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 81`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-81): brain harness: experiments/brain shared harness (store over pxc, dataset/synthetic, oracle, bench, bracket/judge/decide, finding, map_part, navigate through pql), map module, backend package, brain extra in pyproject and neat copy-venv install of [drawing,brain]`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
