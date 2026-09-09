# Brief for Haven: the disc golf work and the system that grew out of it

Written 2026-09-09 for a first-time reader with no shared context. Every term is defined where it
first appears. Nothing here is compressed for brevity; the short version is `pyto/BOARD.md`.

## 0. The one-paragraph orientation

Sam builds two disc golf apps. **ChainSpot** parses a phone screenshot of a disc golf course map
into course objects (tees, baskets, badges with hole numbers) with computer vision, under a hard
budget of five seconds on a phone. **DiscStudio** is a static website, no server, where a player
keeps a shelf of discs, composes cards with disc art, and produces many output formats (cards, a
printable shelf sheet, share images, exports). Under both sits a small design Sam proved three
times in JavaScript and TypeScript (ChainSpot, ChessLab, an embodied Wumpus world) and then
transferred to Python as **pyto**: a store of named values, pure functions over them, and a
program that names which functions run in which order, where every run leaves receipts that say
what each function read and wrote. Over one long day (2026-09-09) that design was reframed as a
tiny operating system for agents, a landing protocol and a version-control layer called **neat**
were built around it, and a loop was closed in which Sam talks, agents work in isolated copies,
verified work lands with receipts, and one page keeps Sam in the loop. This brief is the record of
all of that.

## 1. The object model

### 1.1 The primitives, in the order they depend on each other

**Address.** A dotted lowercase string such as `px.badges.px` or `fn.ablation.split`. Identity is
the address, never the current value. Addresses form a tree. The rule under adoption (decided by
default this session, see section 5) is three roots only: `px` for values, `fn` for pure
functions, `oc` for effects; a small set of reserved second segments under `px` (`scratch`,
`view`, `proposal`, `run`, `pql`, `receipt`); and worlds (a course, a game, a bag, a repository)
are never segments of an address. A world is a **mount**, an id outside the address space, so one
address means the same thing in every world. Today only the `fn.` rule is enforced in code; the
rest is described by a validator (`pyto/src/pyto/address.py`) that enforces nothing and a census
of what would fail.

**Part.** A value at an address. In Python, `Part(address)` is a frozen dataclass whose only field
is the address; the value lives in the store. "Everything is a Part" is the design's version of
Unix's "everything is a file": receipts, decisions, proposals and logs are meant to be Parts too,
so one small set of tools reads all of them.

**Calculation.** A named pure function: `Calculation(address, calculate)` where the address must
start with `fn.`. It takes one argument, a mapping of named inputs, and returns one result. Every
non-trivial thing in the apps is a Calculation: a stage of the vision pipeline, a card renderer, an
output format, a constraint of a competition.

**PxC.** The store plus the registry; section 2 defines it fully. Five verbs: `has`, `get`, `set`,
`register`, `call`.

**PCR, Tick, Invocation.** A **PCR** (PrincipleComponentRender, Sam's name: the render definition
of a computation's principal components) is a program: a named sequence of **Ticks**, each Tick a
named group of **Invocations**, each Invocation a Calculation called with bindings. A **binding**
names an input parameter and points it at a Part (`px:<address>`) or at the result of an earlier
invocation (`fn:<id>`, a **ResultRef**). An invocation may publish its result into a Part (`into`).
Ticks run in first-mention order; a Tick is the unit at which you are allowed to look (Sam's
founding need, section 4.1). In Python a PCR is authored with `PCR(name).calc(tick, calculation,
id=..., into=..., args=..., **inputs)` and executed with `PCR.run(pxc, observe=False)`. Two rules
are enforced at authoring time: one writer per Part address, and unique invocation ids. One
rewrite happens silently at authoring time: an input bound to a Part that an earlier invocation
writes is replaced by a ResultRef to that invocation (recorded as an open question, `SilentRules`).

**PcrRun, testimony.** What a run returns: the PCR name, a tuple of Tick testimonies (each Tick's
name and its invocations with their bindings, in testimony spelling), the results by invocation
id, and, only when `observe=True`, receipts. The testimony is byte-identical whether observation
is on or off; that guarantee is what lets the production vision runtime run with visibility
stripped for speed while the workshop runs the same program with visibility on.

**Receipt.** What the run observed for one invocation when observing: the frozen Calculation
(address, a sha256 of its source text with line endings normalized, an identity scope), start and
duration in milliseconds, declared reads (the `px:` bindings, in binding order) and declared
produces (`into`), actual reads and writes as the store saw them, each write's kind (new address,
refinement, replacement), a sha256 of the result when it is JSON-serializable, and which inputs
were shadowed by arguments. Receipts are the founding object: the function stopped being the
subject, the receipt became the subject.

