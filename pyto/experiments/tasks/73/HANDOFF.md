# Task 73: the Tick is the thing a person compares: px tick <record> [<name>] prints one Tick's projection of the record in the LAB's receipt shape (consumes, produces, writes with their kinds, frozen Calculations with source digests, latency, mode), byte-stable; px diff compares Tick by Tick before invocation by invocation and says which Ticks differ and in what; the viewer's Tick card shows the same four facts at the top of each Tick; derived from the record, no kernel change, no record change

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
git fetch origin exp/73
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/73:pyto/experiments/tasks/73/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 301495f origin/exp/73 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the Tick is the thing a person compares: px tick <record> [<name>] prints one Tick's projection of the record in the LAB's receipt shape (consumes, produces, writes with their kinds, frozen Calculations with source digests, latency, mode), byte-stable; px diff compares Tick by Tick before invocation by invocation and says which Ticks differ and in what; the viewer's Tick card shows the same four facts at the top of each Tick; derived from the record, no kernel change, no record change

## Starting point

d4a44b9d1c315a9cfdca66f9c8ed3917e77f5594 (land(task-72): what the ChainSpot LAB says a Tick is: pyto/research/chainspot-stages-ticks.md records, with sha:path:line evidence from the lab tips, how Stages S0 to S3 are composed of Ticks in YAML (Mermaid compiled to it, Python mirroring it), that a Tick is a chain of dependent Calculations whose results become inspectable together, that dependencies cross Tick boundaries by Part, that the gateway publishes one Receipt per Tick with no rollback and no parallelism, what compare.ts and the neon sheet compare Tick by Tick, and that tidy's manifest is tidy.manifest.yaml naming S0 to S3 with version, clean and hash, which corrects the tidy scout's .tidy/manifest.json). MAIN may have moved since: `git log --oneline 301495f..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/src/pyto/px.py
- M  pyto/tests/fixtures/px/diff-students-flipped.txt
- M  pyto/tests/fixtures/px/diff-students-students.txt
- A  pyto/tests/fixtures/px/tick-parallel-demo.txt
- A  pyto/tests/fixtures/px/tick-students.txt
- M  pyto/tests/test_px.py
- M  pyto/viewer/adapters.js
- M  pyto/viewer/test/students-card-tree.golden.txt
- A  pyto/viewer/test/tick-projection.test.mjs
- M  pyto/viewer/tick-viewer.js

```
pyto/src/pyto/px.py                               | 252 ++++++++++++++++++++--
 pyto/tests/fixtures/px/diff-students-flipped.txt  |   5 +
 pyto/tests/fixtures/px/diff-students-students.txt |   5 +
 pyto/tests/fixtures/px/tick-parallel-demo.txt     |  20 ++
 pyto/tests/fixtures/px/tick-students.txt          |  27 +++
 pyto/tests/test_px.py                             | 149 ++++++++++++-
 pyto/viewer/adapters.js                           | 103 +++++++++
 pyto/viewer/test/students-card-tree.golden.txt    |  36 ++++
 pyto/viewer/test/tick-projection.test.mjs         | 118 ++++++++++
 pyto/viewer/tick-viewer.js                        |  37 +++-
 10 files changed, 733 insertions(+), 19 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_px && python -m unittest discover -s viewer/test -p 'test_*.py' && node --test viewer/test/*.test.mjs` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.FRzHBK5w8P) (evidence/check_all.txt)
    suite                         tests  status
    library                         379  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} InternalWording: I named the packet's "MINUS addresses produced inside the Tick" set `internal` (packet's own parenthetical: "those are internal to the chain") -- the field name, the CLI label, and the JSON key all read `internal`. If the owner would rather `chain`, `links`, or something else, it is one rename in `tick_projection` (px.py), `tickProjection` (adapters.js) and their tests/fixtures.

{?} WriteKindInConsumes: `produces` carries each write's kind (RECORD.md `writes[].kind`, one of new-address/refinement/replacement); `consumes` and `internal` carry bare addresses only, no kind, because a *read* has no write kind of its own to report -- the kind describes what happened when the address was written, elsewhere in the same or an earlier Tick. If the owner wants each `consumes`/`internal` entry annotated with the kind under which it was originally produced, that is an additional lookup (which invocation, anywhere in the record, first wrote this address) rather than a Tick-local one.

{?} ProduceDigestIsInvocationLevel: RECORD.md carries one `result_sha256` per invocation and no per-produce digest (`{?} RecordProduceDigest`, already on the record). `tick_projection`'s `produces` therefore gives every write of a multi-produce invocation the *same* digest -- its one `result_sha256` -- rather than a digest specific to that one address. This is exercised by neither fixture (students and grouped-ablation are one-address invocations throughout); if RECORD.md ever grows a `produce_sha256` per address (as the Receipt already carries, "Receipts as Parts"), `tick_projection` should prefer it there.

{?} DiffModeLatencyExcluded: `px diff`'s Tick section compares only consumes/internal/produces/calculations, per the packet; a Tick whose `latency_ms` or run-level `parallel` mode changed between two records (same computation, different schedule) reads `same`. This mirrors the existing invocation-level rule ("Two records that differ only in how long they took are not different") but is worth confirming, since RECORD.md frames `parallel`/`latency_ms` as schedule rather than program on purpose.

{?} FnReadFallbackDivergence: `tick_projection`'s consumes/internal reuse `tick_laws._reads`/`_writes` verbatim, as asked. That function's handling of a produce-qualified `fn:<id>#<address>` binding whose `id` is *not* in this record's `into_by_id` differs from `adapters.js` `parseBinding` (tick_laws still adds the bare address; parseBinding adds nothing) -- a pre-existing divergence between the two shared readers, not something this task introduced, and not exercised by either fixture (neither uses multi-produce).

{?} LatencyRoundingDivergence: the two *shared* Tick-latency fallbacks already disagreed before this task -- `viewer/test/record_schema.py` `tick_latency_ms` sums raw durations; `adapters.js` `tickLatencyMsFromRecord` rounds that sum to 3 decimals -- but nothing had compared them on the no-explicit-`latency_ms` path until `viewer/test/tick-projection.test.mjs` did, for the students record. The new test tolerates it by rounding both sides to 3 decimals before comparing `latency_ms`, rather than changing either shared reader. Flagging in case the owner wants the two harmonized instead.

{?} RegeneratedGolden: `viewer/test/students-card-tree.golden.txt` (task 40's committed tree) is regenerated, not kept green -- adding the facts block to every Tick card necessarily changes it. Regenerated with a small throwaway script using the same `serialize`/`createStubDocument` shim `effects-view.test.mjs` defines inline; the diff is four new lines (`dl.tick-facts` and its eight `dt`/`dd` children) per Tick, nothing else moved.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 73 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 73`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-73): the Tick is the thing a person compares: px tick <record> [<name>] prints one Tick's projection of the record in the LAB's receipt shape (consumes, produces, writes with their kinds, frozen Calculations with source digests, latency, mode), byte-stable; px diff compares Tick by Tick before invocation by invocation and says which Ticks differ and in what; the viewer's Tick card shows the same four facts at the top of each Tick; derived from the record, no kernel change, no record change`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
