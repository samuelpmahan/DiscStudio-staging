# Pyto Day 2 brief: second experiment, retain and replay, the receipts seam

This brief is written to be executed by any capable coding agent with no other context. It is
the same brief the reference run is executing. Start from the same commit so results compare.

## Bake-off rules

- Repository: `samuelpmahan/DiscStudio-staging`, branch `claude/python-ultracode-supercharge-st8hnu`.
- Base commit: `d9dded6`. Everything you need is in the repository at that commit. Read anything;
  write only under `pyto/`. Do not edit `src/*.js` or `index.html` (the browser app is out of scope).
- Environment: Python 3.11 or newer, `python3 -m pip install -e ./pyto[drawing]`, Node 22 for one
  optional check. No pytest; use `python3 -m unittest`. No network needed.
- Time box: one working session. Commit to a branch of your own; do not push to the base branch.
- Return: the list in "What to hand back". Every number in a ledger must be computed by code at
  run time and traceable to a file in your tree. Prose counts are rejected at scoring.

## What Pyto is, in the 30 seconds that matter

Pyto is a Python transfer of the LAB, a runtime already proven in three TypeScript/JavaScript
projects (ChainSpot computer vision, ChessLab, EmbodiedWumpusWorld). Learn the vocabulary from the
code, not from familiar concepts:

- **Part**: a semantic address (`Part("px.disc.art.svg")`). Identity is the address, never the value.
- **Calculation**: a named callable (`Calculation("fn.disc.render", fn)`) taking one args mapping.
  Addresses must start with `fn.`.
- **PxC**: the store. `set`/`get`/`has` by address, fail-loud on missing reads, plus a registry that
  rejects a different callable at a known address. It is the manipulable representation of the
  working domain; everything else is a view of it.
- **PCR** (uppercase, `pyto.pcr`): an executable composition. `pcr.calc(tick, calculation, id=,
  into=, args=, **inputs)` declares an invocation; `pcr.run(pxc)` executes ticks in first-mention
  order and returns a **PcrRun** whose `ticks` are testimony (id, calculation address, input
  references `px:<address>` or `fn:<id>`, literal args, published `into`) and whose `results` are
  the values by id.
- The one distinctive operation: when an invocation binds a Part that an earlier invocation in the
  same PCR publishes with `into`, the binding is rewritten at declaration time to that producer's
  result (`fn:<id>`). That is how twelve fit/score invocations share one `split` and the testimony
  proves it.
- **PQL**: a query over PxC values by exact address or prefix with a Python predicate. It cannot
  see Calculations, cannot traverse dependencies, cannot execute.
- **Pcr** (lowercase, `pyto.graph`): a non-executing graph authoring class that emits JSON and
  Mermaid. It is not the same format as PCR and must not be presented as one.

Silent rules you must respect rather than fix: literal `args` override a same-named bound input
without error; a ResultRef to a later id fails only at run; a failing calculation mid-run leaves
earlier `into` writes in the PxC. These are characterized in `pyto/tests/test_semantics.py`.

What exists at the base commit: `pyto/scripts/check_all.sh` runs every suite (library 43,
grouped-ablation 31, s3-synthetic 5, consumer 18, disc-stats 4, examples 2). The Day 1
experiment `pyto/experiments/grouped-ablation/` holds a synthetic grouped feature ablation (5 groups
x 3 features, leave-one-group-out) with an explicit `REGISTRY` of module-level Calculations,
`program.py` (`build_program`, `family()`), `run.py`, and retained evidence in `evidence/run-1/`
whose `comparison.json` ranking is drop_g3 > drop_g0 > drop_g1 and whose `testimony.json` is
exactly `{pcr, ticks}`.

## The proven reference

Read `pyto/research/lab-transfer-ledger.md`. The Day 2 library seam is a transfer of the LAB Tick
receipt, not a new design. Reference sources are copied under `pyto/reference/lab/`:
`chesslab-lab/contract.ts` (Receipt: declared vs actual consumes and produces, writes with kinds,
frozen calculations with an implementation hash and honest scope fields), `chesslab-lab/host.ts`
(exact-conformance failure), `wumpus-core/execute.js` and `pxc.js` (transactional tick, receipt
with input and output values, calculation calls), and this repository's `src/core/exec.js`
(`trackAccess` write kinds new-address, refinement, replacement).

## Goal

Answer the research question with evidence: does a second experiment reuse the first one's
grouping, execution shape and comparison procedure with measurable saved work, and can a
composition be retained declaratively and replayed in a genuinely fresh process? Land exactly one
library change on the way, the receipts seam, without changing a byte of the testimony consumers
already embed in their receipts.

## Deliverables