**Run record.** One JSON document per executed PCR, schema `pyto-run-record@1`, defined in
`pyto/viewer/RECORD.md`, produced by Python's materializer and by JavaScript adapters from the
apps' own receipts. It carries, per Tick, per invocation, everything above plus the value as
material (JSON, text, SVG, a PNG data URL, or "omitted" with a note), a derived `hit` flag (the
Part or Calculation was reused), and a derived parts index (who wrote and read each address). Both
runtimes must speak it exactly. The viewer (`pyto/viewer/tick-viewer.html`) is a dependency-free
page that renders it per Tick; one page opens ChainSpot, ChessLab, Wumpus, DiscStudio and pyto
records side by side.

**Materials store.** A content-addressed cache: a key is a sha256 over the calculation's source
digest and its inputs; a hit returns the stored value without calling the function; it is a
directory of files, so a fresh process, or another process, hits the same key. Experiment-local
today (`pyto/experiments/grouped-ablation/materials.py`), proven across processes.

**Mounts.** `pyto/src/pyto/mounts.py`: `mount(root, pxc)`, `get`, `has`, `roots`, `entries`,
`slice`, with human labels in a side map. The root id is meant to be content-derived (ChainSpot
uses a sha256 of the image). No address is ever rewritten; the negative test asserts that no
address in a mounted store contains the root.

