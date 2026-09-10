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

### {?} WarmupBudget
Does a storage or vision dependency's load time count against the 5000 ms budget?
Status: resolved 2026-09-09 by owner. Yes. DuckDB was tried and archived because it took 5.3 s to
warm, slower than the target; OpenCV is excluded for the same reason. A backend or library is
judged first by cold-start cost in the browser, which is why every LAB is dependency-free JS.
Bites: `{?} StorageKinds` (a specialized backend must warm inside the budget or it is not a
backend for the runtime, only for the workshop), `research/library-candidates.md`, Day 5 budget
ledger.

### {?} PerAppBudget
Is the cold-start budget global?
Status: resolved 2026-09-09 by owner. No, per application. ChainSpot needs extreme single-purpose
speed; neat can use the same runtime to render a board cheaply, but its ticket storage is a
different story: durable and larger, not budget-bound. A backend is therefore chosen per
namespace against that application's declared budget, and the choice is itself a recorded
decision. Bites: `{?} StorageKinds`, the mounts model (`lab/pxc-root-mounts`), a per-namespace
budget Part.

### {?} PortableKernel
Is this becoming a portable AI Linux?
Status: provisional, owner's framing 2026-09-09. The correspondence: PxC plus PCR and Ticks as the
kernel; namespaces as mount points; storage backends as filesystems chosen per mount; PQL as the
shell; the PCR render as the terminal; receipts as the syscall trace; the `{?}` root as the
questions a session boots on; LABs as distributions; JS and Python as two architectures the same
programs run on. What it is not: there is no scheduler and Ticks are sequential. The design rule
that follows: keep the kernel tiny and build only the two mounts that exist today (ChainSpot's fast
raster material, neat's durable tickets); let the third mount name itself.

### {?} WhoWritesJS
JS is first class, and the owner does not write TS or JS. Who writes it?
Status: resolved 2026-09-09 by owner and agent. Agents write it; the owner directs and inspects
through the PxC vocabulary, receipts, the PCR render and this root. That is how DiscStudio,
ChessLab and Wumpus were built (`research/github-growth-review.md`), and it is the reason the
human-facing surfaces (record, render, `{?}`) come before more code. Bites: every brief must be
executable cold by an agent and inspectable by a non-JS reader.

### {?} Focus
What is the focus right now?
Status: resolved 2026-09-09 by owner. "DiscStudio is the focus rn". Bites: Lane 2 first; Lane 1
addressing only as far as DiscStudio surfaces need it.

### {?} HorizonDump
Where does the owner brain-dump the horizon, and who manages the files and git?
Status: resolved 2026-09-09 by owner. "set up a local neat that allows me to brain dump the
horizon"; "I just dont want to have to slow down and debug shit"; "braindump is interactive";
"notice how the tree is designed so I dont manage even git?". So: the dump is the conversation
with the Socratic session; the owner talks, the session reads each decision back in the owner's
words, writes it here, commits and pushes. The owner opens no file and types no git command. A
horizon file in EXP/0 was made and removed for that reason. Bites: this file, `BOARD.md` lanes,
the Socratic session's write rules.

### {?} AddressRootIsAMount
Do `disc`, `chess`, `wumpus`, `neat`, `tidy` leave the address and become mounts, three roots
only (`px`, `fn`, `oc`), so `px.badges.px` means the same thing in every world?
Status: resolved 2026-09-09 by owner, by default. Owner: "MDL is good but if u need to start
with a wider footprint and refine over time thats fine the whole point is learning while moving
safely"; asked the question itself: "idk any of this". So the board's proposal is the target; a
wider footprint may ship first if it is named and can be narrowed without breaking records; the
owner is not asked addressing questions again, agents stress-test instead. A Sonnet stress test
(2026-09-09, read-only census of `pyto/`) found: no Part root is enforced today (`core.py:17-19`),
which let in bare `scratch.` (526 hits) and `input.` (113) in grouped-ablation, `material.<sha>`
in `materials.py:39,222`, and world names as second segments in two hand-written viewer
fixtures (`chesslab-s0-s1.json`, the `buzzz-mint` card); Python has no mount type at all, so
trimming addresses to bare nouns without building one makes two experiments collide; adopting
the proposal regenerates 37 retained evidence files and needs a per-version record validator
(`adapters.js:13,179` accepts one schema string); the viewer hard-codes two roots in four places
(`adapters.js:105-112,234,247,336`), so `oc` needs those edits. Its own `{?}` lines, each with the
default the agent takes: MaterialRootRename (default: exempt the experiment-scoped store until it
is promoted to `pyto/src`); OcNoPrecedent (default: enforce `oc` only when the first `oc` exists);
DiscProductSegment (default: `px.disc.*` and `px.card.*` are allowed, DiscStudio is the consumer,
not a per-instance world); ReceiptSegmentReserved (default: `receipt` joins the reserved second
segments); ScratchStoreShape (default: `px.scratch.<experiment>.*`); FixtureHonesty (default:
relabel the two fixtures "pre-mount, illustrative", do not rewrite); PartyMountType (default:
build the Python mount type in round five, since nothing else prevents collisions). Bites: round
five, `core.py`, `adapters.js`, `materials.py`, Day 5.

### {?} Purpose
What is all of this for?
Status: resolved 2026-09-09 by owner. "the point of all this is to explore things idk that I want
to." and "im not linus torvalds I just did lots of weird systems programming but all in Java at
Adaptiva basically being a ghost behind Windows managing and optimizing everything so I have a
weird OS insticnt but 0 understanding". Filed as: pyto is an exploration instrument for its owner;
questions to the owner are invitations to explore in OS-instinct vocabulary, never decisions that
need the theory. Bites: every prompt on the board; `{?} AddressRootIsAMount` (why it went by
default).

### {?} TheTestSeen
When it works on D:/, what is the first thing the owner wants to see?
Status: resolved 2026-09-09 by owner. "every delulu out there thinks they have AIOS. I need proof
im not one of them". Filed as: not a demo, proof a skeptic can run and cannot talk around. Bites:
"The test" on the board; the fresh-clone proof below.

### {?} ProofShape
Who is the skeptic, and what must fail to break?
Status: resolved 2026-09-09 by owner. "Uh me in 5 hours might be skeptical this is all worth it
but in general every kook thinks they have an ai os. Not every kook worked at Adaptiva which
manages mega corporate fleets. I turned my cv alg into workflow engine (like they had but yknow
generic stuff nothing protectable). Then kept chasing primitives then an agent I started with an
art tourney went from 'this is a function registry' to talking bout AIOS and function schedulers
and Claude has not been helpful on this project for like 2 weeks while I did this generalization
and then suddenly THAT happens". Filed as: the skeptic is the owner five hours from now; the proof
is what that reader can run from a fresh clone on D:/ and cannot dismiss, and its result is
written on the board as a result, never as a claim. Owner, later: "My entire past month of GitHub is proof this process works." First run, 2026-09-09 08:22, fresh clone of
3b8b5e5 into `D:/pyto-fresh-20260909`, the board's commands verbatim: the venv and install
worked; `run_cached.py` gave one miss and one hit with a write, from a fresh process; the tick
page rendered (296 KB); the suite was red on one test and its nested twin:
`retained.commit` names `dbc069dd…-dirty`, a working-tree sha from the experiment that produced
the evidence, which exists in no clone. Every other suite was green. That failure is Lane 4's
open prompt made concrete. Bites: `{?} EvidenceDirtiness`, `{?} VerificationOracleStamp`, Lane 4;
the proof run after every landing.

### {?} RecordRemembersCommit
Should a saved run remember its commit at all?
Status: resolved 2026-09-09 by owner. "I made neat to not care about git but let's say max
telemetry since ur gonna try to selfbootstrap and go ham overnight lol". So the field stays, and
the record may carry more, not less: neat is what spares the owner git, the stamp's job is to be
true. Consequence for the fresh-clone failure (`{?} ProofShape`): a stamp must name a landed
commit that every clone has, never a working-tree sha; evidence regenerated inside an experiment
is stamped at its landing base, and the proof run after each landing is the check. Bites: Lane 4's
open prompt (closed), `{?} EvidenceDirtiness`, `{?} VerificationOracleStamp`,
`experiments/grouped-ablation/run.py:235-265`, `replay.py`, the landing script.

### {?} RenderersForUsers
Should the studio stay static with the Python card renderers ported to JS and proven
byte-identical, or get a backend?
Status: resolved 2026-09-09 by owner, by default. Owner: "Bruh idk what you're saying. Idk any of
this it just happened." Default taken: port to JS with digest equality (same inputs, same SVG
bytes in both runtimes, the record is the proof), the site stays static, Python stays the
workshop where formats are designed and verified before they ship. Plain words: the studio is a
website with no server, browsers cannot run Python, so the drawers are rewritten in the browser's
language and the rewrite is proven identical byte for byte. Bites: Lane 2's open prompt (closed),
the DiscShelf and OnTheCourse brief, Astra's painter-port package.