**A. The receipts seam** (the only change under `pyto/src`): `PCR.run(pxc, *, observe: bool =
False)`. `PcrRun` gains a trailing field `receipts: dict[str, Receipt]` defaulting to empty, keyed
by invocation id. `Receipt` is a frozen dataclass modelled on the ChessLab Receipt: invocation id;
`calculation` as a FrozenCalculation (address, `implementation_sha256` of the callable's source when
`inspect.getsource` works else None, `identity_scope='runtime-function-body'`, and the ChessLab
`limitation` string); `started_ms`, `duration_ms`; `declared_consumes` (bound Part addresses),
`declared_produces` (`into`); `actual_consumes`, `actual_produces` observed through a tracked view
of the PxC during that invocation (document that PCR.run performs these on the invocation's behalf);
`writes` with kind new-address, refinement (the address was among the invocation's bound Part
inputs) or replacement; `result_sha256` of `json.dumps(value, sort_keys=True,
separators=(',',':'))` with no `default=` (catch TypeError and ValueError and record None);
`effective_arg_keys` and `shadowed_inputs` (args keys that collided with bound input names,
recorded, not raised). `CalculationTestimony`, `TickTestimony`, `pcr`, `ticks`, `results` are
unchanged. Tests in `pyto/tests/test_receipts.py`, including byte equality of
`json.dumps([asdict(t) for t in run.ticks])` with observe on and off and against
`evidence/run-1/testimony.json`. Add `pyto/CHANGES.md` with before and after test names and a
note citing `docs/PYTHON-LAB-STEWARDSHIP.md:53` that this seam records digests and durations and
makes no external-input boundary decision.

**B. Retain, compare, document** (experiment-local, under `pyto/experiments/grouped-ablation/`):
`retain.py` with `to_program(pcr)` producing `{name, ticks:[{name, calculations:[{id,
calculation, inputs:{name:'px:<addr>'|'fn:<id>'}, args, into}]}]}`, `from_program(program,
registry)` rebuilding through `PCR.calc` so writer and id rules re-apply, a missing registry
address raising KeyError naming the address before any execution, an args key that shadows a bound
input refused at export naming the invocation, `graph.Pcr` JSON rejected with a message citing the
stewardship doc, and `retain_run(pxc, run, external_addresses)` producing `{program, external,
provider, results}` where non-JSON external values go to a digest-plus-reference sidecar file and
`provider` records the pyto version, source hashes of `core.py` and `pcr.py`, and registry
addresses with module source hashes. `compare_local.py` with `explain_changes(record_a,
record_b)` returning changed ids, a reason per id (digest, args, input, calculation, external),
downstream affected and unchanged upstream, by traversal over `fn:` references, plus
`consumers_of(program, ref)`; include the false-unchanged cases (args shadowing an input; unchanged
program with a changed external digest). `pql_document.py` with `to_pql_document(program)`
emitting the browser grammar `{PrincipleComponentRender, Ticks:[{name, Calculations:[{call,
with, args, into}]}]}` only when every binding is `px:` and every invocation has `into`, otherwise
raising with the first offending invocation; optionally prove node accepts it through
`src/core/exec.js` `readPql`. Write three candidate retained-program schemas as scratch under
`candidates/` and record why two lose. Retain the disc-stats run
(`pyto/consumers/discstudio-card/experiments/disc-stats/run_experiment.py`) and show its non-JSON
values go to the sidecar (`evidence/disc-stats-sidecar.json`).

**C. The second experiment**: `run_regrouped.py` (a cross-cutting grouping, 3 groups x 5
features), `run_reinput.py` (seed 11, n=800), `run_from_retained.py` (consumes run-1's retained
split as an external Part and counts the skipped Prepare invocations' time as saved). Change only
input Parts and the variants list. If `program.py` or `calculations.py` must change, stop and write
`evidence/run-2-regroup/RECONSTRUCTION-REQUIRED.md` saying exactly what had to change; that is the
primary result of the day, not a failure to hide. Each run writes the Day 1 file set plus
`retained.json`, `receipts.json` (separate from `testimony.json`), `saved-work.json` (Calculations
inherited and added, program lines changed measured by an actual diff, input Parts changed,
invocations skippable by digest from `explain_changes`, milliseconds saved) and `interpretation.md`.
Tests in `test_second_experiment.py`: split digest equal between run-1 and the regroup run,
different for the re-input run; rankings per run; ledger fields numeric; regeneration
deterministic except timings.

**D. Fresh-process replay**: `replay.py` and `test_replay.py`. Replay `evidence/run-1/retained.json`
in a subprocess `python3 -I -c ...` with the environment stripped to PATH, cwd outside the
repository, the experiment directory passed as argv and inserted into `sys.path` once with a log
line (intra-repository, which the run-record contract allows; cross-repository injection is not).
Assert byte-identical `comparison.json` rows and result digests versus run-1. Dump the command
line, `sys.path` before and after, and sorted module names into `evidence/replay/fresh-process.log`.
Tamper test (edit one variant's columns in a copy; only that fit and its score digests change).
Registry-hole test (remove `fn.ablation.rmse`; loud failure before execution). Determinism matrix:
`python3 -I` ignores PYTHONHASHSEED, so run hash-seed rows with `-s -P` and no `-E`, record
`sys.flags.hash_randomization` and `hash('pyto')` per row in `evidence/determinism.log`, and
assert digests equal across rows; add a row with an LF-converted copy of `pyto/src` (the sources are
CRLF) on PYTHONPATH. Any half of a check that cannot run must skip with a named reason, never pass
silently.

## Hard rules

- Exactly one library change (A). PQL untouched. No pickled callables, no lambdas in retained data or
  registries, no retained data claiming to contain executable code.
- Testimony bytes are the invariant: `json.dumps([asdict(t) for t in run.ticks])` must be
  identical before and after the seam for every program; consumer suites (18 and 4) and both
  examples must pass unchanged.
- Never enumerate feature subsets; leave-one-group-out and one cross-cutting regroup only.
- No memoization or dependency-aware caching: saved work is shown by digest equality and explicit
  seeding of retained Parts. Step 5 of the stewardship spec is an explanation, not a cache.
- Do not decide the external-input versus calculation-result boundary for the owner; mark it `{?}`.
- New files use LF line endings.

## Acceptance

```sh
cd pyto && bash scripts/check_all.sh          # every suite green, per-suite counts printed
python3 -m unittest discover -s tests -v     # includes test_receipts
python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py' -v   # includes test_replay spawning python3 -I
python3 experiments/grouped-ablation/run_regrouped.py   # prints the second ranking and 'split digest equal to run-1: True'
grep -c 'lambda\|<function' experiments/grouped-ablation/evidence/run-1/retained.json   # 0
git diff --stat d9dded6 -- pyto/src            # exactly pcr.py
```

## Kill criteria

- Regroup or re-input needs edits beyond input Parts and the variants list: record
  RECONSTRUCTION-REQUIRED and do not add a library feature to hide it.
- Fresh-process replay yields different digests from the same retained record because of pyto
  semantics (declaration-order rewrite, args override, aliasing): keep the retain format as a failed
  variant with an interpretation and say so in the return.
- The seam changes consumer testimony bytes: revert it the same day and record `{?} ObservationSeam`.

## What to hand back

- The commit range and `git diff --stat` against `d9dded6`.
- `check_all.sh` output with per-suite counts (before and after).
- `evidence/run-1/retained.json`, `evidence/run-2-regroup/`, `run-3-reinput/`,
  `run-4-from-retained/` with `saved-work.json` and `interpretation.md`.
- `evidence/replay/fresh-process.log`, `evidence/tamper/`, `evidence/registry-hole.log`,
  `evidence/determinism.log`.
- `pyto/CHANGES.md` and a `questions.md` listing every open judgment as `{?} Label: detail`,
  including SeamGate (why this seam is not the replay seam) and Telemetry (failed-run receipts are
  deferred).
- One paragraph: what the second experiment inherited, what it had to add, and the measured saved
  work, with the file each number comes from.

## Scoring the bake-off

Score each run 0 to 3 per criterion; anchor 3 means the owner could verify it by running one
command and reading one file.

| Criterion | 0 | 3 |
|---|---|---|
| Reuse evidence | second experiment re-authored the program | zero program edits, split digest equal on regroup, ledger numbers computed |
| Testimony invariance | ticks bytes changed | byte-equality test against run-1 passes, consumer suites unchanged |
| Replay honesty | replay in the same process | `python3 -I`, stripped env, cwd outside repo, sys.path logged, tamper and registry-hole tests |
| Determinism audit | hash-seed rows run under `-I` (seed ignored) | rows prove `hash_randomization == 0`, digests equal, LF row recorded |
| Transfer fidelity | receipt fields invented | receipt mirrors the ChessLab Receipt and Wumpus executeTick fields, with the honesty strings |
| Prohibitions | pickled callables, PQL changed, second library change | one change under `pyto/src`, no code in retained data |
| Killable tests | tests that pass against a mutated library | each new test names a one-line mutation that fails it |
| Owner legibility | numbers in prose | every number in a ledger or interpretation resolves to a retained file |

Compare the two trees by running each other's replay against each other's retained record; a
retain format that the other side can replay is the strongest evidence either side can produce.
