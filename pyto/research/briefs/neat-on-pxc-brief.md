# neat and tidy on PxC: a state memory for work items and git

Version 1, 2026-09-09. Written for the owner's neat expert. It is standalone: everything it cites is
in `samuelpmahan/DiscStudio-staging` (branch `claude/python-ultracode-supercharge-st8hnu`) or in the
neat and tidy repositories the expert already owns. It is a brief to execute, refine, or reject; the
open decisions are `{?}` entries at the end and belong to the owner.

## Owner intent, in the owner's words

- neat expanded, using its own PxC as a state memory of the issue tracker, so it can instantly
  resolve changes.
- The computer manages git. Make it deterministic. No branch sprawl: one tree, plus tidy and neat.
- Each imported external application gets its own namespace (neat, tidy). No registrations.
- `{?} Label: description` is where an agent records "I was confused here"; it is the root of the
  address tree. See `pyto/questions.md`.

## What exists (read before designing)

**neat**, reference copy at `pyto/reference/neat-delivery-src/` (11 TypeScript files, the
`neat-delivery-wip` tree; not vendored: the frozen v4 payload and its manifest, so the
self-bootstrap evidence is reported, not reproducible here).

- `pxc.ts`: a persistent PxC. Every operation returns a new value; `registerCalculation` throws on
  any re-registration; telemetry is a total order of read, write and invocation events with
  sequence numbers, failed reads recorded before the error is thrown, and the error carries the
  PxC that already contains the failed read. This is the strongest telemetry model of any runtime
  in the family and is the reference for pyto's Day 2 receipts.
- `pql.ts`: `PqlProgram {PrincipleComponentRender, Ticks:[{name, Calculations:[{call, with, args,
  into}]}]}`, executed by `runPql` in declared order; first failure stops the run and returns
  status `failed` with the partial PxC and telemetry.
- `pcr.ts`: `Pcr` is a declaration of expected Tick ids plus a run result; `composePcr` rejects a
  run whose Tick ids are missing, extra or reordered, and its testimony is execution evidence,
  "intentionally not an acceptance claim".
- `work-items.ts`: the contracts. `WorkTarget {kind: calculation | tick | pcr, identity: fn.* |
  tick.* | pcr.*}`; `Checkpoint {commit, observationRef, verificationRefs, executionRefs,
  inspectionRefs}`; `AcceptanceReference {human, subjectCommit, requirementScope, disposition}`;
  `PromotionReference {subjectCommit, source}`; `Dependency {item, requires: verified | accepted |
  promoted}`. Declared intent is kept separate from facts produced by execution or a human.
- `board.ts`: a three-Tick PQL program (Assess, Dependencies, View) over seed Parts
  `px.neat.items` and `px.neat.facts`, composed into `pcr.neat.board`. Its calculations never use
  the context (the adapter throws on read, write, invoke).
- `delivery-spine.ts` and `delivery.ts`: the five-Tick spine (Freeze, Offer, Inspect, Consume,
  Disposition) as pure views over one context Part; the actual freeze (payload inventory with
  per-file sha256, `payloadDigest`, `deliveryDigest`), the stage table, mailbox obligations,
  immutable receipt writes (`wx`, identical re-write tolerated) and the state lock live in
  `delivery.ts` and are invoked by `cli.ts`, not through PQL. neat's own START-HERE says so.

**tidy**, scout at `pyto/research/tidy-delivery-freeze.md`. A working-tree lineage guard: `check`
validates `.tidy/manifest.json`; `promote TYPE EXPERIMENT PATH` copies one file from the
experiment directory to `clean` and runs the configured tests; `up -v` records a version. It
inspects no git state at all: no base SHA, no status, no untracked enumeration, no diff, no rename
or deletion record, no content hashes, no freeze inventory, no `.neat` awareness. Every one of
those is an observed gap in the scout's table.

**pyto**, what it offers neat: the LAB Tick receipt in `PcrRun.receipts` (`pyto/src/pyto/pcr.py`,
`observe=True`), the shared run record `pyto/viewer/RECORD.md` (`pyto-run-record@1`) that the PCR
render will display for any runtime, the transfer ledger `pyto/research/lab-transfer-ledger.md`,
and the `{?}` root.

## Goal

Give neat a PxC that is the memory of the work (issue tracker items, checkpoints, acceptances,
promotions) and of the tree (git state), so that a change, whether a new commit, a working-tree
edit, or a tracker update, resolves deterministically against that memory: which items it
affects, which checkpoints it makes stale, which obligations it satisfies, what the next action
is. Every resolution is a PQL run with telemetry, and the same inputs give the same outputs and
the same receipts, byte for byte.

## Addressing (provisional until the owner's round five)

Namespace is the first segment and is the domain that owns the meaning. No registration.

