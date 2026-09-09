# {?} The root

`{?} Label: description` is the mark an agent leaves when it is unsure and needs the owner: "I was
confused here, let me check." If the addressing were a tree, `{?}` is its root: every Part,
Calculation and decision below it exists because a question here was answered or is still open.
Agents read this file before anything else, append to it whenever they resolve something on their
own that the owner could reasonably disagree with, and never delete an entry; a resolved entry keeps
its answer, its date and who answered.

Format: `{?} Label` heading, the question, `Status: open | resolved <date> by owner | provisional`,
the answer or the current lean, and where it bites (files, days).

## Resolved by the owner this session

### {?} PrimaryUse
Is PxC first a cache, an inspection surface, or a workflow engine?
Status: resolved 2026-09-09 by owner. The main use is a cache for the CV algorithm under a 5000 ms
budget for a phone-size course screenshot; the founding need (`research/origin.md`) is seeing what
the algorithm used, per Tick. Same store, two reasons. Bites: `research/ULTRACODE-WEEK.md` Reframings
2 and 3; Day 3 materials store.

### {?} ReferenceRuntime
Is Pyto the design, or a transfer of a proven design?
Status: resolved 2026-09-09 by owner. Pyto is a Python transfer of the LAB proven in ChainSpot,
ChessLab and EmbodiedWumpusWorld; JS is first class unless it cannot meet the budget. Bites:
`research/lab-transfer-ledger.md`, Reframing 4, `viewer/RECORD.md` (JS semantics are the reference).

### {?} HitDefinition
What counts as a cache hit?
Status: resolved 2026-09-09 by owner. Any Part or Calculation being used is a hit. Do not
over-define. Bites: `viewer/RECORD.md` `hit`, Day 3 `hits.py`.

### {?} Architecture
What is the reference architecture?
Status: resolved 2026-09-09 by owner. ELK: Calculations compose meaning like Logstash, PxC stores
like Elasticsearch, and the PCR itself is Kibana (a PrincipleComponentRender is the render
definition per Tick). PQL is the query DSL and is expected to grow. Bites: Reframing 4, the viewer.

### {?} SubagentModels
Which models run subagents?
Status: resolved 2026-09-09 by owner. Opus, Sonnet or Haiku at high effort only. Bites: every
workflow after Day 1.

### {?} KeepLosers
Are tournament losers deleted, or kept?
Status: resolved 2026-09-09 by owner. Keep everything until it can be tested in the browser.
Bites: `consumers/discstudio-card/art_registry.py`, `ART-REGISTRY.md`.

### {?} TableScope
Is the store per user or shared?
Status: provisional. The owner's thesis is a per-user engram table developed with agents over time
and reusable across projects; shareability is not yet decided. Bites: Reframing 3, Day 5
cross-project hit.

### {?} FailureCriterion
What makes the week a failure?
Status: resolved 2026-09-09 by owner. The week fails if pyto's Python coverage is not seeded in a
set of interesting DiscStudio surfaces, chosen through a propose-and-refine loop (owner proposes
the final answer after five rounds). Bites: the surface list in the conversation and, once final,
Reframing 5.

### {?} GrowthStyle
Constrain possibilities, or anchor and grow?
Status: resolved 2026-09-09 by owner. Give a crystal an anchor and watch it grow. Refusal lists in
the plan mean "not this week", never design limits.

## Questions I resolved alone and should have asked (recorded late, 2026-09-09)

### {?} PlanPrimacy
Should the research docs' framing (DiscStudio stewardship) override the workload framing (CV cache)?
Status: resolved by owner after the fact. It should not have. Cost: Days 1 and 2 planned with
caching deferred.

### {?} TournamentScope
Was the art tournament on the critical path of the vision?
Status: open. It produced 16 families and 8 renderers and the owner loved it; whether it was the
best use of 2.1 million tokens is the owner's call. Bites: budget for Days 3 to 5.

### {?} StewardshipGate
The stewardship doc says no Pyto implementation starts before the owner confirms the
external-input boundary (`docs/PYTHON-LAB-STEWARDSHIP.md:56`). Day 2 landed the receipts seam
anyway, arguing it makes no boundary decision.
Status: provisional, owner to confirm. Bites: `CHANGES.md`, `{?} ExternalInputBoundary`.

## Questions I resolved alone in Day 2's third fixer round (2026-09-09)

### {?} EvidenceDirtiness
evidence trees are excluded from the `-dirty` stamp; the owner may prefer stamping
outputs too.
Status: provisional, decided by me 2026-09-09. `commit.txt` and `retained.commit` are
`git rev-parse HEAD` plus `-dirty` when watched code differs from HEAD. The watch used
to exclude only the evidence directory being written, so regenerating run-2 after run-1
saw run-1's fresh output as dirt and stamped itself `-dirty` -- the stamp stopped
distinguishing "the code was uncommitted" from "the evidence was just regenerated",
which is the only thing it exists to say. The whole `evidence/` tree is now excluded
(`run.evidence_excludes`, used by `run.py`, `second_experiment.py` and `replay.py`);
uncommitted edits to any producing source still stamp `-dirty`. The owner may prefer
the opposite reading -- a regenerated-but-uncommitted evidence tree is also a state no
commit describes -- in which case the fix is to delete `evidence_excludes` and accept a
permanent `-dirty`. Bites: `experiments/grouped-ablation/run.py:229-257`,
`second_experiment.py:184,278`, `replay.py:151`, every `evidence/*/commit.txt`.