**The `{?}` root.** Not an address. `{?} Label: description` is the mark an agent leaves when it
is unsure and needs the owner; `pyto/questions.md` collects them with a status (open, provisional
with a default taken, resolved by owner with the date and the owner's words). If the addressing
were a tree, `{?}` is its root: the human is init.

### 1.2 How they relate, in one picture

```
{?} root (the owner's decisions)
   |
<mount>  world id, outside the address space (imgid:<sha>, disc:<bag>, chess:<game>)
   |
   +-- px.<noun>.…          Parts (values); reserved: px.scratch, px.view, px.proposal, px.run, px.pql, px.receipt
   +-- fn.<ns>.<name>       Calculations (pure)
   +-- oc.<ns>.<effect>     OperationalCalculations (effects; designed, not built)

PCR -> Tick[] -> Invocation[] -> (Calculation, bindings, into)
PCR.run(pxc, observe) -> PcrRun { ticks (testimony), results, receipts (if observe) }
run_record(PcrRun) -> pyto-run-record@1 JSON -> viewer page
materials store: sha256(source digest + inputs) -> value (hit across processes)
```

## 2. PxC, in full

**Definition.** PxC ("pixel cache", from its origin in ChainSpot) is a fail-loud semantic Part
store plus a Calculation registry. In Python (`pyto/src/pyto/core.py`, under 100 lines):

- `has(part)`: whether the address holds a value.
- `get(part)`: the value; raises `KeyError` if the Part was never produced (fail loud, never
  `None`).
- `set(part, value)`: stores and returns a `PxWrite(address, kind)` where kind is `new-address`
  or `replacement` (a `refinement` kind exists in the receipt vocabulary).
- `register(calculation)`: adds a Calculation by its `fn.` address.
- `call(calculation_or_address, args)`: runs a registered Calculation.
- `addresses()`, `items()`: enumeration, used by PQL.

The JavaScript original (`src/core/exec.js` in DiscStudio, `createExecBoard`) is the same five
verbs, with `trackAccess` wrapping a board so a Tick's reads and writes are recorded.

**The problem it solves.** Origin (`pyto/research/origin.md`): while building ChainSpot's
pathfinding, nothing the algorithm used was visible, and every attempt to look at an intermediate
meant rerunning everything. PxC gives every intermediate an address, so it can be looked at,
cached, compared and replayed, and gives every function a name, so what ran is a fact rather than
a guess. Sam's later words: the main use is a cache for the vision algorithm under a five-second
budget, and the founding need is seeing what the algorithm used, per Tick. The same store serves
both because a receipt is what a cache and an inspector both need.

**Where it sits.** Below everything. A PCR reads and writes through it; receipts are its
observations; the run record is a view of it; the materials store is its disk twin; mounts sit
above it; PQL queries it. In the ELK reading Sam adopted (the log stack Elasticsearch, Logstash,
Kibana): Calculations compose meaning (Logstash), PxC stores it (Elasticsearch), the PCR itself is
the render definition (Kibana), and PQL is the query language.

**Rules that shape it.** Simple stays simple: five verbs and no configuration. Identity is the
address, never the value. Fail loud: a missing Part is an error. Visibility costs nothing when
off. Storage backends are chosen per mount by measured cold-start cost in the browser, never by
configuration; DuckDB (5.79 s to start in the browser) and OpenCV are out of the runtime for that
reason.

## 3. PQL, in full

PQL ("PxC query language") names two things that share the initials, and both are real:

### 3.1 The Python query class

`pyto/src/pyto/pql.py`: a tiny composable query over a PxC. Exact Parts and address prefixes are
first class; refinement is ordinary Python.

Grammar, as an API:

```
PQL.part(part_or_address)         -> the one Part at that address, if present
PQL.prefix("px.badges.")          -> every Part whose address starts with the prefix
query.where(lambda match: ...)    -> filter; match has .address and .value
query.matches(pxc) -> tuple[Match]  query.values(pxc) -> tuple[values]
query.one(pxc)    -> exactly one value or ValueError
query.optional(pxc) -> one value or None
```

Real examples:

```python
from pyto.pql import PQL
badges = PQL.prefix("px.badges.").values(pxc)              # every badge Part
big = PQL.prefix("px.tees.").where(lambda m: m.value["px"] > 40).matches(pxc)
run = PQL.part("px.pql.disc-shelf-sheet").one(pxc)          # the record of one composition
```

Once receipts are Parts (in progress), `PQL.prefix("px.receipt.")` reads a run's receipts like any
other values, which is the "everything is a file" payoff.

### 3.2 The composition document

The apps author programs as a document, YAML or JSON, called a PQL composition. Grammar
(`readPql` in `src/core/exec.js`; the same shape is emitted by pyto's `Pcr.to_pcr_dict()` and by
ChainSpot's Mermaid compiler):

```
document        := { PrincipleComponentRender: <name>, Ticks: [ tick... ] }
tick            := { name: <name>, Calculations: [ calculation... ] }
calculation     := { call: fn.<address>, with: { <param>: <address>... }, args: { <param>: <literal>... }, into: <address> }
```

Rules the reader enforces: `call` must be a registered `fn.` address; a parameter may appear in
`with` or `args` but not both; every `with` value is an address string; `into` is required.
Execution (`invokePql`) runs Ticks in order, resolves each `with` by `pxc.get`, merges `args`,
calls the Calculation, writes the result to `into`, and finally writes the whole run to
`px.pql.<name>`. DiscStudio's runtime also writes `px.receipt.<name>` beside it.

A real example, from `tests/formats.test.js` on the branch:

```json
{ "PrincipleComponentRender": "disc-shelf-sheet",
  "Ticks": [ { "name": "ShelfSheet", "Calculations": [
    { "call": "fn.disc.format.shelfSheet",
      "with": { "bag": "px.input.bag", "discs": "px.input.discs",
                "molds": "px.input.molds", "manufacturers": "px.input.manufacturers" },
      "into": "px.format.shelfSheet" } ] } ] }
```

And the Python authoring of the same idea, from the grouped-ablation experiment:

```python
pcr = PCR("ablation.grouped")
split = pcr.calc("Prepare", REGISTRY["fn.ablation.split"], id="split", raw=Part("scratch.ablation.raw"), args={"seed": 7}, into="scratch.ablation.split")
fit = pcr.calc("Fit", REGISTRY["fn.ablation.fit"], id="fit.all", split=split, args={"variant": "all"}, into="scratch.ablation.model.all")
run = pcr.run(pxc, observe=True)
```

PQL is expected to grow; it is the query DSL of the ELK reading.

## 4. The agentic operating system: what exists, how it talks, what is theory

### 4.1 Why it is called that

`pyto/research/from-registry-to-os.md` records the fifteen steps by which a function registry
came to read as a kernel, each step caused by one of Sam's sentences. The mapping that resulted:

| operating system | this system |
|---|---|
| kernel | PxC's five verbs, PCR and Ticks, receipts |
| filesystem, mounts | the address space; worlds are mounts |
| syscall table | `oc` OperationalCalculations (designed, not built) |
| scheduler, quantum | the JavaScript event loop; a Tick boundary is the yield, observation and budget point (designed, not built) |
| processes | neat's EXP copies of the tree, each with its own Python |
| /proc, dmesg | the run record; the board's Today log |
| terminal | the PCR render page |
| compiler | the retained program plus registry, run with visibility on in the workshop and off in the runtime, equal digests as proof (designed) |
| package manager | `px add <address>` verified by replaying its record (designed); the landing script's receipts (built) |
| init, root | the owner, through the `{?}` root and the board |

The metaphor is a lens for design decisions, not a product. Sam's rule: nobody says "AI OS".

### 4.2 The layers that are built

**neat** (`pyto/scripts/neat.sh`, 10 commands): one MAIN (the clone), one EXP folder, a task is a
number. `neat new "intent"` makes `EXP/<id>`, a git worktree on branch `exp/<id>` with its own
`.venv` so its suite tests that copy's kernel, and reserves the id on origin at once. An agent
works there. `neat pack <id>` commits, runs the suite in the copy, writes the **packet**
(`pyto/experiments/tasks/<id>/packet.md`: Intent, Starting point, Verify, Allow, Candidate as a
diff from the merge base, Evidence with the suite table, Uncertain with `{?}` lines) and a
**hand-off page** (`HANDOFF.md`) a fresh agent can act from after cloning, with a primer on why
the repository is worth its time. `neat land <id>` merges onto MAIN as it is now, verifies there,
writes a receipt, commits `land(task-<id>): ...`, pushes, writes one line under Today on the
board, and removes the copy. `neat undo <id>` reverts a landed task through the same protocol.
`neat update <id>` brings MAIN into a copy. `neat drop`, `kill`, `show`, `list`. Tested end to end
in a scratch clone with its own origin, and used for every landing since.

**The landing protocol** (`pyto/LANDING.md`, `pyto/scripts/land.sh`): one script, one receipt per
landing under `pyto/experiments/landings/<id>/` (schema `pyto-landing-receipt@1`: base commit,
claimed and unclaimed files with digests, verifier command and output digest, suite counts), a
failed receipt on every refusal with the reason, refusals that name the file and the fix,
checkpoints labelled `checkpoint:` that never claim anything. Rules: no landing while MAIN is
behind origin; refusal bookkeeping never blocks the next landing; the three log files
(`BOARD.md`, `questions.md`, `CHANGES.md`) merge by union so two machines can append.

**The board** (`pyto/BOARD.md`): the one owner-facing page. "The test" (Sam's acceptance: AHI,
Augmented Human Intelligence, running on his Windows D:/ drive from a fresh clone), "Interrupts"
(the rule for when the owner is told anything), "Today" (one line per landing attempt, newest
first, written by the scripts and the sessions), five lanes with a statement and a "Stands" line,
and at most three open prompts. A proof script (`pyto/scripts/proof.sh`, from Sam's local
session) clones the branch fresh, runs the board's test block verbatim, and writes a green or red
line with a receipt.

**The explicability gate** (in `LANDING.md`): before a self-improvement task may land, a cold
reader who has seen nothing but its hand-off page explains what changed and which files; a judge
compares that to the real diff; a mismatch refuses the landing and the reason goes on the packet.
Ran once tonight: four branches, three passed, one refused for a hand-off that said "two checks"
where the script made three.

**The record and the viewer**: `pyto/src/pyto/materialize.py` (`run_record`, `tick_sheets`),
`pyto/viewer/` (adapters for four runtimes, validation, an embed script that bakes a record into a
standalone page, a multi-record picker), 80-plus JavaScript tests and a Python schema suite.

**The experiments** (`pyto/experiments/`): grouped-ablation (Day 1 and 2: retain a run as a
declarative record, replay it in a fresh process with digests that refuse forgeries, a second
experiment reusing the first's Parts with zero program edits, the materials store with hit
counters, the determinism matrix, the line-ending probe), the art tournament (sixteen disc-art
families judged and registered as Calculations), hiding-primitives (a SUBDUE-style substructure
miner over the paint studio's call graphs, section 5), and the per-task packets.

**The painter port**: sixteen art families and two card renderers as dependency-free JavaScript,
byte-identical to Python across 440 fixture cases, including a correctly rounded `hypot`, `sin`,
`cos` and `atan2` because Node's math library differs from glibc by one bit often enough to flip
branches. Wired into DiscStudio's own card renderer tonight (Astra's package one, landed).

### 4.3 The agents and how they talk

- **This session** ("Fable", the cloud Claude Code session on the branch): owns the kernel lane and
  orchestrates workflows of Claude subagents (Opus and Sonnet at high effort) as pipelines:
  builders on disjoint files, an adversarial refuter that re-derives every claim and runs the whole
  suite, repair rounds until green, then pack and land. Talks to the owner in plain words; every
  decision taken by default is written at the `{?}` root in the owner's words.
- **The owner's local session** on D:/ (Claude Code on Windows): the Socratic partner. Sam talks;
  it writes decisions into `questions.md` and the board, commits and pushes; Sam opens no file.
  It also landed the Windows fixes, `proof.sh`, `questions.sh`, and the multi-record viewer. The
  two sessions coordinate only through the repository: pull before write, union merges on the
  logs, task ids reserved on origin.
- **Astra, Terra, Luna** (an OpenAI hierarchy Sam runs: Astra assigns, a Terra operates, Lunas
  implement): receive self-contained package briefs pasted by Sam (a `mailbox/to-gpt/` folder in
  the repository archives them; it is not a channel, since Astra cannot read a repository), hand
  back a branch `astra/<name>` with a report and `{?}` lines; this session verifies with the
  package's command and lands it or returns findings. Package one (art in the browser plus a shelf
  sheet) landed tonight with two fixes on top.
- **Codex**: task 3, "neat anywhere" (the scripts in any repository, with a self-test), briefed as
  two Lunas under one Terra; not yet returned.
- **The work brain**: a separate private repository and session for Sam's day job (no code, no
  customer data), run from his phone with four utterances ("what's next", "someone said", "done",
  "not sure") plus "tidy"; out of scope here except as the pattern.
