# Pyto Day 2 brief: second experiment, retain and replay, the receipts seam

Version 2. Revised after two independent cold reads found five load-bearing errors and about
twenty under-specifications in version 1; the corrections are folded in below and the reader
reports are retained at `pyto/experiments/runs/day2/brief-cold-read.json`.

This brief is written to be executed by any capable coding agent with no other context. It is the
same brief the reference run is executing. Start from the same commit so results compare.

## Bake-off rules

- Repository: `samuelpmahan/DiscStudio-staging`, branch `claude/python-ultracode-supercharge-st8hnu`.
- Base commit: `d9dded6`. The brief itself is not in that commit; take it from `d80ec56` or later at
  `pyto/research/briefs/day2-brief.md`. This brief is the specification. `pyto/research/ULTRACODE-WEEK.md`
  (Day 2 section) and `pyto/experiments/runs/day1/prompt.md` are optional context; where they
  conflict with this brief, the brief wins.
- Read anything; write only under `pyto/`. Do not edit `src/*.js` or `index.html`.
- Environment: Python 3.11 or newer, Node 22 for one optional check, no network. Install the
  library editable **from your own checkout**: from the repository root,
  `python3 -m pip install -e './pyto[drawing]'`. Then confirm
  `python3 -c "import pyto; print(pyto.__file__)"` prints a path inside your checkout's `pyto/src`.
  The test runner, the examples and the fresh-process replay all import the installed package, so an
  editable install pointing at another tree silently tests someone else's library.
- Before writing anything, run `bash pyto/scripts/check_all.sh` and confirm every suite is green:
  library 43, grouped-ablation 31, s3-synthetic 5, consumer 18, disc-stats 4, examples 2. If
  grouped-ablation fails on `commit.txt`, your working copy is not a git checkout.
- No pytest; use `python3 -m unittest`.
- Time box: one working session. Commit to a branch of your own; do not push to the base branch.
- Return the list under "What to hand back". Every number in a ledger must be computed by code at
  run time and traceable to a file in your tree. Prose counts are rejected at scoring.

## What Pyto is, in the thirty seconds that matter

Pyto is a Python transfer of the LAB, a runtime already proven in three TypeScript and JavaScript
projects (ChainSpot computer vision, ChessLab, EmbodiedWumpusWorld). Learn the vocabulary from the
code, not from familiar concepts:

- **Part**: a semantic address (`Part("px.disc.art.svg")`). Identity is the address, never the value.
- **Calculation**: a named callable (`Calculation("fn.disc.render", fn)`) taking one args mapping.
  Addresses must start with `fn.`.
- **PxC**: the store. `set`, `get`, `has` by address, fail-loud on a missing read, plus a registry
  that rejects a different callable at a known address. It is the manipulable representation of the
  working domain; everything else is a view of it.
- **PCR** (uppercase, `pyto.pcr`): an executable composition. `pcr.calc(tick, calculation, id=,
  into=, args=, **inputs)` declares an invocation; `pcr.run(pxc)` executes ticks in first-mention
  order and returns a **PcrRun** whose `ticks` are testimony (id, calculation address, input
  references `px:<address>` or `fn:<id>`, literal args, published `into`) and whose `results` are
  the values by id.
- The one distinctive operation: when an invocation binds a Part that an earlier invocation in the
  same PCR publishes with `into`, the binding is rewritten at declaration time to that producer's
  result (`fn:<id>`), and the authored Part is not kept on the invocation. In the Day 1 program
  thirteen of fifteen invocations bind only results; only `select` and `split` bind Parts.
- **PQL**: a query over PxC values by exact address or prefix with a Python predicate. It cannot
  see Calculations, cannot traverse dependencies, cannot execute.
- **Pcr** (lowercase, `pyto.graph`): a non-executing graph authoring class that emits JSON and
  Mermaid. It is not the same format as PCR and must not be presented as one.

Silent rules you must respect rather than fix: literal `args` override a same-named bound input
without error; a ResultRef to a later id fails only at run; a failing calculation mid-run leaves
earlier `into` writes in the PxC. They are characterized in `pyto/tests/test_semantics.py`.

