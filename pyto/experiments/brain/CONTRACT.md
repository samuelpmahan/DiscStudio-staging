# PxC brain: the contract every vertical builds against

The owner's brief (2026-09-11), verbatim where it matters: "give PxC a brain.
Build the complete computational intelligence layer as native PxC: every
statistics, machine learning, and data-science capability worth having, as
Calculations, on a backend fast enough to deserve them. numpy/scipy are in.
Maximum augmented surface. GO WILD. This is deliberately too big and too wide —
you will not finish, and that is expected." Lanes, non-negotiable: "Parts in,
Parts out ... everything lives in the store, nothing important in /tmp or chat.
Everything lowercase (proposal.* / px.exp.*) with its `for`. Nothing gets
promoted tonight. Use PQL to navigate what you're building. Findings are
first-class." Done for tonight: "1. The territory map ... as Parts in the
store, readable via PQL. 2. The foundation: every calculation, branch,
benchmark, oracle — all lowercase, all with receipts. 3. The direction:
findings list — backend needs, PQL needs, next tasks, each with its `for`."

## The repository and neat

- MAIN is `/home/user/DiscStudio-staging`, branch `claude/os-sprint-st8hnu`.
  Every landing goes through neat; a task is `bash pyto/scripts/neat.sh new
  "<intent>" --verify "<cmd>" --allow "<paths>"` run FROM MAIN; it makes the
  copy `EXP/<id>` (a git worktree with its own `.venv`). Work only inside your
  copy. `bash pyto/scripts/neat.sh update <id>` (from MAIN) brings MAIN's newer
  landings in. Pack with `bash pyto/scripts/neat.sh pack <id>` (from MAIN),
  land with `flock $S/land.lock bash $S/land_one.sh <id> $S/sprint-landings.log`
  where `S=/tmp/claude-0/-home-user-DiscStudio-staging/c7ad5950-a39c-58bb-9747-e1301075cf94/scratchpad`
  (serial by design; it re-verifies in the copy after an update, packs, lands,
  pushes). Read `pyto/USE.md` sections 1-6 and `pyto/LANDING.md` first: the
  kernel (`Part`, `PxC`, `Calculation`, `PCR`, `Tick`, `PcrRun(observe=True)`,
  `PQL`) and the landing rules. Kernel source: `pyto/src/pyto/`.
- Verify for brain tasks: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'`.
  Allow: `pyto/experiments/brain pyto/experiments/tasks` (the harness task also
  `pyto/scripts/check_all.sh pyto/pyproject.toml pyto/scripts/neat.sh`).
- numpy and scipy: MAIN's `.venv` has them. The harness task declares the
  extra `brain = ["numpy", "scipy"]` in `pyto/pyproject.toml` and makes `neat
  new` install `-e "pyto[drawing,brain]"` into a copy's venv (neat.sh line
  ~166 installs `[drawing]` today). `check_all.sh` discovers every
  `experiments/*/test_*.py` on its own, so the brain suite registers itself.
  Until the extra lands, a copy's venv needs `EXP/<id>/.venv/bin/pip install numpy scipy`.
- MAIN commits are serialised by one lock: run `neat new`, `neat pack` and the
  landing under `flock $S/land.lock ...` (the landing script already does);
  a `neat new` or `pack` outside the lock can collide with a landing's commit.

## Where things live

```
pyto/experiments/brain/
  CONTRACT.md            this page (the harness task copies it in)
  harness.py             the shared harness (below)
  map.py                 python -m ... prints the territory through PQL
  stats/    ml/    backend/    data/     one package per vertical, each with test_*.py
  store/<vertical>.json  the vertical's Parts, persisted (address -> value), merged by harness.load_store()
  records/<name>.json    run records (pyto.materialize.write_record) for every PCR run
```

Verticals do not edit each other's directories. `harness.py` is owned by the
backend vertical; anyone needing a harness change proposes it as a finding and
routes around it.

## Addresses (all lowercase, all with `for`)

