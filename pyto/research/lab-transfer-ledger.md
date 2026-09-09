# LAB transfer ledger

Pyto is a Python transfer of the LAB, which is proven (if not fully implemented) across ChainSpot,
ChessLab and EmbodiedWumpusWorld. That reframes the week: the open question is not whether PxC
helps, but how faithfully and completely pyto carries the proven mechanisms, and which of them the
Python workshop needs first. Every row below cites the proven source (copied under
`pyto/reference/lab/`) and pyto's current state at a4dc559. "Absent" is a transfer gap, not a
design decision.

## Ledger

| Proven mechanism | Where it is proven | Pyto today | Transfer status |
|---|---|---|---|
| Address-keyed store with fail-loud reads; registry rejects a different callable at a known address | exec.js:12-21 (DiscStudio/ChainSpot); chesslab board.ts:48-72; wumpus pxc.js:86-107 | core.py PxC | Transferred |
| Declared consumes/produces per Tick, actual access tracked, exact-conformance failure when they differ | chesslab host.ts:20-26 (`accessConformance==='exact'`), board.ts trackAccess:84-146 | None: PCR records declared bindings only (pcr.py:144-157), no observed reads | Absent |
| Write kinds new-address / refinement / replacement, replacements never hidden as ordinary output | contract.ts PxWriteTestimony; board.ts:113-122; wumpus pxc.js:134-140 | PxWrite has new-address/replacement only (core.py:62-66) and PCR.run discards it (pcr.py:164) | Partial |
| Frozen calculations in the receipt: address + implementation hash + honest identity scope | chesslab host.ts:27-31, contract.ts FrozenCalculation | Consumers hand-roll module source hashes (app.py PYTO_SOURCE_SHA256, card_composition.py) | Absent in library; duplicated in consumers |
| Receipt per Tick: opId, duration, declared vs actual, writes, probes, artifacts | contract.ts Receipt; host.ts:32-36 | PcrRun has ticks/ids/refs/args/into and a results dict; no duration, no actual access, no artifacts | Partial |
| Transactional Tick: begin on a working copy, commit on success, rollback on throw; values captured on every get/set so a Tick cannot mutate shared state | wumpus pxc.js:113-160, execute.js:10-49 (core.api.test.js proves typed-array isolation) | None: a failing calculation leaves earlier `into` writes in the PxC (pcr.py:163-164); values are shared by reference | Absent |
| Receipt records resolved input and output values and every calculation call (address, input, output) | wumpus execute.js:23-37 | results dict holds output values by id; inputs recorded as refs only | Partial |
| Provenance trace over receipts: which receipt produced an address, from which inputs, through which calculations | wumpus provenance.js traceAddress | None; the fan-out example does a 6-line traversal by hand | Absent |
| Content-addressed material Parts: key = sha256(canonical({revision, source hash, frame, dimensions, seed, masks, knobs})); `matrix.material.<key>`; later variants reuse by `board.has`; counters requests/hits/misses/writes; pose reads cached at `matrix.material.profile.<key>` | chainspot-matrix materials.ts:263-317 (createMatrixMaterials), tests matrixMaterials.test.ts | None: PxC keys are author-chosen strings; no canonical serializer, no counters | Absent |
| Case x variant matrix with manifest hash, job keys, progress, receipts, parity report | chainspot-matrix types.ts (MatrixManifest, MatrixJob, MatrixReceipt, ParityReport), matrix.ts | None; Day 1 adds an experiment-local family() helper | Absent |
| Memoization by (revision, full input values) with a reuse trace | DiscStudio runtime.js:13-25 (application adapter, not core) | None | Absent (and not core in JS either) |
| Executable declarative document (readPql grammar) with overrides and run record published as `px.pql.<name>` | exec.js:34-66 | Pcr emits a different, non-executable document; PCR has no reader or writer | Absent |
| Shadow rejection: an arg that shadows a bound input fails loud | exec.js:45, :58 | args silently override inputs (pcr.py:159-160) | Absent (semantic difference) |
| Direct-result bindings (fn:) and multiple-writer rejection | pyto only (pcr.py:112-123) | Present | Python-only addition; JS sets `into` inside the loop instead |
| Replay: navigation changes the viewed frame, never reruns the experiment | chesslab replay.ts | None | Absent |

## What this changes in the week

The winning plan (experiment-reuse-first) stands, but each day's library seam and comparison
baseline is now a transfer of a proven mechanism rather than a new design:

- **Day 2 seam** is the LAB Tick receipt, not an invented Observation: per-invocation duration,
  actual consumes/produces observed through a tracked PxC view, write kinds including
  `refinement`, calculation calls with input/output digests, and frozen-calculation identity
  (address + implementation hash with the ChessLab honesty fields `identityScope` and
  `limitation`). It stays in a new `PcrRun.receipts` mapping so consumer testimony bytes are
  unchanged (critic gap and judge 3 finding). Reference: chesslab contract.ts Receipt,
  wumpus execute.js.
- **Day 2 retain format** must be readable by the browser `readPql` grammar wherever the program
  has no fn: bindings, and the Day 5 parity check runs the same document through node exec.js
  and Python (the reader phase's 45-line port already produced byte-identical run records for a
  two-tick document with an override).
- **Day 3 conventional comparison** gains the proven baseline: content-addressed material Parts
  as in ChainSpot matrix/materials.ts, ported experiment-locally (canonical serializer, sha256
  key, `has`-before-`call`, counters). The saved-work ledger reports hits and misses the way
  MatrixMaterialCounters does. joblib and functools.cache remain the conventional comparators.
- **Day 3 kernel ablation** adds the transactional Tick as a candidate primitive: the failing
  calculation mid-run test from Day 1 is the characterization, and the ablation asks what a
  rollback would cost.
- **Day 4 fixture** keys the shared art result by content address (request digest + painter
  source hash + pyto version) so "render-disc need not rerun" is shown by a cache hit counter as
  well as by the comparison explanation.
- **Day 5 parity** adds a cross-language check: the same PQL JSON document executed by node
  `src/core/exec.js` and by the Python reader, canonical run records compared byte for byte.
  Deviations are transfer defects and are listed as such in the returns.

## Not transferred this week, recorded as open

- `{?} TransactionalTick`: rollback semantics change what a failed run leaves in PxC; a
  behavior flip for existing consumers, so it lands only as a characterization and an ablation
  row until the owner decides.
- `{?} ShadowRule`: JS fails loud, pyto overrides silently; same authored program gives an error
  in one and a wrong value in the other. Characterized on Day 1, refused at export by retain.py,
  left unchanged in pcr.py.
- `{?} MatrixManifest`: the case x variant manifest, job keys and progress rows are a bigger
  transfer than the week needs; the experiment-local family() helper is the placeholder and its
  saved-work ledger uses the same counter names so the later transfer is mechanical.