```
neat.items.<id>            a work item mirrored from the tracker, with its source reference
neat.facts.<id>            facts produced by execution or a human: checkpoints, acceptances, promotions
neat.board.<view>          the resolved board (per item: affected, stale, satisfied, next)
neat.delivery.<id>.*       delivery context, phases, receipts (today px.neat.delivery.*)
tidy.git.head              HEAD sha
tidy.git.base              the base sha a checkpoint or freeze was taken against
tidy.git.status.<path>     tracked | modified | untracked | deleted, per path
tidy.git.diff.<path>       summary of the change per path (hunks, or a content hash pair)
tidy.freeze.<id>.*         inventory with per-path sha256, payload and delivery digests
proposal.neat.<id>.*       suggested next actions, never facts; a person promotes them
run.neat.<pcr>.<id>        run records, exported as pyto-run-record@1
?.<Label>                  questions for the owner
```

Today neat writes `px.neat.*`. Under the scheme `px` is pixel material and neat is its own
namespace; `{?} AddressMigration` covers the rename.

## Deliverables

**A. Ingest (Logstash).** Calculations that read the issue tracker and git and write Parts, each
with receipts. `fn.neat.ingest.items` takes a tracker export (JSON from the connector the owner
uses; Linear is connected in this session, JIRA-shaped exports are the same idea) and writes
`neat.items.<id>` with the item's identity, status, targets (`fn.*`, `tick.*`, `pcr.*`),
dependencies and the source reference (URL and updated-at). `fn.tidy.ingest.git` runs
`git rev-parse HEAD`, `git status --porcelain`, and per-path content hashes deterministically
(sorted paths, no timestamps) and writes `tidy.git.*`. Both are pure over their inputs: the shell
output is captured into a Part first, and the Calculation reads that Part, so a replay from the
retained Part reproduces the same writes without a shell.

**B. Resolve (the board).** One PQL program with Ticks Ingest, Resolve, View. Resolve computes,
per item: `affected` (a target identity appears among the addresses or `fn.*` names touched by
the change, from receipts when the change has a run record, from the diff's file paths otherwise),
`stale` (a checkpoint whose `subjectCommit` is not an ancestor of HEAD, or whose observed paths
changed), `satisfied` (mailbox obligations whose receipts exist and match the delivery digest),
and `next` (one proposed action written to `proposal.neat.<id>.next`, never into the item). View
writes `neat.board.markdown` and `neat.board.json`. Determinism: two runs over the same Parts
produce identical Parts and identical telemetry minus timestamps; assert it.

**C. Freeze inventory for tidy.** Close the scout's gaps without changing tidy's stance (git owns
history): `fn.tidy.freeze` writes `tidy.freeze.<id>.inventory` with base sha, every tracked and
untracked path, per-path sha256, deletions and renames (from `git diff --name-status` against the
base), binary paths marked, and the two digests computed the way `delivery.ts` computes them. A
freeze is a Part, immutable once written (same `wx` rule as receipts).

**D. Export.** Every run of the board or the spine writes a `pyto-run-record@1` document under
`run.neat.*` and to disk, so the PCR render in this repository (`pyto/viewer/`, Day 3) shows
neat's Ticks, reads, writes and values with no neat-specific code. The adapter for neat's
telemetry is the one thing the expert may need to add to the viewer; the ChessLab and Wumpus
adapters are the pattern.

**E. One tree, no branch sprawl.** Document and test the working rule: work happens on one tree;
a checkpoint is a `neat.facts` Part naming the subject commit; a delivery is a freeze, not a
branch; promotion is tidy's single-file copy plus tests, recorded as a `PromotionReference`. If
a step genuinely needs a branch, that is a `{?}` for the owner, not a default.

## Hard rules

- neat's semantics are the reference for neat: persistent PxC, total-order telemetry, failed runs
  return a result. Do not weaken them to match pyto.
- Declared intent and produced facts stay separate (`work-items.ts` header). Proposals never
  write into item or fact addresses.
- No registration of namespaces. An unknown namespace becomes `?.UnknownNamespace.<name>`.
- Retained data never contains code. Shell output is captured into Parts before any Calculation
  reads it.
- Every number a person will read comes from a Part or a receipt, not prose.

## Acceptance

- Two consecutive board runs over identical inputs: identical Parts and identical telemetry
  minus timestamps.
- A synthetic change (one modified path that a work item targets) flips exactly that item to
  `affected` and marks exactly the checkpoints whose subject commit predates it as `stale`.
- A replay from retained `tidy.git.*` Parts, with no shell available, reproduces the board.
- A freeze inventory verifies against the working tree it froze and fails against a tree with one
  byte changed.
- The exported run record opens in the PCR render and shows the three Ticks.

## What to hand back

The commit range, the test output, one exported run record, one freeze inventory, the board
Markdown for a real set of items, and the `{?}` entries below with any the expert adds.

## {?} for the owner

- `{?} AddressMigration`: rename `px.neat.*` to `neat.*` now, or only for new material?
- `{?} TrackerSource`: which tracker and which fields are authoritative for `neat.items` (Linear is
  connected here; the owner said JIRA)?
- `{?} AffectedRule`: is "affected" decided by receipts (exact) or by file paths (approximate) when
  a change has no run record? The brief proposes both, receipts winning when present.
- `{?} FreezeScope`: does a freeze include untracked files by default?
- `{?} ProposalPromotion`: which command promotes a `proposal.neat.*.next` into an action, and does
  it require a human every time?
