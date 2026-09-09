# Day 2 brief (verbatim excerpts from research/ULTRACODE-WEEK.md at base d9dded6)

Copied by the record-stage agent per experiments/CAPTURE.md. Section boundaries:
"### Day 2" (plan line 162) up to "### Day 3" (line 186); critic amendments naming
Day 2: gaps 3, 4, 9, 10, 12, 14, 18a, 18d, 19; plus research/lab-transfer-ledger.md
"What this changes in the week" (the Day 2 paragraph).

## Day 2 section

### Day 2: Second experiment #1: re-group and re-input without reconstruction; fresh-process replay; first library seam (run observations)

**Goal.** Apply the Day 1 comparison procedure to a cross-cutting 3x5 grouping
and to a second input (new seed, n=800) by changing only input Parts and the
variants list; prove reuse validity by digest rather than by naming (split
digest equal across regroup, different across reinput); retain the program
declaratively with an explicit registry and replay it in a genuinely fresh
`python3 -I` process; land one library seam that gives testimony digests and
durations without changing the asdict(tick) shape consumers serialize.

**Deliverables.**

- Library seam (one change, gated by Day 1 tests): PCR.run(pxc, *, observe:
  bool = False) -> PcrRun; PcrRun gains `observations: Mapping[str,
  Observation]` (default empty) where Observation(result_sha256: str | None,
  duration_ms: float, effective_arg_keys: tuple[str, ...], shadowed_inputs:
  tuple[str, ...]) — result digest of json.dumps(value, sort_keys=True,
  separators=(',',':'), default=str) when serializable else None;
  CalculationTestimony and TickTestimony fields unchanged; tests/test_observations.py
  including a byte-equality test that json.dumps([asdict(t) for t in
  run.ticks]) is identical with observe on/off and identical to the pre-seam
  bytes retained on Day 1 for the fan-out example; 18 consumer tests,
  disc-stats 4, examples unchanged
- pyto/experiments/grouped-ablation/retain.py (experiment-local, NOT in
  pyto/src): to_program(pcr) -> {name, ticks:[{name,
  calculations:[{id, calculation, inputs:{name:'px:<addr>'|'fn:<id>'}, args,
  into}]}]} walking pcr.ticks[*].calculations[*] (Invocation imported from
  pyto.pcr since __init__ omits it); from_program(program, registry)
  rebuilding through PCR.calc so writer/id rules re-apply; retain_run(pxc,
  run, external_addresses) -> record {program, external:{addr: value |
  {digest, ref}} with non-JSON values written to a sidecar file,
  provider:{pyto version, sha256 of core.py/pcr.py, registry addresses +
  module source sha256}, results:{id: digest}}; missing registry address
  raises KeyError naming the address before any execution; feeding
  graph.Pcr.to_pcr_dict output to from_program is rejected (PCR and Pcr are
  not one format, stewardship:19)