| Part | address | value |
|---|---|---|
| dataset | `px.exp.brain.data.<name>` | `{"for": ..., "columns": [...], "rows": [[...]]}` or `{"for": ..., "shape": [n, m], "values": [[...]]}`; JSON-able only, so records and digests work |
| calculation result | `px.exp.brain.result.<vertical>.<calc>.<case>` | whatever the Calculation returns, JSON-able |
| oracle | `px.exp.brain.oracle.<vertical>.<calc>.<case>` | `{"for", "calc", "reference": "scipy.stats.ttest_ind", "expected", "got", "tolerance", "pass": bool}` |
| benchmark | `px.exp.brain.bench.<vertical>.<calc>.<backend>.<size>` | `{"for", "backend", "size", "n", "wall_ms_median", "wall_ms_min", "inputs_sha256"}` |
| bracket | `px.exp.brain.bracket.<vertical>.<problem>` | `{"for", "problem", "criteria": [...] (written BEFORE judging), "candidates": [{"branch", "calc", "address"}], "judged": [{"judge", "candidate", "scores": {...}, "note"}], "winner", "refined": bool}` |
| map | `px.exp.brain.map.<vertical>` | `{"for", "built": [addresses], "stubbed": [{"address", "why"}], "next": [{"what", "for"}]}` |
| finding | `proposal.brain.<vertical>.<k>` | `{"for", "kind": "strength" or "friction", "text", "workaround"?, "proposal"?}` |

Calculations are `Calculation("fn.brain.<vertical>.<name>", fn)`: pure over
their inputs, inputs are Parts (dataset dicts) plus `args`, outputs JSON-able.
A Calculation that needs an effect (a clock, a random draw) is `oc.` and takes
it through the effects handle (`args["effects"]`), never `time`/`random` directly.

## Backends: one facade, many engines

`fn.brain.<v>.<name>` takes `args["backend"]`: `"py"` (pure Python, the
reference), `"np"` (numpy), `"sp"` (scipy) and whatever else a vertical builds.
Same inputs, same outputs within `tolerance` (relative 1e-9 unless the oracle
says otherwise). **A backend that changes semantics is a failed backend**: every
backend gets its own oracle Part against the same reference, and a bracket
between backends records speed (benchmark Parts) only among candidates whose
oracles pass.

## Tournaments

For each hard problem (the vertical decides which): 2-3 branches (a Sonnet
each), criteria recorded in the bracket Part BEFORE any judging (correctness by
oracle Parts, speed by benchmark Parts, clarity by lines and docstring), judges
(a Sonnet that did not build) score every candidate, the winner is refined, the
harness stays re-runnable (`python -m experiments.brain.<vertical>.tournament`
or a test that rebuilds the bracket from the candidates). Losers stay in the
store as candidates; nothing is deleted.

## The harness (backend vertical builds it first; task 81)

`harness.py` exports, minimally:

- `Store`: wraps `PxC`; `put(address, value)`, `get`, `save(vertical)` /
  `load_store()` (merge every `store/*.json`), and `run(name, ticks)` that
  builds a `PCR`, runs it with `PcrRun(observe=True)`, writes the record under
  `records/`, and returns the run.
- `dataset(name, for_, columns, rows)` -> address; `synthetic(name, for_, seed, shape, kind)` (the seed is an arg, the draw is numpy's generator inside a pure function of the seed).
- `oracle(store, vertical, calc, case, got, expected, reference, tolerance, for_)` -> writes the oracle Part, returns pass.
- `bench(store, vertical, calc, backend, size, fn, n=7, for_=...)` -> the benchmark Part (median and min of n wall-clock runs; `time.perf_counter` is allowed HERE, in the host, not inside a Calculation).
- `bracket(store, vertical, problem, criteria, candidates, for_)` and `judge(store, vertical, problem, judge, candidate, scores, note)` and `decide(store, vertical, problem)` (winner from the recorded scores, by the recorded criteria).
- `finding(store, vertical, k, kind, text, for_, workaround=None, proposal=None)`.
- `map_part(store, vertical, built, stubbed, next_, for_)`.
- `navigate(store)`: PQL over `px.exp.brain.*` and `proposal.brain.*`: what exists (by kind and vertical), what won, what is unjudged, what is stubbed, the findings. `python -m experiments.brain.map` prints it.

Until the harness lands, verticals prototype their Calculations and oracles as
pure functions with tests, then wire them to the harness after `neat update`.

## Findings

Where the facade carried you: a `strength`. Where it fought (a query PQL can't
express, a store that can't hold a value, an effect a Calculation needs, a
backend that had to change semantics): a `friction` with its `for` (why it
matters), the workaround taken, and the proposal. As Parts, in your vertical's
store, from `harness.finding`. Not prose pages.