- **Windsurf and Rovo** on the work laptop: executors of single self-contained shots the work brain
  writes; not part of this repository.

Contract for every agent: no configuration files; checks that cause friction get disabled; one
writer per directory at a time; a package is bounded and decides itself with a verifier that exits
0 or 1; anything the owner must decide becomes a `{?}` with a default and the work continues.

### 4.4 What is still theory

Designed and written down, not built: the `oc` syscall table (effects allowed by name, recording
reads and writes as Parts so replay plays the Part back), the Tick scheduler on the JavaScript
event loop, the compile relationship proven by equal digests, `px add <address>` verified by
replaying its shipped record, competition Ticks with proposals kept apart from facts, near hits
via approximate nearest neighbours over course-screenshot vectors, residue mining (SUBDUE over the
pixels no stage claimed), and the students' audience (below). Receipts as Parts and the studio's
run-record export are being built as this brief is written.

## 5. Progress so far

### 5.1 Landed, with receipts, in order

Day 1 (the experiment runs and its tests, mutation-checked); Day 2 (receipts, retain, fresh-process
replay, second experiment with zero program edits); Windows safety (digests ignore line endings,
kernel files LF, evidence regenerated, harness paths from their own location, child processes keep
SystemRoot); the landing protocol; the address validator and census (task 2); the Day 3 close-out
(task 0: the record contract says what both runtimes do, nested array cap identical in both,
`run_cached` derives hit or miss from counters); Day 3's own receipt (render page, materializer,
materials store); neat update; union merges; Mounts (task 11); four self-improvement branches
(tasks 4, 5, 7 landed, 9 refused by the gate); the Windows work from Sam's side (task 1: `neat
new` on Windows, a bit-portable fixture, the card server draining a 413 body; tasks 12, 13, 14, 16,
17, 18: `proof.sh`, `questions.sh`, a determinism oracle that survives a different interpreter,
the multi-record viewer); the painter port (task 19); the primitives miner (task 20); Astra's
package one. Roughly twenty-five landings, every one green on the whole suite (nine suites, about
five hundred tests) at the time it landed.

### 5.2 Decisions the owner made (resolved at the root)

Primary use is a cache under a five-second budget; pyto is a transfer of a proven design and
JavaScript is first class; a hit is any use of a Part or Calculation; the architecture reads as
ELK with the PCR as Kibana; subagents run on Opus, Sonnet or Haiku at high effort; CV is deferred
and DiscShelf plus OnTheCourse with many formats is the user demo; DiscStudio is the focus now;
the brain dump is the conversation; addressing goes by default (worlds are mounts, three roots);
renderers port to JavaScript and the site stays static; the record keeps its commit ("max
telemetry") and a stamp must name a landed commit; the kernel must be stable and explainable
because Sam writes services above it and does not want to know how it works; minimal hard stops,
everything lands on green, undo is the way back; the owner is interrupted for three reasons only.

### 5.3 Open questions and unresolved trade-offs

Ninety-one `{?}` entries exist; the ones that still change what gets built:

- **EverythingIsAPart**: receipts, packets, decisions and proposals as Parts under reserved
  segments, written only when visibility is on, never read by a Calculation. Being built.
- **TickEqualsReceipt**: keep testimony and receipt separate (the byte-identity guarantee) and
  join in the materializer. Current lean: keep separate.
- **SilentRules / ShadowRule**: Python silently rewrites a Part binding to a result reference and
  lets arguments shadow inputs; JavaScript fails loud. Lean: make Python loud.
- **PartialWritesOnFailure**: keep a failed Tick's earlier writes (ChainSpot) or roll back
  (Wumpus). Lean: keep and record.
- **UndoStack**: one field on the write receipt (the previous value) makes undo a query plus one
  Calculation; queued behind receipts as Parts.
- **MountSyntaxUnspecified**: nothing says how a mount is written beside an address in prose, a
  composition or the viewer.
- **HidingPrimitives**: the miner finds structural idioms, not leaf helpers; its scores are per
  round and its list is capped by iterations; it waits for receipts to mine real logs.
- **Students**: hashing makes the record a classroom guarantee ("show your work" made literal, a
  replay that proves a claim, identical digests as identical work, a port judged by a verifier),
  and personal Parts and Calculations per student would let a tutoring agent learn how each
  student learns from their own records: what they retry, where they write `{?}`, what they undo,
  how long each Tick takes them. Nothing built; after DiscStudio.
- The trade-off underneath several of these: speed versus visibility. The runtime strips
  observation to meet the budget; every feature that depends on receipts must cost nothing when
  they are off.

## 6. What is next

In order, everything landing on green with a line on the board:

1. Receipts as Parts (task 13, running) and the studio's run-record export (task 12, running).
2. The undo stack, built on the receipt's previous-value field.
3. The `oc` syscall table; then the primitives miner over real receipts.
4. Astra's package three: the remaining two formats (a share image for a round, a bag data
   export), same shape as package one; and Codex's task 3, neat anywhere.
5. Then, per the owner's order: users first; the CV cache returns after DiscStudio ships (near
   hits, residue mining, the compile relationship, `px add`).
6. A standing weekly critic whose only job is to say where the operating-system lens misled us.

## 7. Documents to ingest

All paths are relative to the repository root on branch
`claude/python-ultracode-supercharge-st8hnu` of `samuelpmahan/DiscStudio-staging`. The bundle
`haven-bundle.zip` that accompanies this brief contains every file listed.

- `pyto/BOARD.md`: the one page; the test, interrupts, the Today log, five lanes.
- `pyto/questions.md`: the `{?}` root, every decision and open question with status.
- `pyto/LANDING.md`: the landing protocol, neat, the explicability gate.
- `pyto/viewer/RECORD.md`: the run-record schema both runtimes speak.
- `pyto/research/from-registry-to-os.md`: the fifteen steps and the mapping table.
- `pyto/research/origin.md`: why PxC exists, in Sam's words.
- `pyto/research/ULTRACODE-WEEK.md`: the week's plan and its six reframings.
- `pyto/research/lab-transfer-ledger.md` and `tick-observability-ledger.md`: what was transferred
  from the three proven implementations and what a person can see per Tick in each.
- `pyto/research/chainspot-branch-mining.md`: what fourteen ChainSpot branches decided about
  addressing, the viewer, storage, receipts.
- `pyto/research/briefs/ASTRA.md`, `port-painter-to-js-brief.md`, `neat-on-pxc-brief.md`: the
  package briefs.
- `pyto/CHANGES.md`: the change log with reasons.
- Kernel sources: `pyto/src/pyto/core.py`, `pcr.py`, `pql.py`, `graph.py`, `mounts.py`,
  `address.py`, `materialize.py`.
- The JavaScript reference: `src/core/exec.js`, `src/runtime.js`; the viewer `pyto/viewer/*.js`.
- Scripts: `pyto/scripts/neat.sh`, `land.sh`, `check_all.sh`, `proof.sh`.
- A real record: `pyto/viewer/fixtures/pyto-grouped-ablation.json`; a real packet and hand-off:
  `pyto/experiments/tasks/19/`; a landing receipt: any `pyto/experiments/landings/*/receipt.json`.
- Mailbox archive: `mailbox/to-gpt/*.md`.