What exists at the base commit: the Day 1 experiment `pyto/experiments/grouped-ablation/` holds a
synthetic grouped feature ablation (5 groups x 3 features, leave-one-group-out) with an explicit
`REGISTRY` in `calculations.py` of five module-level Calculations (`fn.ablation.selectVariants`,
`fn.ablation.split`, `fn.ablation.fit`, `fn.ablation.score`, `fn.ablation.compare`), `program.py`
(`build_program`, `family()`), `run.py` (`--out` resolves relative to the experiment directory, not
the cwd; a non-empty `--out` is refused without `--force`; `write_evidence` writes exactly nine
files and `saved_work` deliberately carries no reuse counts, both pinned by tests), and retained
evidence in `evidence/run-1/` (`comparison.json` ranking drop_g3 > drop_g0 > drop_g1, then drop_g4
and drop_g2 as uninformative; `testimony.json` exactly `{pcr, ticks}` dumped with `indent=2,
sort_keys=True`). There is no `retained.json` or `receipts.json` at the base; Day 2 creates them.
Sources under `pyto/src/pyto/` are CRLF; everything else is LF.

## The proven reference

Read `pyto/research/lab-transfer-ledger.md`. The Day 2 library seam is a transfer of the LAB Tick
receipt, not a new design. Reference sources are copied under `pyto/reference/lab/`:
`chesslab-lab/contract.ts` (Receipt with declared versus actual consumes and produces, writes with
kinds, frozen calculations with an implementation hash and honest scope fields), `chesslab-lab/host.ts`
(exact-conformance failure), `wumpus-core/execute.js` and `pxc.js` (transactional tick, receipts with
input and output values, calculation calls), and this repository's `src/core/exec.js`
(`trackAccess`: a write is a refinement when the address existed and is among the tick's declared
consumes).

## Goal

The main use of PxC is as a cache for a computer-vision pipeline that must parse a phone-size disc
golf course screenshot within a 5000 ms budget. Every millisecond of recomputation avoided and every
digest-proven reuse in this experiment is the accounting that budget needs; the receipts' durations
and the reuse ledger exist for it. The synthetic fixture's timings say nothing about the browser or
about image-sized Parts; label them as synthetic wall time and never extrapolate to the target.

Answer the research question with evidence: does a second experiment reuse the first one's
grouping, execution shape and comparison procedure with measurable saved work, and can a
composition be retained declaratively and replayed in a genuinely fresh process? Land exactly one
library change on the way, the receipts seam, without changing a byte of the testimony consumers
already embed in their receipts.

## Deliverables

### A. The receipts seam (the only change under `pyto/src`)

`PCR.run(pxc, *, observe: bool = False)`. `PcrRun` gains a trailing field
`receipts: dict[str, Receipt] = field(default_factory=dict)`, keyed by invocation id (ids are unique
per PCR), empty when `observe` is False. The new types are defined in `pyto/src/pyto/pcr.py` and are
**not** added to `pyto/src/pyto/__init__.py` this day (the acceptance diff must show `pcr.py` alone;
tests import `from pyto.pcr import Receipt, FrozenCalculation, WriteTestimony`; record the export as
`{?} ReceiptExport`). `pcr.py` stays CRLF; new lines in it use CRLF.

```python
@dataclass(frozen=True, slots=True)
class FrozenCalculation:
    address: str
    implementation_sha256: str | None   # sha256(inspect.getsource(fn).encode('utf-8')); None on TypeError or OSError
    identity_scope: str = "runtime-function-body"
    limitation: str = "called helpers, constants, templates, and assets are not covered"

@dataclass(frozen=True, slots=True)
class WriteTestimony:
    address: str
    kind: str   # 'new-address' | 'refinement' | 'replacement'

@dataclass(frozen=True, slots=True)
class Receipt:
    id: str
    calculation: FrozenCalculation
    started_ms: float                    # time.time() * 1000
    duration_ms: float                   # perf_counter delta * 1000, rounded to 3 places
    declared_consumes: tuple[str, ...]   # 'px:<addr>' | 'fn:<id>' in binding order, mirroring testimony inputs
    declared_produces: tuple[str, ...]   # (into,) or ()
    actual_consumes: tuple[str, ...]     # PxC addresses PCR.run read for this invocation (px: bindings only)
    actual_produces: tuple[str, ...]     # PxC addresses PCR.run wrote for this invocation
    writes: tuple[WriteTestimony, ...]
    result_sha256: str | None            # sha256 of json.dumps(value, sort_keys=True, separators=(',',':')).encode('utf-8'); no default=; None on TypeError or ValueError
    effective_arg_keys: tuple[str, ...]  # sorted keys of the mapping handed to the callable, resolved inputs included
    shadowed_inputs: tuple[str, ...]     # sorted(set(literal args) & set(resolved inputs)); recorded, never raised
```