- run_regrouped.py, run_reinput.py, run_from_retained.py (consumes run-1's
  retained split as an external Part, joins provenance to run-1's fn:split by
  digest, counts the skipped Prepare invocation's ms as saved); each writes
  evidence/run-{2-regroup,3-reinput,4-from-retained}/ with the Day 1 file set
  plus saved-work.json (Calculations inherited 5/5, added 0, program lines
  changed 0, input Parts changed 1, invocations skippable by digest, ms
  saved) and interpretation.md (cross-cutting grouping: no single drop
  exceeds +0.9 RMSE because each group holds at most two planted weights)
- replay.py + test_replay.py: subprocess [sys.executable, '-I', '-c', ...]
  with env stripped to PATH only, cwd outside the repo, imports only pyto +
  calculations.REGISTRY + retain, replays evidence/run-1/retained.json and
  asserts byte-identical comparison.json and result digests; the replay
  report dumps sys.path and sys.modules to prove no leakage; a tamper test
  edits one variant's columns in a copy and asserts only that fit and its
  score change; a registry-hole test removes 'fn.ablation.rmse' and asserts
  loud failure before execution; a determinism run repeats replay 5x under
  PYTHONHASHSEED=0..4 and against an LF-converted copy of src (src/pyto/*.py
  are CRLF) and records any digest drift as evidence/determinism.log
- experiments/runs/day2/ record; CHANGES.md started (empty semantic-flip
  section — the seam is additive)

**Workflow shape.** Fan out three lanes: (a) library seam,
characterization-first (write the failing observation test, then the field);
(b) retain.py exporter/importer/registry with 3 candidate schemas as scratch
(testimony-shaped; Pcr JSON-shaped; JS readPql-shaped from
src/core/exec.js:37-49) refuted by three lenses (round-trip equality with
post-JSON testimony; expressiveness for fn: refs and optional into; no code
leakage) — expected survivor: testimony-shaped; (c) regroup/reinput/from-retained
runs. Cross-verification gate: lane (c)'s outputs must be reproduced by lane
(b)'s fresh-process replay carrying lane (a)'s digests before any lane is
accepted. Adversarial verify: hidden-state auditor tries to make replay pass
through leaked state (mutating the registry dict after retain, pre-seeding
into Parts, exploiting results aliasing at pcr.py:162-164) and must be
defeated by the report; determinism auditor (hashseed x line endings);
shadow auditor plants an args key equal to a bound input and requires
retain.py to refuse at export naming the invocation; consumer-bytes auditor
diffs compositionEvidence bytes from test_art_backend before/after the seam.
Synthesize: saved-work ledgers written from measured numbers only; a critic
recomputes inherited-vs-added from program diffs and rejects prose counts.

**Verification.**

```sh
cd /home/user/DiscStudio-staging/pyto && python3 -m unittest discover -s tests -v   # includes test_observations; python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py' -v   # includes test_replay spawning python3 -I; python3 experiments/grouped-ablation/run_regrouped.py   # prints second ranking and 'split digest equal to run-1: True'; cd consumers/discstudio-card && mkdir -p data && python3 -m unittest discover -s . -p 'test_*.py'   # 18 OK; grep -c 'lambda\|<function' experiments/grouped-ablation/evidence/run-1/retained.json   # 0
```

**Evidence retained.** evidence/run-1/retained.json (+ sidecars if any);
evidence/run-{2,3,4}/ full sets with saved-work.json and interpretation.md;
evidence/replay/fresh-process.log (command line, sys.path, module list,
digest equality); evidence/tamper/, evidence/registry-hole.log,
evidence/determinism.log; tests/test_observations.py as the executable spec
of the seam; experiments/runs/day2/*.

**Depends on.** Day 1 (test_semantics.py as the gate for touching pcr.py;
program.py and calculations.REGISTRY as the retained objects; run-1
testimony bytes as the byte-equality oracle).

## Critic amendments naming Day 2

### Gap 3 (high): evidence would not survive scrutiny

**Gap.** Day 2 determinism auditor runs replay '5x under
PYTHONHASHSEED=0..4' with `python3 -I`; verified that -I ignores
PYTHONHASHSEED (hash_randomization stays 1, hashes differ per process).
determinism.log would show whatever randomization the OS gives, labelled as
seeded runs.

**Amendment.** Day 2 replay.py: keep `python3 -I` for the isolation replay,
and run the hashseed matrix with `env -i PATH=$PATH PYTHONHASHSEED=n python3
-s -P` (no -E), dumping sys.flags.hash_randomization and hash('pyto') into
determinism.log so the log proves the seed took effect; test_replay asserts
hash_randomization==0 in those rows.

### Gap 4 (high): prohibition the plan sets for itself is violated by schedule

**Gap.** Day 4 promotes compare.py into pyto/src with the gate 'both Day 3
and Day 4 called the experiment-local version successfully first' and 'the
experiment-local copy in grouped-ablation', but no Day 2 or Day 3 deliverable
creates or calls an experiment-local explain_changes; Day 3's 'kernel
meta-run' use is asserted only in Day 4's workflow prose. The plan's own
'land only after two experiment-local uses' rule is unmet on the schedule.

**Amendment.** Day 2: add grouped-ablation/compare_local.py (explain_changes
over program dicts + external digests) and use it in
run_reinput.py/run_from_retained.py to compute 'invocations skippable by
digest' and interpretation.md. Day 3: promotion's PromotionRefused report and
conventional-comparison's 'recomputation avoided on regroup rerun' call
compare_local. Day 4 gate then cites those two call sites by file:line.
Otherwise keep compare.py experiment-local and say so in the returns.

### Gap 9 (medium): underspecified dependency / prohibition tension

**Gap.** Fresh-process replay (Day 2 `python3 -I -c`, Day 4 fixture replay)
must import calculations.REGISTRY, retain, paint_components and the card
composer; under -I (which in 3.11 implies -P) neither cwd nor PYTHONPATH is
on sys.path, so the -c snippet must sys.path.insert the experiment/consumer
directory. The plan never says so, and worktree-workflow.md:17 forbids
'cross-repository sys.path injection' while Day 5 removes the /mnt/d line
for exactly that reason.

**Amendment.** Day 2 replay.py: the child receives the experiment directory
as argv and does one explicit, logged sys.path.insert of that intra-repo
directory; fresh-process.log records sys.path before and after; CAPTURE.md
distinguishes intra-repo registry path from cross-repository injection. Same
for Day 4's consumer replay.

### Gap 10 (medium): contradiction inside a day

**Gap.** Day 2 Observation.result_sha256 is 'json.dumps(value,
sort_keys=True, ..., default=str) when serializable else None'. With
default=str nothing is unserializable, so None never occurs and non-JSON
values (a PxC object, a dataclass with default repr) get a digest of their
repr — process-dependent for objects whose repr includes an address — which
the determinism auditor would then report as pyto-caused drift.

**Amendment.** Day 2 seam: no default=; catch TypeError/ValueError -> None;
the retain.py sidecar policy handles None-digest values. test_observations
adds a case with a non-JSON value asserting result_sha256 is None and a case
with tuple keys (disc-stats shape).

### Gap 12 (medium): required return lacks retained evidence (provenance lens would reject it)

**Gap.** Day 5 return G lists 'cross-PCR px: provenance loss' and
'disc-stats non-JSON values' as counterexamples, and the next-experiment
section cites 's3.build_investigation running without the corpus'. All three
rest on scratch probes (probe_rules.py P6, the disc-stats json.dumps
TypeError probe, probe_reference.py) that no day retains, so
generate_returns.py must either exit non-zero or cite files outside the
repo.

**Amendment.** Day 1 test_semantics.py: add
test_cross_pcr_consumer_records_px_not_fn (second PCR over the same PxC
records 'px:' — writers map is per PCR, pcr.py:118-123). **Day 2 retain
tests**: run
consumers/discstudio-card/experiments/disc-stats/run_experiment.build through
retain_run and assert external -> {digest, ref} sidecar and results digest
None, retained as evidence/disc-stats-sidecar.json. Day 5 (or Day 1 lane D):
retain probe_reference.py's synthetic S3 snapshot under
experiments/s3-synthetic/ with a unittest that s3.build_investigation runs
on it and records testimony inputs {'ledger': 'fn:accountRings'}
(s3.py:73-89), so the next-experiment proposal cites a retained file.

### Gap 14 (medium): prohibition/gate tension

**Gap.** docs/PYTHON-LAB-STEWARDSHIP.md:53: 'No Pyto implementation starts
until the consumer fixture establishes the calculation boundaries and the
owner confirms which presentation/config values are external inputs versus
calculation results.' Day 2's PcrRun.observations seam and Day 4's
compare.py both land in pyto/src before the owner answers
{?} ExternalInputBoundary; Day 4's gate cites the brief's promotion policy,
not this precondition.

**Amendment.** Day 2 and Day 4 workflow: the gate agent must cite
stewardship:53 and record why each seam is not 'the replay seam'
(observations: digests only, no boundary decision; compare: traversal over
retained data) — or keep compare.py experiment-local until the owner
answers. Add `{?} SeamGate` to open_judgments either way.

### Gap 18 (low): small accuracy issues the user will hit when running commands

**Gap.** (a) Day 2 verification `grep -c ... | # 0` exits 1 when the count
is 0, failing under set -e; (b) Day 1 saved-work.json hard-codes
'calculations_authored': 5 while the Day 2 critic 'rejects prose counts';
(c) Day 1 Lane A cites README.md line 20 — the manual invocation is on line
19; **(d) after the Day 2 seam, run.py's testimony.json = asdict(run) minus
results gains an 'observations' key, so run-2+ testimony files differ in
shape from run-1 while the byte oracle is defined on ticks only**; (e) Day 5
extract_substructures 'over the graph PCR.mermaid() emits' implies parsing
Mermaid text; (f) Day 5 'seed-manifest drift refreshed' overwrites a
retention record of the original source.

**Amendment.** (a) use `! grep -q`; (b) len(REGISTRY) and wc -l computed at
run time; (c) cite README.md:19; **(d) define testimony.json as {pcr, ticks}
and put observations in observations.json from Day 2**; (e) operate on the
retained program dict and assert node/edge sets equal what pcr.py:196-217
emits; (f) write seed-manifest-<sha>.json alongside rather than
overwriting, or record the overwrite in CHANGES.md.

### Gap 19 (low): opportunity from the maps not used and not refused

**Gap.** The neat map's one transferable idea — sequence-ordered
read/write/invocation receipts and a failed-run PcrRun instead of a raise
(pxc.ts:26-62, pql.ts:470-479) — is neither scheduled nor listed under
refused/open judgments; the observations seam covers digests and durations
only.

**Amendment.** Add `{?} Telemetry: read/write receipts and failed-run status
deferred; observations seam covers digests/durations only` to
open_judgments so the omission is a recorded decision, and let gap 13's
test_failure_mid_run_leaves_prior_writes be its characterization.

## research/lab-transfer-ledger.md: "What this changes in the week" — Day 2 paragraph

> **Day 2 seam** is the LAB Tick receipt, not an invented Observation:
> per-invocation duration, actual consumes/produces observed through a
> tracked PxC view, write kinds including `refinement`, calculation calls
> with input/output digests, and frozen-calculation identity (address +
> implementation hash with the ChessLab honesty fields `identityScope` and
> `limitation`). It stays in a new `PcrRun.receipts` mapping so consumer
> testimony bytes are unchanged (critic gap and judge 3 finding). Reference:
> chesslab contract.ts Receipt, wumpus execute.js.
>
> **Day 2 retain format** must be readable by the browser `readPql` grammar
> wherever the program has no fn: bindings, and the Day 5 parity check runs
> the same document through node exec.js and Python (the reader phase's
> 45-line port already produced byte-identical run records for a two-tick
> document with an override).

This is the transfer ledger's correction of the plan text above: the Day 2
library seam actually landed is `PcrRun.receipts` (`Receipt`,
`FrozenCalculation`, write kinds `new-address|refinement|replacement`)
transferred from `reference/lab/chesslab-lab/contract.ts` (Receipt,
FrozenCalculation, PxWriteTestimony) and `reference/lab/chesslab-lab/host.ts`
(receipt assembly from tracked access), with timing from
`reference/lab/wumpus-core/execute.js` (`executeTick`) and the tracked-view
write-kind rule from `/home/user/DiscStudio-staging/src/core/exec.js:22-33`
(`trackAccess`) — not the plan's originally sketched `Observation` type. No
file under `src/*.js` was edited; the JS files are read-only reference.

## Reference sources cited by name

- `pyto/reference/lab/chesslab-lab/contract.ts` — Receipt, FrozenCalculation,
  PxWriteTestimony kinds.
- `pyto/reference/lab/chesslab-lab/host.ts` — how a receipt is assembled from
  tracked access.
- `pyto/reference/lab/wumpus-core/execute.js`, `pxc.js` — per-invocation
  timing and transaction-derived actual consumes/produces.
- `/home/user/DiscStudio-staging/src/core/exec.js` — `trackAccess`, the
  write-kind classification (`new-address` / `refinement` / `replacement`).

## Hard rules for this day (as issued to the lanes)

Exactly ONE library change this day (the receipts seam in `pcr.py`, lane A
only); it must not change the bytes of
`json.dumps([asdict(t) for t in run.ticks])` for any program (consumers
embed those in `compositionEvidence`:
`pyto/consumers/discstudio-card/card_composition.py:177`,
`pyto/consumers/discstudio-card/app.py:53`). No pickled callables; no
lambdas in retained data or registries; retained data never claims to
contain executable code (`docs/PYTHON-LAB-STEWARDSHIP.md:39`). PQL
untouched. No edits to `/home/user/DiscStudio-staging/src/*.js`. Do not git
commit. New files LF. Use `python3 -m unittest` (no pytest). Cite file:line
for every claim. Every number in a ledger is computed at run time, never a
literal.