### {?} VerificationOracleStamp
The retained-record oracle compares everything except `retained.commit`.
Status: provisional, decided by me 2026-09-09. `replay.ensure_retained_record` now
rebuilds the Day 1 record into a temp directory and compares it against the committed
`evidence/run-1/retained.json` instead of overwriting it. The comparison blanks
`retained.commit` on both sides (`replay.unstamped`), because that field is a fact
about the working tree at the moment of retaining and would otherwise turn the oracle
into a test of whether anyone has committed since. The stamp is checked separately, on
its shape and on git knowing the sha. An owner who wants the stamp inside the oracle
would have to accept that the record must be regenerated after every commit. Bites:
`experiments/grouped-ablation/replay.py:171-235`, `test_replay.py`.

### {?} InputPartsChangedScope
`input_parts_changed` counts an input Part that one run reads and the other does not.
Status: provisional, decided by me 2026-09-09. The field is now computed from the two
retained records' external digests rather than passed as a literal, over the UNION of
both records' external addresses. run-4 therefore reports both
`input.ablation.rows` (dropped: it consumes run-1's retained split instead) and
`scratch.ablation.split` (added), where the old literal named only the addition. The
owner may prefer the narrower reading -- "the input Parts of THIS run that changed" --
which would list only the addition and leave the removal to `explain_changes`. Bites:
`experiments/grouped-ablation/second_experiment.py:220-249`, every
`evidence/run-*/saved-work.json`.

## Open, from the plan and the days

### {?} ExternalInputBoundary
In the DiscStudio card path, normalized presentation is computed outside the PCR and seeded as a
Part while the stewardship spec lists it as a calculation result. Which is it?
Status: open. Bites: Day 4 fixture, `retain.py` moving toward the library.

### {?} CacheInvalidation
The content key's `revision` is a calculation identity; `implementation_sha256` excludes helpers
and assets (ChessLab's own limitation). What does a revision mean for a CV stage?
Status: open. Bites: Day 3 materials store.

### {?} CrossProjectReuse
Can a second domain get a verified hit on material the first produced?
Status: open until Day 5 runs it.

### {?} StorageKinds
Should PxC keep one facade over several specialized backends (raster, graph, JSON), chosen by
address prefix or a declared Part kind?
Status: provisional, owner leaning yes ("the precise opposite of S3"), with the anti-Spring rule: a
backend is added only when a consumer needs it, and every backend honors the same receipts.
Bites: `Part` has no kind today (`tick-observability-ledger.md` section 3, item 4); Day 3 record.

### {?} NeatOnPxC
Should neat and tidy keep work-item and git state as Parts in their own PxC, so a change resolves
against that memory deterministically, with one tree and no branch sprawl?
Status: provisional, owner intent stated 2026-09-09. Bites: a surface for the week
(`neat-delivery-wip` reference under `reference/neat-delivery-src`).

### {?} ProposalsNotFacts
Predicted transitions (a score rises, a card grows) are written to `px.proposal.*`, never to the
state addresses; a person promotes them through the reducer.
Status: provisional, proposed 2026-09-09, owner has not objected. Bites: Competition Ticks surface.

### {?} ObservationSeam
Digests and durations live in `PcrRun.receipts` rather than testimony fields, so consumer bytes
stay identical. Status: open (owner may prefer testimony-level fields).

### {?} SilentRules
Args silently override inputs; a forward ResultRef fails only at run; `Tick.calc` bypasses PCR
rules. Characterized, unchanged. Status: open (JS fails loud on the shadow case).

### {?} ShadowRule
Same authored program errors in JS and returns a wrong value in Python. Status: open.

### {?} TransactionalTick
Wumpus rolls back a failed Tick; pyto leaves earlier writes. Status: open.

### {?} KernelMerge
`Pcr` (graph) and `PCR` emit identical Mermaid; merging would give PCR an exporter. Status: open.

### {?} PromotionScope, {?} ReceiptExport, {?} ReplayIsolation, {?} SeamGate, {?} Telemetry,
### {?} LineEndings, {?} JoblibComparison, {?} DiscStatsCodec, {?} WheelVersion, {?} MatrixManifest,
### {?} ValueRetention, {?} MaterialsLocation, {?} InteriorPartVisibility, {?} AdapterHashChange
Status: open; each is described where it was raised (`research/ULTRACODE-WEEK.md`, `CHANGES.md`,
`experiments/*/questions.md`). They are listed here so the root is complete; move any the owner
answers into the resolved section with the date.