### {?} StableAndExplainable
What does the owner need from the kernel, given they do not want to know how it works?
Status: resolved 2026-09-09 by owner. "My Adaptiva work was all java so I can basically write sick
services above the os so that's why it needs to be stable and explainable. I know nothing. U
explain it. That's why this works." Filed as the working contract: the kernel is the stable layer
the owner writes services above, the way Adaptiva's services sat above Windows; every question to
the owner comes with a plain-words explanation and a default; the agent explains, the owner
decides at the altitude of the services; "it just happened" is fine, the record is what makes it
explainable after the fact. Bites: every prompt on the board; `LANDING.md`'s explicability gate;
the hand-off primer (`{?} ConvincingAFreshAgent`).

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
permanent `-dirty`. Bites: `experiments/grouped-ablation/run.py:235-265`,
`second_experiment.py:184,325`, `replay.py:178`, every `evidence/*/commit.txt`.

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
`experiments/grouped-ablation/replay.py:185-249`, `test_replay.py`.

### {?} InputPartsChangedScope
`input_parts_changed` counts an input Part that one run reads and the other does not.
Status: provisional, decided by me 2026-09-09. The field is now computed from the two
retained records' external digests rather than passed as a literal, over the UNION of
both records' external addresses. run-4 therefore reports both
`input.ablation.rows` (dropped: it consumes run-1's retained split instead) and
`scratch.ablation.split` (added), where the old literal named only the addition. The
owner may prefer the narrower reading -- "the input Parts of THIS run that changed" --
which would list only the addition and leave the removal to `explain_changes`. Bites:
`experiments/grouped-ablation/second_experiment.py:202-249`, every
`evidence/run-*/saved-work.json`.

## Questions the Day 2 verifier resolved alone (2026-09-09)

### {?} DirtyStampUnderAConcurrentSession
Does a `-dirty` working tree caused by ANOTHER session's in-flight files count as
finding 7 failing?
Status: provisional, decided by me 2026-09-09. The Day 2 acceptance check is
"`evidence/run-1..4` carry a bare sha on the current tree when only evidence
differs". On the live tree that precondition is not satisfiable right now: a
concurrent Day 3 session has four untracked files in the experiment directory
(`hits.py`, `materials.py`, `run_cached.py`, `test_materials.py`) plus
`evidence/run-6-cached/`, so `run.commit_sha(exclude=run.evidence_excludes())`
returns `dee7879...-dirty` and `run.dirty_paths(...)` is
`['hits.py', 'materials.py', 'run_cached.py']`. I judged this a property of the
tree at this instant, not a regression in the stamp, and verified the mechanism
in a clean throwaway clone at the same HEAD instead: there, modifying committed
evidence and adding an untracked file under `evidence/` both leave the stamp
bare, while touching `run.py` or `pyto/src/pyto/pcr.py` stamps `-dirty`, and
regenerating all four runs with `--force` writes a bare 40-hex sha into every
`commit.txt` and every `retained.commit`. The owner may prefer the stricter
reading -- that the criterion is about the real tree and is therefore failing
until the Day 3 files are committed or removed, and that no clone may stand in
for it. Bites: `experiments/grouped-ablation/run.py:235-265`,
`evidence/OPEN-FINDINGS.md` Round 3 item 1, `{?} EvidenceDirtiness`.

### {?} VerifierSuiteCountBaseline
Is the pinned grouped-ablation count 211 or 228?
Status: provisional, decided by me 2026-09-09. `check_all.sh` reported 211 and a
later `unittest discover` over the same directory reported 228. The difference is
entirely the concurrent session's untracked `test_materials.py` (17 tests), which
appeared mid-verification; the Day 2 four modules are
`test_grouped_ablation` 33 + `test_replay` 81 + `test_retain` 55 +
`test_second_experiment` 42 = 211. I took 211 as the Day 2 number and treated 228
as Day 3 bleed rather than suite growth needing a pin. The owner may prefer the
suite counted as it stands on disk. Bites: `scripts/check_all.sh` (grouped-ablation
carries no pin today), `experiments/runs/day2/meta.json` `counts_note`.

## Five questions from Astra (GPT-6, via the owner, 2026-09-10), answered by this session

### {?} GuardEnforcement
An agent writes through a shell command instead of the editor. Is that caught before or after?
Status: after, today. The only guard is `git status` after the suites (`test_replay.py::CheckAllLeavesTheTreeClean`).
The design answer is the `oc` rule on the board: effects happen only through named OperationalCalculations
with receipts, allowed by name. Not enforced for agents yet; a pre-commit check (tidy's hook) is the
cheapest enforcement. Open.

### {?} StaleContext
An agent reads B to edit A; B changes. Is the proposed edit recognized as stale?
Status: for Parts, yes: receipts record `actual_consumes` with digests and `explain_changes` flags an
input whose digest moved. For files agents read outside PxC, no. The fix is the same mechanism:
agent reads as `oc` receipts carrying file digests, so staleness is a digest mismatch. Open.

### {?} ConflictingEvidence
The tracker says done; the latest tests failed. Are both kept and the disagreement exposed?
Status: by rule, yes: neat keeps declared intent separate from produced facts, and the board never
derives "done" from either alone. By tooling, not yet: the neat brief's board program is where
both facts become Parts and the disagreement becomes a row. Open until neat lands it.

### {?} Recovery
The orchestrator stops halfway. On restart, can it tell proposed, written and checked apart?
Status: per day, yes: `experiments/runs/dayN/` holds prompt (proposed), diff.patch (written),
verdicts and tests.txt (checked), and workflows resume from a journal with cached results. Mid-lane,
partial: an agent's uncommitted edits are visible only as a diff without a receipt. Same fix as
above. Partial.

### {?} Completion
Tests pass but the result misses the request. What keeps "execution succeeded" from becoming "done"?
Status: acceptance is a human fact and is never derived from tests (`AGENTS.md`: never record
acceptance on the owner's behalf; neat's AcceptanceReference names the human). The board's
prompts and each brief's "what to hand back" are the request; verification is the other column.
Rule exists; the tooling that refuses to mark done without the human row is neat's. Open.

One mechanism answers all five: every agent read and write becomes an `oc` receipt with a digest,
and "done" is a human Part. That is the agent-git the owner described, stated as two rules.

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

## From the ChainSpot branch mining (2026-09-09, `research/chainspot-branch-mining.md` §7)

Each entry keeps the miner's question; the lean is this session's recommendation to the owner.

### {?} AddressRootIsAMount
ChainSpot keeps the world (course, game, repo) outside the address as a mount and has a test that
`px.DashsTrack.s1.badges` is never created; round four put `disc`, `chess`, `wumpus`, `neat`,
`tidy` inside the address. Status: open, lean adopt the mount. One address means one thing in every
world, so a cross-project hit is an identity check, not a lookup. Bites: round five, Day 5.

### {?} RootIdIsContent
ChainSpot's mount id is a content digest of the image, with the human label in a side map. Status:
open, lean adopt: same material implies same root, which is what `px add <address>` needs; labels
stay readable in the side map. Bites: the materials store, `px add`.

### {?} ScratchRootConflict
ChainSpot's TS puts scratch inside `px.<stage>.exp.*`, its Python uses a `scratch.*` root, neither
enforced. Status: open, lean: three roots only (`px`, `fn`, `oc`), enforced for Parts the way `fn`
is for Calculations, with four reserved second segments (`scratch`, `view`, `proposal`, `run`).
Bites: `Part` validation, PQL prefix queries.

### {?} MaterialIsAKindNotARoot
Round four had a `material.<sha>` root; ChainSpot carries `kind` as a declared field on a
content-addressed reference and never chooses storage by string-matching an address. Status: open,
lean adopt the declared kind and drop the root. Bites: `{?} StorageKinds`, Day 3 materials store.

### {?} DuckDBIsAWorkshopBackend
The archive measured 3.80 s Node and 5.79 s browser startup against 69 to 228 ms queries; the owner
recorded 5.3 s. Status: open, lean: out of the runtime as decided; allowed in the Python workshop
only if a comparison needs it, none does this week. Canonical figure: 5.79 s (browser). Bites: none
this week.

### {?} TickEqualsReceipt
ChainSpot production declares a Tick's testimony and its receipt to be one type; pyto freezes the
testimony byte-identical with `observe` on or off. Status: open, lean keep separate and join in
the materializer; the byte-identity guarantee is what lets visibility be stripped. Bites: Day 3.

### {?} StorybookAsVehicle
ChainSpot's per-Tick viewer ships through Storybook and a staging build. Status: open, lean yes:
copy the six-section layout and the fail-loud UNKNOWN discipline, discard the toolchain; Day 3
already did. Bites: `viewer/tick-viewer.html`.

### {?} SilentRewritePredatesPyto
The declaration-time rewrite of a Part binding to its writer's ResultRef was already in ChainSpot's
Python, and silent, two days before pyto raised `{?} SilentRules`. Status: open, lean: JS is first
class and fails loud on the shadow case, so Python should too; a small kernel change with a test.
Bites: `{?} SilentRules`, `{?} ShadowRule`.

### {?} UnrunProofsCount
The Mermaid PCR compiler's seven rejection rules are a design that was never run. Status: open,
lean: port each rule with its own test in pyto; the port's tests are the proof, ChainSpot need not
run first. Bites: `{?} KernelMerge`.

### {?} S3DefectOwnership
Three of eighteen accepted Tee objects on one course are iOS map-chrome false positives, reported
with coordinates and not fixed. Status: open, lean: a ChainSpot ticket for neat's list; no pyto
surface inherits it. Bites: a caveat on the neon-sheet port.

### {?} MiningCoverage
Four tips failed on output formatting (fa44a45, the parent of the two most important tips, among
them) and three were mined after the synthesis. Status: open, being re-mined in plain text now.

## Landing and communication (2026-09-09)

### {?} ParkingIsManual
Should the landing script move another writer's files aside itself? Status: provisional, no: it
refuses, names the files and prints the parking command; a script that stashes a live writer's
files mid-write destroys work. Bites: `LANDING.md` step 1.

### {?} LandingBootstrap
How do the protocol's own files land? Status: resolved 2026-09-09 by circumstance: the session's
stop hook commits the tree at every turn end, so they entered as a labelled checkpoint; their
receipt comes from `land.sh landing-protocol --base 4641ea8` once Day 3 stops writing. Checkpoints
never claim; landings do. Bites: `LANDING.md`.

### {?} MailboxInRepo
The owner offered `D:\mailbox\` for messages to Astra; this session runs in a cloud container and
cannot reach it. Status: provisional: `mailbox/to-gpt/` and `mailbox/from-gpt/` in the repository,
the owner relays by pulling and pushing. Bites: `mailbox/`.

### {?} TheTest
The owner wrote "the test: we get AHI running on my local D:/ drive". Status: resolved 2026-09-09
by owner: AHI is Augmented Human Intelligence, human centric, AI extends. The test is the whole
loop (board, `{?}` root, landing with receipts, record viewer, mailbox) running from a clone on
the owner's Windows D:/ drive. The owner also confirmed `{?}` is good: the human stays the root.
Bites: everything; Windows-safety of scripts, suites and `px`.

## From the four re-mined ChainSpot tips (2026-09-09, mining appendix)

### {?} PartialWritesOnFailure
ChainSpot's S1 lane keeps a failed Tick's earlier writes visible in its fork and defers partial
records (`fa44a45` REVIEW.md:13); Wumpus rolls back. Status: open, lean keep writes and record
the failure; rollback is a Calculation-level choice (`{?} TransactionalTick` now has prior art
both ways). Bites: `PCR.run` failure path.

### {?} ThreeReceiptShapes
One ChainSpot tip carries three receipt vocabularies at once. Status: provisional: pyto has one,
`pyto-run-record@1`, and every lane writes it; an experimental lane that forks its own fails
landing. Bites: `viewer/RECORD.md`.

### {?} MaterializerAsTemplate
A plain script that runs the PCR, queries the finished store by address, asserts a partition
invariant, then renders (`fa44a45` render-badge-ownership.cjs) predates neon-first by hours.
Status: provisional yes: that shape is `embed.mjs` plus a check; keep the six-section layout for
the page. Bites: Day 3.

### {?} PqlRunRootStatus
`px.pql.<Name>` has two independent ChainSpot precedents. Status: open, lean: `pql` joins the
reserved second segments (`scratch`, `view`, `proposal`, `run`, `pql`). Bites: round five.

### {?} MatrixAddressRoot
`matrix.material.<key>` is a live unprefixed cache address in shipped LAB tooling. Status: open,
lean: cache keys are content digests under the materials store, never addresses; no exemption
from the three roots. Bites: `materials.py`.

### {?} TelemetryGateRule
A value computed only for logging must never influence its own Calculation's output. Status:
provisional adopt as a receipt-design rule; enforcement is the byte-identity test with `observe`
on and off. Bites: `{?} ObservationSeam`.

### {?} TruthTaintAsReceiptField
ChainSpot marks truth-assisted evaluations with a mode so no consumer treats them as production
evidence. Status: open, lean adopt as a field on the record (`blind`, `truth-assisted`,
`proposal`); the concrete mechanism for `{?} ProposalsNotFacts`. Bites: `RECORD.md`.

### {?} VisibilityAxisInOracle
A truth-holder can mark a case UNKNOWN, so a miss is neither pass nor fail. Status: open, lean
add the third bucket to replay verification. Bites: `replay.py`.

### {?} SnapshotVsMaterialization
A whole-board serialized snapshot, digest-gated, is a third storage answer. Status: open, lean
workshop-only; per-address declared kind stays the runtime answer. Bites: materials store.

### {?} CustodyReceiptFamily, {?} OperationLevelReceiptWrapper, {?} ForkAsTickTransaction,
### {?} ReceiptWordCollision, {?} ScratchRootOrigin, {?} TelemetryGateBoundary
Status: open; described in the mining appendix. Lean: custody facts are ordinary Parts; the
feature-set envelope stays out of the kernel; fork isolation is tournament isolation, not
rollback; keep the word receipt for the run record only; `scratch` was incidental and round five
settles it; enforcement is the byte-identity test, not prose.

## Added by the Day 3 record stage (2026-09-09)

Both labels were already named, undetailed, in the mega-list above ("{?} ValueRetention,
{?} MaterialsLocation, ..."); these two entries are where they are actually raised, per
`viewer/RECORD.md` and `experiments/grouped-ablation/materials.py`.

### {?} ValueRetention
What happens to a Part's value when it is too large for the run record to carry whole?
Status: open. Records carry values up to 256 KB; image Parts beyond that are digests + sidecars.
`viewer/RECORD.md:112` ("Values over 256 KB are replaced by `omitted` with a note carrying the
size and the digest") is the rule pinned on the pyto side by
`pyto/src/pyto/materialize.py` (`VALUE_CAP_BYTES = 262144`, `ARRAY_CAP = 200`, materialize.py:49-50)
and on the JS side by `viewer/adapters.js`'s `capped()`. The owner has not said whether 256 KB is the
right budget for an image Part specifically (a rendered course crop is routinely larger), or
whether a sidecar file next to the record (rather than a bare digest) should be the norm for
every over-cap value, image or not. Bites: `viewer/RECORD.md` field rules, `materialize.py`
`tick_sheets` (which never hits this cap because SVG panels are rendered to disk, not embedded),
Day 4/5 if a corpus-sized image Part is retained.

### {?} MaterialsLocation
Where does the content-addressed materials store live, and is it shared or per checkout?
Status: open. Default `~/.pyto/materials`, per user (`experiments/grouped-ablation/materials.py`
`DEFAULT_MATERIALS_DIR`/`default_root()`, overridable by `PYTO_MATERIALS_DIR`). This is the
Reframing 3 "durable, per-user engram table" answer as far as Day 3 goes: a plain-JSON-file
store rooted outside any repository checkout, so a Part produced in one project's process can in
principle be verified and reused in another (`{?} CrossProjectReuse`, not yet run). Not yet
decided: whether the same root should be shared across a team (a workstation-level table) or
stay strictly per-`$HOME`, and whether a repo-local override (as `run_cached.py`'s tests use, via
`PYTO_MATERIALS_DIR`) should ever be the default for CI rather than only for isolation in tests.
Bites: `experiments/grouped-ablation/materials.py`, `{?} CrossProjectReuse`, `{?} TableScope`,
Day 5's cross-project hit.

## neat, the caveman version (2026-09-09, from the owner's other chat)

### {?} LandingScope
Task 0 changes three files and the owner likes two. Status: resolved 2026-09-09 by design:
`neat drop 0 <path>` puts a file back to the starting point and repacks; the owner lands what is
left. Bites: `neat.sh`.

### {?} TaskIds
Base64 ids or plain numbers? Status: provisional: plain numbers from 0; base64 is an encoding and
can come later without changing anything. Bites: `neat.sh` next_id.

### {?} FoldersNotBranches
The owner wants one tree, no branch sprawl. Status: provisional: EXP/<id> is a folder the owner
opens; underneath it is a git worktree on `exp/<id>`, deleted at landing, pushed only so a fresh
agent elsewhere can fetch the packet. The owner never types a branch name. Bites: `neat.sh`.

### {?} PacketTravels
Where does the packet live so a fresh agent on another machine gets it? Status: provisional:
inside the experiment at `pyto/experiments/tasks/<id>/`, committed on `exp/<id>`, so it travels
with the branch and lands with the candidate as the record of what landed. Bites: `neat pack`.

### {?} ConvincingAFreshAgent
Fresh agents often dismiss pyto. Status: provisional: the hand-off carries a short primer that
makes no claim the agent cannot check in two minutes (the suite, the cache hit across processes,
the viewer page), plus the `{?}` root. To be tested with cold readers. Bites: HANDOFF.md.

### {?} BPlusTree
Could neat be a B+ tree? Status: open, lean later: a B+ tree organizes stored records for lookup;
it can sit under neat's PxC once tasks are Parts; it gives no isolation or landing by itself.

## Everything is a file (2026-09-09, the owner's line)

### {?} EverythingIsAPart
The owner: "The function stopped being the subject; the receipt became the subject. One of the
few things I actually know about Linux is 'everything file'." The mapping: in Unix the file is
not the interesting object either; one interface (a path, read, write) covers devices, pipes and
processes, so a few tools compose over all of them. pyto's version: everything is a Part (an
address and a value), and every use leaves a receipt, which is a Part too. The reference runtime
already does this: `src/runtime.js:57` writes `px.receipt.<name>` beside `px.pql.<name>`. Python
keeps receipts on the run object (`PcrRun.receipts`, `pcr.py:145`) instead of in the store, which
is the one place the transfer breaks the rule. Status: provisional, lean adopt: receipts, landing
receipts, packets, decisions and proposals are Parts under reserved second segments (`receipt`,
`proposal`, ...), written only when visibility is on and never read by a Calculation (ChainSpot's
`px.view.*` precedent), so the CV runtime with visibility off writes none and the byte-identity
guarantee holds. This collapses `{?} ObservationSeam`, `{?} TickEqualsReceipt`,
`{?} ReceiptSegmentReserved` and the "agent reads become oc receipts" half of `{?} GuardEnforcement`
into one rule; PQL is then `ls` and `grep` over all of them, the viewer is `cat`. Bites: `pcr.py`
(a `receipt` mount or segment written under `observe=True`), `materialize.py`, `neat`.

### {?} OvernightLanding
What may land while the owner sleeps? Status: resolved 2026-09-09 by owner: "I want minimal hard
stops ... I can't keep track of git and I need to keep track of this. Like go wild too but it's
gotta augment me. AHI." So: everything that passes its verifier and the suite lands, kernel
changes included, with a receipt and a Today line; a decision taken by default is written here in
the owner's words with the default; `neat undo <id>` reverts a landed task with its own receipt,
so control is a way back, not a gate. Nothing is deleted; a losing attempt stays as a packed task.
Bites: tonight's queue on the board, `neat.sh`.


### {?} NearHit
The owner pointed at Annoy (approximate nearest neighbours, read-only mmapped index shared by
processes). Status: provisional: the cache today hits only on identical bytes; a near hit would
reduce a course screenshot to a small vector and reuse the nearest already-parsed course's Parts
as proposals, confirmed by the parser inside the budget. Annoy is a workshop tool (C++, no
browser build, out of the runtime by the cold-start rule); the runtime needs only a brute-force
loop over one user's few hundred vectors. Default: an experiment `near-hit` when CV returns, one
number (how often the nearest prior course is a good proposal), nothing before DiscStudio ships.
Bites: the materials store, the record's `hit` field, Day 5.

### {?} ResidueMining
The owner: could SUBDUE-style mining find shared substructure in ANN logs, or be the CV substrate
itself, detecting residue pixels? Status: provisional. ANN logs: real but plain clustering finds
the same cliques. The residue: yes, and it fits the LAB: every stage already writes
`px.remaining.after<Stage>`; turn the last residue into a labelled component graph (colour, size,
shape labels; touching, above, left, same-screen-region edges) and SUBDUE finds the arrangements
that repeat across courses, which are the objects no stage exists for yet (the S3 iOS map-chrome
false positives are residue structure fixed to screen position). Its output is a candidate with
evidence (instances, compression, where), the owner names it, it becomes
`fn.disc.detect.<name>`, receipts show hits, the residue shrinks: promotion with evidence, the
Lane 5 claim. The same algorithm over run records (Ticks to Calculations to Parts) finds recurring
sub-programs, the Day 5 plan. Default: workshop only, Python, after DiscStudio ships, needing the
dev course images; the one piece that can land any time is a scalar Part with the count of
unclaimed pixels per Tick, which makes competition Ticks scoreable. Bites: Day 5, Lane 5, the
competition Ticks, `research/primary-sources.md` (Cook and Holder 1994).

### {?} HidingPrimitives
The owner: the ANN logs would be neat's, the LAB's, the paint studio's, to see if they hide
command primitives. Status: provisional, running as task 20. A primitive hiding in a log is a
subsequence that recurs with different arguments and has no name; ANN groups near-identical
instances, SUBDUE names the shared skeleton and scores it by compression; the output is a
proposal with evidence, the owner names it, it becomes a Calculation or a neat command. The logs
become Parts when receipts (task 13) and the `oc` table land. First substrate, needing no new
recording: the paint studio's call graphs, mined and reported beside the helpers the JavaScript
port extracted by hand. Bites: Lane 5, Day 5, the `oc` table, `neat`.

### {?} UndoStack
The owner: a generic Part that would do the site good the way undo did neat. Status: provisional,
queued behind receipts as Parts (task 13). Not a structure: one more field on the write receipt,
the previous value (inline when small, by digest in the materials store when large), makes the
undo stack a query over `px.receipt.*` (writes to an address, newest first, with what they
replaced). Undo is one Calculation that writes the previous value back, itself recorded, so
history stays append-only like a revert; redo is the same move forward. For the studio: undo for
customizer and card edits, "what changed since" in the review panel from the same query, and an
accidental inspector write is one undo away. JavaScript first (the runtime's set records the
previous value), Python mirrors the receipt field. No new state store, per AGENTS.md. Bites:
task 13, `RECORD.md` (one field), `src/runtime.js`, the review panel.

### {?} CardRenderer
Astra, handing back `astra/discstudio-1`: "The fixed port cannot preserve arbitrary authored
nodes and styles. Approve extending its interface, or retain the existing generic card renderer?"
Status: provisional, default taken 2026-09-09: retain the generic renderer. The studio's card is
authored (nodes, bindings, styles the customizer edits), so the ported `cards.mjs` stays what it
is, the byte-identical reference for the two promoted layouts used by fixtures and tests, and the
ported painter draws the art inside the generic renderer (`kind: painted`). No renderer fork, per
AGENTS.md. Their delivery already did this; the one gap, the generic renderer showing "Add image"
for painted art, is fixed on their branch before landing. Bites: `src/presentation.js`,
`port/painter/cards.mjs`.

### {?} Students
The owner: "due to hashing guarantees this could be an unusually good tool for students." Status:
provisional, an audience, nothing built. What hashing gives a classroom: the per-Tick record is
"show your work" made literal; a record that replays byte for byte on the grader's machine proves
the student's claim about their own program; identical digests on every Tick are the same work,
whoever typed it; a port across languages is judged by a verifier (the painter port is the
demonstration). From tonight: the explicability gate is a rubric with no teacher in it, and the
`{?}` habit is most of learning to program. The caveat to teach first: identical digests prove
the same computation, not the right answer; a verifier still needs a reference. Default: after
DiscStudio ships, one experiment: a homework-sized PCR with a hand-off page graded by a cold
reader. Bites: `LANDING.md` (the gate), `HANDOFF.md` template, the viewer. Owner, later: "personal
parts and calculations let the agent learn how the student learns": a student's own mount holds
their Parts and the Calculations they wrote, so a tutoring agent reads how they learn from their
own records (what they retry, where they write `{?}`, what they undo, how long a Tick takes them),
never from a profile.
Owner, 2026-09-09 evening, on why any of this exists when ChainSpot and DiscStudio do not need it: "Workspace. Educational." and, of Homeroom Heroes, "this would be a good reason why". So the workspace is not a side effect; it is the product for that audience, and the studio is its first tenant.

### {?} StoppingRule
The owner, 2026-09-10, on how to launch an agent that gains real depth: "Reading is not depth of
understanding. Remember that 2M tokens from like 24 hours ago? And then each and every question
invalidated like 50% of what you assumed? The key to initializing is an agent getting just enough
context to go wtf and ask me what feels like the stupid question that should have an obvious
answer if it could only check another 100k tokens of code." Status: adopted. The hand-off page now
opens with the rule (read three files, no fourth; write the question; ask; stop) and the answer is
written here verbatim. Default: the first task for any newcomer is a question, not a change.

### {?} NeatLearning
The owner, 2026-09-09 night: "imagine neat-learning (like awesome-* but neat based). Easy, neat based
teacher-student stuff. Teacher says okay assignments in, they submit and get instant scores." Status:
an idea, nothing built; task 23 (students) is the seed. The mapping is one to one: course = repo,
teacher owns MAIN; assignment = a package brief (student folder as allowed paths, teacher's tests as
the verifier, a reference the tests encode); start = neat new; submit = neat pack (the score is in
the evidence before anyone looks); accepted = neat land (disjoint folders, no conflicts); grade record
= the landing receipt; gradebook = the Today log; resubmit = a new task, every attempt kept; write-up
= HANDOFF.md read cold by the teacher or an agent first; copying = identical result digests on a
step. The awesome-* part: neat-learning is a repo of assignment packages (brief, verifier, reference,
sample hand-off) and contributors add them through neat, so the collection grades its own additions.
Missing: a score in the receipt (passed of total, not exit 0/1) and `neat list` showing it.
Owner overturned the first default the same night: "Private by default, sharing ez. All controlled by deterministic RBAC to prevent mini hugging face attack like OpenAI." So: a student's desk is its own repo, visible to the student and the teacher only; sharing is a landing into a shared repo (showcase, pair, class) with allowed paths, a verifier and a receipt, and unsharing is undo; who may do what is a plain file at the class root plus the git host's collaborator list, read by neat and never by a model, so a prompt cannot widen access; one desk, one repo, one token scoped to it, so a leaked token reaches one student's work and the leak shows in that desk's receipts; copying still shows because digests travel with a share. Owner, on the note that one desk per repo was a day's change: "Neat assumes one repo with branches per client yes. So?" Right: the student's repo is their MAIN and neat anywhere already runs there; sharing is the class repo fetching a student's branch and landing it, which is land --from behind a remote fetch. What is left is small: a score in the receipt (passed of total, not exit 0/1) and neat land taking a remote and a branch. Remaining defaults: the verifier is the teacher's reference and the cold read stays the real grade; personal Parts accumulate on the student's own desk and that is what a tutoring agent reads, never a profile. Bites: pyto/experiments/students/, LANDING.md, neat.sh.
