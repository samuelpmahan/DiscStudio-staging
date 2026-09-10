# Task 52: the surface a person uses: pyto/USE.md is a quickstart for PxC, Parts, Calculations, PCR and PQL that a test executes block by block and compares printed output byte for byte, so the document is true or the suite is red; the ergonomics gaps it exposes in pql.py and the top-level exports are fixed or written down; the students homework is its worked example

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
git fetch origin exp/52
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/52:pyto/experiments/tasks/52/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff b028f87 origin/exp/52 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the surface a person uses: pyto/USE.md is a quickstart for PxC, Parts, Calculations, PCR and PQL that a test executes block by block and compares printed output byte for byte, so the document is true or the suite is red; the ergonomics gaps it exposes in pql.py and the top-level exports are fixed or written down; the students homework is its worked example

## Starting point

1eb5be232b32fb7f17591b9c6546b5f79f8f9810 (board: **measured** on MAIN after `task-39` landed, by the session, not a copy:). MAIN may have moved since: `git log --oneline b028f87..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/CHANGES.md
- M  pyto/README.md
- A  pyto/USE.md
- M  pyto/src/pyto/pql.py
- A  pyto/tests/fixtures/use/order-record.json
- M  pyto/tests/test_pql.py
- A  pyto/tests/test_use.py

```
pyto/CHANGES.md                           |   1 +
 pyto/README.md                            |   3 +
 pyto/USE.md                               | 551 ++++++++++++++++++++++++++++++
 pyto/src/pyto/pql.py                      |  23 ++
 pyto/tests/fixtures/use/order-record.json | 136 ++++++++
 pyto/tests/test_pql.py                    |  37 ++
 pyto/tests/test_use.py                    | 238 +++++++++++++
 7 files changed, 989 insertions(+)
```

## Evidence

- verify: `cd pyto && python3 -m unittest tests.test_use tests.test_pql tests.test_first_class tests.test_semantics` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.ujjQNgglnQ) (evidence/check_all.txt)
    suite                         tests  status
    library                         327  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} AddressModuleNotExported: `USE.md` section 1 teaches the three roots, and the only code that
knows them lives in a module the package does not export: the block has to say
`from pyto.address import ROOTS, check` while everything else on the page comes from `from pyto
import ...`. `__init__.py` is another team's file this task may not edit. Export `ROOTS`,
`RESERVED_SECOND` and `check`, or leave the address rule a submodule import on purpose?

{?} MaterializeNotExported: same shape, and this one is on the main path -- the record is section 5
of a six-section quickstart, and reaching it reads `from pyto.materialize import run_record` and
`from pyto.px import main` after five sections of `from pyto import ...`. `run_record`,
`write_record` and the `px` entry point are the last step of every program that wants testimony;
`__init__.py` exports neither.

{?} PqlReceiptsIsNotAPQL: every other PQL constructor returns a `PQL` you can refine --
`PQL.prefix("px.").where(...)` -- but `PQL.receipts(pxc, pcr="order")` is a staticmethod that
takes the store and returns the matches, so narrowing receipts further is
`[m for m in PQL.receipts(pxc, pcr="order") if ...]` and not `.where(...)`. Split it into a
selector (`PQL.receipts_of(pcr=..., tick=...) -> PQL`) with `receipts(pxc, ...)` kept as the
one-liner, or leave the asymmetry?

{?} ReceiptConsumesHideResultReads: in `USE.md` section 3 the invocation `split` binds
`px.order.subtotal`, which `sum` published in the same run, and its receipt reports
`declared_consumes == ()` and `actual_consumes == ()` -- the read was resolved from the result,
not from the store. The run record does say so (`inputs: {"subtotal": "fn:sum"}`), and
`px.py:reads_of` unions the two sources to answer "what did this read". A reader looking at a
`Receipt` alone cannot. Is `declared_consumes` meant to be store reads only (then the page should
say it once, as it now does), or should a result read appear there as `fn:<id>`?

{?} HavenBriefSaysOneResult: `research/haven-brief.md:41-44` still defines a Calculation as taking
one mapping and returning "one result", which the kernel stopped meaning when `into=[...]` landed
({?} WhatIsATick, owner 2026-09-10). `USE.md` section 3 says one *or several* and shows both.
`research/` is outside this task's allow list, so the brief is left as it stands.

{?} UseMdFixtureRegeneration: `tests/fixtures/use/order-record.json` is the document section 5's
own block writes, and it carries `calculation.implementation_sha256` -- the digest of that block's
function bodies -- so editing the whitespace of `add_up` or `split_bill` in USE.md turns
`tests.test_use` red until the fixture is written again. That is the intended loudness, and the
regeneration is `python tests/test_use.py --write-fixture` (it cuts section 5's block at the
`# What a process that never saw the program above` comment and appends a `write_record`, so the
digests are the digests of the block as written). It lives in the test because `px` has no write
side today. Is a fixture written by a `--flag` on a test module the right home, or should the `px`
shell learn to write a record it can already read?

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 52 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 52`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-52): the surface a person uses: pyto/USE.md is a quickstart for PxC, Parts, Calculations, PCR and PQL that a test executes block by block and compares printed output byte for byte, so the document is true or the suite is red; the ergonomics gaps it exposes in pql.py and the top-level exports are fixed or written down; the students homework is its worked example`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
