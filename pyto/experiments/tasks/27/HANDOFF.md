# Task 27: a Calculation can produce several Parts: calc(... into=[a, b, ...]) publishes one Part per address from one invocation, the receipt lists every produce with its own digest, the record's produces and writes carry them all, and one-address calls are unchanged byte for byte

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
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/27
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/27:pyto/experiments/tasks/27/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff e2fbbd4 origin/exp/27 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

a Calculation can produce several Parts: calc(... into=[a, b, ...]) publishes one Part per address from one invocation, the receipt lists every produce with its own digest, the record's produces and writes carry them all, and one-address calls are unchanged byte for byte

## Starting point

af0e30f21c2e64cdf66a01932d6c558ab18d509f (root: multi-output Calculations decided by the owner; ResultReadsAreReads answers Codex's question from the record contract). MAIN may have moved since: `git log --oneline e2fbbd4..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/CHANGES.md
- M  pyto/experiments/grouped-ablation/evidence/disc-stats-sidecar.json
- M  pyto/experiments/grouped-ablation/evidence/lf-source-drift.log
- M  pyto/experiments/grouped-ablation/evidence/replay/forged-record-refused.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-2-regroup.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-3-reinput.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-4-from-retained.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/digest-forged.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/module-leak.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/registry-forged.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/source-sha-mismatch.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/value-forged-rows.log
- M  pyto/experiments/grouped-ablation/evidence/run-1/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-1/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/reuse-ledger.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/mutating-baseline-refused-record.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/retained-tampered.json
- M  pyto/experiments/grouped-ablation/retain.py
- M  pyto/experiments/grouped-ablation/test_retain.py
- M  pyto/src/pyto/graph.py
- M  pyto/src/pyto/materialize.py
- M  pyto/src/pyto/pcr.py
- A  pyto/tests/fixture_single_into.py
- A  pyto/tests/fixtures/single_into_pre_change.json
- M  pyto/tests/test_graph.py
- A  pyto/tests/test_multi_into.py
- M  pyto/viewer/RECORD.md
- M  pyto/viewer/adapters.js
- M  pyto/viewer/test/adapters.test.mjs
- M  pyto/viewer/test/record_schema.py
- M  pyto/viewer/test/test_record_schema.py

```
pyto/CHANGES.md                                    |  24 +
 .../evidence/disc-stats-sidecar.json               |   2 +-
 .../grouped-ablation/evidence/lf-source-drift.log  |   8 +-
 .../evidence/replay/forged-record-refused.log      |  18 +-
 .../replay/fresh-process-run-2-regroup.log         |  18 +-
 .../replay/fresh-process-run-3-reinput.log         |  18 +-
 .../replay/fresh-process-run-4-from-retained.log   |  18 +-
 .../evidence/replay/fresh-process.log              |  18 +-
 .../evidence/replay/refusals/digest-forged.log     |  18 +-
 .../evidence/replay/refusals/module-leak.log       |  18 +-
 .../evidence/replay/refusals/registry-forged.log   |  18 +-
 .../replay/refusals/source-sha-mismatch.log        |  18 +-
 .../evidence/replay/refusals/value-forged-rows.log |  18 +-
 .../grouped-ablation/evidence/run-1/commit.txt     |   2 +-
 .../grouped-ablation/evidence/run-1/receipts.json  | 105 +++-
 .../grouped-ablation/evidence/run-1/retained.json  |   4 +-
 .../evidence/run-1/saved-work.json                 |   8 +-
 .../grouped-ablation/evidence/run-1/timings.json   |   6 +-
 .../evidence/run-2-regroup/commit.txt              |   2 +-
 .../evidence/run-2-regroup/interpretation.md       |   2 +-
 .../evidence/run-2-regroup/receipts.json           |  77 ++-
 .../evidence/run-2-regroup/retained.json           |   4 +-
 .../evidence/run-2-regroup/saved-work.json         |   4 +-
 .../evidence/run-2-regroup/timings.json            |   6 +-
 .../evidence/run-3-reinput/commit.txt              |   2 +-
 .../evidence/run-3-reinput/interpretation.md       |   2 +-
 .../evidence/run-3-reinput/receipts.json           | 105 +++-
 .../evidence/run-3-reinput/retained.json           |   4 +-
 .../evidence/run-3-reinput/saved-work.json         |   4 +-
 .../evidence/run-3-reinput/timings.json            |   6 +-
 .../evidence/run-4-from-retained/commit.txt        |   2 +-
 .../evidence/run-4-from-retained/interpretation.md |   2 +-
 .../evidence/run-4-from-retained/receipts.json     |  98 +++-
 .../evidence/run-4-from-retained/retained.json     |   4 +-
 .../evidence/run-4-from-retained/saved-work.json   |   4 +-
 .../evidence/run-4-from-retained/timings.json      |   2 +-
 .../evidence/run-6-cached/interpretation.md        |   6 +-
 .../evidence/run-6-cached/reuse-ledger.json        |  16 +-
 .../tamper/mutating-baseline-refused-record.json   |   4 +-
 .../evidence/tamper/retained-tampered.json         |   4 +-
 pyto/experiments/grouped-ablation/retain.py        |  63 ++-
 pyto/experiments/grouped-ablation/test_retain.py   | 116 ++++
 pyto/src/pyto/graph.py                             |  80 ++-
 pyto/src/pyto/materialize.py                       |  66 ++-
 pyto/src/pyto/pcr.py                               | 288 +++++++++-
 pyto/tests/fixture_single_into.py                  |  73 +++
 pyto/tests/fixtures/single_into_pre_change.json    | 154 ++++++
 pyto/tests/test_graph.py                           |  47 ++
 pyto/tests/test_multi_into.py                      | 602 +++++++++++++++++++++
 pyto/viewer/RECORD.md                              |  33 +-
 pyto/viewer/adapters.js                            |  92 +++-
 pyto/viewer/test/adapters.test.mjs                 | 113 ++++
 pyto/viewer/test/record_schema.py                  |  83 ++-
 pyto/viewer/test/test_record_schema.py             | 188 ++++++-
 54 files changed, 2347 insertions(+), 350 deletions(-)
```

## Evidence

- verify: `cd pyto && python3 -m unittest tests.test_receipts tests.test_materialize tests.test_semantics tests.test_first_class` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         193  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    244  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             10  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} BindingSpelling: a produce-qualified result binding is spelled `fn:<id>#<address>` and a reader resolves it by using the whole text after `fn:` when it names an invocation in the record and otherwise splitting at the LAST `#` -- which keeps an invocation id that itself carries a `#` readable (`adapters.js uniqueId` mints `<id>#2` for foreign records) but leaves the spelling ambiguous by construction; the alternatives were a separator no id may contain, or refusing `#` in `PCR.calc` ids, and I did not want to add a refusal the owner had not asked for.
{?} ProduceDigestField: the per-produce digest is `Receipt.produce_sha256`, a `{address: sha256 or None}` mapping in declared order, beside the unchanged `result_sha256` of the whole returned value; for a one-address invocation it is `{into: result_sha256}`, which is a restatement -- a field that is only ever new information would have to be null or absent there instead.
{?} RecordProduceDigest: `produce_sha256` is on the Receipt only; the run record document gained no field, because both validators check exact key sets, so a new required key would change the bytes of every record ever written -- including `evidence/run-1/record.json`, which `viewer/fixtures/pyto-grouped-ablation.json` must be a byte copy of and which is outside this task's allowed paths. If the owner wants the digests in the record too, that is a second change and it rewrites every committed record.
{?} MultiReturnShape: a multi-produce Calculation may return EITHER a mapping keyed by the declared addresses OR a sequence in the declared order; both are accepted because both are honest spellings of "one value per address" (a mapping says which is which at the call site, a sequence is what a Python function returns when it returns two things). Picking one would be a smaller contract.
{?} MultiReturnStrict: the split is strict in both directions -- a missing address, an address nobody declared, and a sequence of the wrong length all raise, and nothing is published unless every address has its value. The forgiving reading (publish what matched, ignore the rest) was rejected because it lands a Part holding the wrong value silently.
{?} OneElementList: the SHAPE of `into` decides, not the count: `into=Part("a")` publishes the returned value at one address, `into=["a"]` is the multi-produce form and its Calculation must return a mapping or a sequence of one. So a program cannot slide between the two meanings by the length of a computed list -- at the cost that `into=[x]` and `into=x` are different declarations.
{?} BareRefInARecord: pyto refuses to WRITE a bare `fn:<id>` on an invocation that published several Parts, but a record from another runtime could carry one; both reference readers read it as a read of every Part that invocation published, rather than dropping the edge. A reader that refused it instead would make a foreign record invalid on a clause pyto's kernel already enforces.
- Decided: graph.py and retain.py read every produce address, so no reader crashes on a multi-produce invocation; two tests guard it.
{?} MultiWriteKinds: the writes happen in declared order and each `PxWrite.kind` is decided against the store as it stood at that moment, so publishing two addresses where the second already exists gives `new-address` then `replacement` from one invocation. That is what the tracked board already did per write; a per-invocation kind would have to invent a rule for the mixed case.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 27 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 27`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-27): a Calculation can produce several Parts: calc(... into=[a, b, ...]) publishes one Part per address from one invocation, the receipt lists every produce with its own digest, the record's produces and writes carry them all, and one-address calls are unchanged byte for byte`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