Be honest about what is observed. `PCR.run` resolves every binding itself and hands the callable a
plain mapping, so the callable never touches the PxC. The tracked view therefore wraps the reads and
writes `PCR.run` performs on the invocation's behalf; under this calling convention `actual_*`
equals the `px:` subset of `declared_*` by construction, no conformance check is implemented this
day, and the receipt docstring says so. That is the exact finding the transfer ledger records as
"Absent" for exact conformance; recording it is the point. The `refinement` kind is computed in
`pcr.py` from the `PxWrite` that `PxC.set` returns (core.py is not touched): `replacement` becomes
`refinement` when the address is among that invocation's bound Part addresses. It is reachable only
when one invocation binds `Part('px.a')` and writes `into='px.a'` over a pre-seeded value; that is
the fixture for the test.

`CalculationTestimony`, `TickTestimony`, `pcr`, `ticks` and `results` are unchanged. The guard at
`pyto/tests/test_semantics.py:535` pins `PcrRun`'s field tuple and must be updated to
`('pcr', 'ticks', 'results', 'receipts')` as part of A; its intent (no run id or timestamp on
`PcrRun` itself) is preserved because `receipts` defaults to empty. The sibling guard on `PxWrite`
stays untouched.

Tests in `pyto/tests/test_receipts.py`, each docstring naming the one-line mutation that kills it:

- byte equality of `json.dumps([asdict(t) for t in run.ticks])` with `observe` on and off within one
  process for the Day 1 program (`program.build_program` over the same variants and seed `run.py`
  uses);
- structural equality with the retained testimony: `json.loads(read('evidence/run-1/testimony.json'))['ticks']
  == json.loads(json.dumps([asdict(t) for t in run.ticks]))` (the file is indented and key-sorted, so
  a literal byte comparison against it is impossible);
- `receipts == {}` when `observe` is False;
- a set value and a PxC object give `result_sha256 is None`; tuple keys (the disc-stats shape) give None;
- new-address, replacement and refinement each exercised, refinement through the fixture above;
- `shadowed_inputs` recorded for the args-override case and `effective_arg_keys` includes the resolved
  input names;
- `implementation_sha256` stable across two runs and None for a builtin (`inspect.getsource(len)`
  raises TypeError);
- `duration_ms >= 0`, `started_ms` within a second of `time.time() * 1000`.

`pyto/CHANGES.md`: the seam entry lists the test names added (`test_receipts.py`), any existing test
whose assertion changed (expected: only the field-tuple guard), and the before and after
`Ran N tests` line per suite; it cites `docs/PYTHON-LAB-STEWARDSHIP.md:54` (step 2, retaining program,
bound inputs, result identities, provider identity, selected result hashes) and `:56` (the owner's
external-input boundary decision) to say that this seam records digests and durations and makes no
boundary decision, and `:57` (step 5) to say it is an explanation, not a cache.

### B. Retain, compare, document (experiment-local, under `pyto/experiments/grouped-ablation/`)

**`retain.py`.** `to_program(pcr)` produces
`{name, ticks:[{name, calculations:[{id, calculation, inputs:{name:'px:<addr>'|'fn:<id>'}, args, into}]}]}`
walking `pcr.ticks[*].calculations[*]` (`Invocation` is importable from `pyto.pcr`).
`from_program(program, registry)` rebuilds through `PCR.calc` so writer and id rules re-apply; a
missing registry address raises `KeyError` naming the address before any invocation is declared; an
args key that shadows a bound input is refused at export with the invocation id; a `graph.Pcr`
`to_pcr_dict()` document (its `with` values are `{kind, ref}` objects) is rejected with a message
citing `docs/PYTHON-LAB-STEWARDSHIP.md:19`. `retain_run(pxc, run, external_addresses)` produces
`{program, external, provider, results}`: `external` maps each external address to its JSON value, or
to `{sha256, ref}` when the value is not JSON-serializable, with the value's `repr` written to
`evidence/sidecar/<address>.txt` and the digest taken over those bytes; `provider` records
`importlib.metadata.version('pyto-lab')` (there is no `pyto.__version__`), sha256 of the raw bytes of
`pyto.core.__file__` and `pyto.pcr.__file__` as resolved at run time, and the registry addresses with
the sha256 of each callable's module source; `results` maps each invocation id to
`{sha256: str | None}` using the same canonicalization as `Receipt.result_sha256`, never values.
Retained data never contains executable code.

**`compare_local.py`.** `explain_changes(record_a, record_b)` returns `{changed:[ids],
reason:{id: 'digest'|'args'|'input'|'calculation'|'external'}, downstream_affected:[ids],
unchanged_upstream:[ids]}` by traversal over `fn:` references in the program dict, plus
`consumers_of(program, ref)`. Tests include the false-unchanged cases: an args key shadowing an
input, and an unchanged program with a changed external digest, both reported as changed.

**`pql_document.py`.** `to_pql_document(program)` emits the browser grammar
`{PrincipleComponentRender, Ticks:[{name, Calculations:[{call, with, args, into}]}]}` with the `px:`
prefix stripped so `with` values are bare addresses as `src/core/exec.js` `readPql` requires; it
succeeds only when every binding is `px:` and every invocation has `into`, otherwise raising
`PqlDocumentError` naming the first offending invocation. The Day 1 program is the negative case (it
raises on the first `fn:` binding). The positive fixture is a two-invocation px-only program built in
the test, each invocation binding a distinct seeded Part with an `into`. Optional node check:
`candidates/readpql_check.mjs` imports `readPql` from `src/core/exec.js` with `JSON.parse` as the
parser and asserts the positive document is accepted and every `with` value is a seeded address; skip
with the named reason if node is absent.

**Candidates.** Write three retained-program schema candidates as scratch under `candidates/`
(testimony-shaped; `graph.Pcr` JSON-shaped; browser `readPql`-shaped) and record in
`candidates/README.md` why two lose against three lenses: round-trip equality with the post-JSON
testimony, expressiveness for `fn:` references and optional `into`, and no code leakage.

**Disc-stats retention.** `retain_disc_stats.py` under grouped-ablation performs one logged
`sys.path.insert` of `pyto/consumers/discstudio-card/experiments/disc-stats/` (intra-repository,
which the run-record contract allows), imports `stats`, reconstructs the same PxC and PCR that
`run_experiment.py` builds (read it and re-declare its `annotate` function and fixture in the
harness; do not import or modify it, it executes and prints at import), and writes
`evidence/disc-stats-sidecar.json` proving the non-JSON values (tuple keys in the mold counts, date
objects in the observations) went to the sidecar and the results digest is None.

### C. The second experiment

Permitted change surface, by file: `program.py` and `calculations.py` must stay byte-identical to the
base (`git diff d9dded6 -- <file>` empty). `features.py` and `run.py` may gain parameters (a `groups`
argument, `--observe`) as long as the Day 1 31 tests pass unchanged, which means `write_evidence`
still returns exactly the nine Day 1 files and `saved_work` still carries no reuse counts. Day 2 files
are written by a new experiment-local writer (`evidence_writer.py`) that calls `write_evidence` for the
nine and then adds `retained.json`, `receipts.json` (separate from `testimony.json`),
`reuse-ledger.json` (the Day 2 ledger, a distinct file from run.py's `saved-work.json`) and
`interpretation.md`. Regenerate run-1 through that writer with `--out <absolute path to evidence/run-1>
--force` and assert that `testimony.json`, `comparison.json`, `variants.json`, `failed-variants.md` and
`mermaid.mmd` come back byte-identical; `commit.txt`, `timings.json` and `saved-work.json` are
expected to change.

- `run_regrouped.py`: a cross-cutting grouping of 3 groups x 5 features, each group holding at most
  two planted weights, passed as the `groups` parameter; variants from `fn.ablation.selectVariants`.
- `run_reinput.py`: seed 11, n = 800, the Day 1 grouping.
- `run_from_retained.py`: builds its PCR with `retain.from_program` over run-1's retained program
  with the Prepare tick's invocations removed and `scratch.ablation.split` seeded from run-1's
  retained external value. This is a variants-list and input change, not a `program.py` edit, and does
  not trigger the kill criterion. Saved milliseconds are the `duration_ms` of `select` and `split` in
  run-1's `receipts.json`.

If `program.py` or `calculations.py` must change, stop and write
`evidence/run-2-regroup/RECONSTRUCTION-REQUIRED.md` saying exactly what had to change. That is the
primary result of the day, not a failure to hide.

The new run scripts resolve a relative `--out` against their own directory, like `run.py`, with
defaults `evidence/run-2-regroup`, `evidence/run-3-reinput`, `evidence/run-4-from-retained`.
`reuse-ledger.json` records: Calculations inherited and added (from registry addresses), program lines
changed (an actual diff of `program.py` and `calculations.py` against the base, expected 0), input
Parts changed, invocations skippable by digest (from `explain_changes` against run-1's record), and
milliseconds saved. `interpretation.md` states, from `comparison.json` numbers, whether the
cross-cutting grouping produces any drop above +0.9 RMSE and why, and takes the fixture size from `n`.
Tests in `test_second_experiment.py`: split digest equal between run-1 and run-2-regroup, different
for run-3-reinput; ranking assertions per run; ledger fields present and numeric; regeneration
deterministic except timings.

### D. Fresh-process replay

`replay.py` and `test_replay.py`. The child contract: `[sys.executable, '-I', '-c', SNIPPET,
experiment_dir, retained_json_path, registry_module_name]` with `env={'PATH': os.environ['PATH']}` and
`cwd` a temporary directory outside the repository. The child performs one explicit
`sys.path.insert(0, experiment_dir)` and logs it (intra-repository; cross-repository injection is
forbidden), imports `pyto`, the registry module and `retain`, replays with `observe=True`, and prints
exactly one JSON object on stdout: `{results: {id: sha256}, comparison_rows: [...], pyto_file,
sys_path_before, sys_path_after, modules}`. The parent parses stdout and asserts byte-identical
`comparison.json` rows and result digests versus run-1, and writes the command line and the child's
JSON to `evidence/replay/fresh-process.log`.

State the isolation honestly: the child imports `pyto` through the editable install's `.pth`, which
points into the repository, so `-I` and the stripped environment isolate the child from the
experiment package, the cwd and the environment, not from the library tree. `replay.py` asserts
`pyto_file` starts with your checkout's `pyto/src` and skips with a named reason otherwise; record
`{?} ReplayIsolation` in `questions.md`.

- Tamper test: copy `retained.json`, edit one variant's columns; the changed digests are exactly
  `{fit.<key>, score.<key>, compare}` (compare consumes all six scores, so its inclusion is the point:
  it is the `downstream_affected` set `explain_changes` must also report) and `unchanged_upstream` is
  `{select, split}` plus the other ten fit and score ids. Evidence under `evidence/tamper/`.
- Registry-hole test: remove `fn.ablation.score` from the registry handed to `from_program`; it
  raises `KeyError` naming the address before any invocation is declared. Evidence in
  `evidence/registry-hole.log`.
- Determinism matrix, `evidence/determinism.log`, one row per line with argv, env keys,
  `sys.flags.hash_randomization`, `hash('pyto')`, `pyto.__file__` and the result digests:

| Row | argv | env | assertion |
|---|---|---|---|
| replay | `python3 -I -c` | `{PATH}` | digests equal run-1 |
| hash n = 0..4 | `python3 -s -P -c` (no `-E`, no `-I`: `-I` ignores PYTHONHASHSEED) | `{PATH, PYTHONHASHSEED=n}` | `hash_randomization` is 0 for n = 0 and 1 otherwise, `hash('pyto')` differs across n, digests equal across rows |
| LF copy | `python3 -s -P -c` | `{PATH, PYTHONHASHSEED=0, PYTHONPATH=<LF-converted copy of pyto/src>}` | `pyto.__file__` inside the LF copy (else skip with reason); result digests equal; provider source hashes differ (raw bytes, expected); `implementation_sha256` equal (`inspect.getsource` is line-ending invariant) |

Any half of a check that cannot run must skip with a named reason, never pass silently.

## Hard rules

- Exactly one library change (A). PQL untouched. No pickled callables, no lambdas in retained data
  or registries, no retained data claiming to contain executable code.
- Testimony bytes are the invariant: `json.dumps([asdict(t) for t in run.ticks])` must be identical
  with `observe` on and off for every program, and the consumer suites (18 and 4) and both examples
  must pass unchanged.
- Never enumerate feature subsets; leave-one-group-out and one cross-cutting regroup only.
- No memoization or dependency-aware caching: saved work is shown by digest equality and explicit
  seeding of retained Parts. Stewardship step 5 is an explanation, not a cache.
- Do not decide the external-input versus calculation-result boundary for the owner; mark it `{?}`.
- New files use LF line endings; `pcr.py` stays CRLF.

## Output locations

All evidence paths above are relative to `pyto/experiments/grouped-ablation/`. `CHANGES.md` and
`questions.md` live at `pyto/CHANGES.md` and `pyto/questions.md`.

## Acceptance

```sh
python3 -c "import pyto; print(pyto.__file__)"       # inside YOUR checkout's pyto/src
cd pyto && bash scripts/check_all.sh                  # before: 43/31/5/18/4/2 OK; after: green, new suites listed
python3 -m unittest discover -s tests -v              # includes test_receipts
python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py' -v   # includes test_replay spawning python3 -I
python3 experiments/grouped-ablation/run_regrouped.py # prints the second ranking and 'split digest equal to run-1: True'
! grep -q 'lambda\|<function' experiments/grouped-ablation/evidence/run-1/retained.json
git -C .. diff --stat d9dded6 -- pyto/src             # exactly pcr.py
git -C .. diff d9dded6 -- pyto/experiments/grouped-ablation/program.py pyto/experiments/grouped-ablation/calculations.py   # empty
```

## Kill criteria

- Regroup or re-input needs edits to `program.py` or `calculations.py`: record RECONSTRUCTION-REQUIRED
  and do not add a library feature to hide it.
- Fresh-process replay yields different digests from the same retained record because of pyto
  semantics (declaration-order rewrite, args override, aliasing): keep the retain format as a failed
  variant with an interpretation and say so in the return.
- The seam changes consumer testimony bytes: revert it the same day and record `{?} ObservationSeam`.

## What to hand back

- The commit range and `git diff --stat d9dded6`.
- `check_all.sh` output before and after, including its printed `pyto module:` line.
- `evidence/run-1/{retained.json, receipts.json}`; `evidence/run-2-regroup/`, `run-3-reinput/`,
  `run-4-from-retained/` with `reuse-ledger.json` and `interpretation.md`.
- `evidence/replay/fresh-process.log`, `evidence/tamper/`, `evidence/registry-hole.log`,
  `evidence/determinism.log`, `evidence/disc-stats-sidecar.json`.
- `pyto/CHANGES.md` and `pyto/questions.md` listing every open judgment as `{?} Label: detail`,
  including SeamGate (why this seam is not the replay seam), ReceiptExport, ReplayIsolation, and
  Telemetry (failed-run receipts are deferred).
- One paragraph: what the second experiment inherited, what it had to add, and the measured saved
  work, with the file each number comes from.

## Scoring the bake-off

Score each run 0 to 3 per criterion; anchor 3 means the owner could verify it by running one
command and reading one file.

| Criterion | 0 | 3 |
|---|---|---|
| Reuse evidence | second experiment re-authored the program | `program.py` and `calculations.py` byte-identical, split digest equal on regroup, ledger numbers computed |
| Testimony invariance | ticks bytes changed | observe on/off byte-equal, structural equality with run-1 testimony, consumer suites unchanged |
| Replay honesty | replay in the same process | `python3 -I`, stripped env, cwd outside repo, one logged sys.path insert, `pyto_file` recorded, tamper and registry-hole tests |
| Determinism audit | hash-seed rows run under `-I` so the seed was ignored | matrix records `hash_randomization` per row (0 only for seed 0), digests equal across rows, LF row asserts `pyto.__file__` |
| Transfer fidelity | receipt fields invented | receipt matches the dataclass above, honesty strings present, docstring states what `actual_*` observes |
| Prohibitions | pickled callables, PQL changed, second library change | one file under `pyto/src`, no code in retained data |
| Killable tests | tests that pass against a mutated library | each new test names a one-line mutation that fails it |
| Owner legibility | numbers in prose | every number in a ledger or interpretation resolves to a retained file |

Compare the two trees by running each other's replay against each other's retained record; a
retain format that the other side can replay is the strongest evidence either side can produce.
